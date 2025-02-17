import datetime
import typing
from pathlib import Path
import pickle
import xml.etree.ElementTree as ET
import os
import gzip
import shutil
import logging

logger = logging.getLogger()
logger.level = logging.DEBUG


PROJECT_FILES_PATH = "project_files"
TMP_DIR = "tmp"
USER_DATA = "user"
PROJECT_FILES_PATH_PATH = f"{USER_DATA}/project_files_path.p"
LINKED_PROJECTS = f"{USER_DATA}/linked_projects.p"


# links an ableton path to a file in {USER_DATA} which contains information from previous scans
linked_projects: dict[Path: Path] = {}


def load_linked_projects():
    global linked_projects
    linked_projects = pickle.load(open(LINKED_PROJECTS, "rb"))


def init(): # ToDo Maybe call with import? Or move to directory and call in __init__ file?
    global PROJECT_FILES_PATH
    if not os.path.exists(TMP_DIR):
        os.mkdir(TMP_DIR)
    if not os.path.exists(USER_DATA):
        os.mkdir(USER_DATA)
    if not os.path.exists(LINKED_PROJECTS):
        pickle.dump({}, open(LINKED_PROJECTS, "wb"))
    if os.path.exists(PROJECT_FILES_PATH_PATH):
        PROJECT_FILES_PATH = pickle.load(open(PROJECT_FILES_PATH_PATH, "rb"))
        print("Replaced default project path with ", PROJECT_FILES_PATH_PATH, PROJECT_FILES_PATH)
    else:
        print("No user project path provided, ", PROJECT_FILES_PATH_PATH)
    load_linked_projects()
    print("Init Files DONE")


def set_project_path(new_path: str):
    print(f"Writing {new_path} to PROJECT_FILES_PATH_PATH")
    pickle.dump(new_path, open(PROJECT_FILES_PATH_PATH, "wb"))


def save_linked_projects():
    global linked_projects
    pickle.dump(linked_projects, open(LINKED_PROJECTS, "wb"))


def get_project_paths(file_path: str = None, exclude_directories=("Backup", )):
    global PROJECT_FILES_PATH
    if file_path is None:
        file_path = PROJECT_FILES_PATH
    print("CALLED GET PROJECT PATHS ", file_path )
    # ToDo: Preserve directory structure from original directory
    ret = []
    for directory in Path(file_path).glob('**'):
        for item in directory.iterdir():
            if directory.name not in exclude_directories:
                if item.suffix == ".als":
                    ableton_project = item
                    os.path.getmtime(ableton_project)
                    ret.append(item)
    return ret


def get_user_data_for_path(path: Path) -> typing.Optional[typing.Tuple[dict, Path]]:
    global linked_projects
    # TODO: load from RAM if possible
    # print("linked_projects: ", linked_projects)
    info_path = linked_projects.get(path)
    if info_path:
        return pickle.load(open(info_path, "rb")), info_path
    return None


def new_project_info_path()-> Path:
    # ToDo: Raise Error if overwriting other file
    return Path(USER_DATA).joinpath(f"{len(linked_projects)}.p")    # ToDo: THis will bite me in the ass


def upsert_user_data(project_path: Path, last_modified: float, tree_path: Path, user_inputs: dict = None):
    global linked_projects
    user_data = get_user_data_for_path(project_path)
    if user_data is None:
        user_inputs = {}
        project_info = {
            "last_modified": last_modified,
            "tree_path": tree_path,
            "user_inputs": user_inputs
        }
        project_info_path = new_project_info_path()
        linked_projects[project_path] = project_info_path
    else:
        project_info, project_info_path = user_data
    pickle.dump(project_info, open(project_info_path, "wb"))
    save_linked_projects()


def get_last_modified(path) -> float:
    file_stat = os.stat(path)
    last_modified = datetime.datetime.fromtimestamp(file_stat.st_mtime)
    last_access = datetime.datetime.fromtimestamp(file_stat.st_atime)
    file_size_bytes = file_stat.st_size
    file_size_bytes_str = str(file_size_bytes)
    file_size = f"{file_size_bytes} b"
    if 3 <= len(file_size_bytes_str) < 6:
        file_size = f"{file_size_bytes / 3} kb"
    elif len(file_size_bytes_str) > 6:
        file_size = f"{file_size_bytes / 6} mb"
    if not os.path.exists(path):
        raise ValueError("Invalid path for ableton project")
    return last_modified


def load_ableton_project(path: Path) -> tuple:
    # copy .als file, extract it and read
    if not os.path.exists(path):
        raise ValueError("Invalid path for ableton project")
    last_modified = get_last_modified(path)
    user_data = get_user_data_for_path(path)
    if user_data:
        user_data, _info_path = user_data
        if last_modified > user_data["last_modified"]:
            print(f"Reimporting changed project: {path}")
            logger.info(f"Reimporting changed project: {path}")
            tree, tree_path = full_als_import(path)
            user_data["last_modified"] = last_modified
            upsert_user_data(path, last_modified, tree_path)
        else:
            print(f"Loading project from cache: {path}")
            logger.info(f"Loading project from cache: {path}")
            return ET.parse(user_data["tree_path"]), last_modified

    else:
        tree, tree_path = full_als_import(path)
        print(f"Importing unknown project: {path}")
        logger.info(f"Importing unknown project: {path}")
    if tree is not None:
        upsert_user_data(path, last_modified, tree_path)
    return tree, last_modified


def full_als_import(path:Path) -> [ET.ElementTree, Path]:
    print(path)
    tmp_path = Path(TMP_DIR).joinpath(
        str(path.stem) + "-tmp" + ".gz"
    )

    tmp_path_extract = Path(TMP_DIR).joinpath(
        str(path.stem) + "_tmp_extract_.xml"
    )
    shutil.copyfile(path, tmp_path)

    with gzip.open(tmp_path, 'rb') as f:
        file_content = f.read()
        with open(tmp_path_extract, 'w') as ff:
            s = str(file_content)[2:-1].replace("'" , '"').replace("<?" , "<").replace("?>" , ">") + "</xml>"
            ff.write(s)
    try:
        tree = ET.parse(tmp_path_extract)
    except ET.ParseError as e:
        print(f"Could not read {path}: {e}")
        return None, None
    return tree, tmp_path_extract
