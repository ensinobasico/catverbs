# Catverbs - A portable Catalan conjugation reference for Android
# Copyright (C) 2014  Neil Roberts
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import os
import sys

BRACKET_RE = re.compile(r'{([^}]+)}')
COMMENT_RE = re.compile(r'^\s*(?:#|$)')
VARIABLE_RE = re.compile(r'^\s*([a-z0-9A-Z_]+)\s*=\s*(.*?)\s*$')

class Error(Exception):
    pass

class MissingVerbError(Error):
    pass

class MissingValueError(Error):
    pass

class SelfReferencingValueError(Error):
    pass

class ParseError(Error):
    pass

class Dictionary:
    def __init__(self):
        self.verbs = {}
        self.variables = {}

        data_dir = os.path.join(os.path.split(__file__)[0], '..', 'data')

        for short_filename in os.listdir(data_dir):
            if not short_filename.endswith('.txt'):
                continue
            filename = os.path.join(data_dir, short_filename)
            name = os.path.splitext(short_filename)[0]
            self.verbs[name] = Verb(self, filename)

    def __iter__(self):
        return self.verbs.values().__iter__()

    def get_verb(self, name):
        if name in self.verbs:
            return self.verbs[name]

        raise MissingVerbError("The verb “" + name + "” was not found")

class Verb:
    def __init__(self, dictionary, filename):
        self.dictionary = dictionary
        self.values = {}
        self.filename = filename

        f = open(filename, 'r', encoding='UTF-8')
        line_num = 1

        for line in f:
            if COMMENT_RE.match(line):
                continue

            m = VARIABLE_RE.match(line)
            if m == None:
                raise ParseError("Bad line " + str(line_num) +
                                 " in " + filename)

            name = m.group(1)
            value = m.group(2)

            if name in self.values:
                raise ParseError("Duplicate value on line " + str(line_num) +
                                 " in " + filename)

            self.values[name] = value
            dictionary.variables[name] = -1

            line_num += 1

        f.close()

    def get_value(self, name, depth=0):
        if depth > 100:
            raise SelfReferencingValueError("A value is referring to itself")

        to_check = self

        while True:
            if name in to_check.values:
                return BRACKET_RE.sub(lambda x: self.get_value(x.group(1),
                                                               depth + 1),
                                          to_check.values[name])
            elif "parent" in to_check.values:
                to_check = self.dictionary.get_verb(to_check.values["parent"])
            else:
                raise MissingValueError("No value for " + name)

if __name__ == "__main__":
    dictionary = Dictionary()

    for verb in dictionary.verbs:
        print(verb + ":")
        verb = dictionary.get_verb(verb)
        for value in sorted(verb.values.keys()):
            print(" " + value + " = " + verb.get_value(value))
