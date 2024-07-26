import pathlib

from flask import Flask, render_template, request, jsonify
from ableton import how_to_work_with_the_script, Ableton_Project
from files import get_project_paths, project_files_path
from flask_cors import CORS, cross_origin
app = Flask(__name__)

Cors = CORS(app)
# CORS(app, resources={r'/*': {'origins': '*'}}, CORS_SUPPORTS_CREDENTIALS = True)
CORS(app, resources={r'/*': {'origins': '*'}})

app.config['CORS_HEADERS'] = 'Content-Type'
ableton_projects: list[Ableton_Project] = []
project_paths: list[pathlib.Path] = get_project_paths()

print(project_paths)


@app.route('/test')
def test():
    return render_template("vuetest.html")


@app.route("/get_project", methods=["GET"])
def get_project():
    headers = {
        'Content-type': 'application/json' ,
        'Accept': 'application/json'
    }
    response_object = {'status': 'success'}
    print("WOOP")
    return jsonify(response_object)

def load_projects():
    print("LOading Projects")
    for path in project_paths:
        ableton_projects.append(Ableton_Project(path))


@app.route('/')
def hello_world():  # put application's code here
    load_projects()
    return render_template("index.html", paths=project_paths)


@app.route("/project")
def project_view():
    project_id = request.args.get('project_id')
    print(project_id)
    project = ableton_projects[int(project_id)-1]
    return render_template("project_view.html", tracks=project.build_json_object())


if __name__ == '__main__':
    app.run()
