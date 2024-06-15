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
This module provides classes and functions for analyzing .rel and .lib files
"""

from . import rel_matchers
from . import asm_analysis
from . import debug


class Module:
    """
    Class to represent a module in the .rel or .lib file.

    Attributes:
        path (str): Path to the file containing the module.
        line (int): Line number in the file where the module starts.
        name (str): The name of the module.
        referenced_symbols (list): Symbols referenced by this module.
        defined_symbols (list): Symbols defined by this module.
        referenced_by (list): ASM functions that reference this module.
        references (list): ASM Functions or constants referenced by this module.
    """

    def __init__(self, path, line):
        """
        Initializes the Module with the given path and line.

        Args:
            path (str): The file path of the module.
            line (int): The line number in the file.
        """
        self.path = path
        self.line = line
        self.name = "UNNAMED MODULE"  # Some modules don't have a name
        self.referenced_symbols = []
        self.defined_symbols = []
        self.referenced_by = []
        self.references = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def print(self):
        """
        Prints the details of the module.
        """
        print(f"Module: {self.name}")
        print("Referenced Symbols:")
        for symbol in self.referenced_symbols:
            print(f"\t{symbol}")
        print("Defined Symbols:")
        for symbol in self.defined_symbols:
            print(f"\t{symbol}")
        print("Referenced By:")
        for ref in self.referenced_by:
            print(f"\t{ref}")
        print("References:")
        for ref in self.references:
            print(f"\t{ref}")

    def set_name(self, name):
        """
        Sets the name of the module.

        Args:
            name (str): The name to set for the module.
        """
        self.name = name

    def add_referenced_symbol(self, symbol):
        """
        Adds a symbol to the list of referenced symbols.

        Args:
            symbol (str): The symbol to add.
        """
        self.referenced_symbols.append(symbol)

    def add_defined_symbol(self, symbol):
        """
        Adds a symbol to the list of defined symbols.

        Args:
            symbol (str): The symbol to add.
        """
        self.defined_symbols.append(symbol)

    def resolve_references(self, functions, constants):
        """
        Resolves references for the module.
        Resolving means:
            - Find the functions that reference this module's defined symbols
            - Find the functions and constants that this module references

        Args:
            functions (list): List of all function objects.
            constants (list): List of all constant objects.
        """
        # Resolve functions that reference this module's defined symbols
        for symbol in self.defined_symbols:
            match = asm_analysis.functions_referencing_external(functions, symbol.name)
            if match:
                self.referenced_by.extend(match)
                for function in match:
                    self.referenced_by.append(self)
                    debug.pdbg(
                        f"Function {function.name} in {function.path}:{function.start_line} references external symbol {symbol.name} in {self.path}:{self.line}"
                    )

        # If the module isn't referenced by any other, no need to check further
        if not self.referenced_by:
            return

        # Resolve functions and constants that this module references
        for symbol in self.referenced_symbols:
            for function in functions:
                if symbol.name == function.name:
                    self.references.append(function)
                    debug.pdbg(
                        f"Module {self.name} in {self.path}:{self.line} references Function {function.name} in {function.path}:{function.start_line}"
                    )
                    break
            for constant in constants:
                if symbol.name == constant.name:
                    self.references.append(constant)
                    debug.pdbg(
                        f"Module {self.name} in {self.path}:{self.line} references Constant {constant.name} in {constant.path}:{constant.start_line}"
                    )
                    break
