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
This module provides classes and functions to pattern match STM8 SDCC generated assembly code.
"""

import re
from itertools import takewhile
from enum import Enum
from . import settings

############################################
# Helper functions
############################################


# Function to sanitize lines by removing comments and stripping whitespace
def sanitize_line(line):
    """
    Sanitizes a line by removing comments and stripping whitespace.

    Criteria for a comment:
        - Starts at ';'

    Args:
        line (str): The line to sanitize.

    Returns:
        str: The sanitized line.
    """
    return line.split(";")[0].strip()


############################################
# Enums
############################################


class AreaType(Enum):
    """
    Enum to represent relevant types of areas in assembly code.
    """

    CODE = settings.codeseg
    CONST = settings.constseg
    OTHER = None


############################################
# Classes
############################################


class Directive:
    """
    Class to represent a directive in the assembly code.
    """

    def __init__(self, file_path, line_number, line):
        """
        Initializes a Directive object.

        Args:
            file_path (str): The path of the file containing the directive.
            line_number (int): The line number of the directive.
            line (str): The directive line itself.
        """
        self.line = sanitize_line(line)

        if not self.line.startswith("."):
            raise ValueError(f"Not a directive statement: {line}")

        self.file_path = file_path
        self.line_number = line_number

        split = self.line.split(None, 1)
        self.value = split[1] if len(split) == 2 else None

    def is_area(self, area_name=None):
        """
        Checks if the directive is an area directive, optionally of a specific area.

        Args:
            area_name (str, optional): The area to check for.

        Returns:
            bool: True if the directive is an area directive (and matches the area, if provided), False otherwise.
        """
        if not area_name:
            return self.line.startswith(".area")

        pattern = rf"\.area\s+{area_name}"
        return re.match(pattern, self.line)

    def is_global(self):
        """
        Checks if the directive is a global directive.

        Returns:
            bool: True if the directive is a global directive, False otherwise.
        """
        return self.line.startswith(".globl")

    def is_dw(self):
        """
        Checks if the directive is a .dw directive.

        Returns:
            bool: True if the directive is a .dw directive, False otherwise.
        """
        return self.line.startswith(".dw")

    @staticmethod
    def is_area_directive(eval, area_name=None):
        """
        Static method to check if an instance is a Directive and is an area directive.

        Args:
            eval: The instance to check.
            area_name (str, optional): The area to check for.

        Returns:
            bool: True if the instance is a Directive and is an area directive (and matches the area, if provided), False otherwise.
        """
        return isinstance(eval, Directive) and eval.is_area(area_name)

    @staticmethod
    def is_global_directive(eval):
        """
        Static method to check if an instance is a Directive and is a global directive.

        Args:
            eval: The instance to check.

        Returns:
            bool: True if the instance is a Directive and is a global directive, False otherwise.
        """
        return isinstance(eval, Directive) and eval.is_global()

    @staticmethod
    def is_dw_directive(eval):
        """
        Static method to check if an instance is a Directive and is a .dw directive.

        Args:
            eval: The instance to check.

        Returns:
            bool: True if the instance is a Directive and is a .dw directive, False otherwise.
        """
        return isinstance(eval, Directive) and eval.is_dw()

    def __str__(self):
        return self.line

    def __repr__(self):
        return f"Directive: {self.line}"


class Label:
    """
    Class to represent a label in the assembly code.
    """

    def __init__(self, file_path, line_number, line):
        """
        Initializes a Label object.

        Args:
            file_path (str): The path of the file containing the label.
            line_number (int): The line number of the label.
            line (str): The label line itself.
        """
        self.line = sanitize_line(line)

        if not self.line.endswith(":"):
            raise ValueError(f"Not a label statement: {line}")

        self.file_path = file_path
        self.line_number = line_number

        self.name = self.line[:-1]

    def is_absolute(self):
        """
        Checks if the label is an absolute label.

        Returns:
            bool: True if the label is absolute, False otherwise.
        """
        return self.line[-2] != "$"

    def is_relative(self):
        """
        Checks if the label is a relative label.

        Returns:
            bool: True if the label is relative, False otherwise.
        """
        return self.line[-2] == "$"

    @staticmethod
    def is_absolute_label(eval):
        """
        Static method to check if an instance is a Label and is an absolute label.

        Args:
            eval: The instance to check.

        Returns:
            bool: True if the instance is a Label and is an absolute label, False otherwise.
        """
        return isinstance(eval, Label) and eval.is_absolute()

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Label: {self.line}"


class Instruction:
    """
    Class to represent an instruction in the assembly code.
    """

    _REGISTER_ARGS = [
        "a",
        "x",
        "xl",
        "xh",
        "y",
        "yl",
        "yh",
        "sp",
        "pc",
        "pcl",
        "pch",
        "pce",
        "cc",
    ]

    _LONG_READ_INSTRUCTIONS = [
        "ld",
        "ldf",
        "ldw",
        "mov",
        "adc",
        "add",
        "and",
        "bcp",
        "cp",
        "or",
        "sub",
        "sbc",
        "xor",
        "addw",
        "subw",
        "cpw",
        "btjt",
        "btjf",
        "push",
        "call",
        "callf",
        "jp",
        "jpf",
        "int",
    ]

    def __init__(self, file_path, line_number, line):
        """
        Initializes an Instruction object.

        Args:
            file_path (str): The path of the file containing the instruction.
            line_number (int): The line number of the instruction.
            line (str): The instruction line itself.
        """
        self.line = sanitize_line(line)

        mnemonic, args = self._split_instruction(self.line)
        if not mnemonic:
            raise ValueError(f"Not an instruction statement: {line}")

        self.file_path = file_path
        self.line_number = line_number

        self.mnemonic = mnemonic
        self.args = args

    @staticmethod
    def _split_instruction(line):
        """
        Splits an instruction into its components ([mnemonic, arg1, arg2, ...]).
        This function handles the parsing of instructions into mnemonic and arguments,
        taking care of special cases like parentheses.

        Args:
            line (str): The line containing the instruction.

        Returns:
            tuple: A tuple containing the mnemonic and a list of arguments or an empty list if there are no arguments.
        """
        if not line:
            return None, []

        split = line.split(None, 1)
        mnemonic = split[0]

        if len(split) == 1:
            return mnemonic, []

        allargs = split[1]
        ret = []

        i = 0
        while i < len(allargs):
            # Do not split on commas inside parentheses!
            if allargs[i] == "(":
                while i < len(allargs) and allargs[i] != ")":
                    i += 1
                continue
            elif allargs[i] == ",":
                ret.append(allargs[:i].strip())
                allargs = allargs[i + 1 :]
                i = 0
            i += 1
        ret.append(allargs.strip())

        return mnemonic, ret

    def _is_register(self, arg):
        """
        Checks if the instruction argument is a register.

        Args:
            arg (str): The argument to check.

        Returns:
            bool: True if the argument is a register, False otherwise.
        """
        return arg.lower() in self._REGISTER_ARGS

    def is_call(self):
        """
        Returns the call target if the line is a call instruction, None otherwise.
        Precondition: line is after a function label.

        Criteria for a call:
            - Starts with 'call'
            or
            - Starts with 'jp'
            - Followed by a label which:
                - Starts with _ or a letter
                - Only contains letters, numbers, and '_'

        Returns:
            str: The call target if it is a call instruction, None otherwise.
        """
        if self.mnemonic == "call":
            return self.args[0]

        if self.mnemonic == "jp":
            label = self.args[0]
            if not (label.startswith("_") or label[0].isalpha()):
                return None
            if all(c.isalnum() or c == "_" for c in label):
                return label

    def is_iret(self):
        """
        Determines if the line marks an interrupt return.
        Precondition: line is after a function label.

        Criteria for an interrupt return:
            - Is 'iret'

        Returns:
            bool: True if the line marks an interrupt return, False otherwise.
        """
        return self.line == "iret"

    def is_int(self):
        """
        Determines if the line is an interrupt definition and the name of the interrupt if it is one.

        Criteria for an interrupt definition:
            - Starts with 'int'

        Returns:
            str: The interrupt name if it is an interrupt definition, None otherwise.
        """
        if self.mnemonic == "int":
            return self.args[0]
        return None

    def is_long_label_read(self):
        """
        Determines if a long addressing capable instruction reads from a label.
        If it does, it returns a tuple with the instruction mnemonic and the label.

        Criteria for a long label read:
            - Starts with an entry in LONG_READ_INSTRUCTIONS
            - If the instruction has a single argument:
                - The argument must contain a label
            - If the instruction has two comma separated arguments:
                - The src argument (right side of the comma) must contain a label
            - If the instruction has three comma separated arguments (btjt, btjf):
                - Either argument must contain a label

        A label is defined as:
            - Is preceded only by non-alphanumeric characters (else hex numbers would be detected)
            - Starts with a letter or '_'
            - Only contains letters, numbers, and '_'
            - Is not a register

        Note that this pattern match does not care how the label is referenced (immediate vs indirect).
        This means, both 'ldw x, #(_label+0)' and 'ldw x, _label+0' will match.

        Returns:
            tuple: A tuple containing the labels ([label1, label2, ...]) if it reads from one or more labels, None otherwise.
        """

        def is_valid_label_start(char, prev_char):
            return (char.isalpha() or char == "_") and (
                prev_char is None or not prev_char.isalnum()
            )

        def extract_label(arg):
            for i, char in enumerate(arg):
                if is_valid_label_start(char, arg[i - 1] if i > 0 else None):
                    label = "".join(
                        takewhile(lambda c: c.isalnum() or c == "_", arg[i:])
                    )
                    return label if not self._is_register(label) else None
            return None

        if self.mnemonic not in self._LONG_READ_INSTRUCTIONS:
            return None

        eval_args = (
            self.args
            if len(self.args) == 3
            else self.args[1:] if len(self.args) == 2 else self.args
        )

        labels = []
        for arg in eval_args:
            label = extract_label(arg)
            if label and label not in labels:
                labels.append(label)

        if labels:
            return labels

        return None

    @staticmethod
    def is_iret_instruction(eval):
        """
        Static method to check if an instance is an Instruction and is an iret instruction.

        Args:
            eval: The instance to check.

        Returns:
            bool: True if the instance is an Instruction and is an iret instruction, False otherwise.
        """
        return isinstance(eval, Instruction) and eval.is_iret()

    @staticmethod
    def is_interrupt_instruction(eval):
        """
        Static method to check if an instance is an Instruction and is an interrupt instruction.

        Args:
            eval: The instance to check.

        Returns:
            bool: True if the instance is an Instruction and is an interrupt instruction, False otherwise.
        """
        return isinstance(eval, Instruction) and eval.is_int()

    @staticmethod
    def is_call_instruction(eval):
        """
        Static method to check if an instance is an Instruction and is a call instruction.

        Args:
            eval: The instance to check.

        Returns:
            bool: True if the instance is an Instruction and is a call instruction, False otherwise.
        """
        return isinstance(eval, Instruction) and eval.is_call()

    @staticmethod
    def is_long_label_read_instruction(eval):
        """
        Static method to check if an instance is an Instruction and is a long label read instruction.

        Args:
            eval: The instance to check.

        Returns:
            bool: True if the instance is an Instruction and is a long label read instruction, False otherwise.
        """
        return isinstance(eval, Instruction) and eval.is_long_label_read()

    def __str__(self):
        return self.line

    def __repr__(self):
        return f"Instruction: {self.line}"


def _split_instruction_with_label(line):
    """
    Determines if a line contains a label followed by an instruction.
    If it does, it returns an iterator with the label and the instruction.
    If it doesn't, it returns an iterator with the line only.

    Criteria for a line with a label and instruction:
        - Starts with a label followed by ':'.
        - Followed by the instruction.

    Args:
        line (str): The line to check.

    Returns:
        iterator: An iterator containing the label and the instruction if the line contains a label and an instruction,
        an iterator containing only the line otherwise.
    """
    sline = sanitize_line(line)
    split = sline.split(":", 1)
    if len(split) == 2 and split[1].strip():
        return iter((split[0].strip() + ":", split[1].strip()))

    return iter((line.strip(),))


def match_asm_line(file_path, line_number, line):
    """
    Attempts to match a line of assembly code to its corresponding class(es) (Directive, Label, Instruction).
    If the line contains a label and an instruction, it will return a list of both.
    If there's no matching class for the line, an empty list is returned.

    Args:
        file_path (str): The path of the file containing the line.
        line_number (int): The line number of the line.
        line (str): The assembly line itself.

    Returns:
        list: A list containing the matched class(es) if any, an empty list otherwise.
    """
    line = sanitize_line(line)

    ret = []

    for part in _split_instruction_with_label(line):
        try:
            ret.append(Directive(file_path, line_number, part))
            continue
        except ValueError:
            pass

        try:
            ret.append(Label(file_path, line_number, part))
            continue
        except ValueError:
            pass

        try:
            ret.append(Instruction(file_path, line_number, part))
            continue
        except ValueError:
            pass

    return ret


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
