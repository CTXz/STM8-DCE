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
This module provides classes and functions to parse STM8 SDCC generated assembly files.
"""

from . import settings
from . import debug
from . import matchers
from . import analysis

############################################
# Classes
############################################


class FileIterator:
    """
    Class to iterate over lines in a file.

    Attributes:
        path (str): The path of the file.
        index (int): The current line number.
    """

    def __init__(self, file_obj):
        """
        Initializes the FileIterator with the given file object.

        Args:
            file_obj (file): The file object to iterate over.
        """
        self.path = file_obj.name
        self.iterable = file_obj.readlines()
        self.index = 0

    def __iter__(self):
        return self

    def next(self):
        """
        Returns the next line in the file.

        Returns:
            str: The next line in the file.

        Raises:
            StopIteration: If the end of the file is reached.
        """
        if self.index < len(self.iterable):
            ret_line = self.iterable[self.index]
            self.index += 1
            return ret_line
        else:
            raise StopIteration

    def prev(self):
        """
        Moves back one line in the file.

        Returns:
            str: The previous line in the file.

        Raises:
            StopIteration: If the beginning of the file is reached.
        """
        if self.index > 0:
            self.index -= 1
            return self.iterable[self.index]
        else:
            raise StopIteration


############################################
# Parsing
############################################


def parse_file(file_path):
    """
    Parses a file and returns a list of:
        - Function objects
        - GlobalDef objects
        - IntDef objects
        - Constant objects

    This function opens the file and creates a FileIterator.
    The actual parsing is done by the parse() function.

    Args:
        file_path (str): The path to the file to be parsed.

    Returns:
        tuple: A tuple containing lists of global definitions, interrupt definitions, constants, and functions.
    """
    debug.pdbg()
    debug.pdbg(f"Parsing file: {file_path}")
    debug.pseperator()

    with open(file_path, "r") as file_obj:
        file_iterator = FileIterator(file_obj)
        return parse(file_iterator)


def parse(file_iterator):
    """
    Parses the file iterator and returns a list of:
        - Function objects
        - GlobalDef objects
        - IntDef objects
        - Constant objects

    Parsing includes:
        - Detecting global definitions
        - Detecting interrupt definitions
        - Detecting and parsing code sections (see parse_code_section)
        - Detecting and parsing constant sections (see parse_const_section)

    Args:
        file_iterator (FileIterator): The file iterator to parse.

    Returns:
        tuple: A tuple containing lists of global definitions, interrupt definitions, constants, and functions.
    """
    globals_list = []
    interrupts_list = []
    functions_list = []
    constants_list = []
    while True:
        try:
            current_line = file_iterator.next()
        except StopIteration:
            break

        # Global definitions
        global_defs = matchers.is_global_defs(current_line)
        if global_defs:
            globals_list.append(
                analysis.GlobalDef(file_iterator.path, global_defs, file_iterator.index)
            )
            debug.pdbg(f"Line {file_iterator.index}: Global definition {global_defs}")
            continue

        # Interrupt definitions
        int_def = matchers.is_int_def(current_line)
        if int_def:
            interrupts_list.append(
                analysis.IntDef(file_iterator.path, int_def, file_iterator.index)
            )
            debug.pdbg(f"Line {file_iterator.index}: Interrupt definition {int_def}")
            continue

        # Code section
        area = matchers.is_area(current_line)
        if area == "CODE":
            functions_list += parse_code_section(file_iterator)

        # Constants section
        if area == "CONST":
            constants_list += parse_const_section(file_iterator)

    return globals_list, interrupts_list, constants_list, functions_list


def parse_code_section(file_iterator):
    """
    Parses the code section of the file and returns a list of Function objects within the code section.

    Parsing includes:
        - Detecting and parsing functions (see parse_function)
        - Detecting end of code section

    Args:
        file_iterator (FileIterator): The file iterator to parse.

    Returns:
        list: A list of Function objects.
    """
    debug.pdbg(f"Line {file_iterator.index}: Code section starts here")

    functions_list = []
    while True:
        try:
            current_line = file_iterator.next()
        except StopIteration:
            break

        # Check if this is the end of the code section (start of a new area)
        area = matchers.is_area(current_line)
        if area:
            file_iterator.prev()  # Set back as this line is not part of the code section
            break

        # Parse function if a function label is found
        function_label = matchers.is_function_label(current_line)
        if function_label:
            functions_list += [parse_function(file_iterator, function_label)]

    debug.pdbg(f"Line {file_iterator.index}: Code section ends here")

    return functions_list


def parse_const_section(file_iterator):
    """
    Parses the constants section of the file and returns a list of Constant objects.

    Parsing includes:
        - Detecting constants
        - Detecting end of constants section

    Args:
        file_iterator (FileIterator): The file iterator to parse.

    Returns:
        list: A list of Constant objects.
    """
    debug.pdbg(f"Line {file_iterator.index}: Constants section starts here")

    constants_list = []
    while True:
        try:
            current_line = file_iterator.next()
        except StopIteration:
            break

        # Check if this is the end of the constants section (start of a new area)
        area = matchers.is_area(current_line)
        if area:
            file_iterator.prev()  # Set back as this line is not part of the constants section
            break

        # Parse constant if a constant label is found
        constant_label = matchers.is_constant_label(current_line)
        if constant_label:
            constants_list += [parse_constant(file_iterator, constant_label)]

    debug.pdbg(f"Line {file_iterator.index}: Constants section ends here")

    return constants_list


def parse_function(file_iterator, label):
    """
    Parses a function and returns a Function object.

    Parsing includes:
        - Detecting if the function is empty
        - Detecting calls made by the function
        - Detecting if the function is an IRQ handler
        - Detecting the end of the function

    Args:
        file_iterator (FileIterator): The file iterator to parse.
        label (str): The label of the function.

    Returns:
        Function: The parsed Function object.
    """
    debug.pdbg(f"Line {file_iterator.index}: Function {label} starts here")

    ret_function = analysis.Function(file_iterator.path, label, file_iterator.index)
    while True:
        try:
            current_line = file_iterator.next()
        except StopIteration:
            break

        # Ignore comments
        if matchers.is_comment(current_line):
            continue

        # Check if this is an IRQ handler
        if matchers.is_iret(current_line):
            debug.pdbg(
                f"Line {file_iterator.index}: Function {label} detected as IRQ Handler"
            )
            ret_function.isr = True
            continue

        # Check if this is the end of the function
        if matchers.is_function_label(current_line) or matchers.is_area(current_line):
            # Set back as this line is not part of the function
            file_iterator.prev()
            ret_function.end_line = file_iterator.index
            break

        # From here on we can assume the function is not empty
        ret_function.empty = False

        # Keep track of calls made by this function
        call_match = matchers.is_call(current_line)
        if call_match:
            debug.pdbg(f"Line {file_iterator.index}: Call to {call_match}")
            if call_match not in ret_function.calls_str:
                ret_function.calls_str.append(call_match)
            continue

        # Keep track of labels read by long address capable instructions
        # Note that calls are excluded from this list as they are already
        # handled above
        match_long_label_read = matchers.is_long_label_read(current_line)
        if match_long_label_read:
            operation, long_labels = match_long_label_read
            for long_label in long_labels:
                debug.pdbg(
                    f"Line {file_iterator.index} ({operation}): long address label {long_label} is read here"
                )
                if long_label not in ret_function.long_read_labels_str:
                    ret_function.long_read_labels_str.append(long_label)
            continue

    if ret_function.empty:
        debug.pdbg(f"Line {file_iterator.index}: Function {label} is empty!")
    debug.pdbg(f"Line {file_iterator.index}: Function {label} ends here")

    return ret_function


def parse_constant(file_iterator, label):
    """
    Parses a constant and returns a Constant object.

    Args:
        file_iterator (FileIterator): The file iterator to parse.
        label (str): The label of the constant.

    Returns:
        Constant: The parsed Constant object.
    """
    debug.pdbg(f"Line {file_iterator.index}: Constant {label} starts here")

    ret_constant = analysis.Constant(file_iterator.path, label, file_iterator.index)
    while True:
        try:
            current_line = file_iterator.next()
        except StopIteration:
            break

        # Ignore comments
        if matchers.is_comment(current_line):
            continue

        # Check if this is the end of the constant
        if matchers.is_constant_label(current_line) or matchers.is_area(current_line):
            # Set back as this line is not part of the constant
            file_iterator.prev()
            ret_constant.end_line = file_iterator.index
            break

    debug.pdbg(f"Line {file_iterator.index}: Constant {label} ends here")

    return ret_constant
