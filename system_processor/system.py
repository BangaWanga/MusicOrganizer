import uuid


class SystemRef:
    def __init__(self, name: str):
        self._link_id = uuid.uuid4()
        self.name = name

    @property
    def link_id(self):
        return self._link_id


class Relation:
    pass


class System:
    def __init__(self):
        self._system_id = SystemRef()

    def tick(self) -> int:
        # returns number of ticks until next update is needed (-1 means no more update is required)
        return - 1


