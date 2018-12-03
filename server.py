from flask import *
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
    if survey_codes.find_one(survey=slug, code=code) is None:
        abort(403)
    return code


def invalidate_code(slug, code):
    survey_codes.delete(survey=slug, code=code)


def survey_get(slug):
    survey_row = surveys.find_one(slug=slug)
    if survey_row is None:
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
    if survey_row is None:
        abort(404)
    code = code_access_check(slug)
    print(dict(request.form))
    invalidate_code(slug, code)
    return "sent"


@app.route("/s/<slug>", methods=["GET", "POST"])
def survey(slug):
    if request.method == "GET":
        return survey_get(slug)
    elif request.method == "POST":
        return survey_post(slug)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
