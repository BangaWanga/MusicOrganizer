import dataclasses
import enum
import os.path
import pathlib
import typing
import xml.etree.ElementTree as ET
import gzip

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


class NestedTable:
    def __init__(self, rows: list[dict[str, typing.Any]]):
        self._rows = rows
        self.expanded_rows = set()

    def toggle_row(self, idx: int):
        raise NotImplemented
        if idx in self.expanded_rows:
            self.expand_row(idx)

    @property
    def rows(self):
        return self._rows

    def expand_row(self, idx: int):
        depth = self.rows[idx]["depth"]
        splice_list = []    # start, delete_count, *insert_items
        splice_start = idx + 1
        step_skipped = False

        def _splice_arg(added_row: dict, skipped: bool = False):
            if skipped:
                splice_list.append([splice_start, 0, added_row])
            else:
                splice_list[-1].append(added_row)

        if splice_start >= len(self._rows):
            return None

        for row_idx in range(idx + 1, len(self._rows)):

            row = self.rows[row_idx]
            row_depth = row["depth"]
            if row_depth == depth + 1:
                _splice_arg(row, step_skipped)
                step_skipped = False
            elif row_depth <= depth:
                break
            elif row_depth > depth + 1:
                step_skipped = True
                splice_start = row_idx + 1
        return splice_list



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

            print("\t\t" * depth, i.tag, i.attrib, depth)
            if len(i) > 0:
                Ableton_Project._iter_print(i, depth + 1, search_list, exclude_list, search_for_occurence)

    def rec_search(self,
                   search_list: typing.Optional[typing.Iterable] = None,
                   exclude_list: typing.Iterable = ("ParameterList",),
                   search_for_occurence: bool = False):
        if exclude_list is None:
            exclude_list = set()
        if search_list is None:
            search_list = set()
        return self._rec_search(self.root, 0, exclude_list, search_list, search_for_occurence)

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
            value = i.attrib
            if "Value" in value:
                value = value["Value"]

            # print(i.attrib, type(i.attrib))
            if len(str(value)) > 200:
                print("Wow ", len(value), value)
            r = {"depth": depth, "tag": i.tag, }
            if value:
                r["value"] = value
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


if __name__=="__main__":
    from files import get_project_paths
    project_paths = get_project_paths()
    if project_paths:

        path = project_paths[0]
        tracks = how_to_work_with_the_script(path)
        ableton_project = Ableton_Project(pathlib.Path(path))
        # Find tags in project with iter_print-method
        ableton_project.iter_print(search_list=("Session", ), search_for_occurence=True)
    print("No paths found")