from flask import *

app = Flask(__name__)

title = "Survey Test"

description = "This is just a simple test."

questions = [
    {
        "type": "text-one-line", 
        "title": "Say something.", 
        "placeholder": "Hint: Lorem ipsum", 
        "name": "test1"
    }, 
    {
        "type": "text-one-line", 
        "title": "Say something again.",
        "placeholder": "Hint: Dolor sit", 
        "name": "test2"
    },
    {
        "type": "multiple-choice", 
        "title": "When will this project be completed?",
        "placeholder": "Multiple choice question", 
        "name": "test3", 
        "options": ["today", "tomorrow", "in 3 days", "next week", "at some point in time"]
    }
]

@app.route("/")
def index():
    return render_template("survey.html", title=title, description=description, questions=questions)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
