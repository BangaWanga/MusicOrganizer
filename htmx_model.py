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

    track_delay: int
    pan: float
    volume: float
    plug_ins: list[dict[str, str]]
    audio_output_routing: str


@dataclasses.dataclass
class AbletonProject:
    project_path: str
    last_change: str    # ToDo: maybe solve with timestamp
    is_loaded: bool


class AbletonProjectTable(HTMX_Model):
    xml_path = "htmx/ableton_project_table.html"

    def __init__(self, ableton_project: AbletonProject, tracks: list[AbletonTrack]):
        ableton_project = ableton_project.__dict__
        tracks = [track.__dict__ for track in tracks]
        header = AbletonTrack.__annotations__.keys()
        super().__init__(ableton_project=ableton_project, tracks=tracks, header=header)
