from flask import Flask, render_template
from ableton import get_tracks_from_projectpath
app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    tracks = get_tracks_from_projectpath("C:/Users/Nicolas/PycharmProjects/MusicOrganizer/tmp/Ohre.als")
    for t in tracks:
        print(t)
    return render_template("index.html", tracks=tracks)


if __name__ == '__main__':
    app.run()
