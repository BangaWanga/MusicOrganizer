import dataclasses

import flask


class HTMX_Model:
    xml_path: str = ""

    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def render(self):
        print("RENDER: ", self._kwargs)
        return flask.render_template(self.xml_path, **self._kwargs)


@dataclasses.dataclass
class AbletonTrack:
    track_id: int
    name: str
    track_type: str
    parent_group_id: int
    color: str

    bpm: float
    track_delay: float
    pan: float
    volume: float
    plug_ins: list[dict[str, str]]
    audio_output_routing: str
    is_visible: bool


@dataclasses.dataclass
class AbletonProject:
    project_path: str
    last_modified: str    # ToDo: maybe solve with timestamp
    # last_access: str
    is_loaded: bool
    is_cached: bool
    meta: dict

    # ToDo: get last_modified from cached file


class AbletonProjectTable(HTMX_Model):
    xml_path = "htmx/ableton_project_table.html"

    def __init__(self, ableton_project: AbletonProject, tracks: list[AbletonTrack], project_idx: int):
        ableton_project = ableton_project.__dict__
        tracks = [track.__dict__ for track in tracks]
        header = AbletonTrack.__annotations__.keys()
        super().__init__(ableton_project=ableton_project, tracks=tracks, header=header, project_idx=project_idx)


class AbletonProjectOverview(HTMX_Model):
    xml_path = "htmx/ableton_project_overview.html"

    def __init__(self, ableton_projects: list[AbletonProject]):
        ableton_projects = [project.__dict__ for project in ableton_projects]
        header = AbletonProject.__annotations__.keys() - {"meta"}
        print(ableton_projects)
        super().__init__(ableton_projects=ableton_projects, header=header)
