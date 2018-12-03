from flask import *

app = Flask(__name__)

questions = [
    {
        "type": "text-one-line", 
        "title": "Sag mal was.", 
        "placeholder": "Tipp: Lorem ipsum", 
        "name": "test1"
    }, 
    {
        "type": "text-one-line", 
        "title": "Sag mal noch was.",
        "placeholder": "Tipp: Dolor sit", 
        "name": "test2"
    },
    {
        "type": "multiple-choice", 
        "title": "Wann wird dieses Projekt fertig?",
        "placeholder": "Auswahlfrage", 
        "name": "test3", 
        "options": ["heute", "morgen", "in 3 Tagen", "nächste Woche", "irgendwann"]
    }
]

@app.route("/")
def index():
    return render_template("survey.html", questions=questions)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
