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
This module provides functions to pattern match STM8 SDCC generated .rel and .lib files.
For more information on the STM8 .rel and .lib file formats, see:
    https://sourceforge.net/p/sdcc/code/HEAD/tree/trunk/sdcc/sdas/doc/format.txt
"""

from enum import Enum
import re

############################################
# Enums
############################################


class SymbolType(Enum):
    """
    Enum to represent the type of a symbol.
    DEF: Defined symbol
    REF: Referenced symbol
    """

    DEF = "Def"
    REF = "Ref"


############################################
# Classes
############################################


class Symbol:
    """
    Class to represent a symbol in a .rel or .lib file.
    """

    def __init__(self, name, type_, offset):
        """
        Initializes a Symbol object.

        Args:
            name (str): The name of the symbol.
            type_ (str): The type of the symbol (DEF or REF).
            offset (int): The offset of the symbol.
        """
        self.name = name
        self.type = SymbolType(type_)
        self.offset = offset


############################################
# Matchers
############################################


def is_header_line(line):
    """
    Checks if a line is a header line in a .rel or .lib file.

    Citeria for a header line:
        - Starts with "H "

    Args:
        line (str): The line to check.

    Returns:
        bool: True if the line is a header line, False otherwise.
    """
    return line.startswith("H ")


def is_module_line(line):
    """
    Checks if a line is a module line in a .rel or .lib file.

    Criteria for a module line:
        - Starts with "M "

    Args:
        line (str): The line to check.

    Returns:
        str: The module name if the line is a module line, None otherwise.
    """
    if line.startswith("M "):
        return line.split()[1]
    return None


def is_symbol_line(line):
    """
    Checks if a line is a symbol line in a .rel or .lib file.

    Criteria for a symbol line:
        - Starts with "S "
        - Followed by a symbol name
        - Followed by a "Def" or "Ref" with a hexadecimal offset

    Args:
        line (str): The line to check.

    Returns:
        Symbol: A Symbol object if the line is a symbol line, None otherwise.
    """
    match = re.match(r"S (\S+) (Def|Ref)([0-9A-Fa-f]+)", line)
    if match:
        return Symbol(
            name=match.group(1),
            type_=match.group(2),
            offset=int(match.group(3), 16),
        )
    return None
