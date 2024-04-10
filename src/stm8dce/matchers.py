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

# Description:
#   Functions to pattern match STM8 SDCC generated assembly code


# Removes comments from a line
# This is used to prevent comments from
# polluting the pattern matching
# Criteria for a comment:
#   - Starts at ';'
def remove_comments(line):
    return line.split(";")[0].strip()


# Returns if the line is a comment
# Criteria for a comment:
#   - Start with ';'
def is_comment(line):
    return line.strip().startswith(";")


# Returns if the line is a function label
# Precondition: line is in code section
# Critera for a function label:
#   - Is not a comment
#   - Ends with ':'
#   - Second last character is not a '$' (nnnnn$ are local labels)
def is_function_label(line):
    sline = line.strip()

    if is_comment(sline):
        return None

    sline = remove_comments(sline)

    if sline.endswith(":") and sline[-2] != "$":
        return sline[:-1]


# Returns if the line is a constant label
# Precondition: line is in constants section
# Critera for a constant label:
#   - Same as function label
def is_constant_label(line):
    return is_function_label(line)


# Preconditions: line is after a function label
# Returns the call target if the line is a call
# instruction, None otherwise
# Critera for a call:
#   - Starts with 'call'
# or
#   - Starts with 'jp'
#   - Followed by a label which:
#       - Starts with _ or a letter
#       - Only contains letters, numbers, and '_'
def is_call(line):
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


# Preconditions: line is after a function label
# Returns if the line marks a interrupt return
# Critera for a interrupt return:
#   - Is 'iret'
def is_iret(line):
    sline = remove_comments(line.strip())
    if sline == "iret":
        return True
    return False


# Returns if the line is an area directive
# and which area it is
# Criteria for an area directive:
#   - Start with '.area'
def is_area(line):
    sline = remove_comments(line.strip())
    if sline.startswith(".area"):
        return sline.split(".area")[1].strip()
    return None


# Returns if the line is a global definition
# and the name of the global if it is one
# Critera for a global definition:
#   - Start with '.globl'
def is_global_defs(line):
    sline = remove_comments(line.strip())
    if sline.startswith(".globl"):
        return sline.split(".globl")[1].strip()
    return None


# Returns if the line is an interrupt definition
# and the name of the interrupt if it is one
# Critera for an interrupt definition:
#   - Start with 'int'
def is_int_def(line):
    sline = remove_comments(line.strip())
    if sline.startswith("int"):
        return sline.split("int")[1].strip()
    return None


# Returns if the line is a load with a label
# as src
# Criteria for a load:
#   - Start with 'ld' or 'ldw' or 'ldf'
#   - Dst (Left) and src (Right) are separated by ','
#   - Src must contain a label appended with a + and a number (e.g., _label+1)
def is_load_src_label(line):
    sline = remove_comments(line.strip())
    if not (
        sline.startswith("ld") or sline.startswith("ldw") or sline.startswith("ldf")
    ):
        return None

    if "," not in sline:
        return None

    src = sline.split(",")[1].strip()
    if "+" not in src:
        return None

    label = src.split("+")[0].strip()
    # Label might currently include parantheses etc.
    # Remove them until we get to the actual label
    for i in range(len(label)):
        if label[i].isalnum() or label[i] == "_":
            return label[i:]

    return None
