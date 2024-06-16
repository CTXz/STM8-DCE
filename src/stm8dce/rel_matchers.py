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
This module provides classes and function to pattern match STM8 SDCC generated .rel and .lib files.
For more information on the STM8 .rel and .lib file formats, see:
    https://sourceforge.net/p/sdcc/code/HEAD/tree/trunk/sdcc/sdas/doc/format.txt
"""

from enum import Enum
import re

############################################
# Classes
############################################


class SymbolLine:
    """
    Class to represent a symbol line in a .rel or .lib file.
    """

    class Type(Enum):
        """
        Enum to represent the type of a symbol line.
        """

        DEF = "Def"
        REF = "Ref"

    def __init__(self, file_path, line_number, line):
        """
        Initializes a SymbolLine object.

        Args:
            file_path (str): The path to the file containing the symbol line.
            line_number (int): The line number of the symbol line.
            line (str): The line containing the symbol line.
        """

        match = re.match(r"S (\S+) (Def|Ref)([0-9A-Fa-f]+)", line)
        if match:
            self.name = match.group(1)
            self.type_ = SymbolLine.Type(match.group(2))
            self.offset = int(match.group(3), 16)
        else:
            raise ValueError(f"Not a symbol line: {line}")

        self.file_path = file_path
        self.line_number = line_number
        self.line = line


class HeaderLine:
    """
    Class to represent a header line in a .rel or .lib file.
    """

    def __init__(self, file_path, line_number, line):
        """
        Initializes a HeaderLine object.

        Args:
            file_path (str): The path to the file containing the header line.
            line_number (int): The line number of the header line.
            line (str): The line containing the header line.
        """
        if not line.startswith("H "):
            raise ValueError(f"Not a header line: {line}")

        self.file_path = file_path
        self.line_number = line_number
        self.line = line

        # This class is only used to identify header lines
        # Further matching can be done here but is currently not needed


class ModuleLine:
    """
    Class to represent a module line in a .rel or .lib file.
    """

    def __init__(self, file_path, line_number, line):
        """
        Initializes a ModuleLine object.

        Args:
            file_path (str): The path to the file containing the module line.
            line_number (int): The line number of the module line.
            line (str): The line containing the module line.
        """
        if not line.startswith("M "):
            raise ValueError(f"Not a module line: {line}")

        self.name = line.split()[1]
        self.file_path = file_path
        self.line_number = line_number
        self.line = line


def match_rel_line(file_path, line_number, line):
    """
    Matches a line from a .rel or .lib file to a SymbolLine, HeaderLine, or ModuleLine.

    Args:
        file_path (str): The path to the file containing the line.
        line_number (int): The line number of the line.
        line (str): The line to be matched.

    Returns:
        SymbolLine, HeaderLine, or ModuleLine: The matched object, or None if no match is found.
    """
    try:
        return SymbolLine(file_path, line_number, line)
    except ValueError:
        pass

    try:
        return HeaderLine(file_path, line_number, line)
    except ValueError:
        pass

    try:
        return ModuleLine(file_path, line_number, line)
    except ValueError:
        pass

    return


############################################
# Documentation
############################################

# Include private members in documentation
__pdoc__ = {
    name: True
    for name, _class in globals().items()
    if name.startswith("_") and isinstance(_class, type)
}
__pdoc__.update(
    {
        f"{name}.{member}": True
        for name, _class in globals().items()
        if isinstance(_class, type)
        for member in _class.__dict__.keys()
        if member not in {"__module__", "__dict__", "__weakref__", "__doc__"}
    }
)
