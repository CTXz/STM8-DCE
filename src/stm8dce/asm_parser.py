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
This module provides a class to parse STM8 SDCC generated assembly files.
"""

from . import settings
from . import debug
from . import asm_analysis
from .asm_matchers import *

############################################
# Classes
############################################


class ASMParser:
    """
    Class to parse STM8 SDCC generated assembly files.

    Attributes:
        globals (list): A list of global definitions.
        interrupts (list): A list of interrupt definitions.
        functions (list): A list of functions.
        constants (list): A list of constants.
    """

    def __init__(self, file_path):
        """
        Initializes the ASMParser with a file path and parses the file.

        Args:
            file_path (str): The path to the assembly file to be parsed.
        """
        self.globals = []
        self.interrupts = []
        self.functions = []
        self.constants = []
        self.initializers = []

        self._relevant = []  # Stack of relevant lines to be parsed

        debug.pdbg()
        debug.pdbg(f"Parsing file: {file_path}")
        debug.pseperator()

        with open(file_path, "r") as file_obj:
            for line_number, line in enumerate(file_obj.readlines(), 1):
                match = match_asm_line(file_path, line_number, line)
                if match:
                    self._relevant.extend(match)

        self._parse()

    def _parse(self):
        """
        Parses the relevant lines of the assembly file and extracts
        globals, interrupts, functions, and constants.
        """
        while self._relevant:
            eval = self._relevant.pop(0)

            # Global definitions
            if Directive.is_global_directive(eval):
                self.globals.append(
                    asm_analysis.GlobalDef(eval.file_path, eval.line_number, eval.value)
                )
                debug.pdbg(f"Line {eval.line_number}: Global definition {eval.value}")
                continue

            # Interrupt definitions
            if Instruction.is_interrupt_instruction(eval):
                intdef = eval.is_int()
                self.interrupts.append(
                    asm_analysis.IntDef(eval.file_path, eval.line_number, intdef)
                )
                debug.pdbg(f"Line {eval.line_number}: Interrupt definition {intdef}")
                continue

            # Code section
            if Directive.is_area_directive(eval, settings.codeseg):
                self._parse_code_section(eval)
                continue

            # Constants section
            if Directive.is_area_directive(eval, settings.constseg):
                self._parse_const_section(eval)
                continue

            # Initializer section
            if Directive.is_area_directive(eval, "INITIALIZER"):
                self._parse_initializer_section(eval)
                continue

    def _parse_code_section(self, area):
        """
        Parses the code section of the file and extracts functions.

        Args:
            area (Directive): The directive indicating the start of the code section.
        """
        debug.pdbg(f"Line {area.line_number}: Code section starts here")

        while self._relevant:
            eval = self._relevant.pop(0)

            # Check if this is the end of the code section (start of a new area)
            if Directive.is_area_directive(eval):
                self._relevant.insert(0, eval)
                break

            # Parse function if a function label is found
            if Label.is_absolute_label(eval):
                self._parse_function(eval)
                continue

        debug.pdbg(f"Line {area.line_number}: Code section ends here")

    def _parse_const_section(self, area):
        """
        Parses the constants section of the file and extracts constants.

        Args:
            area (Directive): The directive indicating the start of the constants section.
        """
        debug.pdbg(f"Line {area.line_number}: Constants section starts here")

        while self._relevant:
            eval = self._relevant.pop(0)

            # Check if this is the end of the constants section (start of a new area)
            if Directive.is_area_directive(eval):
                self._relevant.insert(0, eval)
                break

            # Parse constant if a constant label is found
            if Label.is_absolute_label(eval):
                self._parse_constant(eval)
                continue

        debug.pdbg(f"Line {area.line_number}: Constants section ends here")

    def _parse_initializer_section(self, area):
        """
        Parses the initializer section of the file.

        Args:
            area (Directive): The directive indicating the start of the initializer section.
        """
        debug.pdbg(f"Line {area.line_number}: Initializer section starts here")

        while self._relevant:
            eval = self._relevant.pop(0)

            # Check if this is the end of the initializer section (start of a new area)
            if Directive.is_area_directive(eval):
                self._relevant.insert(0, eval)
                break

            # Parse initializer if an absolute label is found
            if Label.is_absolute_label(eval):
                self._parse_initializer(eval)
                continue

        debug.pdbg(f"Line {area.line_number}: Initializer section ends here")

    def _parse_function(self, label):
        """
        Parses a function and extracts relevant information.

        Args:
            label (Label): The label indicating the start of the function.
        """
        debug.pdbg(f"Line {label.line_number}: Function {label.name} starts here")

        function = asm_analysis.Function(label.file_path, label.line_number, label.name)

        while self._relevant:
            eval = self._relevant.pop(0)

            # Check if this is an IRQ handler
            if Instruction.is_iret_instruction(eval):
                debug.pdbg(
                    f"Line {label.line_number}: Function {label.name} detected as IRQ Handler"
                )
                function.isr = True
                continue

            # Check if this is the end of the function
            if Label.is_absolute_label(eval) or Directive.is_area_directive(eval):
                function.end_line_number = (
                    eval.line_number - 1  # -1 Since we're already past end
                )
                self._relevant.insert(0, eval)
                break

            # From here on we can assume the function is not empty
            function.empty = False

            # Keep track of calls made by this function
            if Instruction.is_call_instruction(eval):
                call = eval.is_call()
                debug.pdbg(f"Line {eval.line_number}: Call to {call}")
                if call not in function.calls_str:
                    function.calls_str.append(call)
                continue

            # Keep track of labels read by long address capable instructions
            if Instruction.is_long_label_read_instruction(eval):
                long_labels = eval.is_long_label_read()
                if long_labels:
                    for long_label in long_labels:
                        debug.pdbg(
                            f"Line {eval.line_number} ({eval.mnemonic}): long address label {long_label} is read here"
                        )
                        if long_label not in function.long_read_labels_str:
                            function.long_read_labels_str.append(long_label)
                    continue

        if function.empty:
            debug.pdbg(f"Line {label.line_number}: Function {label.name} is empty!")
        debug.pdbg(f"Line {label.line_number}: Function {label.name} ends here")

        self.functions.append(function)

    def _parse_constant(self, label):
        """
        Parses a constant and extracts relevant information.

        Args:
            label (Label): The label indicating the start of the constant.
        """
        debug.pdbg(f"Line {label.line_number}: Constant {label.name} starts here")

        ret_constant = asm_analysis.Constant(
            label.file_path, label.line_number, label.name
        )

        while self._relevant:
            eval = self._relevant.pop(0)

            # Check if this is the end of the constant
            if Label.is_absolute_label(eval) or Directive.is_area_directive(eval):
                ret_constant.end_line_number = (
                    eval.line_number - 1  # -1 Since we're already past end
                )
                self._relevant.insert(0, eval)
                break

        debug.pdbg(f"Line {label.line_number}: Constant {label.name} ends here")
        self.constants.append(ret_constant)

    def _parse_initializer(self, label):
        """
        Parses an initializer and extracts relevant information.

        Args:
            label (Label): The label indicating the start of the initializer.
        """
        debug.pdbg(f"Line {label.line_number}: Initializer {label.name} starts here")

        ret_initializer = asm_analysis.Initializer(
            label.file_path, label.line_number, label.name
        )

        while self._relevant:
            eval = self._relevant.pop(0)

            # Check if this is the end of the initializer
            if Label.is_absolute_label(eval) or Directive.is_area_directive(eval):
                self._relevant.insert(0, eval)
                break

            # Check for .dw directive and see if it defines a label
            # If so, this is a pointer
            if (
                Directive.is_dw_directive(eval)
                and (eval.value[0].isalpha() or eval.value[0] == "_")
                and all(char.isalnum() or char == "_" for char in eval.value)
            ):
                ret_initializer.pointers_str.append(eval.value)
                debug.pdbg(
                    f"Line {eval.line_number}: Initializer contains pointer to symbol {eval.value}"
                )

        debug.pdbg(f"Line {label.line_number}: Initializer {label.name} ends here")
        self.initializers.append(ret_initializer)


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
