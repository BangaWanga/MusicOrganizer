from flask import Flask, render_template
from ableton import get_tracks_from_projectpath
app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    # path = "tmp/ZugSkizze.als
    path = "bin/sisy21.als"
    tracks = get_tracks_from_projectpath(path)
    for t in tracks:
        print(t)
    return render_template("index.html", tracks=tracks)


def rec_print(node, depth=0, max_depth=10, omit=["FreezeSequencer", "MacroDefaults", "MacroDisplayNames", "MacroColor", "MacroControls", "ExcludeMacroFromRandomization", "ForceDisplayGenericValue"], search_word=None):
    s = depth * "\t"
    for i in node:
        if i.tag in omit:
            continue
        if type(search_word) == str and search_word.lower() in i.tag.lower():
            s += "--->"
        print(s, i.tag, i.attrib)
        if depth < max_depth:
            rec_print(i, depth+1, max_depth, omit)

if __name__ == '__main__':
    app.run()
