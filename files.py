from pathlib import Path


PROJECT_FILES_PATH = "project_files"


def get_project_paths():
    ret = []
    for directory in Path(PROJECT_FILES_PATH).glob('**'):
        print(directory)
        for item in directory.iterdir():
            print(item)
            if item.suffix == ".als":
                ret.append(item)
    return ret


