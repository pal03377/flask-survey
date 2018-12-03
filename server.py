from flask import *
import dataset
import json

app = Flask(__name__)


db = dataset.connect(
    'sqlite:///data.db', engine_kwargs={"connect_args": {'check_same_thread': False}})
surveys = db["surveys"]
survey_codes = db["survey_codes"]
survey_responses = db["survey_responses"]


@app.route("/s/<slug>")
def survey(slug):
    survey_row = surveys.find_one(slug=slug)
    if survey_row is None:
        abort(404)
    return render_template(
        "survey.html", 
        title=survey_row["title"], 
        description=survey_row["description"],
        questions=json.loads(survey_row["questions"]))


if __name__ == "__main__":
    app.run(port=5000, debug=True)
