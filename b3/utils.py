import re
import xml.etree.ElementTree as ET


def parse_xml(path):
    with path.open("r") as f:
        xmlstring = re.sub(r" xmlns=['\"][^'\"]+['\"]", "", f.read(), count=1)
    return ET.fromstring(xmlstring)