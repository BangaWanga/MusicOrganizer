import pathlib
import sys
import typing

from files import get_project_paths, PROJECT_FILES_PATH, init, set_project_path
from flask_cors import CORS, cross_origin
import flask
from flask import Flask, render_template, request, jsonify
import time
from htmx_model import AbletonProjectTable, AbletonProject, AbletonProjectOverview

from ableton import Ableton_Project, NestedTable, ProjectInfoXML
import webbrowser
app = Flask(__name__)
Cors = CORS(app)
CORS(app, resources={r'/*': {'origins': '*'}}, CORS_SUPPORTS_CREDENTIALS=True)

app.config['CORS_HEADERS'] = 'Content-Type'
init()

project_table_url = "/project_table"
project_table_xml_url = "/project_table_xml"

visible_rows = []
ableton_projects: list[Ableton_Project] = []

project_paths: list[pathlib.Path] = get_project_paths()
nested_tables: dict[int, NestedTable] = dict()
bookmarks = set()


port = None
current_table: typing.Optional[int] = None
file_pick_proc = None


webbrowser.open("http://localhost:5000")


def load_projects():
    print("LOAD ABLETON PROJECTS")
    global ableton_projects, project_paths
    ableton_projects = []
    for path in project_paths:
        print(path)
        ableton_projects.append(Ableton_Project(path))


load_projects()
import tkinter as tk
from tkinter import filedialog

def reload_projects():
    global project_paths, current_table, nested_tables
    current_table = None
    nested_tables = dict()
    print("RELOAD PROJECTS")
    project_paths = get_project_paths()
    load_projects()
    #  load_projects()

def OpenFileDialog():
    root = tk.Tk()
    root.withdraw()
    root.focus_set()
    file_path = filedialog.askdirectory()
    if file_path:
        set_project_path(file_path)
    else:
        print("nofp")

@app.route('/reload')
def reload_projects_endpoint():
    load_projects()
    return flask.redirect("/")


@app.route('/test')
def test():
    return render_template("vuetest.html")


def parse_str(it):
    return [str(i) for i in it]


def project_search(search_word: str = "", project_id: int = None):
    if project_id is None:
        return {'status': 'error, no project_id provided'}
    project = ableton_projects[project_id]
    print("project.is_loaded: ", project.is_loaded)
    if not project.is_loaded:
        success = project.load_ableton_project()
        if not success:
            raise ValueError("Error when opening project: ", project.project_path)
    rows = project.rec_search(search_word=search_word, search_for_occurence=True)
    return rows


def load_all_projects():
    for project_idx in range(len(ableton_projects)):
        try:
            _ = get_project(project_idx)
        except ValueError as e:
            print("Failed loading project: ", e)


def get_project(project_id: int) -> Ableton_Project:
    global ableton_projects
    assert project_id in range(len(ableton_projects))
    project = ableton_projects[project_id]
    if not project.is_loaded:
        success = project.load_ableton_project()
        ableton_projects[project_id] = project  # maybe do all of this in a <load-project>-function?
        if not success:
            raise ValueError("Error when opening project: ", project.project_path)
    project.build_project_info_object()
    return project


@app.route("/load-selected-projects", methods=["GET"])
def load_selected_projects():
    load_all_projects()
    resp = flask.make_response("status: ok")
    resp.headers["HX-Refresh"] = "true"
    return resp


@app.route("/toggle_table_mode", methods=["GET"])
def toggle_table_mode():
    global XML_MODE
    XML_MODE = not XML_MODE
    return {"status": 200}


def toggle_track(project, parent_group_id, collapse: bool, force_invisible=False):
    for i in range(len(project.project_info.track_infos)):
        if project.project_info.track_infos[i].parent_group_id == parent_group_id:
            if force_invisible:
                project.project_info.track_infos[i].is_visible = False
            else:
                project.project_info.track_infos[i].is_visible = not project.project_info.track_infos[i].is_visible
            if collapse and project.project_info.track_infos[i].track_type == "GroupTrack":
                project = toggle_track(project, project.project_info.track_infos[i].track_id, collapse, True)
    return project

@app.route("/toggle-group-track", methods=["GET"])
def toggle_group_track():
    global ableton_projects
    project_id = request.args.get('project_idx', None)
    track_id = request.args.get('track_id', None)

    if track_id is None or project_id is None:
        raise ValueError("Parameter missing")
    elif not track_id.isdigit() or not track_id.isdigit():
        raise ValueError("Invalid parameter")
    track_id = int(track_id)
    project_id = int(project_id)
    project = ableton_projects[project_id]
    if project.project_info.track_infos:
        collapse = project.project_info.track_infos[0].is_visible
        project = toggle_track(project, track_id, collapse)

    proj_table = AbletonProjectTable(ableton_project=project.model, tracks=project.project_info.build_tracks_args(), project_idx=project_id)
    return proj_table.render()


@app.route("/bookmark", methods=["GET"])
def bookmark():
    tag = request.args.get('tag', None)
    idx = request.args.get('idx', None)
    global current_table, bookmarks
    if idx in bookmarks or tag is not None and (idx, tag,) in bookmarks:
        raise ValueError("Cant bookmark item again")
    if tag is None:
        bookmarks.add(idx)
    else:
        bookmarks.add((idx, tag,))
    if current_table is None:
        raise ValueError("Invalid current_table", current_table)
    if str(idx).isnumeric():
        idx = int(idx)
    else:
        raise ValueError(f"{idx} is not a valid row-index for bookmark with tag {tag}")

    row = nested_tables[current_table].rows[idx]
    value = row.get("value", None)
    if value and tag:
        value = value[tag]

    return render_template("bookmark.html", tag=tag, row=row, value=value)



@app.route(project_table_url, methods=["GET"])
def project_table_new():
    global nested_tables, current_table, bookmarks, ableton_projects
    bookmarks = set()
    project_id = request.args.get('project_id', None)
    search_word = request.args.get('search_word', None)
    # search_word = ".//Buffer"
    if str(project_id).isnumeric():
        project_id = int(project_id)
    else:
        raise ValueError(f"{project_id} is not a valid project_id")
    project = get_project(project_id=project_id)
    """
    nt = NestedTable(rows, project_id)  # ToDO: Does NestedTable really need id?
    nested_tables[project_id] = nt
    # print("Found ", len(rows), " rows with size ", sys.getsizeof(rows))
    current_table = project_id
    _template = nt.build_table_template()
    return _template  # render_template("project_xml_table.html", rows=rows[:1000])
    """
    #print("project_info.build_tracks_args(): ", project_info.build_tracks_args())
    proj_table = AbletonProjectTable(ableton_project=project.model, tracks=project.project_info.build_tracks_args(), project_idx=project_id)
    # AbletonProject(str(project.project_path), project.last_modified, project.is_loaded,
    #                                   project.is_cached, project.meta),
    return proj_table.render()


@app.route("/toggle_row", methods=["GET"])
@cross_origin(supports_credentials=True)
def toggle_row():
    row_idx = request.args.get('row', None)
    project_id = request.args.get('project_id', None)
    if not str(project_id).isnumeric() or int(project_id) not in nested_tables:
        raise ValueError(f"{project_id} is not a valid project-id for {len(nested_tables)} projects")
    if int(project_id) not in nested_tables:
        return flask.redirect(flask.url_for('.project_table', project_id=project_id))
    nt = nested_tables[int(project_id)]
    if not str(row_idx).isnumeric() or (0 < int(row_idx) >= len(nt.rows)):
        raise ValueError(f"{row_idx} is not a valid row-idx")

    project_id = int(project_id)
    row_idx = int(row_idx)
    nt = nested_tables[project_id]
    is_expanded = nt.toggle_row(row_idx)
    row_group = nt.build_new_row_group(row_idx)
    return row_group


@app.route("/get_project_search", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_project_search():
    project_id = request.args.get('project_id', None)
    search_word = request.args.get('search_word', None)
    if str(project_id).isnumeric():
        project_id = int(project_id)
    else:
        raise ValueError(f"{project_id} is not a valid project_id")

    rows = project_search(search_word, project_id)
    nt = NestedTable(rows, project_id)
    nested_tables[project_id] = nt
    response_object = {'status': 'success', "rows": rows}
    return response_object


@app.route("/get_project_paths", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_projects():
    response_object = {'status': 'success', "projects": [parse_str(project_paths)]}
    return response_object


@app.route('/project_paths', methods=["GET",  "POST"])
def add_project_paths():
    # print("add_project_paths ", request.is_json, request.args, request.data, request.files)
    import multiprocessing
    global file_pick_proc
    file_pick_proc = multiprocessing.Process(target=OpenFileDialog, args=tuple())
    file_pick_proc.start()
    file_pick_proc.join()
    print("After JOIN")
    init()
    reload_projects()
    resp = flask.make_response("status: ok")
    resp.headers["HX-Refresh"] = "true"
    return resp


@app.route('/')
def index():  # put application's code here
    # load_projects()
    global ableton_projects, nested_tables
    nt_id = len(nested_tables)
    # print("OUR BASE: ", ableton_projects)
    nt = NestedTable.from_ableton_project_list(ableton_projects, page_link="project_table", nested_table_id=nt_id)
    nested_tables[nt_id] = nt
    proj_tables = []
    for project in ableton_projects:
        if project.is_loaded:
            project.build_project_info_object()
            # print("project_info.build_tracks_args(): ", project_info.build_tracks_args())
            tracks = project.project_info.build_tracks_args()
            for track in tracks:
                project.update_contains_vst2(track.plug_ins)
        proj_tables.append(project.model)   # AbletonProject(str(project.project_path), project.last_modified, project.is_loaded, project.is_cached))
    proj_overview_table = AbletonProjectOverview(ableton_projects=proj_tables)
    table_template = proj_overview_table.render()
    return render_template("index.html", paths=project_paths, table_template=table_template)



