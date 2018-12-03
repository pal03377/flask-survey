from flask import *
from collections import Counter
import dataset
import json

app = Flask(__name__)


db = dataset.connect(
    'sqlite:///data.db', engine_kwargs={"connect_args": {'check_same_thread': False}})
surveys = db["surveys"]
survey_codes = db["survey_codes"]
survey_responses = db["survey_responses"]


def code_access_check(slug):
    code = request.args.get("code") or request.args.get("c")
    if not code:
        abort(403)
    if not survey_codes.find_one(survey=slug, code=code):
        abort(403)
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


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if request.method == "GET":
        return render_template(
            "dashboard/dashboard.html", 
            surveys=surveys.all()
        )
    if "survey_to_view" in request.form:
        slug = request.form.get("survey_to_view")
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


if __name__ == "__main__":
    app.run(port=5000, debug=True)
