from xml.etree import ElementTree as ET


class AbletonProjectClass:
    def __init__(self, element: ET.Element):
        self.element = element

    @property().getter
    def attrib(self) -> dict:
        return self.element.attrib


class FloatEvent(AbletonProjectClass):
    def __init__(self, element: ET.Element):
        # assert element.tag == "FloatEvent"
        super().__init__(element)

    @property
    def attrib(self):
        _attrib = self.element.attrib
        return {"Id": int(_attrib["Id"]), "Time": int(_attrib["Time"]), "Value": int(_attrib["Value"])}

