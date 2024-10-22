import pathlib
import sys
import typing

from files import get_project_paths, PROJECT_FILES_PATH, init, set_project_path
from flask_cors import CORS, cross_origin
import flask
from flask import Flask, render_template, request, jsonify
import time

from ableton import Ableton_Project, NestedTable
from flask_socketio import SocketIO, emit
app = Flask(__name__)

Cors = CORS(app)
CORS(app, resources={r'/*': {'origins': '*'}}, CORS_SUPPORTS_CREDENTIALS=True)
# CORS(app, resources={r'/*': {'origins': '*'}})

app.config['CORS_HEADERS'] = 'Content-Type'
socketio = SocketIO(app)
init()

XML_MODE = True
project_table_url = "/project_table"
project_table_xml_url = "/project_table_xml"
if XML_MODE:
    project_table_url = "/project_table_"
    project_table_xml_url = "/project_table"

ableton_projects: list[Ableton_Project] = []
project_paths: list[pathlib.Path] = get_project_paths()
nested_tables: dict[int, NestedTable] = dict()
bookmarks = set()
ENABLE_MIDI = False
if ENABLE_MIDI:
    from midi import get_midi_outs, Midi_Port, MIDI_Signal, MIDI_Type

    midi_port: Midi_Port = typing.Optional[None]
port = None
current_table: typing.Optional[int] = None
file_pick_thread = None

def load_projects():
    global ableton_projects
    ableton_projects = []
    for path in project_paths:
        ableton_projects.append(Ableton_Project(path))


load_projects()
import tkinter as tk
from tkinter import filedialog


def OpenFileDialog():
    root = tk.Tk()
    root.withdraw()
    root.focus_set()
    file_path = filedialog.askdirectory()
    set_project_path(file_path)


@app.route('/reload_projects')
def reload_projects():
    load_projects()


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


def get_project(project_id: int):
    global ableton_projects
    assert project_id in range(len(ableton_projects))
    return ableton_projects[project_id]


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


@app.route("/send_midi_signal", methods=["Get", "POST"])
@cross_origin(headers=['Content-Type'])
def send_midi_signal():
    global midi_port
    print("Sending Tone ", request.args, request.form, request.values)
    note = request.form.get("note", None)
    velocity = request.form.get("velocity", None)
    assert note is not None and note.isnumeric()
    assert velocity is not None and velocity.isnumeric()
    note, velocity = int(note), int(velocity)
    assert 0 < note < 128
    assert 0 < velocity < 128

    channel = 0
    note_on = MIDI_Type.Note_On(channel, note, velocity)
    note_off = MIDI_Type.Note_Off(channel, note, velocity)
    midi_port.send(note_on, )
    time.sleep(0.5)
    midi_port.send(note_off,)
    return {"status": 200}


@app.route("/midi_device", methods=["GET"])
def midi_device():
    global midi_port, port
    _port = request.args.get('port', None)
    assert _port and _port.isnumeric()
    if port is None or port != _port:
        port = int(_port)
        midi_port = Midi_Port(port)
    return flask.render_template("midi_device.html", name=get_midi_outs()[port])


@app.route("/midi_devices", methods=["GET"])
def midi_devices():
    return flask.render_template("midi_devices.html", midi_outs=get_midi_outs())


@app.route(project_table_url, methods=["GET"])
def project_table():
    global nested_tables, current_table, bookmarks
    bookmarks = set()
    project_id = request.args.get('project_id', None)
    search_word = request.args.get('search_word', None)
    # search_word = ".//Buffer"
    if str(project_id).isnumeric():
        project_id = int(project_id)
    else:
        raise ValueError(f"{project_id} is not a valid project_id")
    project = get_project(project_id=project_id)
    if not project.is_loaded:
        success = project.load_ableton_project()
        if not success:
            raise ValueError("Error when opening project: ", project.project_path)
    project_info = project.build_project_info_object()
    rows = project_info.build_render_info()
    nt = NestedTable(rows, project_id)  # ToDO: Does NestedTable really need id?
    nested_tables[project_id] = nt
    # print("Found ", len(rows), " rows with size ", sys.getsizeof(rows))
    current_table = project_id
    _template = nt.build_table_template()
    return _template    # render_template("project_xml_table.html", rows=rows[:1000])


@app.route(project_table_xml_url, methods=["GET"])
def project_table_xml():

    global nested_tables, current_table, bookmarks
    bookmarks = set()
    project_id = request.args.get('project_id', None)
    search_word = request.args.get('search_word', None)
    # search_word = ".//Buffer"
    if str(project_id).isnumeric():
        project_id = int(project_id)
    else:
        raise ValueError(f"{project_id} is not a valid project_id")

    if project_id in nested_tables and False:   # Deactivated persistent projects. table gets rebuilt every time
        nt: NestedTable = nested_tables[project_id]
        current_table = project_id
        return nt.build_table_template()
    else:
        rows = project_search(search_word, project_id)
        nt = NestedTable(rows, project_id)
        # nt.open_row(70248)
        nested_tables[project_id] = nt
        # print("Found ", len(rows), " rows with size ", sys.getsizeof(rows))
        current_table = project_id
        _template = nt.build_table_template()
        return _template # render_template("project_xml_table.html", rows=rows[:1000])


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
    # print(f"is_expanded: {is_expanded}. Added rows for row {row_idx}: {len(row_group)}", )
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
    print("WOOP Quadrat")
    return response_object


@app.route("/get_project_depr", methods=["POST"])
@cross_origin(supports_credentials=True)
def get_project_depr():
    project_id = request.json["project_id"]
    project = ableton_projects[int(project_id)]

    response_object = {'status': 'success', "headers": project.get_table_headers(), "data": project.generate_display_table()}
    for tr, idx in enumerate(project.generate_display_table()):
        print(idx, tr)
    return response_object


@app.route('/project_paths', methods=["GET"])
def add_project_paths():
    # print("add_project_paths ", request.is_json, request.args, request.data, request.files)
    import multiprocessing
    global file_pick_thread
    file_pick_thread = multiprocessing.Process(target=OpenFileDialog, args=tuple())
    file_pick_thread.start()
    return flask.render_template("project_selection.html", )

@app.route('/')
def index():  # put application's code here
    load_projects()
    global ableton_projects, nested_tables
    nt_id = len(nested_tables)
    nt = NestedTable.from_ableton_project_list(ableton_projects, page_link="project_table", nested_table_id=nt_id)
    nested_tables[nt_id] = nt
    table_template = nt.build_table_template()
    return render_template("index.html", paths=project_paths, table_template=table_template)


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
    print("Sock")
    socketio.run(app)
