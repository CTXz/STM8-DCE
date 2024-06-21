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

# SDCC STM8 Dead Code Elimination Tool
# Description: Main file for the STM8 SDCC dead code elimination tool.

# Credits: This tool has been largely inspired by XaviDCR92's sdccrm tool:
#          https://github.com/XaviDCR92/sdccrm
#

"""
Unit tests for the STM8 SDCC dead code elimination tool.
"""

import unittest
import subprocess
import os
import sys
import colour_runner
import colour_runner.runner
from contextlib import contextmanager

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from stm8dce.__main__ import run


@contextmanager
def suppress_output():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


def asmsym(symbolname, filename, output_dir="build/dce"):
    return ("_" + symbolname, output_dir + "/" + filename.replace(".c", ".asm"))


def create_asmsyms(symbol_names, filename, output_dir="build/dce"):
    return [asmsym(name, filename, output_dir) for name in symbol_names]


def create_all_functions(output_dir="build/dce"):
    return (
        create_asmsyms(
            [
                "main",
                "alternative_main",
                "alternative_main_sub",
                "NON_EMPTY_IRQ_HANDLER_sub",
                "NON_EMPTY_IRQ_HANDLER",
                "EMPTY_IRQ_HANDLER",
            ],
            "main.c",
            output_dir,
        )
        + create_asmsyms(
            [
                "unused_function",
                "used_function_sub",
                "used_function",
                "function_used_by_ptr_sub",
                "function_used_by_ptr",
                "excluded_function_sub",
                "excluded_function",
                "local_excluded_function_sub",
                "local_excluded_function",
                "function_expected_by_module",
                "function_expected_by_module_sub",
                "local_function",
                "_main",
            ],
            "_main.c",
            output_dir,
        )
        + create_asmsyms(
            [
                "external_function_sub",
                "external_function",
                "local_excluded_function",
                "local_function",
            ],
            "extra.c",
            output_dir,
        )
    )


def create_all_constants(output_dir="build/dce"):
    return create_asmsyms(
        [
            "UNUSED_CONSTANT",
            "USED_CONSTANT",
            "CONSTANT_EXPECTED_BY_MODULE",
            "EXCLUDED_CONSTANT",
            "LOCAL_CONSTANT",
            "LOCAL_EXCLUDED_CONSTANT",
        ],
        "_main.c",
        output_dir,
    ) + create_asmsyms(
        ["EXTERNAL_CONST_ARRAY", "LOCAL_CONSTANT", "LOCAL_EXCLUDED_CONSTANT"],
        "extra.c",
        output_dir,
    )


def assert_eq_elements(expected, received):
    expected_set = set(expected)
    received_set = set(received)

    missing_elements = expected_set - received_set
    extraneous_elements = received_set - expected_set

    if missing_elements or extraneous_elements:
        raise AssertionError(
            f"Missing elements: {missing_elements}\n"
            f"Extraneous elements: {extraneous_elements}"
        )


def stm8dce_obj_to_asmsym(obj_list):
    return [(obj.name, obj.path) for obj in obj_list]


def antilist(full_list, sublist):
    return [item for item in full_list if item not in sublist]


def assert_dce(
    expected_kept_functions,
    expected_kept_constants,
    keep_functions,
    keep_constants,
    remove_functions,
    remove_constants,
    output_dir="build/dce",
    expected_removed_functions=None,
    expected_removed_constants=None,
):
    received_kept_functions = stm8dce_obj_to_asmsym(keep_functions)
    assert_eq_elements(expected_kept_functions, received_kept_functions)

    if expected_removed_functions is None:
        expected_removed_functions = antilist(
            create_all_functions(output_dir=output_dir), expected_kept_functions
        )
    received_removed_functions = stm8dce_obj_to_asmsym(remove_functions)
    assert_eq_elements(expected_removed_functions, received_removed_functions)

    received_kept_constants = stm8dce_obj_to_asmsym(keep_constants)
    assert_eq_elements(expected_kept_constants, received_kept_constants)

    if expected_removed_constants is None:
        expected_removed_constants = antilist(
            create_all_constants(output_dir=output_dir), expected_kept_constants
        )
    received_removed_constants = stm8dce_obj_to_asmsym(remove_constants)
    assert_eq_elements(expected_removed_constants, received_removed_constants)


class TestDeadCodeElimination(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # CD into the test directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Execute make clean
        result = subprocess.run(["make", "clean"], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"make clean failed with error: {result.stderr}")

        # Execute make asm
        result = subprocess.run(["make", "asm"], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"make asm failed with error: {result.stderr}")

        result = subprocess.run(["make", "asm_rel_lib"], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"make asm_rel_lib failed with error: {result.stderr}")

        # Execute make asm_custom_codeconstseg
        result = subprocess.run(
            ["make", "asm_custom_codeconstseg"], capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"make asm_custom_codeconstseg failed with error: {result.stderr}"
            )

        # Execute make rel
        result = subprocess.run(["make", "rel"], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"make rel failed with error: {result.stderr}")

        # Execute make lib
        result = subprocess.run(["make", "lib"], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"make lib failed with error: {result.stderr}")

    def test_general_optimization(self):
        output_dir = "build/dce"
        expected_kept_functions = (
            create_asmsyms(
                [
                    "main",
                    "NON_EMPTY_IRQ_HANDLER_sub",
                    "NON_EMPTY_IRQ_HANDLER",
                    "EMPTY_IRQ_HANDLER",
                ],
                "main.c",
            )
            + create_asmsyms(
                [
                    "_main",
                    "used_function",
                    "used_function_sub",
                    "local_function_sub",
                    "local_function",
                    "function_used_by_ptr",
                    "function_used_by_ptr_sub",
                ],
                "_main.c",
            )
            + create_asmsyms(
                [
                    "external_function",
                    "external_function_sub",
                ],
                "extra.c",
            )
        )

        expected_kept_functions.append(asmsym("NON_EMPTY_IRQ_HANDLER", "main.c"))

        expected_kept_constants = [
            asmsym("USED_CONSTANT", "_main.c"),
            asmsym("LOCAL_CONSTANT", "_main.c"),
            asmsym("EXTERNAL_CONST_ARRAY", "extra.c"),
        ]

        # Delete build/dce directory if it exists
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                os.remove(os.path.join(output_dir, file))
            os.rmdir(output_dir)

        # Create build/dce directory
        os.makedirs(output_dir)

        with suppress_output():
            (
                remove_functions,
                remove_constants,
                keep_functions,
                keep_constants,
            ) = run(
                input_files=[
                    "build/asm/main.asm",
                    "build/asm/_main.asm",
                    "build/asm/extra.asm",
                ],
                output_dir=output_dir,
                entry_label="_main",
                exclude_functions=None,
                exclude_constants=None,
                codeseg="CODE",
                constseg="CONST",
                verbose=False,
                debug_flag=False,
                opt_irq=False,
            )

        assert_dce(
            expected_kept_functions,
            expected_kept_constants,
            keep_functions,
            keep_constants,
            remove_functions,
            remove_constants,
            output_dir,
        )

        result = subprocess.run(["make", "elf_test"], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"make elf_test failed with error: {result.stderr}")

    def test_irq_optimization(self):
        output_dir = "build/dce"
        expected_kept_functions = (
            create_asmsyms(
                [
                    "main",
                    "NON_EMPTY_IRQ_HANDLER_sub",
                ],
                "main.c",
            )
            + create_asmsyms(
                [
                    "_main",
                    "used_function",
                    "used_function_sub",
                    "local_function_sub",
                    "local_function",
                    "function_used_by_ptr",
                    "function_used_by_ptr_sub",
                ],
                "_main.c",
            )
            + create_asmsyms(
                [
                    "external_function",
                    "external_function_sub",
                ],
                "extra.c",
            )
        )

        expected_kept_functions.append(asmsym("NON_EMPTY_IRQ_HANDLER", "main.c"))

        expected_kept_constants = [
            asmsym("USED_CONSTANT", "_main.c"),
            asmsym("LOCAL_CONSTANT", "_main.c"),
            asmsym("EXTERNAL_CONST_ARRAY", "extra.c"),
        ]

        # Delete build/dce directory if it exists
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                os.remove(os.path.join(output_dir, file))
            os.rmdir(output_dir)

        # Create build/dce directory
        os.makedirs(output_dir)

        with suppress_output():
            (
                remove_functions,
                remove_constants,
                keep_functions,
                keep_constants,
            ) = run(
                input_files=[
                    "build/asm/main.asm",
                    "build/asm/_main.asm",
                    "build/asm/extra.asm",
                ],
                output_dir=output_dir,
                entry_label="_main",
                exclude_functions=None,
                exclude_constants=None,
                codeseg="CODE",
                constseg="CONST",
                verbose=False,
                debug_flag=False,
                opt_irq=True,
            )

        assert_dce(
            expected_kept_functions,
            expected_kept_constants,
            keep_functions,
            keep_constants,
            remove_functions,
            remove_constants,
            output_dir,
        )

        result = subprocess.run(["make", "elf_test"], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"make elf_test failed with error: {result.stderr}")

    def test_exclusion(self):
        output_dir = "build/dce"
        expected_kept_functions = (
            create_asmsyms(
                [
                    "main",
                    "NON_EMPTY_IRQ_HANDLER_sub",
                    "NON_EMPTY_IRQ_HANDLER",
                    "EMPTY_IRQ_HANDLER",
                ],
                "main.c",
            )
            + create_asmsyms(
                [
                    "_main",
                    "used_function",
                    "used_function_sub",
                    "local_function_sub",
                    "local_function",
                    "function_used_by_ptr",
                    "function_used_by_ptr_sub",
                    "excluded_function",
                    "excluded_function_sub",
                    "local_excluded_function",
                    "local_excluded_function_sub",
                ],
                "_main.c",
            )
            + create_asmsyms(
                [
                    "external_function",
                    "external_function_sub",
                ],
                "extra.c",
            )
        )

        expected_kept_constants = [
            asmsym("USED_CONSTANT", "_main.c"),
            asmsym("EXCLUDED_CONSTANT", "_main.c"),
            asmsym("LOCAL_CONSTANT", "_main.c"),
            asmsym("LOCAL_EXCLUDED_CONSTANT", "_main.c"),
            asmsym("EXTERNAL_CONST_ARRAY", "extra.c"),
        ]

        # Delete build/dce directory if it exists
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                os.remove(os.path.join(output_dir, file))
            os.rmdir(output_dir)

        # Create build/dce directory
        os.makedirs(output_dir)

        with suppress_output():
            # Should raise a ValueError since _local_excluded_function
            # and _LOCAL_EXCLUDED_CONSTANT are defined multiple times
            # and must be provided with file:name syntax
            with self.assertRaises(ValueError):
                (
                    remove_functions,
                    remove_constants,
                    keep_functions,
                    keep_constants,
                ) = run(
                    input_files=[
                        "build/asm/main.asm",
                        "build/asm/_main.asm",
                        "build/asm/extra.asm",
                    ],
                    output_dir=output_dir,
                    entry_label="_main",
                    exclude_functions=[
                        "_excluded_function",
                        "_local_excluded_function",
                    ],
                    exclude_constants=[
                        "_EXCLUDED_CONSTANT",
                        "_LOCAL_EXCLUDED_CONSTANT",
                    ],
                    codeseg="CODE",
                    constseg="CONST",
                    verbose=False,
                    debug_flag=False,
                    opt_irq=False,
                )

        with suppress_output():
            (
                remove_functions,
                remove_constants,
                keep_functions,
                keep_constants,
            ) = run(
                input_files=[
                    "build/asm/main.asm",
                    "build/asm/_main.asm",
                    "build/asm/extra.asm",
                ],
                output_dir=output_dir,
                entry_label="_main",
                exclude_functions=[
                    "_excluded_function",
                    "_main.asm:_local_excluded_function",
                ],
                exclude_constants=[
                    "_EXCLUDED_CONSTANT",
                    "_main.asm:_LOCAL_EXCLUDED_CONSTANT",
                ],
                codeseg="CODE",
                constseg="CONST",
                verbose=False,
                debug_flag=False,
                opt_irq=False,
            )

        assert_dce(
            expected_kept_functions,
            expected_kept_constants,
            keep_functions,
            keep_constants,
            remove_functions,
            remove_constants,
            output_dir,
        )

        result = subprocess.run(["make", "elf_test"], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"make elf_test failed with error: {result.stderr}")

    def test_alternative_entry_point(self):
        output_dir = "build/dce"
        expected_kept_functions = (
            create_asmsyms(
                [
                    "alternative_main",
                    "alternative_main_sub",
                    "NON_EMPTY_IRQ_HANDLER_sub",
                    "NON_EMPTY_IRQ_HANDLER",
                    "EMPTY_IRQ_HANDLER",
                ],
                "main.c",
            )
            + create_asmsyms(
                [
                    "_main",
                    "used_function",
                    "used_function_sub",
                    "local_function_sub",
                    "local_function",
                    "function_used_by_ptr",
                    "function_used_by_ptr_sub",
                ],
                "_main.c",
            )
            + create_asmsyms(
                [
                    "external_function",
                    "external_function_sub",
                ],
                "extra.c",
            )
        )

        expected_kept_constants = [
            asmsym("USED_CONSTANT", "_main.c"),
            asmsym("LOCAL_CONSTANT", "_main.c"),
            asmsym("EXTERNAL_CONST_ARRAY", "extra.c"),
        ]

        # Delete build/dce directory if it exists
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                os.remove(os.path.join(output_dir, file))
            os.rmdir(output_dir)

        # Create build/dce directory
        os.makedirs(output_dir)

        with suppress_output():
            (
                remove_functions,
                remove_constants,
                keep_functions,
                keep_constants,
            ) = run(
                input_files=[
                    "build/asm/main.asm",
                    "build/asm/_main.asm",
                    "build/asm/extra.asm",
                ],
                output_dir=output_dir,
                entry_label="_alternative_main",
                exclude_functions=None,
                exclude_constants=None,
                codeseg="CODE",
                constseg="CONST",
                verbose=False,
                debug_flag=False,
                opt_irq=False,
            )

        assert_dce(
            expected_kept_functions,
            expected_kept_constants,
            keep_functions,
            keep_constants,
            remove_functions,
            remove_constants,
            output_dir,
        )

        # Afaik, sdcc doesn't even support alternative entry points atm...
        # result = subprocess.run(["make", "elf_alt_entry_test"], capture_output=True, text=True)
        # if result.returncode != 0:
        #     raise RuntimeError(f"make elf_alt_entry_test failed with error: {result.stderr}")

    def test_rel(self):
        output_dir = "build/dce_rel_lib"
        expected_kept_functions = (
            create_asmsyms(
                [
                    "main",
                    "NON_EMPTY_IRQ_HANDLER_sub",
                    "NON_EMPTY_IRQ_HANDLER",
                    "EMPTY_IRQ_HANDLER",
                ],
                "main.c",
                output_dir,
            )
            + create_asmsyms(
                [
                    "_main",
                    "used_function",
                    "used_function_sub",
                    "local_function_sub",
                    "local_function",
                    "function_used_by_ptr",
                    "function_used_by_ptr_sub",
                    "function_expected_by_module",
                    "function_expected_by_module_sub",
                ],
                "_main.c",
                output_dir,
            )
            + create_asmsyms(
                [
                    "external_function",
                    "external_function_sub",
                ],
                "extra.c",
                output_dir,
            )
        )

        expected_kept_constants = create_asmsyms(
            [
                "USED_CONSTANT",
                "CONSTANT_EXPECTED_BY_MODULE",
                "LOCAL_CONSTANT",
            ],
            "_main.c",
            output_dir,
        ) + create_asmsyms(
            ["EXTERNAL_CONST_ARRAY"],
            "extra.c",
            output_dir,
        )

        # Delete build/dce directory if it exists
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                os.remove(os.path.join(output_dir, file))
            os.rmdir(output_dir)

        # Create build/dce directory
        os.makedirs(output_dir)

        with suppress_output():
            (
                remove_functions,
                remove_constants,
                keep_functions,
                keep_constants,
            ) = run(
                input_files=[
                    "build/asm_rel_lib/main.asm",
                    "build/asm_rel_lib/_main.asm",
                    "build/asm_rel_lib/extra.asm",
                    "build/obj/rel.rel",
                ],
                output_dir=output_dir,
                entry_label="_main",
                exclude_functions=None,
                exclude_constants=None,
                codeseg="CODE",
                constseg="CONST",
                verbose=False,
                debug_flag=False,
                opt_irq=False,
            )

        assert_dce(
            expected_kept_functions,
            expected_kept_constants,
            keep_functions,
            keep_constants,
            remove_functions,
            remove_constants,
            output_dir,
        )

        result = subprocess.run(
            ["make", "elf_rel_test"], capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"make elf_rel_test failed with error: {result.stderr}")

    def test_lib(self):
        output_dir = "build/dce_rel_lib"

        ALL_FUNCTIONS_WITHOUT_MAIN = [
            f
            for f in create_all_functions(output_dir=output_dir)
            if f
            not in create_asmsyms(
                [
                    "main",
                    "alternative_main_sub",
                    "alternative_main",
                    "NON_EMPTY_IRQ_HANDLER_sub",
                    "NON_EMPTY_IRQ_HANDLER",
                    "EMPTY_IRQ_HANDLER",
                ],
                "main.c",
                output_dir=output_dir,
            )
        ]

        expected_kept_functions = create_asmsyms(
            [
                "_main",
                "used_function",
                "used_function_sub",
                "local_function_sub",
                "local_function",
                "function_used_by_ptr",
                "function_used_by_ptr_sub",
                "function_expected_by_module",
                "function_expected_by_module_sub",
            ],
            "_main.c",
            output_dir,
        ) + create_asmsyms(
            [
                "external_function",
                "external_function_sub",
            ],
            "extra.c",
            output_dir,
        )

        expected_kept_constants = create_asmsyms(
            [
                "USED_CONSTANT",
                "CONSTANT_EXPECTED_BY_MODULE",
                "LOCAL_CONSTANT",
            ],
            "_main.c",
            output_dir,
        ) + create_asmsyms(
            ["EXTERNAL_CONST_ARRAY"],
            "extra.c",
            output_dir,
        )

        # Delete build/dce directory if it exists
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                os.remove(os.path.join(output_dir, file))
            os.rmdir(output_dir)

        # Create build/dce directory
        os.makedirs(output_dir)

        with suppress_output():
            (
                remove_functions,
                remove_constants,
                keep_functions,
                keep_constants,
            ) = run(
                input_files=[
                    "build/asm_rel_lib/_main.asm",
                    "build/asm_rel_lib/extra.asm",
                    "build/obj/lib.lib",
                ],
                output_dir=output_dir,
                entry_label="_main",
                exclude_functions=None,
                exclude_constants=None,
                codeseg="CODE",
                constseg="CONST",
                verbose=False,
                debug_flag=False,
                opt_irq=False,
            )

        expected_removed_functions = antilist(
            ALL_FUNCTIONS_WITHOUT_MAIN, expected_kept_functions
        )
        expected_removed_constants = antilist(
            create_all_constants(output_dir=output_dir), expected_kept_constants
        )

        assert_dce(
            expected_kept_functions,
            expected_kept_constants,
            keep_functions,
            keep_constants,
            remove_functions,
            remove_constants,
            output_dir,
            expected_removed_functions=expected_removed_functions,
            expected_removed_constants=expected_removed_constants,
        )

    def test_custom_codeconstseg(self):
        # Same as general but with custom code and const segments
        output_dir = "build/dce_custom_codeconstseg"
        expected_kept_functions = (
            create_asmsyms(
                [
                    "main",
                    "NON_EMPTY_IRQ_HANDLER_sub",
                    "NON_EMPTY_IRQ_HANDLER",
                    "EMPTY_IRQ_HANDLER",
                ],
                "main.c",
                output_dir,
            )
            + create_asmsyms(
                [
                    "_main",
                    "used_function",
                    "used_function_sub",
                    "local_function_sub",
                    "local_function",
                    "function_used_by_ptr",
                    "function_used_by_ptr_sub",
                ],
                "_main.c",
                output_dir,
            )
            + create_asmsyms(
                [
                    "external_function",
                    "external_function_sub",
                ],
                "extra.c",
                output_dir,
            )
        )

        expected_kept_functions.append(
            asmsym("NON_EMPTY_IRQ_HANDLER", "main.c", output_dir)
        )

        expected_kept_constants = [
            asmsym("USED_CONSTANT", "_main.c", output_dir=output_dir),
            asmsym("LOCAL_CONSTANT", "_main.c", output_dir=output_dir),
            asmsym(
                "EXTERNAL_CONST_ARRAY",
                "extra.c",
                output_dir=output_dir,
            ),
        ]

        # Delete build/dce directory if it exists
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                os.remove(os.path.join(output_dir, file))
            os.rmdir(output_dir)

        # Create build/dce directory
        os.makedirs(output_dir)

        with suppress_output():
            (
                remove_functions,
                remove_constants,
                keep_functions,
                keep_constants,
            ) = run(
                input_files=[
                    "build/asm_custom_codeconstseg/main.asm",
                    "build/asm_custom_codeconstseg/_main.asm",
                    "build/asm_custom_codeconstseg/extra.asm",
                ],
                output_dir=output_dir,
                entry_label="_main",
                exclude_functions=None,
                exclude_constants=None,
                codeseg="XDDCODE",
                constseg="XDDCONST",
                verbose=False,
                debug_flag=False,
                opt_irq=False,
            )

        assert_dce(
            expected_kept_functions,
            expected_kept_constants,
            keep_functions,
            keep_constants,
            remove_functions,
            remove_constants,
            output_dir,
        )

        result = subprocess.run(
            ["make", "elf_custom_codeconstseg_test"], capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"make elf_custom_codeconstseg_test failed with error: {result.stderr}"
            )


if __name__ == "__main__":
    colour_runner.runner.ColourTextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromTestCase(TestDeadCodeElimination)
    )
