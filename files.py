from pathlib import Path


def init_dir(path_str: str):
    path = Path(path_str)
    for directory in Path(path).glob('**'):
        for item in directory.iterdir():
            print(item)


