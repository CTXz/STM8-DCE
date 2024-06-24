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
Unit tests for the STM8 SDCC dead code elimination tool.
"""

import unittest
import subprocess
import os
import sys
import shutil
import colour_runner
import colour_runner.runner
from contextlib import contextmanager

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from stm8dce.__main__ import run

build_dir = "build"


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


def asmsym(symbolname, filename, output_dir):
    return ("_" + symbolname, output_dir + "/" + filename.replace(".c", ".asm"))


def create_asmsyms(symbol_names, filename, output_dir):
    return [asmsym(name, filename, output_dir) for name in symbol_names]


def create_all_functions(output_dir):
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
                "_main",
                "used_function_sub",
                "used_function",
                "unused_function",
                "unused_function_with_fptr",
                "function_used_by_ptr_sub",
                "recursive_function",
                "function_used_by_ptr",
                "excluded_function_sub",
                "excluded_function",
                "local_excluded_function_sub",
                "local_excluded_function",
                "function_expected_by_module",
                "function_expected_by_module_sub",
                "local_function",
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


def create_all_constants(output_dir):
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

    error_message = ""
    if missing_elements:
        error_message += f"Missing elements: {missing_elements}\n"
    if extraneous_elements:
        error_message += f"Extraneous elements: {extraneous_elements}\n"

    if error_message:
        raise AssertionError(error_message.strip())


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
    output_dir,
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


def c2asm(input_c_files, output_dir, args=[]):
    ret = []
    for input_c_file in input_c_files:
        ret.append(f"{output_dir}/{input_c_file.replace('.c', '.asm')}")
        subprocess.run(
            [
                "sdcc",
                "-o",
                ret[-1],
                "-mstm8",
                "--out-fmt-elf",
                "-DSTM8S103",
                "-S",
                input_c_file,
            ]
            + args,
            check=True,
        )
    return ret


def c2rel(input_c_files, output_dir, args=[]):
    ret = []
    for input_c_file in input_c_files:
        ret.append(
            f"{output_dir}/{os.path.basename(input_c_file).replace('.c', '.rel')}"
        )
        subprocess.run(
            [
                "sdcc",
                "-o",
                ret[-1],
                "-mstm8",
                "--out-fmt-elf",
                "-DSTM8S103",
                "-c",
                input_c_file,
            ]
            + args,
            check=True,
        )
    return ret


def asm2rel(input_asm_files, output_dir, args=[]):
    ret = []
    for input_asm_file in input_asm_files:
        ret.append(
            f"{output_dir}/{os.path.basename(input_asm_file).replace('.asm', '.rel')}"
        )
        subprocess.run(
            [
                "sdasstm8",
                "-plosg",
                "-ff",
                "-o",
                ret[-1],
                input_asm_file,
            ]
            + args,
            check=True,
        )
    return ret


def rel2lib(input_rel_files, out, args=[]):
    for input_rel_file in input_rel_files:
        subprocess.run(
            [
                "sdar",
                "-rcs",
                out,
                input_rel_file,
            ]
            + args,
            check=True,
        )


def create_elf(input_rel_or_lib_files, out, args=[]):
    subprocess.run(
        [
            "sdcc",
            "-o",
            out,
            "-mstm8",
            "--out-fmt-elf",
            "-DSTM8S103",
        ]
        + args
        + input_rel_or_lib_files,
        check=True,
    )


class TestDeadCodeElimination(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # CD into the test directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

    def setUp(self):
        self.build_dir = os.path.join(build_dir, self._testMethodName)
        self.dce_input_dir = self.build_dir + "/asm"
        self.dce_output_dir = self.build_dir + "/dce"
        self.rel_output_dir = self.build_dir + "/rel"
        self.lib_output_dir = self.build_dir + "/lib"

        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)

        os.makedirs(self.build_dir)
        os.makedirs(self.dce_input_dir)
        os.makedirs(self.dce_output_dir)
        os.makedirs(self.rel_output_dir)
        os.makedirs(self.lib_output_dir)

    def test_general_optimization(self):
        input_files = c2asm(
            [
                "main.c",
                "_main.c",
                "extra.c",
            ],
            self.dce_input_dir,
        )

        expected_kept_functions = (
            create_asmsyms(
                [
                    "main",
                    "NON_EMPTY_IRQ_HANDLER_sub",
                    "NON_EMPTY_IRQ_HANDLER",
                    "EMPTY_IRQ_HANDLER",
                ],
                "main.c",
                self.dce_output_dir,
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
                    "recursive_function",
                ],
                "_main.c",
                self.dce_output_dir,
            )
            + create_asmsyms(
                [
                    "external_function",
                    "external_function_sub",
                ],
                "extra.c",
                self.dce_output_dir,
            )
        )

        expected_kept_constants = create_asmsyms(
            [
                "USED_CONSTANT",
                "LOCAL_CONSTANT",
            ],
            "_main.c",
            self.dce_output_dir,
        ) + create_asmsyms(
            ["EXTERNAL_CONST_ARRAY"],
            "extra.c",
            self.dce_output_dir,
        )

        with suppress_output():
            (
                remove_functions,
                remove_constants,
                keep_functions,
                keep_constants,
            ) = run(
                input_files=input_files,
                output_dir=self.dce_output_dir,
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
            self.dce_output_dir,
        )

        rels = asm2rel(
            [
                f"{self.dce_output_dir}/main.asm",
                f"{self.dce_output_dir}/_main.asm",
                f"{self.dce_output_dir}/extra.asm",
            ],
            self.rel_output_dir,
        )

        create_elf(
            rels,
            f"{self.build_dir}/{self._testMethodName}.elf",
        )

    def test_irq_optimization(self):
        input_files = c2asm(
            [
                "main.c",
                "_main.c",
                "extra.c",
            ],
            self.dce_input_dir,
        )

        expected_kept_functions = (
            create_asmsyms(
                [
                    "main",
                    "NON_EMPTY_IRQ_HANDLER_sub",
                    "NON_EMPTY_IRQ_HANDLER",
                ],
                "main.c",
                self.dce_output_dir,
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
                    "recursive_function",
                ],
                "_main.c",
                self.dce_output_dir,
            )
            + create_asmsyms(
                [
                    "external_function",
                    "external_function_sub",
                ],
                "extra.c",
                self.dce_output_dir,
            )
        )

        expected_kept_constants = create_asmsyms(
            [
                "USED_CONSTANT",
                "LOCAL_CONSTANT",
            ],
            "_main.c",
            self.dce_output_dir,
        ) + create_asmsyms(
            ["EXTERNAL_CONST_ARRAY"],
            "extra.c",
            self.dce_output_dir,
        )

        with suppress_output():
            (
                remove_functions,
                remove_constants,
                keep_functions,
                keep_constants,
            ) = run(
                input_files=input_files,
                output_dir=self.dce_output_dir,
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
            self.dce_output_dir,
        )

        rels = asm2rel(
            [
                f"{self.dce_output_dir}/main.asm",
                f"{self.dce_output_dir}/_main.asm",
                f"{self.dce_output_dir}/extra.asm",
            ],
            self.rel_output_dir,
        )

        create_elf(
            rels,
            f"{self.build_dir}/{self._testMethodName}.elf",
        )

    def test_exclusion(self):
        input_files = c2asm(
            [
                "main.c",
                "_main.c",
                "extra.c",
            ],
            self.dce_input_dir,
        )

        expected_kept_functions = (
            create_asmsyms(
                [
                    "main",
                    "NON_EMPTY_IRQ_HANDLER_sub",
                    "NON_EMPTY_IRQ_HANDLER",
                    "EMPTY_IRQ_HANDLER",
                ],
                "main.c",
                self.dce_output_dir,
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
                    "recursive_function",
                    "excluded_function",
                    "excluded_function_sub",
                    "local_excluded_function",
                    "local_excluded_function_sub",
                ],
                "_main.c",
                self.dce_output_dir,
            )
            + create_asmsyms(
                [
                    "external_function",
                    "external_function_sub",
                ],
                "extra.c",
                self.dce_output_dir,
            )
        )

        expected_kept_constants = create_asmsyms(
            [
                "USED_CONSTANT",
                "EXCLUDED_CONSTANT",
                "LOCAL_CONSTANT",
                "LOCAL_EXCLUDED_CONSTANT",
            ],
            "_main.c",
            self.dce_output_dir,
        ) + create_asmsyms(
            ["EXTERNAL_CONST_ARRAY"],
            "extra.c",
            self.dce_output_dir,
        )

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
                    input_files=input_files,
                    output_dir=self.dce_output_dir,
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
                input_files=input_files,
                output_dir=self.dce_output_dir,
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
            self.dce_output_dir,
        )

        rels = asm2rel(
            [
                f"{self.dce_output_dir}/main.asm",
                f"{self.dce_output_dir}/_main.asm",
                f"{self.dce_output_dir}/extra.asm",
            ],
            self.rel_output_dir,
        )

        create_elf(
            rels,
            f"{self.build_dir}/{self._testMethodName}.elf",
        )

    def test_alternative_entry_point(self):
        input_files = c2asm(
            [
                "main.c",
                "_main.c",
                "extra.c",
            ],
            self.dce_input_dir,
        )

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
                self.dce_output_dir,
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
                    "recursive_function",
                ],
                "_main.c",
                self.dce_output_dir,
            )
            + create_asmsyms(
                [
                    "external_function",
                    "external_function_sub",
                ],
                "extra.c",
                self.dce_output_dir,
            )
        )

        expected_kept_constants = create_asmsyms(
            [
                "USED_CONSTANT",
                "LOCAL_CONSTANT",
            ],
            "_main.c",
            self.dce_output_dir,
        ) + create_asmsyms(
            ["EXTERNAL_CONST_ARRAY"],
            "extra.c",
            self.dce_output_dir,
        )

        with suppress_output():
            (
                remove_functions,
                remove_constants,
                keep_functions,
                keep_constants,
            ) = run(
                input_files=input_files,
                output_dir=self.dce_output_dir,
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
            self.dce_output_dir,
        )

        # Afaik, sdcc doesn't even support alternative entry points atm...
        # so we can't create an elf file for this test

    def test_rel(self):
        input_files = c2asm(
            [
                "main.c",
                "_main.c",
                "extra.c",
            ],
            self.dce_input_dir,
            args=["-DEXT"],
        ) + c2rel(["rel.c"], self.rel_output_dir)

        expected_kept_functions = (
            create_asmsyms(
                [
                    "main",
                    "NON_EMPTY_IRQ_HANDLER_sub",
                    "NON_EMPTY_IRQ_HANDLER",
                    "EMPTY_IRQ_HANDLER",
                ],
                "main.c",
                self.dce_output_dir,
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
                    "recursive_function",
                    "function_expected_by_module",
                    "function_expected_by_module_sub",
                ],
                "_main.c",
                self.dce_output_dir,
            )
            + create_asmsyms(
                [
                    "external_function",
                    "external_function_sub",
                ],
                "extra.c",
                self.dce_output_dir,
            )
        )

        expected_kept_constants = create_asmsyms(
            [
                "USED_CONSTANT",
                "CONSTANT_EXPECTED_BY_MODULE",
                "LOCAL_CONSTANT",
            ],
            "_main.c",
            self.dce_output_dir,
        ) + create_asmsyms(
            ["EXTERNAL_CONST_ARRAY"],
            "extra.c",
            self.dce_output_dir,
        )

        with suppress_output():
            (
                remove_functions,
                remove_constants,
                keep_functions,
                keep_constants,
            ) = run(
                input_files=input_files,
                output_dir=self.dce_output_dir,
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
            self.dce_output_dir,
        )

        rels = asm2rel(
            [
                f"{self.dce_output_dir}/main.asm",
                f"{self.dce_output_dir}/_main.asm",
                f"{self.dce_output_dir}/extra.asm",
            ],
            self.rel_output_dir,
        ) + [f"{self.rel_output_dir}/rel.rel"]

        create_elf(
            rels,
            f"{self.build_dir}/{self._testMethodName}.elf",
        )

    def test_lib(self):
        rels = c2rel(
            [
                "main.c",
                "rel.c",
            ],
            self.rel_output_dir,
        )

        lib = f"{self.lib_output_dir}/lib.lib"
        rel2lib(
            rels,
            lib,
        )

        input_files = c2asm(
            [
                "_main.c",
                "extra.c",
            ],
            self.dce_input_dir,
            args=["-DEXT"],
        ) + [lib]

        ALL_FUNCTIONS_WITHOUT_MAIN = [
            f
            for f in create_all_functions(output_dir=self.dce_output_dir)
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
                output_dir=self.dce_output_dir,
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
                "recursive_function",
                "function_expected_by_module",
                "function_expected_by_module_sub",
            ],
            "_main.c",
            self.dce_output_dir,
        ) + create_asmsyms(
            [
                "external_function",
                "external_function_sub",
            ],
            "extra.c",
            self.dce_output_dir,
        )

        expected_kept_constants = create_asmsyms(
            [
                "USED_CONSTANT",
                "CONSTANT_EXPECTED_BY_MODULE",
                "LOCAL_CONSTANT",
            ],
            "_main.c",
            self.dce_output_dir,
        ) + create_asmsyms(
            ["EXTERNAL_CONST_ARRAY"],
            "extra.c",
            self.dce_output_dir,
        )

        with suppress_output():
            (
                remove_functions,
                remove_constants,
                keep_functions,
                keep_constants,
            ) = run(
                input_files=input_files,
                output_dir=self.dce_output_dir,
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
            create_all_constants(output_dir=self.dce_output_dir),
            expected_kept_constants,
        )

        assert_dce(
            expected_kept_functions,
            expected_kept_constants,
            keep_functions,
            keep_constants,
            remove_functions,
            remove_constants,
            self.dce_output_dir,
            expected_removed_functions=expected_removed_functions,
            expected_removed_constants=expected_removed_constants,
        )

        rels = asm2rel(
            [
                f"{self.dce_output_dir}/_main.asm",
                f"{self.dce_output_dir}/extra.asm",
            ],
            self.rel_output_dir,
        )

        create_elf(
            rels + [lib],
            f"{self.build_dir}/{self._testMethodName}.elf",
        )

    def test_custom_codeconstseg(self):
        input_files = c2asm(
            [
                "main.c",
                "_main.c",
                "extra.c",
            ],
            self.dce_input_dir,
            args=["--codeseg", "XDDCODE", "--constseg", "XDDCONST"],
        )

        expected_kept_functions = (
            create_asmsyms(
                [
                    "main",
                    "NON_EMPTY_IRQ_HANDLER_sub",
                    "NON_EMPTY_IRQ_HANDLER",
                    "EMPTY_IRQ_HANDLER",
                ],
                "main.c",
                self.dce_output_dir,
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
                    "recursive_function",
                ],
                "_main.c",
                self.dce_output_dir,
            )
            + create_asmsyms(
                [
                    "external_function",
                    "external_function_sub",
                ],
                "extra.c",
                self.dce_output_dir,
            )
        )

        expected_kept_constants = create_asmsyms(
            [
                "USED_CONSTANT",
                "LOCAL_CONSTANT",
            ],
            "_main.c",
            self.dce_output_dir,
        ) + create_asmsyms(
            ["EXTERNAL_CONST_ARRAY"],
            "extra.c",
            self.dce_output_dir,
        )

        with suppress_output():
            (
                remove_functions,
                remove_constants,
                keep_functions,
                keep_constants,
            ) = run(
                input_files=input_files,
                output_dir=self.dce_output_dir,
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
            self.dce_output_dir,
        )

        rels = asm2rel(
            [
                f"{self.dce_output_dir}/main.asm",
                f"{self.dce_output_dir}/_main.asm",
                f"{self.dce_output_dir}/extra.asm",
            ],
            self.rel_output_dir,
        )

        create_elf(
            rels,
            f"{self.build_dir}/{self._testMethodName}.elf",
        )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        build_dir = sys.argv[1]

    res = colour_runner.runner.ColourTextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromTestCase(TestDeadCodeElimination)
    )

    if res.failures or res.errors:
        sys.exit(1)
