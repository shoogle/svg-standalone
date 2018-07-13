#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK - see https://argcomplete.readthedocs.io/

# Argcomplete generates Bash completions dynamically by running the file up to
# the point where arguments are parsed. Want minimal code before this point.

import argparse

try:
    import argcomplete
except ImportError:
    pass # no bash completion :(

parser = argparse.ArgumentParser()

parser.add_argument("svg", nargs='+', help="path to input SVG(s)")

parser.add_argument("-r", "--recursion-levels", type=int, default=5, help="number of levels of recursion")

try:
    argcomplete.autocomplete(parser)
except NameError:
    pass # no bash completion :(

args = parser.parse_args()

# argcomplete has exited by this point, so here comes the actual program code.

import sys
import xml.etree.ElementTree as ET   # XML parser: <tag attrib="val">text</tag>
import base64
import os
import re

class SVG:
    def __init__(self, file_path):
        self.file_path = file_path
        self.directory = os.path.dirname(file_path)
        self.tree = ET.parse(file_path)
        self.root = self.tree.getroot()
        self.root.tail = "\n"
        self.parent_map = {c:p for p in self.root.iter() for c in p}

    def get_indentation(self, element, parent, element_index):
        assert(parent[element_index] is element)
        if element_index == 0:
            match = re.match(r"[\r\n]([^\r\n]*)$", parent.text)
            indentation = match[1] if match else ""
        else:
            match = re.match(r"^([^\r\n]*)[\r\n]", parent[element_index-1].text)
            indentation = match[1] if match else ""
        return ""

    def add_indentation(self, element, indentation):
        for child in element.iter():
            if child.text:
                child.text += indentation # TODO re.sub()
            if child.tail:
                child.tail += indentation

    def make_standalone(self):
        for image in self.root.findall("image[@href]"):
            file_path = image.get("href")
            if file_path.startswith("data:"):
                continue
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.directory, file_path)
            extension = os.path.splitext(file_path)[1][1:].lower()
            if extension == "svg":
                parent = self.parent_map[image]
                index = list(parent).index(image)
                indentation = self.get_indentation(image, parent, index)
                parent.remove(image)
                r = SVG(file_path)
                self.add_indentation(r.root, indentation)
                r.root.tail = image.tail
                parent.insert(index, r.root)
            else:
                with open(file_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read())
                    image.set("href", "data:image/" + extension + ";base64," + encoded_string.decode('utf-8'))

    def write_to_file(self, file):
        self.tree.write(file, encoding="UTF-8", xml_declaration="True")

for file in args.svg:
    s = SVG(file)
    s.make_standalone()
    s.write_to_file(sys.stdout.buffer)
