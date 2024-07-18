from flask import Flask, render_template, request, current_app
from ableton import how_to_work_with_the_script
app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    tracks = how_to_work_with_the_script("C:/Users/Nicolas/PycharmProjects/MusicOrganizer/tmp/Ohre.als")
    for t in tracks:
        print(t)
    return render_template("index.html", tracks=tracks)


if __name__ == '__main__':
    app.run()
