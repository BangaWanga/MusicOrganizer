from pathlib import Path


project_files_path = "project_files"


def get_project_paths():
    ret = []
    for directory in Path(project_files_path).glob('**'):
        print(directory)
        for item in directory.iterdir():
            print(item)
            if item.suffix == ".als":
                ret.append(item)
    return ret


