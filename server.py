from flask import *
from functools import wraps
from collections import Counter
from hashlib import sha512
import dataset
import codecs
import json
import secrets

app = Flask(__name__)


db = dataset.connect(
    'sqlite:///data.db', engine_kwargs={"connect_args": {'check_same_thread': False}})
surveys = db["surveys"]
survey_codes = db["survey_codes"]
survey_responses = db["survey_responses"]


with codecs.open("texts.json", "rb", "utf-8") as f:
    app.config["texts"] = json.load(f)

with codecs.open("credentials.json", "rb", "utf-8") as f:
    credentials_hash = json.load(f)


# http://flask.pocoo.org/snippets/8/

def check_auth(username, password):
    if sha512((password + credentials_hash["salt"]).encode()).hexdigest() != credentials_hash["sha512"]:
        return False
    return username == "admin"


def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ---
# http://flask.pocoo.org/snippets/28/

import re

from jinja2 import evalcontextfilter, Markup, escape

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
        for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result

# ---


def code_access_check(slug):
    code = request.args.get("code") or request.args.get("c")
    if not code:
        abort(403, "no_code_found")
    if not survey_codes.find_one(survey=slug, code=code):
        abort(403, "invalid_code")
    return code


def invalidate_code(slug, code):
    survey_codes.delete(survey=slug, code=code)


def survey_get(slug):
    survey_row = surveys.find_one(slug=slug)
    if not survey_row:
        abort(404)
    code = code_access_check(slug)
    return render_template(
        "survey.html",
        code=code,
        title=survey_row["title"],
        description=survey_row["description"],
        questions=json.loads(survey_row["questions"]))


def survey_post(slug):
    survey_row = surveys.find_one(slug=slug)
    if not survey_row:
        abort(404)
    code = code_access_check(slug)
    form = {}
    for question in json.loads(survey_row["questions"]):
        answer = request.form.get("s_" + question["name"])
        if answer:
            form[question["name"]] = answer
        elif question["required"]:
            print(question)
            abort(400)
    survey_responses.insert(dict(survey=slug, response=json.dumps(form)))
    invalidate_code(slug, code)
    return render_template(
        "sent.html", 
        title=survey_row["title"]
    )


@app.route("/s/<slug>", methods=["GET", "POST"])
def survey(slug):
    if request.method == "GET":
        return survey_get(slug)
    elif request.method == "POST":
        return survey_post(slug)


@app.route("/dashboard")
@requires_auth
def dashboard():
    if request.args.get("view"):
        slug = request.args.get("view")
        survey_row = surveys.find_one(slug=slug)
        if not survey_row:
            abort(404)
        resp_count = {}
        for resp in survey_responses.find(survey=slug):
            resp = json.loads(resp["response"])
            for name, value in resp.items():
                resp_count.setdefault(name, Counter())
                resp_count[name][value] += 1
        for name in resp_count:
            resp_count[name] = dict(resp_count[name])
        return render_template(
            "dashboard/view_survey.html", 
            survey=dict(survey_row), 
            responses=resp_count
        )
    return render_template(
        "dashboard/dashboard.html",
        surveys=surveys.all()
    )


def basic_slugify(title):
    slug = ""
    for s in title.lower().replace(" ", "-"):
        if s in "abcdefghijklmnopqrstuvwxyz0123456789-_":
            slug += s
    return slug


@app.route("/dashboard/create_survey", methods=["POST"])
@requires_auth
def create_survey():
    title = request.form["title"]
    slug = basic_slugify(title)
    description = request.form["description"]
    questions = request.form["questions"]
    questions_converted = []
    for question in questions.split("\n"):
        question = question.strip()
        if question != "":
            questions_converted.append({})
            required = question[0] == "*"
            if required:
                question = question[1:]
                question = question.strip()
            q_type = "text-one-line"
            if question[-1] == ")":
                if "(" in question:
                    q_type = "multiple-choice"
                    options = question[question.rfind(
                        "(")+1:question.rfind(")")].split("/")
                    options = [option.strip() for option in options]
                    options = list([{
                        "value": basic_slugify(option), 
                        "name": option
                    } for option in options])
                    questions_converted[-1]["options"] = options
                    question = question[:question.rfind("(")]
            questions_converted[-1]["type"] = q_type
            questions_converted[-1]["title"] = question
            questions_converted[-1]["placeholder"] = question
            questions_converted[-1]["name"] = basic_slugify(question)
            questions_converted[-1]["required"] = required
    question_json = json.dumps(questions_converted)
    surveys.insert(dict(slug=slug, title=title, description=description, questions=question_json))
    return "Successfully created."


def generate_random_sequence(length):
    return "".join(
        [secrets.choice("abcdefghijklmnopqrstuvwxyz1234567890") for i in range(length)])


@app.route("/dashboard/generate_codes")
@requires_auth
def generate_codes():
    survey = request.args.get("survey")
    if not survey:
        abort(400)
    try:
        number_of_codes = int(request.args.get("number_of_codes"))
    except ValueError:
        abort(400)
    except TypeError:
        abort(400)
    codes = [generate_random_sequence(8) for _ in range(number_of_codes)]
    code_rows = [{"survey": survey, "code": code} for code in codes]
    survey_codes.insert_many(list(code_rows))
    return Response(
        "\n".join(codes),
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename={}-codes.csv".format(survey)})


@app.route("/dashboard/reset_survey")
@requires_auth
def reset_survey():
    survey = request.args.get("survey")
    if not survey:
        abort(400)
    if survey != request.args.get("survey_confirm"):
        return "Please confirm that you want to reset the survey.", 400
    survey_responses.delete(survey=survey)
    survey_codes.delete(survey=survey)
    return "Survey {} successfully reset.".format(survey)


@app.route("/legal")
def legal():
    return render_template("legal.html")


@app.errorhandler(403)
def access_denied(error):
    if error.description == "no_code_found":
        return render_template("enter_code.html")
    elif error.description == "invalid_code":
        return render_template("invalid_code.html")
    return error.description


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html")


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
