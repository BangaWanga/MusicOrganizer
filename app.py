import pathlib
import sys
from flask import Flask, render_template, request, jsonify
from ableton import how_to_work_with_the_script, Ableton_Project, NestedTable
from files import get_project_paths, PROJECT_FILES_PATH
from flask_cors import CORS, cross_origin
app = Flask(__name__)

Cors = CORS(app)
CORS(app, resources={r'/*': {'origins': '*'}}, CORS_SUPPORTS_CREDENTIALS=True)
#CORS(app, resources={r'/*': {'origins': '*'}})

app.config['CORS_HEADERS'] = 'Content-Type'
ableton_projects: list[Ableton_Project] = []
project_paths: list[pathlib.Path] = get_project_paths()
nested_tables: dict[int, NestedTable] = dict()
print(project_paths)

current_table = None
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


def project_search(search_word: str = None, project_id: int = None):
    if project_id is None:
        return {'status': 'error, no project_id provided'}
    search_words = {}
    if search_word:
        search_words = {search_word}
        print("search_words ", search_words)
    project = ableton_projects[project_id]
    rows = project.rec_search(search_list=search_words, search_for_occurence=True)
    return rows


@app.route("/project_table", methods=["GET"])
def project_table():
    global nested_tables, current_table
    project_id = request.args.get('project_id', None)
    search_word = request.args.get('search_word', None)
    if str(project_id).isnumeric():
        project_id = int(project_id)
    else:
        raise ValueError(f"{project_id} is not a valid project_id")

    if project_id in nested_tables and False:
        nt: NestedTable = nested_tables[project_id]
        current_table = project_id
        return nt.build_table_template()

    else:
        rows = project_search(search_word, project_id)
        nt = NestedTable(rows, project_id)
        nested_tables[project_id] = nt
        print("Found ", len(rows), " rows with size ", sys.getsizeof(rows))
        current_table = project_id
        return nt.build_table_template() # render_template("project_table.html", rows=rows[:1000])


@app.route("/toggle_row", methods=["GET"])
@cross_origin(supports_credentials=True)
def toggle_row():
    row_idx = request.args.get('row', None)
    project_id = request.args.get('project_id', None)
    if not str(project_id).isnumeric() or (0 < int(project_id) >= len(nested_tables)):
        raise ValueError(f"{project_id} is not a valid project-id for {len(nested_tables)} projects")
    nt = nested_tables[int(project_id)]
    if not str(row_idx).isnumeric() or (0 < int(row_idx) >= len(nt.rows)):
        raise ValueError(f"{row_idx} is not a valid row-idx")

    project_id = int(project_id)
    row_idx = int(row_idx)
    nt = nested_tables[project_id]
    print("Before toggle row")
    is_expanded = nt.toggle_row(row_idx)
    row_group = nt.build_new_row_group(row_idx)
    print(f"is_expanded: {is_expanded}. Added rows for row {row_idx}: {len(row_group)}", )
    return row_group


@app.route("/get_project_search", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_project_search():
    print("get_project_search ", request.args)
    project_id = request.args.get('project_id', None)
    search_word = request.args.get('search_word', None)
    if str(project_id).isnumeric():
        project_id = int(project_id)
    else:
        raise ValueError(f"{project_id} is not a valid project_id")

    rows = project_search(search_word, project_id)
    nt = NestedTable(rows, project_id)
    nested_tables[project_id] = nt
    print("Found ", len(rows), " rows with size ", sys.getsizeof(rows))
    response_object = {'status': 'success', "rows": rows}
    return response_object


@app.route("/get_project_paths", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_projects():

    response_object = {'status': 'success', "projects": [parse_str(project_paths)]}
    print("WOOP Quadrat")
    return response_object


@app.route("/get_project", methods=["POST"])
@cross_origin(supports_credentials=True)
def get_project():
    project_id = request.json["project_id"]
    project = ableton_projects[int(project_id)]

    response_object = {'status': 'success', "headers": project.get_table_headers(), "data": project.generate_display_table()}
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


@app.route("/system")
def system_view():
    project_id = request.args.get('project_id')
    print(project_id)
    project = ableton_projects[int(project_id)-1]
    return render_template("project_view.html", tracks=project.build_json_object())




if __name__ == '__main__':
    app.run()
