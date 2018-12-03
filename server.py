from flask import *

app = Flask(__name__)

questions = [
    {
        "type": "text-one-line", 
        "question": "Sag mal was.", 
        "placeholder": "Tipp: Lorem ipsum", 
        "name": "test1"
    }, 
    {
        "type": "text-one-line", 
        "question": "Sag mal noch was.", 
        "placeholder": "Tipp: Dolor sit", 
        "name": "test2"
    }
]

@app.route("/")
def index():
    return render_template("survey.html", questions=questions)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
