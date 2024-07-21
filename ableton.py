import dataclasses
import enum
import os.path
import pathlib
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
class Track:
    name: dict
    group_id: str
    track_type: str


class Ableton_Project:
    def __init__(self, project_path: pathlib.Path):
        self.project_path = project_path
        self.exports: list[pathlib.Path] = []
        self.project_files: list[pathlib.Path] = []
        self.tmp_path = "tmp"
        self.init_dirs()
        self.scan_project_dir()

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

    def load_ableton_project(self, path: pathlib.Path):
        # copy .als file, extract it and read
        import shutil
        tmp_path = pathlib.Path(TMP_DIR).joinpath(
            str(path.stem) + "-tmp" + ".gz"
        )

        tmp_path_extract = pathlib.Path(TMP_DIR).joinpath(
            str(path.stem) + "_tmp_extract_.xml"
        )
        shutil.copyfile(path, tmp_path)

        with gzip.open(tmp_path, 'rb') as f:
            file_content = f.read()
            with open(tmp_path_extract, 'w') as ff:
                s = str(file_content)[2:-1].replace("'" , '"').replace("<?" , "<").replace("?>" , ">") + "</xml>"
                ff.write(s)
        return ET.parse(tmp_path_extract)

    @staticmethod
    def iter_print(node, depth=0):
        for i in node:
            if i.tag == "ParameterList":
                continue
            print("\t\t" * depth, i.tag, i.attrib, depth)
            if len(i) > 0:
                Ableton_Project.iter_print(i, depth + 1)

    @staticmethod
    def get_next_by_tag(node: ET.ElementTree, tag: str):
        return next(node.iter(tag))
    
    @staticmethod
    def resolve_node_to_dict(node):
        r = {}
        for n in node:
            if "Value" in n.attrib:
                r[n.tag] = n.attrib
            else:
                r[n.tag] = Ableton_Project.resolve_node_to_dict(n)
        return r

    @staticmethod
    def get_tracks(root):
        tracks = []
        track_nodes = next(root.iter("Tracks"))
        group_ids = [next(t.iter("TrackGroupId")) for t in track_nodes]
        for t in track_nodes:
            track_type = t.tag
            group_id = next(t.iter("TrackGroupId")).attrib["Value"]
            name = {n.tag: n.attrib for n in next(t.iter("Name"))}
            plug_ins = [i.attrib["Value"] for i in t.iter("PlugName")]
            if [i for i in t.iter("PlugName")]:
                print("Say WHat ", [i for i in t.iter("PlugName")])
            audio_input_routing = Ableton_Project.resolve_node_to_dict(next(t.iter("AudioInputRouting")))
            audio_output_routing = Ableton_Project.resolve_node_to_dict(next(t.iter("AudioOutputRouting")))
            midi_input_routing = Ableton_Project.resolve_node_to_dict(next(t.iter("MidiInputRouting")))
            midi_output_routing = Ableton_Project.resolve_node_to_dict(next(t.iter("MidiOutputRouting")))
            mixer = Ableton_Project.resolve_node_to_dict(next(t.iter("Mixer")))

            device_info = []
            for track_id, t in enumerate(track_nodes):
                devices = list(t.iter("DeviceChain"))[1][0]
                for device in devices:
                    device_info.append({
                        "name": device.tag
                    })

            track_info = {
                    "type": track_type,
                    "track_id": t.attrib["Id"],
                    "group_id": group_id,
                    "name": name,
                    "sub_tracks": [],
                    "PlugIns": plug_ins,
                    "audio_output_routing": audio_output_routing,
                    "midi_output_routing": midi_output_routing,
                    "audio_input_routing": audio_input_routing,
                    "midi_input_routing": midi_input_routing,
                    "mixer": mixer
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



def get_tracks_from_projectpath(path: str):
    example_project = Ableton_Project(pathlib.Path(path))
    tree = example_project.load_ableton_project(example_project.project_path)
    root = tree.getroot()
    return example_project.get_tracks(root)


if __name__=="__main__":
    dirname = os.path.dirname(__file__)
    path = os.path.join(dirname, "bin/sisy21.als")
    example_project = Ableton_Project(pathlib.Path(path))
    tree = example_project.load_ableton_project(example_project.project_path)
    root = tree.getroot()
    tracks = get_tracks_from_projectpath(path)