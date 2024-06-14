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
This module provides functions to pattern match STM8 SDCC generated assembly code
"""

from itertools import takewhile

############################################
# Constants
############################################

# List of all possible register arguments
REGISTER_ARGS = [
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

# Read instructions that support long addressing mode
# The following resources were used to determine this list:
#  - PM0044 STM8 CPU Programming Manual
#  - SDCC Source Code:
#   - sdcc/sdas/asstm8/stm8mch.c
#   - sdcc/sdas/asstm8/stm8pst.c
#   - sdcc/sdas/asstm8/stm8.h

LONG_READ_INSTRUCTIONS = [
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

############################################
# Helper Functions
############################################


def remove_comments(line):
    """
    Removes comments from a line to prevent them from affecting pattern matching.

    Criteria for a comment:
        - Starts at ';'

    Args:
        line (str): The line from which comments need to be removed.

    Returns:
        str: The line without comments.
    """
    return line.split(";")[0].strip()


def split_instruction(line):
    """
    Splits an instruction into its components ([mnem, arg1, arg2, ...]).
    This function handles the parsing of instructions into mnemonic and arguments,
    taking care of special cases like parentheses.

    Args:
        line (str): The line containing the instruction.

    Returns:
        list: A list of instruction components.
    """
    sline = remove_comments(line)

    if not sline:
        return None

    split = sline.split(None, 1)
    mnem = split[0]

    if len(split) == 1:
        return [mnem]

    allargs = split[1]
    ret = [mnem]

    i = 0
    while i < len(allargs):
        # Do not split on commas inside parentheses!
        if allargs[i] == "(":
            while allargs[i] != ")":
                i += 1
            continue
        elif allargs[i] == ",":
            ret.append(allargs[:i].strip())
            allargs = allargs[i + 1 :]
            i = 0
        i += 1
    ret.append(allargs.strip())

    return ret


############################################
# Matchers
############################################


def is_comment(line):
    """
    Determines if the line is a comment.

    Criteria for a comment:
        - Starts with ';'

    Args:
        line (str): The line to check.

    Returns:
        bool: True if the line is a comment, False otherwise.
    """
    return line.strip().startswith(";")


def is_register(arg):
    """
    Checks if the instruction argument is a register.

    Args:
        arg (str): The argument to check.

    Returns:
        bool: True if the argument is a register, False otherwise.
    """
    return arg.lower() in REGISTER_ARGS


def is_function_label(line):
    """
    Checks if the line is a function label.
    Precondition: line is in the code section.

    Criteria for a function label:
        - Is not a comment
        - Ends with ':'
        - Second last character is not a '$' (nnnnn$: are local labels)

    Args:
        line (str): The line to check.

    Returns:
        str: The function label if it is a function label, None otherwise.
    """
    sline = remove_comments(line)

    if sline.endswith(":") and sline[-2] != "$":
        return sline[:-1]

    return None


def is_constant_label(line):
    """
    Checks if the line is a constant label.
    Precondition: line is in the constants section.

    Criteria for a constant label:
        - Same as function label

    Args:
        line (str): The line to check.

    Returns:
        str: The constant label if it is a constant label, None otherwise.
    """
    return is_function_label(line)


def is_call(line):
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

    Args:
        line (str): The line to check.

    Returns:
        str: The call target if it is a call instruction, None otherwise.
    """
    sline = remove_comments(line.strip())

    if sline.startswith("call"):
        return sline.split("call")[1].strip()

    if sline.startswith("jp"):
        label = sline.split("jp")[1].strip()
        if not (label.startswith("_") or label[0].isalpha()):
            return None
        if all(c.isalnum() or c == "_" for c in label):
            return label

    return None


def is_iret(line):
    """
    Determines if the line marks an interrupt return.
    Precondition: line is after a function label.

    Criteria for an interrupt return:
        - Is 'iret'

    Args:
        line (str): The line to check.

    Returns:
        bool: True if the line marks an interrupt return, False otherwise.
    """
    sline = remove_comments(line.strip())
    if sline == "iret":
        return True
    return False


def is_area(line):
    """
    Determines if the line is an area directive and which area it is.

    Criteria for an area directive:
        - Starts with '.area'

    Args:
        line (str): The line to check.

    Returns:
        str: The area name if it is an area directive, None otherwise.
    """
    sline = remove_comments(line.strip())
    if sline.startswith(".area"):
        return sline.split(".area")[1].strip()
    return None


def is_global_defs(line):
    """
    Determines if the line is a global definition and the name of the global if it is one.

    Criteria for a global definition:
        - Starts with '.globl'

    Args:
        line (str): The line to check.

    Returns:
        str: The global name if it is a global definition, None otherwise.
    """
    sline = remove_comments(line.strip())
    if sline.startswith(".globl"):
        return sline.split(".globl")[1].strip()
    return None


def is_int_def(line):
    """
    Determines if the line is an interrupt definition and the name of the interrupt if it is one.

    Criteria for an interrupt definition:
        - Starts with 'int'

    Args:
        line (str): The line to check.

    Returns:
        str: The interrupt name if it is an interrupt definition, None otherwise.
    """
    sline = remove_comments(line.strip())
    if sline.startswith("int"):
        return sline.split("int")[1].strip()
    return None


def is_long_label_read(line):
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

    Args:
        line (str): The line to check.

    Returns:
        tuple: A tuple containing the mnemonic and the label(s) (mnem, [label1, label2, ...])
        if it reads from one or more labels, None otherwise.
    """

    def is_valid_label_start(char, prev_char):
        return (char.isalpha() or char == "_") and (
            prev_char is None or not prev_char.isalnum()
        )

    def extract_label(arg):
        for i, char in enumerate(arg):
            if is_valid_label_start(char, arg[i - 1] if i > 0 else None):
                label = "".join(takewhile(lambda c: c.isalnum() or c == "_", arg[i:]))
                return label if not is_register(label) else None
        return None

    sline = remove_comments(line.strip())
    split = split_instruction(sline)
    if not split or split[0] not in LONG_READ_INSTRUCTIONS:
        return None

    mnem, *args = split
    eval_args = args if len(args) == 3 else args[1:] if len(args) == 2 else args

    labels = []
    for arg in eval_args:
        label = extract_label(arg)
        if label and label not in labels:
            labels.append(label)

    if labels:
        return mnem, labels

    return None
