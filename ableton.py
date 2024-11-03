from __future__ import annotations
import dataclasses
import datetime
import enum
import pathlib
import typing
import xml.etree.ElementTree as ET
import gzip
from ableton_project_classes import AbletonProjectClass, FloatEvent
import flask
import math
from htmx_model import AbletonProject, AbletonTrack
TMP_DIR = "tmp"
import shutil


class TrackType(enum.Enum):
    midi = 0
    audio = 1
    group = 2

    @staticmethod
    def from_str(s: str):
        if s == "GroupTrack":
            return TrackType.group
        elif s == "AudioTrack":
            return TrackType.audio
        elif s == "MidiTrack":
            return TrackType.midi
        else:
            raise ValueError(f"Unknown track-type {s}")


@dataclasses.dataclass
class Track_Type:
    name: dict
    group_id: str
    track_type: str


class Track:
    @staticmethod
    def plug_ins(track) -> list[str]:
        return [i.attrib["Value"] for i in track.iter("PlugName")]

    @staticmethod
    def track_type(track):
        return track.tag

    @staticmethod
    def group_id(track):
        """
        Returns IDs for all Ableton-groups
        :return:
        :rtype:
        """
        return next(track.iter("TrackGroupId")).attrib["Value"]

    @staticmethod
    def name(track) -> dict:
        return {n.tag: n.attrib for n in next(track.iter("Name"))}


class ProjectInfoXML:
    def __init__(self, root: ET.Element):
        self.tracks = root.find(".//Tracks")
        self.master_track = root.find(".//MasterTrack")
        self.project = root.find(".//Ableton")

        self.track_infos = [self.build_track_info(track) for track in self.tracks]
        self.track_infos.append(self.build_master_track_info())

    def build_tracks_args(self) -> list[AbletonTrack]:
        _tracks = self.track_infos
        # print(_tracks)
        return _tracks

    @staticmethod
    def extract_plugin_info(node: ET.Element):
        plugin_infos = node.findall(".//VstPluginInfo")
        relevant_infos = []
        for plugin_info in plugin_infos:
            vst_version = plugin_info.find("VstVersion")
            plug_name = plugin_info.find("PlugName")
            plug_path = plugin_info.find("Path")
            relevant_infos.append({
                "vst_version": vst_version.attrib["Value"],
                "name": plug_name.attrib["Value"],
                "path": plug_path.attrib["Value"]
            })
        return relevant_infos

    def build_master_track_info(self):
        master_track: ET.Element = self.master_track
        master_envelopes = master_track.findall("AutomationEnvelopes/Envelopes/AutomationEnvelope")
        bpm = None
        bpm_envelope = list(
            # ToDo: Find out why it's a different key in Dex-File. maybe because it is from an older version? -> Indicator for UI
            filter(lambda env: True if env.find("EnvelopeTarget/PointeeId[@Value='8']") is not None else False,
                   master_envelopes))
        if not bpm_envelope:
            bpm_envelope = list(  # Fix for Dex-File
                filter(lambda env: True if env.find("EnvelopeTarget/PointeeId[@Value='497']") is not None else False,
                       master_envelopes))
        if bpm_envelope:
            bpm_envelope = bpm_envelope[0]
            bpm_events: list = bpm_envelope.findall("Automation/Events/FloatEvent")
            apcs = [FloatEvent(elem) for elem in bpm_events]
            if len(apcs) > 1 or not apcs:
                pass
                # raise ValueError("multiple bpms or no bpm")
            else:
                bpm = apcs[0]
        else:
            raise ValueError("No BPM FOUND")
        plug_ins = self.extract_plugin_info(master_track)
        return AbletonTrack(None, "Master", "MasterTrack", -1, "#000000", 0., bpm,  .5, 1., plug_ins, "", True)

    def render_fader(self, value: float, min_val: float, max_val: float, tag: str, sideways=True):
        offset = (50, 50,)
        value_norm = (value - min_val) / (max_val - min_val)
        return flask.render_template("fader.html", offset=offset, value=value_norm, sideways=sideways, tag=tag)

    def render_poti(self, value: float, min_val: float, max_val: float, ):
        offset = (50, 50,)

        r = 40
        value_norm = (value - min_val) / (max_val - min_val)
        a = value_norm * (2 * math.pi / 1)
        line_pos0 = offset
        line_pos1 = (int(offset[0] + r * math.cos(a)), int(offset[1] + r * math.sin(a)),)
        return flask.render_template("poti.html", line_pos0=line_pos0, line_pos1=line_pos1, radius=r, value=value)

    def build_track_info(self, track: ET.Element) -> AbletonTrack:
        track_delay = int(track.find("TrackDelay/Value").attrib["Value"])  # has .attrib["Value"]
        # print("track_delay.attrib: ", track_delay.attrib)
        name = track.find("Name/EffectiveName").attrib["Value"]
        color = track.find("Color").attrib["Value"]
        pan = float(track.find("DeviceChain/Mixer/Pan/Manual").attrib["Value"])
        sends: list = track.findall("DeviceChain/Mixer/Sends/TrackSendHolder/Send")
        # print("SENDS:  ", sends)
        volume = float(track.find("DeviceChain/Mixer/Volume/Manual").attrib["Value"])
        parent_group_id = int(track.find("TrackGroupId").attrib["Value"])  # next(track.iter("TrackGroupId")).attrib["Value"]
        audio_output_routing = track.find("DeviceChain/AudioOutputRouting/Target").attrib["Value"]
        track_type = track.tag
        track_id = int(track.attrib["Id"])
        # print(track, track.tag, track.attrib)
        # ToDo: Extract value right here
        # Create some visual representations and store as <additional_data> to include it as rendered html
        # additional_data = [self.render_fader(value=float(pan.attrib["Value"]), min_val=-1., max_val=1, tag="Pan")]
        is_visible = parent_group_id == -1
        return AbletonTrack(track_id, name, track_type, parent_group_id, color, track_delay, None, pan, volume, self.extract_plugin_info(track), audio_output_routing, is_visible)


class NestedTable:
    def __init__(self, rows: list[dict[str, typing.Any]], project_id: int, ):
        self._rows = rows
        self.expanded_rows = set()
        self.visible_rows = list()
        self.max_depth = 0
        self.init_rows()
        self.project_id = project_id
        self._new_rows = list()
        # self.test_table()

    def pop_new_rows(self):
        tmp = self._new_rows
        self._new_rows = list()
        # print("_new_rows :", len(tmp))
        return tmp

    def init_rows(self):
        if not self._rows:
            raise ValueError("No rows provided")
        self._rows[0].update({"has_children": len(self._rows) > 1, })
        for row_idx in range(len(self._rows)):
            self._rows[row_idx].update({"idx": row_idx})
            self.max_depth = max(self.max_depth, self._rows[row_idx]["depth"])

    def build_new_row_group(self, group_idx: int, rows=None) -> str:
        if not rows:
            new_rows = self.pop_new_rows()
            if not new_rows:
                raise ValueError("No new rows available")
            rows = new_rows
        # print(rows)
        row_templates = [flask.render_template("project_xml_row.html", row=row, project_id=self.project_id,
                                               additionals=row.get("additional_data", None)) for row in rows]
        row_group = flask.render_template("row-group.html", idx=group_idx, rows=row_templates)
        return row_group

    def build_table_template(self) -> str:
        if self.visible_rows:
            rows = None  # [self._rows[idx] for idx in self.visible_rows]
            # rows = [row for row in rows if "text" in row]
        else:
            print("Project INIT")
            # self.toggle_row(0)
            self.visible_rows.append(0)
            rows = [self._rows[0]]
        row_group = 0
        if rows:
            print(f"building template with {len(rows)} rows: ")
        row_group = self.build_new_row_group(row_group, rows)
        template = flask.render_template("project_xml_table.html", row_group=row_group, max_depth=self.max_depth)
        # print(template)
        return template

    def toggle_row(self, idx: int) -> bool:
        # print("toggle row ", idx)
        if not self.has_children(idx):
            # print(idx, self._rows)
            raise ValueError("Cant toggle row ", idx)
        if idx in self.expanded_rows:
            self.collapse_row(idx)
            return False
        else:
            self.expand_row(idx)
            return True

    @property
    def rows(self):
        return self._rows

    @staticmethod
    def is_chield_of(child, parent):
        return child["depth"] == parent["depth"] + 1

    def has_children(self, idx):
        """
        :return: bool = whether row has children
        :rtype:
        """
        return len(self._rows) > idx + 1 and self.is_chield_of(self._rows[idx + 1], self._rows[idx])

    def open_row(self, row_idx):
        raise NotImplemented("This is buggy")
        # open arbitrary row, let the code handle the rest
        row_path = []
        if row_idx in self.visible_rows:  # that means, the row has a parent assigned to it
            raise NotImplemented  # too tired..
        elif 0 > row_idx or row_idx >= len(self._rows):
            raise ValueError("Invalid row", row_idx)
        target_row = self.rows[row_idx]
        # self.visible_rows.append(row_idx)
        # print("TARGET ROW ", target_row)
        for _idx in reversed(range(len(self.rows))[row_idx + 1:]):
            depth = target_row["depth"]
            if self.rows[_idx]["depth"] == depth - 1:
                self.expanded_rows.add(_idx)
                target_row.update(
                    {"parent": _idx, "has_children": True if _idx != row_idx else self.has_children(row_idx)}
                )
                row_path.append(target_row)
            target_row = self.rows[_idx]
            if _idx == 0:
                target_row.update({"parent": None, "has_children": True})
                row_path.append(target_row)
        _new_rows = list(reversed(row_path))
        indices = [r["idx"] for r in _new_rows]
        self._new_rows = _new_rows
        self.visible_rows.extend(indices)
        return list(reversed(row_path))


    def test_table(self):
        for row_idx, row in enumerate(self.rows):
            if self.has_children(row_idx):
                self.expand_row(row_idx)
        invisible_rows = set(range(len(self.rows))) - set(self.visible_rows)
        if invisible_rows:
            print("INVISIBLE_ROWS: ", invisible_rows)

    def expand_row(self, idx: int):
        # print("expand row ", idx)
        depth = self.rows[idx]["depth"]
        self.expanded_rows.add(idx)
        self._rows[idx].update({"is_expanded": True})
        self._new_rows.append(self._rows[idx])
        for row_idx in range(idx + 1, len(self._rows)):
            row = self.rows[row_idx]
            row_depth = row["depth"]
            if row_depth == depth + 1:
                self.rows[row_idx].update({"parent": idx, "has_children": self.has_children(row_idx)})
                self._new_rows.append(row)
                self.visible_rows.append(row_idx)
            elif row_depth <= depth:
                # print(idx, row_idx, self.rows[row_idx])
                break
        # print(f"init table with {len(self._new_rows)} rows: {[row['idx'] for row in self._new_rows]}")

    def collapse_row(self, idx: int, nested: bool = False):
        # print("Collapse row ", idx, nested, len(self.visible_rows))
        self.expanded_rows.remove(idx)
        expanded_children = [row_idx for row_idx in self.expanded_rows if row_idx > 0 and
                             self._rows[row_idx]["parent"] == idx]
        for child_idx in expanded_children:
            self.collapse_row(child_idx, nested=True)
        if nested:
            self.visible_rows.remove(idx)
        self._rows[idx].update({"is_expanded": False})
        depth = self._rows[idx]["depth"]
        for row_idx in self.visible_rows:  # ToDo: Only iterate over visible rows
            if self._rows[row_idx]["depth"] <= depth:
                break
            parent = self._rows[row_idx].get("parent", None)
            # print("collapse, ", idx, row_idx, parent, row_idx in self.expanded_rows, row_idx in self.visible_rows)
            if parent is not None and parent == idx:
                if row_idx not in self.visible_rows:
                    raise ValueError(f"{row_idx}: {self._rows[row_idx]} is not in visible rows. Nested:")
                self.visible_rows.remove(row_idx)
                self._rows[row_idx].update({"is_expanded": False})
        if not nested:
            self._new_rows.append(self._rows[idx])

    @staticmethod
    def from_ableton_project_list(projects: list[Ableton_Project], page_link: str, nested_table_id: int):
        rows = [
            {
                "tag": "Ableton Projects",
                "idx": 0,
                "value": "",
                "depth": 0,
            }
        ]
        for _idx, project in enumerate(projects):
            row = NestedTable.convert_ableton_project_to_row(project=project, idx=_idx + 1,
                                                             page_link=page_link + f"?project_id={_idx}",
                                                             depth=1, parent=0, has_children=False)
            rows.append(row)
        return NestedTable(rows, nested_table_id)

    @staticmethod
    def convert_ableton_project_to_row(project: Ableton_Project, idx: int, page_link: str, depth: int, parent: int,
                                       has_children: bool):
        proj_path = str(project.project_path).replace("\\", "/")
        return {
            "idx": idx,
            "tag": proj_path,
            "value": proj_path,
            "page_link": page_link,
            "depth": depth,
            "parent": parent,
            "has_children": has_children
        }


class Ableton_Project:
    def __init__(self, project_path: pathlib.Path, ):
        self.project_path = project_path
        self.exports: list[pathlib.Path] = []
        self.project_files: list[pathlib.Path] = []
        self.tmp_path = "tmp"
        self.tree = None
        self.root = None
        # self.scan_project_dir()
        self.is_loaded = False
        self.is_cached = False
        self.last_modified: typing.Optional[datetime.datetime] = None
        from files import get_user_data_for_path
        self.meta = {"contains_vst2": None}  # messages that may be shown in project overview
        user_data = get_user_data_for_path(project_path)
        self.project_info: ProjectInfoXML = None
        if user_data:
            project_info, _project_info_path = user_data
            self.is_cached = True
            self.last_modified = project_info["last_modified"]

    def update_contains_vst2(self, plug_ins: list[dict]):
        versions = [plug["vst_version"] for plug in plug_ins]
        contains_vst2 = any([v.startswith("2") for v in versions])
        self.meta["contains_vst2"] = contains_vst2 or self.meta["contains_vst2"]
    @property
    def model(self):
        last_modified = self.last_modified
        if last_modified:
            last_modified = last_modified.strftime("%Y-%m-%d %H:%M:%S")
        return AbletonProject(str(self.project_path), last_modified, self.is_loaded, self.is_cached, self.meta)

    def build_project_info_object(self) -> ProjectInfoXML:
        self.project_info = ProjectInfoXML(self.root)

    def __str__(self):
        return f"\nAbletonProject\nproj-path: {self.project_path}\nexports: {self.exports}\nproj-files: {self.project_files}"

    def scan_project_dir(self):
        for directory in self.project_path.glob('**'):
            for item in directory.iterdir():
                if item.is_file():
                    # filename = item.stem
                    if item.suffix == ".als":
                        if item.parent == self.project_path:
                            self.project_files.append(item)

    def scan_export_dir(self, keywords: list[str]):
        raise NotImplemented

    def load_ableton_project(self):
        from files import load_ableton_project
        tree, last_modified = load_ableton_project(self.project_path)
        self.tree = tree
        self.last_modified = last_modified
        if self.tree is None:
            self.is_loaded = False
            return False
        self.root = self.tree.getroot()
        self.is_loaded = True

        return True
        # copy .als file, extract it and read
        tmp_path = pathlib.Path(TMP_DIR).joinpath(
            str(path.stem) + "-tmp" + ".gz"  # str(path.stem)[-len(path.suffix):]
        )

        tmp_path_extract = pathlib.Path(TMP_DIR).joinpath(
            str(path.stem) + "_tmp_extract_.xml"  # + str(path.stem)[-len(path.suffix):]
        )
        shutil.copyfile(path, tmp_path)

        with gzip.open(tmp_path, 'rb') as f:
            file_content = f.read()
            with open(tmp_path_extract, 'w') as ff:
                s = str(file_content)[2:-1].replace("'", '"').replace("<?", "<").replace("?>", ">") + "</xml>"
                ff.write(s)
        self.tree = ET.parse(tmp_path_extract)
        self.root = self.tree.getroot()

    def iter_print(self,
                   search_list: typing.Optional[typing.Iterable] = None,
                   exclude_list: typing.Iterable = ("ParameterList",),
                   search_for_occurence: bool = False):
        if exclude_list is None:
            exclude_list = set()
        if search_list is None:
            search_list = set()
        self._iter_print(self.root, 0, exclude_list, search_list, search_for_occurence)

    @staticmethod
    def _iter_print(node, depth: int, exclude_list: typing.Iterable, search_list: typing.Iterable,
                    search_for_occurence: bool):
        for i in node:
            if search_for_occurence:
                if any([i.tag in sl for sl in search_list]) or any([i.tag in el for el in exclude_list]):
                    continue
            else:
                if i.tag not in search_list or i.tag in exclude_list:
                    continue

            # print("\t\t" * depth, i.tag, i.attrib, depth)
            if len(i) > 0:
                Ableton_Project._iter_print(i, depth + 1, search_list, exclude_list, search_for_occurence)

    def rec_search(self,
                   search_word: str = "",
                   exclude_list: typing.Iterable = ("ParameterList",),
                   search_for_occurence: bool = False):
        if exclude_list is None:
            exclude_list = set()

        if search_word:
            print("Searching for ", search_word)
            node = self.root.findall(search_word)
        else:
            node = self.root
        return self._rec_search(node, 0, exclude_list, set(), search_for_occurence)

    @staticmethod
    def _rec_search(node, depth: int, exclude_list: typing.Iterable, search_list: typing.Iterable,
                    search_for_occurence: bool):
        result = []

        for i in node:
            if search_for_occurence:
                if any([i.tag in sl for sl in search_list]) or any([i.tag in el for el in exclude_list]):
                    continue
            else:
                if i.tag not in search_list or i.tag in exclude_list:
                    continue

            r = {"depth": depth, "tag": i.tag, }
            if "Value" in i.attrib:
                r["value"] = i.attrib["Value"]

            text, tail = i.text, i.tail
            text, tail = (prop.replace("\\r", "").replace("\\n", "").replace("\\t", "") if prop else None for prop in
                          (text, tail,))
            if text:
                # print("GOT A text for ", i)
                r["text"] = "MYTEXT " + str(i.text)[:100]
            if tail:
                # print("GOT A tail ", tail)
                r["tail"] = tail
            result.append(r)
            if len(i) > 0:
                result += Ableton_Project._rec_search(i, depth + 1, exclude_list, search_list, search_for_occurence)
        return result



"""
def some_interesting_code():
    rows: list
    import itertools
    from_iter = itertools.chain.from_iterable
    
    keys = set(from_iter([i.keys() for i in rows])) # all possible keys for the dicts in rows
    # returns: {'value', 'depth', 'tag'}
    
    # all possible types for "value"-attributes for rows. None can mean that "value" is not a valid key
    values = set([type(i["value"]) if "value" in i else None for i in rows])    
    # returns: {None, <class 'dict'>, <class 'str'>}
"""

if __name__ == "__main__":
    from files import get_project_paths

    project_paths = get_project_paths()
    if project_paths:
        path = project_paths[0]
        tracks = how_to_work_with_the_script(path)
        ableton_project = Ableton_Project(pathlib.Path(path))
        # Find tags in project with iter_print-method
        ableton_project.iter_print(search_list=("Session",), search_for_occurence=True)
    # interesting row: 177144 (Take Lanes. There is no value  
    print("No paths found")

    # ToDo: Make abstract table
    # ToDo: make redirect to unique url for every table (i.e. project-table/0)
    # ToDo: save state
