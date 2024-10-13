from __future__ import annotations
import dataclasses
import enum
import os.path
import pathlib
import typing
import xml.etree.ElementTree as ET
import gzip
from ableton_project_classes import AbletonProjectClass, FloatEvent
import flask
import math

TMP_DIR = "tmp"


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
        return [i.attrib["Value"] for i in track.iter("PlugName") ]

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


@dataclasses.dataclass
class Track_Info:
    type: str
    track_id: str
    group_id: str
    name: dict
    sub_tracks: list
    PlugIns: list[str]
    is_toggled: bool
    depth: int

    def get_row_data(self, exclude_fields: tuple = ("sub_tracks" ,)):
        # print("name: ", self.name)
        print("plugIns: ", self.PlugIns)

        base_dict = self.__dict__.copy() # [self.type, self.track_id, self.name["EffectiveName"]["Value"], str(self.PlugIns), self.is_toggled]
        headers = self.get_headers()
        base_dict["name"] = base_dict["name"]["EffectiveName"]["Value"]
        for field in exclude_fields:
            if field in self.__dict__:
                del base_dict[field]
        return base_dict

    def get_table_data(self):

        tdata = [self.get_row_data()]
        for st in self.sub_tracks:
            st_data = st.get_table_data()
            tdata.extend(st_data)

        return tdata

    @staticmethod
    def get_headers():
        return ["name", "type", "track_id", "PlugIns", "group_id", "depth"]


class ProjectInfo:
    def __init__(self, root: ET.Element):
        self.tracks = root.find(".//Tracks")
        self.track_infos = [self.build_track_info(track) for track in self.tracks]
        self.master_track = root.find(".//MasterTrack")
        self.project = root.find(".//Ableton")

    def build_render_info(self):
        _rows = [self.make_render_info(self.project, idx=0, has_children=True, depth=0, parent=None),
                 self.make_render_info(element=self.tracks, idx=1, has_children=len(self.track_infos) > 0, depth=1,
                                       parent=0)]
        for track_idx, track_info in enumerate(self.track_infos):
            _rows.append(
                self.make_render_info(element=track_info, idx=len(_rows), has_children=False, depth=2, parent=1))
        _rows.append(self.make_render_info(self.build_master_track_info(),  idx=len(_rows), depth=1, parent=0, has_children=False))
        return _rows

    @staticmethod
    def make_render_info(element: typing.Union[dict, ET.Element, AbletonProjectClass], idx: int, has_children: bool,
                          depth: int, parent: typing.Optional[int]):
        return ProjectInfo._make_render_info(element, idx, has_children, depth, parent)

    @staticmethod
    def _make_render_info(element: typing.Union[dict, ET.Element, AbletonProjectClass], idx: int, has_children: bool,
                          depth: int, parent: typing.Optional[int]):
        is_dict = isinstance(element, dict)
        additional_data = None
        if is_dict:
            def unpack(key, val):
                if isinstance(val, list):

                    print(key, [(i.attrib, i, ) for _idx, i in enumerate(val)])
                    return {_idx: i.attrib["Value"] for _idx, i in enumerate(val)}
                print("Unpack value: ", val)
                return val.attrib["Value"]
            tag = element["tag"]
            additional_data = element.get("additional_data", [])
            value = {key: unpack(key, elem) for key, elem in element.items() if key not in {"tag", "additional_data"}}
        else:
            value = element.attrib
            tag = element.tag
        return {
            "value": value,
            "idx": idx,
            "has_children": has_children,
            "depth": depth,
            "parent": parent,
            "tag": tag,
            "additional_data": additional_data
        }

    def build_master_track_info(self):
        master_track: ET.Element = self.master_track
        master_envelopes = master_track.findall("AutomationEnvelopes/Envelopes/AutomationEnvelope")
        bpm_envelope = list(
            filter(lambda env: True if env.find("EnvelopeTarget/PointeeId[@Value='8']") is not None else False, master_envelopes))[0]
        bpm_events: list = bpm_envelope.findall("Automation/Events/FloatEvent")
        apcs = [FloatEvent(elem) for elem in bpm_events]
        if len(apcs) > 1 or not apcs:
            raise ValueError("multiple bpms or no bpm")
        return {
            "bpm": apcs[0],
            "tag": "Master Track"
        }

    def render_fader(self, value: float, min_val: float, max_val: float, tag: str, sideways=True):
        offset = (50, 50, )
        value_norm = (value - min_val) / (max_val-min_val)
        return flask.render_template("fader.html", offset=offset, value=value_norm, sideways=sideways, tag=tag)

    def render_poti(self, value: float, min_val: float, max_val: float, ):
        offset = (50, 50, )

        r = 40
        value_norm = (value - min_val) / (max_val-min_val)
        a = value_norm * (2*math.pi/1)
        line_pos0 = offset
        line_pos1 = (int(offset[0] + r * math.cos(a)), int(offset[1] + r * math.sin(a)), )
        return flask.render_template("poti.html", line_pos0=line_pos0, line_pos1=line_pos1, radius=r, value=value)

    def build_track_info(self, track: ET.Element):
        track_delay = track.find("TrackDelay/Value")  # has .attrib["Value"]
        print("track_delay.attrib: ", track_delay.attrib)
        name = track.find("Name/EffectiveName")
        color = track.find("Color")
        pan = track.find("DeviceChain/Mixer/Pan/Manual")
        sends: list = track.findall("DeviceChain/Mixer/Sends/TrackSendHolder/Send")
        print("SENDS:  ", sends)
        volume = track.find("DeviceChain/Mixer/Volume/Manual")
        audio_output_routing = track.find("DeviceChain/AudioOutputRouting/Target")
        additional_data = [self.render_fader(value=float(pan.attrib["Value"]), min_val=-1., max_val=1, tag="Pan")]
        return {
            "track_delay": track_delay,
            "name": name,
            "color": color,
            "pan": pan,
            #"sends": sends,
            "volume": volume,
            "audio_output_routing": audio_output_routing,
            "tag": name.attrib["Value"],
            "additional_data": additional_data
        }

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
        print("_new_rows :", len(tmp))
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
        #print(rows)
        row_templates = [flask.render_template("project_xml_row.html", row=row, project_id=self.project_id,
                                               additionals=row.get("additional_data", None)) for row in rows]
        row_group = flask.render_template("row-group.html", idx=group_idx, rows=row_templates)
        return row_group

    def build_table_template(self) -> str:
        if self.visible_rows:
            rows = None# [self._rows[idx] for idx in self.visible_rows]
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
            print(idx, self._rows)
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
        if row_idx in self.visible_rows:    # that means, the row has a parent assigned to it
            raise NotImplemented    # too tired..
        elif 0 > row_idx or row_idx >= len(self._rows):
            raise ValueError("Invalid row", row_idx)
        target_row = self.rows[row_idx]
        # self.visible_rows.append(row_idx)
        print("TARGET ROW ", target_row)
        for _idx in reversed(range(len(self.rows))[row_idx+1:]):
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

    def row_obj(self, idx: int, tag: str, ):
        return {
        }
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
                #print(idx, row_idx, self.rows[row_idx])
                break
        #print(f"init table with {len(self._new_rows)} rows: {[row['idx'] for row in self._new_rows]}")

    def collapse_row(self, idx: int, nested: bool = False):
        #print("Collapse row ", idx, nested, len(self.visible_rows))
        self.expanded_rows.remove(idx)
        expanded_children = [row_idx for row_idx in self.expanded_rows if row_idx > 0 and
                             self._rows[row_idx]["parent"] == idx]
        for child_idx in expanded_children:
            self.collapse_row(child_idx, nested=True)
        if nested:
            self.visible_rows.remove(idx)
        self._rows[idx].update({"is_expanded": False})
        depth = self._rows[idx]["depth"]
        for row_idx in self.visible_rows:   # ToDo: Only iterate over visible rows
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

            row = NestedTable.convert_ableton_project_to_row(project=project, idx=_idx+1, page_link=page_link + f"?project_id={_idx}",
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
    def __init__(self, project_path: pathlib.Path):
        self.project_path = project_path
        self.exports: list[pathlib.Path] = []
        self.project_files: list[pathlib.Path] = []
        self.tmp_path = "tmp"
        self.tree = None
        self.root = None
        self.init_dirs()
        # self.scan_project_dir()
        self.load_ableton_project(project_path)

    def build_project_info_object(self) -> ProjectInfo:
        return ProjectInfo(self.root)

    def init_dirs(self):
        if not os.path.exists(TMP_DIR):
            os.mkdir(TMP_DIR)

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

    def load(self):
        self.load_ableton_project(self.project_path)
        return self.tree

    def load_ableton_project(self, path: pathlib.Path):
        # copy .als file, extract it and read
        import shutil
        tmp_path = pathlib.Path(TMP_DIR).joinpath(
            str(path.stem) + "-tmp" + ".gz"   #str(path.stem)[-len(path.suffix):]
        )

        tmp_path_extract = pathlib.Path(TMP_DIR).joinpath(
            str(path.stem) + "_tmp_extract_.xml" # + str(path.stem)[-len(path.suffix):]
        )
        shutil.copyfile(path, tmp_path)

        with gzip.open(tmp_path, 'rb') as f:
            file_content = f.read()
            with open(tmp_path_extract, 'w') as ff:
                s = str(file_content)[2:-1].replace("'" , '"').replace("<?" , "<").replace("?>" , ">") + "</xml>"
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
        self._iter_print(self.root, 0, exclude_list,search_list, search_for_occurence)

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

            #print("\t\t" * depth, i.tag, i.attrib, depth)
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

    def _rec_search2(self, depth: int, exclude_list: typing.Iterable, search_list: typing.Iterable):
        result = []
        nodes = self.root.findall(search_list)
        print(nodes)


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
            text, tail = (prop.replace("\\r", "").replace("\\n", "").replace("\\t", "") if prop else None for prop in (text, tail, ))
            if text:
                print("GOT A text for ", i)
                r["text"] = "MYTEXT " + str(i.text)[:100]
            if tail:
                print("GOT A tail ", tail)
                r["tail"] = tail
            result.append(r)
            if len(i) > 0:
                result += Ableton_Project._rec_search(i, depth + 1, exclude_list, search_list, search_for_occurence)
        return result

    @staticmethod
    def get_next_by_tag(node: ET.ElementTree, tag: str):
        return next(node.iter(tag))

    def get_tracks(self):
        return next(self.root.iter("Tracks"))

    @staticmethod
    def get_group_id_from_track(track: ET.Element):
        """
        Returns IDs for all Ableton-groups
        :return:
        :rtype:
        """
        return next(track.iter("TrackGroupId")).attrib["Value"]

    def get_table_headers(self):
        return Track_Info.get_headers()

    def generate_display_table(self):
        tracks = self.get_track_objects()
        table_data = []
        for t in tracks:
            for row in t.get_table_data():
                table_data.append(row)
        return table_data

    def get_track_objects(self):
        tracks = []
        track_nodes = self.get_tracks()
        for t in track_nodes:
            track_type = Track.track_type(t)
            group_id = Track.group_id(t)  # self.get_group_id_from_track(t)
            name = Track.name(t)  # {n.tag: n.attrib for n in next(t.iter("Name"))}
            plug_ins = Track.plug_ins(t)
            track_info = Track_Info(
                type=track_type ,
                track_id=t.attrib["Id"],
                group_id=group_id,
                name=name,
                sub_tracks=[],
                PlugIns=plug_ins,
                is_toggled= group_id == "-1",
                depth=0
            )
            if group_id == "-1":
                tracks.append(track_info)
            else:
                def rec_grouper(child, parent: Track_Info):
                    if child.group_id == parent.track_id:
                        child.depth = parent.depth + 1
                        parent.sub_tracks.append(child)
                    else:
                        parent.sub_tracks = [rec_grouper(child, p, ) for p in parent.sub_tracks]
                    return parent

                tracks = [rec_grouper(track_info, t) for t in tracks]
        return tracks

    def build_json_object(self):
        tracks = []
        track_nodes = self.get_tracks()
        for t in track_nodes:
            track_type = Track.track_type(t)
            group_id = Track.group_id(t) # self.get_group_id_from_track(t)
            name = Track.name(t) # {n.tag: n.attrib for n in next(t.iter("Name"))}
            plug_ins = Track.plug_ins(t)
            track_info = {
                    "type": track_type,
                    "track_id": t.attrib["Id"],
                    "group_id": group_id,
                    "name": name,
                    "sub_tracks": [],
                    "PlugIns": plug_ins
            }
            if group_id == "-1":
                tracks.append(track_info)
            else:
                def rec_grouper(child, parent):
                    if child["group_id"] == parent["track_id"]:
                        parent["sub_tracks"].append(child)
                    else:
                        parent["sub_tracks"] = [rec_grouper(child, p) for p in parent["sub_tracks"]]
                    return parent
                tracks = [rec_grouper(track_info, t) for t in tracks]
        return tracks


def how_to_work_with_the_script(path: str):
    example_project = Ableton_Project(pathlib.Path(path))
    tree = example_project.load()
    root = example_project.tree.getroot()
    tree.write('tmp/test.xml')
    print(example_project)
    return example_project.build_json_object()


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
        ableton_project.iter_print(search_list=("Session", ), search_for_occurence=True)
    # interesting row: 177144 (Take Lanes. There is no value  
    print("No paths found")

    # ToDo: Make abstract table
    # ToDo: make redirect to unique url for every table (i.e. project-table/0)
    # ToDo: save state
