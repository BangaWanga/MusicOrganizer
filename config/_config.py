import json
import os.path
import pickle

CONFIG_PATH = "tmp/config.pickle"


class Config:

    def __init__(self, data: dict = None):
        if data is None:
            self.data = self.default_config_file()
        else:
            self.data = data

    def load(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'rb') as infile:
                self.data = pickle.loads(infile.read())
                return True
        return False

    def default_config_file(self):
        return {}

    def save(self):
        with open(CONFIG_PATH, 'wb') as outfile:
            outfile.write(pickle.dumps(self.data))
