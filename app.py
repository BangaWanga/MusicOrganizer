import pathlib

from flask import Flask, render_template, request, jsonify
from ableton import how_to_work_with_the_script, Ableton_Project
from files import get_project_paths, PROJECT_FILES_PATH
from flask_cors import CORS, cross_origin
app = Flask(__name__)

Cors = CORS(app)
CORS(app, resources={r'/*': {'origins': '*'}}, CORS_SUPPORTS_CREDENTIALS = True)
#CORS(app, resources={r'/*': {'origins': '*'}})

app.config['CORS_HEADERS'] = 'Content-Type'
ableton_projects: list[Ableton_Project] = []
project_paths: list[pathlib.Path] = get_project_paths()

print(project_paths)
def load_projects():
    print("LOading Projects")
    for path in project_paths:
        ableton_projects.append(Ableton_Project(path))

load_projects()


@app.route('/test')
def test():
    return render_template("vuetest.html")


def parse_str(it):
    return [str(i) for i in it]


@app.route("/get_project_paths", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_projects():

    response_object = {'status': 'success', "projects": [parse_str(project_paths)]}
    print("WOOP Quadrat")
    return response_object


@app.route("/get_project", methods=["POST"])
@cross_origin(supports_credentials=True)
def get_project():
    print("DATA", request.json)
    project_id = request.json["project_id"]
    print("Project ID: ", project_id)
    project = ableton_projects[int(project_id)]

    response_object = {'status': 'success', "headers": project.get_table_headers(), "data": project.generate_display_table()}
    print("WOOP")
    for tr, idx in enumerate(project.generate_display_table()):
        print(idx, tr)
    return response_object




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
