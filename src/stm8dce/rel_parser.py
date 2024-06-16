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
This module provides functions to parse .rel and .lib files.
"""

from . import rel_analysis
from . import debug
from .rel_matchers import *

############################################
# Classes
############################################


class RELParser:
    """
    Class to parse .rel and .lib files.

    Attributes:
        modules (list): A list of Module objects parsed from the file.
    """

    def __init__(self, file_path):
        """
        Initializes the RELParser with a file path and parses the file.

        Args:
            file_path (str): The path to the .rel or .lib file to be parsed.
        """
        self.modules = []

        debug.pdbg()
        debug.pdbg(f"Parsing file: {file_path}")
        debug.pseperator()

        with open(file_path, "r", errors="replace") as file_obj:
            self._parse(file_obj, file_path)

    def _parse(self, file_obj, file_path):
        """
        Parses the file and extracts modules and symbols.

        Args:
            file_obj (file object): The file object to parse.
            file_path (str): The path to the .rel or .lib file to be parsed.
        """
        for line_number, line in enumerate(file_obj.readlines(), 1):
            match = match_rel_line(file_path, line_number, line)

            if isinstance(match, HeaderLine):
                debug.pdbg(
                    f"Line {match.line_number}: Header definition (new module starts here)"
                )
                self.modules.append(
                    rel_analysis.Module(
                        match.file_path,
                        match.line_number - 1,  # Header is 2nd line of module
                    )
                )

            elif isinstance(match, ModuleLine):
                debug.pdbg(f"Line {match.line_number}: Module name: {match.name}")
                self.modules[-1].set_name(match.name)

            elif isinstance(match, SymbolLine):
                if match.name == ".__.ABS.":
                    debug.pdbg(f"Line {match.line_number}: Ignoring .__.ABS. symbol")
                    continue

                if match.type_ == SymbolLine.Type.DEF:
                    debug.pdbg(
                        f"Line {match.line_number}: Defined symbol: {match.name}"
                    )
                    self.modules[-1].add_defined_symbol(match)
                else:
                    debug.pdbg(
                        f"Line {match.line_number}: Referenced symbol: {match.name}"
                    )
                    self.modules[-1].add_referenced_symbol(match)


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
