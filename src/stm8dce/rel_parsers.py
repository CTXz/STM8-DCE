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
This module provides functions to parse .rel and .lib files
"""

from . import rel_matchers
from . import rel_analysis
from . import debug

from .FileIterator import FileIterator

############################################
# Parsing
############################################


def parse_file(file_path):
    """
    Parses a .rel or .lib file and returns a list of modules.

    This function opens the file and creates a FileIterator.
    The actual parsing is done by the parse() function.

    Args:
        file_path (str): The path to the file to parse.

    Returns:
        list: A list of Module objects parsed from the file.
    """
    debug.pdbg()
    debug.pdbg(f"Parsing file: {file_path}")
    debug.pseperator()

    # Open the file with error handling for quirky characters
    with open(file_path, "r", errors="replace") as file_obj:
        file_iterator = FileIterator(file_obj)
        return parse(file_iterator)


def parse(file_iterator):
    """
    Parses the file using the FileIterator and returns a list of modules.

    Parsing includes:
        - Detecting modules
        - Detecting symbols for each module

    Args:
        file_iterator (FileIterator): The file iterator to parse.

    Returns:
        list: A list of Module objects parsed from the file.
    """
    modules = []
    while True:
        try:
            line = file_iterator.next()
        except StopIteration:
            break

        # Use header_match to determine if a new module is being defined
        # It may seem more logical to use is_module_line, but for some
        # reason not all modules have a M line in some libs
        header_match = rel_matchers.is_header_line(line)
        if header_match:
            debug.pdbg(
                f"Line {file_iterator.index}: Header definition (new module starts here)"
            )

            # Header is the 2nd line in the module
            start_line = file_iterator.index - 1
            modules.append(rel_analysis.Module(file_iterator.path, start_line))

        module_match = rel_matchers.is_module_line(line)
        if module_match:
            debug.pdbg(f"Line {file_iterator.index}: Module name: {module_match}")
            modules[-1].set_name(module_match)

        symbol = rel_matchers.is_symbol_line(line)
        if symbol:
            # Ignore .__.ABS. placeholders, these are irrelevant for DCE
            if symbol.name == ".__.ABS.":
                debug.pdbg(f"Line {file_iterator.index}: Ignoring .__.ABS. symbol")
                continue

            if symbol.type == rel_matchers.SymbolType.DEF:
                debug.pdbg(f"Line {file_iterator.index}: Defined symbol: {symbol.name}")
                modules[-1].add_defined_symbol(symbol)
            else:
                debug.pdbg(
                    f"Line {file_iterator.index}: Referenced symbol: {symbol.name}"
                )
                modules[-1].add_referenced_symbol(symbol)
            continue

    return modules
