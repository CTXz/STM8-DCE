# Copyright (C) 2024 Patrick Pedersen

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
This module provides functions to pattern match STM8 SDCC generated .rel and .lib files
For more information on the STM8 .rel and .lib file formats, see:
    https://sourceforge.net/p/sdcc/code/HEAD/tree/trunk/sdcc/sdas/doc/format.txt
"""

from enum import Enum
import re


class SymbolType(Enum):
    DEF = "Def"
    REF = "Ref"


class Symbol:
    def __init__(self, name, type_, offset):
        self.name = name
        self.type = SymbolType(type_)
        self.offset = offset


def is_header_line(line):
    return line.startswith("H ")


def is_module_line(line):
    if line.startswith("M "):
        return line.split()[1]
    return None


def is_symbol_line(line):
    match = re.match(r"S (\S+) (Def|Ref)([0-9A-Fa-f]+)", line)
    if match:
        return Symbol(
            name=match.group(1),
            type_=match.group(2),
            offset=int(match.group(3), 16),
        )
    return None
