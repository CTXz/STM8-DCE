import unittest
import subprocess
import os
import sys
import colour_runner
import colour_runner.runner

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from stm8dce.__main__ import run


def asmtouple(symbolname, filename, output_dir="build/dce"):
    return ("_" + symbolname, output_dir + "/" + filename.replace(".c", ".asm"))


ALL_FUNCTIONS = [
    asmtouple("main", "main.c"),
    asmtouple("alternative_main_sub", "main.c"),
    asmtouple("NON_EMPTY_IRQ_HANDLER_sub", "main.c"),
    asmtouple("alternative_main", "main.c"),
    asmtouple("unused_function", "_main.c"),
    asmtouple("used_function_sub", "_main.c"),
    asmtouple("used_function", "_main.c"),
    asmtouple("function_used_by_ptr_sub", "_main.c"),
    asmtouple("function_used_by_ptr", "_main.c"),
    asmtouple("excluded_function_sub", "_main.c"),
    asmtouple("excluded_function", "_main.c"),
    asmtouple("local_excluded_function_sub", "_main.c"),
    asmtouple("local_excluded_function", "_main.c"),
    asmtouple("function_expected_by_module", "_main.c"),
    asmtouple("function_expected_by_module_sub", "_main.c"),
    asmtouple("local_function", "_main.c"),
    asmtouple("_main", "_main.c"),
    asmtouple("external_function_sub", "extra.c"),
    asmtouple("external_function", "extra.c"),
    asmtouple("local_excluded_function", "extra.c"),
    asmtouple("local_function", "extra.c"),
]

ALL_IRQ_HANDLERS = [
    asmtouple("NON_EMPTY_IRQ_HANDLER", "main.c"),
    asmtouple("EMPTY_IRQ_HANDLER", "main.c"),
]

ALL_CONSTANTS = [
    asmtouple("UNUSED_CONSTANT", "_main.c"),
    asmtouple("USED_CONSTANT", "_main.c"),
    asmtouple("CONSTANT_EXPECTED_BY_MODULE", "_main.c"),
    asmtouple("EXCLUDED_CONSTANT", "_main.c"),
    asmtouple("LOCAL_CONSTANT", "_main.c"),
    asmtouple("LOCAL_EXCLUDED_CONSTANT", "_main.c"),
    asmtouple("EXTERNAL_CONST_ARRAY", "extra.c"),
    asmtouple("LOCAL_CONSTANT", "extra.c"),
    asmtouple("LOCAL_EXCLUDED_CONSTANT", "extra.c"),
]

ALL_FUNCTIONS_CUSTOM_CODECONSTSEG = [
    asmtouple("main", "main.c", "build/dce_custom_codeconstseg"),
    asmtouple("alternative_main_sub", "main.c", "build/dce_custom_codeconstseg"),
    asmtouple("NON_EMPTY_IRQ_HANDLER_sub", "main.c", "build/dce_custom_codeconstseg"),
    asmtouple("alternative_main", "main.c", "build/dce_custom_codeconstseg"),
    asmtouple("unused_function", "_main.c", "build/dce_custom_codeconstseg"),
    asmtouple("used_function_sub", "_main.c", "build/dce_custom_codeconstseg"),
    asmtouple("used_function", "_main.c", "build/dce_custom_codeconstseg"),
    asmtouple("function_used_by_ptr_sub", "_main.c", "build/dce_custom_codeconstseg"),
    asmtouple("function_used_by_ptr", "_main.c", "build/dce_custom_codeconstseg"),
    asmtouple("excluded_function_sub", "_main.c", "build/dce_custom_codeconstseg"),
    asmtouple("excluded_function", "_main.c", "build/dce_custom_codeconstseg"),
    asmtouple(
        "local_excluded_function_sub", "_main.c", "build/dce_custom_codeconstseg"
    ),
    asmtouple("local_excluded_function", "_main.c", "build/dce_custom_codeconstseg"),
    asmtouple(
        "function_expected_by_module", "_main.c", "build/dce_custom_codeconstseg"
    ),
    asmtouple(
        "function_expected_by_module_sub", "_main.c", "build/dce_custom_codeconstseg"
    ),
    asmtouple("local_function", "_main.c", "build/dce_custom_codeconstseg"),
    asmtouple("_main", "_main.c", "build/dce_custom_codeconstseg"),
    asmtouple("external_function_sub", "extra.c", "build/dce_custom_codeconstseg"),
    asmtouple("external_function", "extra.c", "build/dce_custom_codeconstseg"),
    asmtouple("local_excluded_function", "extra.c", "build/dce_custom_codeconstseg"),
    asmtouple("local_function", "extra.c", "build/dce_custom_codeconstseg"),
]

ALL_IRQ_HANDLERS_CUSTOM_CODECONSTSEG = [
    asmtouple("NON_EMPTY_IRQ_HANDLER", "main.c", "build/dce_custom_codeconstseg"),
    asmtouple("EMPTY_IRQ_HANDLER", "main.c", "build/dce_custom_codeconstseg"),
]

ALL_CONSTANTS_CUSTOM_CODECONSTSEG = [
    asmtouple("UNUSED_CONSTANT", "_main.c", "build/dce_custom_codeconstseg"),
    asmtouple("USED_CONSTANT", "_main.c", "build/dce_custom_codeconstseg"),
    asmtouple(
        "CONSTANT_EXPECTED_BY_MODULE", "_main.c", "build/dce_custom_codeconstseg"
    ),
    asmtouple("EXCLUDED_CONSTANT", "_main.c", "build/dce_custom_codeconstseg"),
    asmtouple("LOCAL_CONSTANT", "_main.c", "build/dce_custom_codeconstseg"),
    asmtouple("LOCAL_EXCLUDED_CONSTANT", "_main.c", "build/dce_custom_codeconstseg"),
    asmtouple("EXTERNAL_CONST_ARRAY", "extra.c", "build/dce_custom_codeconstseg"),
    asmtouple("LOCAL_CONSTANT", "extra.c", "build/dce_custom_codeconstseg"),
    asmtouple("LOCAL_EXCLUDED_CONSTANT", "extra.c", "build/dce_custom_codeconstseg"),
]


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
        expected_kept_functions = [
            asmtouple("main", "main.c"),
            asmtouple("NON_EMPTY_IRQ_HANDLER_sub", "main.c"),
            asmtouple("_main", "_main.c"),
            asmtouple("used_function", "_main.c"),
            asmtouple("used_function_sub", "_main.c"),
            asmtouple("local_function_sub", "_main.c"),
            asmtouple("local_function", "_main.c"),
            asmtouple("function_used_by_ptr", "_main.c"),
            asmtouple("function_used_by_ptr_sub", "_main.c"),
            asmtouple("external_function", "extra.c"),
            asmtouple("external_function_sub", "extra.c"),
        ]

        expected_kept_functions += ALL_IRQ_HANDLERS

        # Delete build/dce directory if it exists
        if os.path.exists("build/dce"):
            for file in os.listdir("build/dce"):
                os.remove(os.path.join("build/dce", file))
            os.rmdir("build/dce")

        # Create build/dce directory
        os.makedirs("build/dce")

        input_files = [
            "build/asm/main.asm",
            "build/asm/_main.asm",
            "build/asm/extra.asm",
        ]
        output_dir = "build/dce"
        entry_label = "_main"
        exclude_functions = None
        exclude_constants = None
        codeseg = "CODE"
        constseg = "CONST"
        verbose = False
        debug_flag = False
        opt_irq = False

        (
            remove_functions,
            remove_constants,
            keep_functions,
            keep_constants,
        ) = run(
            input_files=input_files,
            output_dir=output_dir,
            entry_label=entry_label,
            exclude_functions=exclude_functions,
            exclude_constants=exclude_constants,
            codeseg=codeseg,
            constseg=constseg,
            verbose=verbose,
            debug_flag=debug_flag,
            opt_irq=opt_irq,
        )

        received_kept_functions = []
        for function_obj in keep_functions:
            received_kept_functions.append((function_obj.name, function_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_kept_functions)
        received_set = set(received_kept_functions)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in kept functions: {missing_elements}\n"
                f"Extraneous elements in kept functions: {extraneous_elements}"
            )

        expected_removed_functions = []
        for f in ALL_FUNCTIONS:
            if f not in expected_kept_functions:
                expected_removed_functions.append(f)

        received_removed_functions = []
        for function_obj in remove_functions:
            received_removed_functions.append((function_obj.name, function_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_removed_functions)
        received_set = set(received_removed_functions)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in removed functions: {missing_elements}\n"
                f"Extraneous elements in removed functions: {extraneous_elements}"
            )

        expected_kept_constants = [
            asmtouple("USED_CONSTANT", "_main.c"),
            asmtouple("LOCAL_CONSTANT", "_main.c"),
            asmtouple("EXTERNAL_CONST_ARRAY", "extra.c"),
        ]

        received_kept_constants = []
        for constant_obj in keep_constants:
            received_kept_constants.append((constant_obj.name, constant_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_kept_constants)
        received_set = set(received_kept_constants)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in kept constants: {missing_elements}\n"
                f"Extraneous elements in kept constants: {extraneous_elements}"
            )

        expected_removed_constants = []
        for c in ALL_CONSTANTS:
            if c not in expected_kept_constants:
                expected_removed_constants.append(c)

        received_removed_constants = []
        for constant_obj in remove_constants:
            received_removed_constants.append((constant_obj.name, constant_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_removed_constants)
        received_set = set(received_removed_constants)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in removed constants: {missing_elements}\n"
                f"Extraneous elements in removed constants: {extraneous_elements}"
            )

    def test_irq_optimization(self):
        expected_kept_functions = [
            asmtouple("main", "main.c"),
            asmtouple("NON_EMPTY_IRQ_HANDLER_sub", "main.c"),
            asmtouple("_main", "_main.c"),
            asmtouple("used_function", "_main.c"),
            asmtouple("used_function_sub", "_main.c"),
            asmtouple("local_function_sub", "_main.c"),
            asmtouple("local_function", "_main.c"),
            asmtouple("function_used_by_ptr", "_main.c"),
            asmtouple("function_used_by_ptr_sub", "_main.c"),
            asmtouple("external_function", "extra.c"),
            asmtouple("external_function_sub", "extra.c"),
        ]

        expected_kept_functions.append(asmtouple("NON_EMPTY_IRQ_HANDLER", "main.c"))

        # Delete build/dce directory if it exists
        if os.path.exists("build/dce"):
            for file in os.listdir("build/dce"):
                os.remove(os.path.join("build/dce", file))
            os.rmdir("build/dce")

        # Create build/dce directory
        os.makedirs("build/dce")

        input_files = [
            "build/asm/main.asm",
            "build/asm/_main.asm",
            "build/asm/extra.asm",
        ]

        output_dir = "build/dce"
        entry_label = "_main"
        exclude_functions = None
        exclude_constants = None
        codeseg = "CODE"
        constseg = "CONST"
        verbose = False
        debug_flag = False
        opt_irq = True

        (
            remove_functions,
            remove_constants,
            keep_functions,
            keep_constants,
        ) = run(
            input_files=input_files,
            output_dir=output_dir,
            entry_label=entry_label,
            exclude_functions=exclude_functions,
            exclude_constants=exclude_constants,
            codeseg=codeseg,
            constseg=constseg,
            verbose=verbose,
            debug_flag=debug_flag,
            opt_irq=opt_irq,
        )

        received_kept_functions = []
        for function_obj in keep_functions:
            received_kept_functions.append((function_obj.name, function_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_kept_functions)
        received_set = set(received_kept_functions)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in kept functions: {missing_elements}\n"
                f"Extraneous elements in kept functions: {extraneous_elements}"
            )

        expected_removed_functions = []
        for f in ALL_FUNCTIONS:
            if f not in expected_kept_functions:
                expected_removed_functions.append(f)

        expected_removed_functions.append(asmtouple("EMPTY_IRQ_HANDLER", "main.c"))

        received_removed_functions = []
        for function_obj in remove_functions:
            received_removed_functions.append((function_obj.name, function_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_removed_functions)
        received_set = set(received_removed_functions)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in removed functions: {missing_elements}\n"
                f"Extraneous elements in removed functions: {extraneous_elements}"
            )

        expected_kept_constants = [
            asmtouple("USED_CONSTANT", "_main.c"),
            asmtouple("LOCAL_CONSTANT", "_main.c"),
            asmtouple("EXTERNAL_CONST_ARRAY", "extra.c"),
        ]

        received_kept_constants = []
        for constant_obj in keep_constants:
            received_kept_constants.append((constant_obj.name, constant_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_kept_constants)
        received_set = set(received_kept_constants)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in kept constants: {missing_elements}\n"
                f"Extraneous elements in kept constants: {extraneous_elements}"
            )

        expected_removed_constants = []
        for c in ALL_CONSTANTS:
            if c not in expected_kept_constants:
                expected_removed_constants.append(c)

        received_removed_constants = []
        for constant_obj in remove_constants:
            received_removed_constants.append((constant_obj.name, constant_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_removed_constants)
        received_set = set(received_removed_constants)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in removed constants: {missing_elements}\n"
                f"Extraneous elements in removed constants: {extraneous_elements}"
            )

    def test_exclusion(self):
        expected_kept_functions = [
            asmtouple("main", "main.c"),
            asmtouple("NON_EMPTY_IRQ_HANDLER_sub", "main.c"),
            asmtouple("_main", "_main.c"),
            asmtouple("used_function", "_main.c"),
            asmtouple("used_function_sub", "_main.c"),
            asmtouple("local_function_sub", "_main.c"),
            asmtouple("local_function", "_main.c"),
            asmtouple("function_used_by_ptr", "_main.c"),
            asmtouple("function_used_by_ptr_sub", "_main.c"),
            asmtouple("external_function", "extra.c"),
            asmtouple("external_function_sub", "extra.c"),
            asmtouple("excluded_function", "_main.c"),
            asmtouple("excluded_function_sub", "_main.c"),
            asmtouple("local_excluded_function", "_main.c"),
            asmtouple("local_excluded_function_sub", "_main.c"),
        ]

        expected_kept_functions += ALL_IRQ_HANDLERS

        # Delete build/dce directory if it exists
        if os.path.exists("build/dce"):
            for file in os.listdir("build/dce"):
                os.remove(os.path.join("build/dce", file))
            os.rmdir("build/dce")

        # Create build/dce directory
        os.makedirs("build/dce")

        input_files = [
            "build/asm/main.asm",
            "build/asm/_main.asm",
            "build/asm/extra.asm",
        ]
        output_dir = "build/dce"
        entry_label = "_main"
        exclude_functions = ["_excluded_function", "_local_excluded_function"]
        exclude_constants = ["_EXCLUDED_CONSTANT", "_LOCAL_EXCLUDED_CONSTANT"]
        codeseg = "CODE"
        constseg = "CONST"
        verbose = False
        debug_flag = False
        opt_irq = False

        # Should raise a ValueError since _local_excluded_function
        # and _LOCAL_EXCLUDED_CONSTANT are defined multiple times
        # and must be provided with file:name syntax
        # TODO: Confirm ValueError is really the correct one
        with self.assertRaises(ValueError):
            (
                remove_functions,
                remove_constants,
                keep_functions,
                keep_constants,
            ) = run(
                input_files=input_files,
                output_dir=output_dir,
                entry_label=entry_label,
                exclude_functions=exclude_functions,
                exclude_constants=exclude_constants,
                codeseg=codeseg,
                constseg=constseg,
                verbose=verbose,
                debug_flag=debug_flag,
                opt_irq=opt_irq,
            )

        exclude_functions = ["_excluded_function", "_main.asm:_local_excluded_function"]
        exclude_constants = ["_EXCLUDED_CONSTANT", "_main.asm:_LOCAL_EXCLUDED_CONSTANT"]

        (
            remove_functions,
            remove_constants,
            keep_functions,
            keep_constants,
        ) = run(
            input_files=input_files,
            output_dir=output_dir,
            entry_label=entry_label,
            exclude_functions=exclude_functions,
            exclude_constants=exclude_constants,
            codeseg=codeseg,
            constseg=constseg,
            verbose=verbose,
            debug_flag=debug_flag,
            opt_irq=opt_irq,
        )

        received_kept_functions = []
        for function_obj in keep_functions:
            received_kept_functions.append((function_obj.name, function_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_kept_functions)
        received_set = set(received_kept_functions)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in kept functions: {missing_elements}\n"
                f"Extraneous elements in kept functions: {extraneous_elements}"
            )

        expected_removed_functions = []
        for f in ALL_FUNCTIONS:
            if f not in expected_kept_functions:
                expected_removed_functions.append(f)

        received_removed_functions = []
        for function_obj in remove_functions:
            received_removed_functions.append((function_obj.name, function_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_removed_functions)
        received_set = set(received_removed_functions)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in removed functions: {missing_elements}\n"
                f"Extraneous elements in removed functions: {extraneous_elements}"
            )

        expected_kept_constants = [
            asmtouple("USED_CONSTANT", "_main.c"),
            asmtouple("EXCLUDED_CONSTANT", "_main.c"),
            asmtouple("LOCAL_CONSTANT", "_main.c"),
            asmtouple("LOCAL_EXCLUDED_CONSTANT", "_main.c"),
            asmtouple("EXTERNAL_CONST_ARRAY", "extra.c"),
        ]

        received_kept_constants = []
        for constant_obj in keep_constants:
            received_kept_constants.append((constant_obj.name, constant_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_kept_constants)
        received_set = set(received_kept_constants)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in kept constants: {missing_elements}\n"
                f"Extraneous elements in kept constants: {extraneous_elements}"
            )

        expected_removed_constants = []
        for c in ALL_CONSTANTS:
            if c not in expected_kept_constants:
                expected_removed_constants.append(c)

        received_removed_constants = []
        for constant_obj in remove_constants:
            received_removed_constants.append((constant_obj.name, constant_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_removed_constants)
        received_set = set(received_removed_constants)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in removed constants: {missing_elements}\n"
                f"Extraneous elements in removed constants: {extraneous_elements}"
            )

    def test_alternative_entry_point(self):
        expected_kept_functions = [
            asmtouple("alternative_main", "main.c"),
            asmtouple("alternative_main_sub", "main.c"),
            asmtouple("NON_EMPTY_IRQ_HANDLER_sub", "main.c"),
            asmtouple("_main", "_main.c"),
            asmtouple("used_function", "_main.c"),
            asmtouple("used_function_sub", "_main.c"),
            asmtouple("local_function_sub", "_main.c"),
            asmtouple("local_function", "_main.c"),
            asmtouple("function_used_by_ptr", "_main.c"),
            asmtouple("function_used_by_ptr_sub", "_main.c"),
            asmtouple("external_function", "extra.c"),
            asmtouple("external_function_sub", "extra.c"),
        ]

        expected_kept_functions += ALL_IRQ_HANDLERS

        # Delete build/dce directory if it exists
        if os.path.exists("build/dce"):
            for file in os.listdir("build/dce"):
                os.remove(os.path.join("build/dce", file))
            os.rmdir("build/dce")

        # Create build/dce directory
        os.makedirs("build/dce")

        input_files = [
            "build/asm/main.asm",
            "build/asm/_main.asm",
            "build/asm/extra.asm",
        ]
        output_dir = "build/dce"
        entry_label = "_alternative_main"
        exclude_functions = None
        exclude_constants = None
        codeseg = "CODE"
        constseg = "CONST"
        verbose = False
        debug_flag = False
        opt_irq = False

        (
            remove_functions,
            remove_constants,
            keep_functions,
            keep_constants,
        ) = run(
            input_files=input_files,
            output_dir=output_dir,
            entry_label=entry_label,
            exclude_functions=exclude_functions,
            exclude_constants=exclude_constants,
            codeseg=codeseg,
            constseg=constseg,
            verbose=verbose,
            debug_flag=debug_flag,
            opt_irq=opt_irq,
        )

        received_kept_functions = []
        for function_obj in keep_functions:
            received_kept_functions.append((function_obj.name, function_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_kept_functions)
        received_set = set(received_kept_functions)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in kept functions: {missing_elements}\n"
                f"Extraneous elements in kept functions: {extraneous_elements}"
            )

        expected_removed_functions = []
        for f in ALL_FUNCTIONS:
            if f not in expected_kept_functions:
                expected_removed_functions.append(f)

        received_removed_functions = []
        for function_obj in remove_functions:
            received_removed_functions.append((function_obj.name, function_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_removed_functions)
        received_set = set(received_removed_functions)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in removed functions: {missing_elements}\n"
                f"Extraneous elements in removed functions: {extraneous_elements}"
            )

        expected_kept_constants = [
            asmtouple("USED_CONSTANT", "_main.c"),
            asmtouple("LOCAL_CONSTANT", "_main.c"),
            asmtouple("EXTERNAL_CONST_ARRAY", "extra.c"),
        ]

        received_kept_constants = []
        for constant_obj in keep_constants:
            received_kept_constants.append((constant_obj.name, constant_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_kept_constants)
        received_set = set(received_kept_constants)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in kept constants: {missing_elements}\n"
                f"Extraneous elements in kept constants: {extraneous_elements}"
            )

        expected_removed_constants = []
        for c in ALL_CONSTANTS:
            if c not in expected_kept_constants:
                expected_removed_constants.append(c)

        received_removed_constants = []
        for constant_obj in remove_constants:
            received_removed_constants.append((constant_obj.name, constant_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_removed_constants)
        received_set = set(received_removed_constants)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in removed constants: {missing_elements}\n"
                f"Extraneous elements in removed constants: {extraneous_elements}"
            )

    def test_rel(self):
        expected_kept_functions = [
            asmtouple("main", "main.c"),
            asmtouple("NON_EMPTY_IRQ_HANDLER_sub", "main.c"),
            asmtouple("_main", "_main.c"),
            asmtouple("used_function", "_main.c"),
            asmtouple("used_function_sub", "_main.c"),
            asmtouple("local_function_sub", "_main.c"),
            asmtouple("local_function", "_main.c"),
            asmtouple("function_used_by_ptr", "_main.c"),
            asmtouple("function_used_by_ptr_sub", "_main.c"),
            asmtouple("external_function", "extra.c"),
            asmtouple("external_function_sub", "extra.c"),
            asmtouple("function_expected_by_module", "_main.c"),
            asmtouple("function_expected_by_module_sub", "_main.c"),
        ]

        expected_kept_functions += ALL_IRQ_HANDLERS

        # Delete build/dce directory if it exists
        if os.path.exists("build/dce"):
            for file in os.listdir("build/dce"):
                os.remove(os.path.join("build/dce", file))
            os.rmdir("build/dce")

        # Create build/dce directory
        os.makedirs("build/dce")

        input_files = [
            "build/asm/main.asm",
            "build/asm/_main.asm",
            "build/asm/extra.asm",
            "build/obj/rel.rel",
        ]
        output_dir = "build/dce"
        entry_label = "_main"
        exclude_functions = None
        exclude_constants = None
        codeseg = "CODE"
        constseg = "CONST"
        verbose = False
        debug_flag = False
        opt_irq = False

        (
            remove_functions,
            remove_constants,
            keep_functions,
            keep_constants,
        ) = run(
            input_files=input_files,
            output_dir=output_dir,
            entry_label=entry_label,
            exclude_functions=exclude_functions,
            exclude_constants=exclude_constants,
            codeseg=codeseg,
            constseg=constseg,
            verbose=verbose,
            debug_flag=debug_flag,
            opt_irq=opt_irq,
        )

        received_kept_functions = []
        for function_obj in keep_functions:
            received_kept_functions.append((function_obj.name, function_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_kept_functions)
        received_set = set(received_kept_functions)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in kept functions: {missing_elements}\n"
                f"Extraneous elements in kept functions: {extraneous_elements}"
            )

        expected_removed_functions = []
        for f in ALL_FUNCTIONS:
            if f not in expected_kept_functions:
                expected_removed_functions.append(f)

        received_removed_functions = []
        for function_obj in remove_functions:
            received_removed_functions.append((function_obj.name, function_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_removed_functions)
        received_set = set(received_removed_functions)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in removed functions: {missing_elements}\n"
                f"Extraneous elements in removed functions: {extraneous_elements}"
            )

        expected_kept_constants = [
            asmtouple("USED_CONSTANT", "_main.c"),
            asmtouple("CONSTANT_EXPECTED_BY_MODULE", "_main.c"),
            asmtouple("LOCAL_CONSTANT", "_main.c"),
            asmtouple("EXTERNAL_CONST_ARRAY", "extra.c"),
        ]

        received_kept_constants = []
        for constant_obj in keep_constants:
            received_kept_constants.append((constant_obj.name, constant_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_kept_constants)
        received_set = set(received_kept_constants)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in kept constants: {missing_elements}\n"
                f"Extraneous elements in kept constants: {extraneous_elements}"
            )

        expected_removed_constants = []
        for c in ALL_CONSTANTS:
            if c not in expected_kept_constants:
                expected_removed_constants.append(c)

        received_removed_constants = []
        for constant_obj in remove_constants:
            received_removed_constants.append((constant_obj.name, constant_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_removed_constants)
        received_set = set(received_removed_constants)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in removed constants: {missing_elements}\n"
                f"Extraneous elements in removed constants: {extraneous_elements}"
            )

    def test_lib(self):
        ALL_FUNCTIONS_WITHOUT_MAIN = ALL_FUNCTIONS.copy()
        ALL_FUNCTIONS_WITHOUT_MAIN.remove(asmtouple("main", "main.c"))
        ALL_FUNCTIONS_WITHOUT_MAIN.remove(asmtouple("alternative_main_sub", "main.c"))
        ALL_FUNCTIONS_WITHOUT_MAIN.remove(asmtouple("alternative_main", "main.c"))
        ALL_FUNCTIONS_WITHOUT_MAIN.remove(
            asmtouple("NON_EMPTY_IRQ_HANDLER_sub", "main.c")
        )

        expected_kept_functions = [
            asmtouple("_main", "_main.c"),
            asmtouple("used_function", "_main.c"),
            asmtouple("used_function_sub", "_main.c"),
            asmtouple("local_function_sub", "_main.c"),
            asmtouple("local_function", "_main.c"),
            asmtouple("function_used_by_ptr", "_main.c"),
            asmtouple("function_used_by_ptr_sub", "_main.c"),
            asmtouple("external_function", "extra.c"),
            asmtouple("external_function_sub", "extra.c"),
            asmtouple("function_expected_by_module", "_main.c"),
            asmtouple("function_expected_by_module_sub", "_main.c"),
        ]

        # Delete build/dce directory if it exists
        if os.path.exists("build/dce"):
            for file in os.listdir("build/dce"):
                os.remove(os.path.join("build/dce", file))
            os.rmdir("build/dce")

        # Create build/dce directory
        os.makedirs("build/dce")

        input_files = [
            "build/asm/_main.asm",
            "build/asm/extra.asm",
            "build/obj/lib.lib",
        ]
        output_dir = "build/dce"
        entry_label = "_main"
        exclude_functions = None
        exclude_constants = None
        codeseg = "CODE"
        constseg = "CONST"
        verbose = False
        debug_flag = False
        opt_irq = False

        (
            remove_functions,
            remove_constants,
            keep_functions,
            keep_constants,
        ) = run(
            input_files=input_files,
            output_dir=output_dir,
            entry_label=entry_label,
            exclude_functions=exclude_functions,
            exclude_constants=exclude_constants,
            codeseg=codeseg,
            constseg=constseg,
            verbose=verbose,
            debug_flag=debug_flag,
            opt_irq=opt_irq,
        )

        received_kept_functions = []
        for function_obj in keep_functions:
            received_kept_functions.append((function_obj.name, function_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_kept_functions)
        received_set = set(received_kept_functions)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in kept functions: {missing_elements}\n"
                f"Extraneous elements in kept functions: {extraneous_elements}"
            )

        expected_removed_functions = []
        for f in ALL_FUNCTIONS_WITHOUT_MAIN:
            if f not in expected_kept_functions:
                expected_removed_functions.append(f)

        received_removed_functions = []
        for function_obj in remove_functions:
            received_removed_functions.append((function_obj.name, function_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_removed_functions)
        received_set = set(received_removed_functions)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in removed functions: {missing_elements}\n"
                f"Extraneous elements in removed functions: {extraneous_elements}"
            )

        expected_kept_constants = [
            asmtouple("USED_CONSTANT", "_main.c"),
            asmtouple("CONSTANT_EXPECTED_BY_MODULE", "_main.c"),
            asmtouple("LOCAL_CONSTANT", "_main.c"),
            asmtouple("EXTERNAL_CONST_ARRAY", "extra.c"),
        ]

        received_kept_constants = []
        for constant_obj in keep_constants:
            received_kept_constants.append((constant_obj.name, constant_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_kept_constants)
        received_set = set(received_kept_constants)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in kept constants: {missing_elements}\n"
                f"Extraneous elements in kept constants: {extraneous_elements}"
            )

        expected_removed_constants = []
        for c in ALL_CONSTANTS:
            if c not in expected_kept_constants:
                expected_removed_constants.append(c)

        received_removed_constants = []
        for constant_obj in remove_constants:
            received_removed_constants.append((constant_obj.name, constant_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_removed_constants)
        received_set = set(received_removed_constants)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in removed constants: {missing_elements}\n"
                f"Extraneous elements in removed constants: {extraneous_elements}"
            )

    def test_custom_codeconstseg(self):
        # Same as general but with custom code and const segments
        expected_kept_functions = [
            asmtouple("main", "main.c", output_dir="build/dce_custom_codeconstseg"),
            asmtouple(
                "NON_EMPTY_IRQ_HANDLER_sub",
                "main.c",
                output_dir="build/dce_custom_codeconstseg",
            ),
            asmtouple("_main", "_main.c", output_dir="build/dce_custom_codeconstseg"),
            asmtouple(
                "used_function", "_main.c", output_dir="build/dce_custom_codeconstseg"
            ),
            asmtouple(
                "used_function_sub",
                "_main.c",
                output_dir="build/dce_custom_codeconstseg",
            ),
            asmtouple(
                "local_function_sub",
                "_main.c",
                output_dir="build/dce_custom_codeconstseg",
            ),
            asmtouple(
                "local_function", "_main.c", output_dir="build/dce_custom_codeconstseg"
            ),
            asmtouple(
                "function_used_by_ptr",
                "_main.c",
                output_dir="build/dce_custom_codeconstseg",
            ),
            asmtouple(
                "function_used_by_ptr_sub",
                "_main.c",
                output_dir="build/dce_custom_codeconstseg",
            ),
            asmtouple(
                "external_function",
                "extra.c",
                output_dir="build/dce_custom_codeconstseg",
            ),
            asmtouple(
                "external_function_sub",
                "extra.c",
                output_dir="build/dce_custom_codeconstseg",
            ),
        ]

        expected_kept_functions += ALL_IRQ_HANDLERS_CUSTOM_CODECONSTSEG

        # Delete build/dce directory if it exists
        if os.path.exists("build/dce_custom_codeconstseg"):
            for file in os.listdir("build/dce_custom_codeconstseg"):
                os.remove(os.path.join("build/dce_custom_codeconstseg", file))
            os.rmdir("build/dce_custom_codeconstseg")

        # Create build/dce directory
        os.makedirs("build/dce_custom_codeconstseg")

        input_files = [
            "build/asm_custom_codeconstseg/main.asm",
            "build/asm_custom_codeconstseg/_main.asm",
            "build/asm_custom_codeconstseg/extra.asm",
        ]
        output_dir = "build/dce_custom_codeconstseg"
        entry_label = "_main"
        exclude_functions = None
        exclude_constants = None
        codeseg = "XDDCODE"
        constseg = "XDDCONST"
        verbose = False
        debug_flag = False
        opt_irq = False
        (
            remove_functions,
            remove_constants,
            keep_functions,
            keep_constants,
        ) = run(
            input_files=input_files,
            output_dir=output_dir,
            entry_label=entry_label,
            exclude_functions=exclude_functions,
            exclude_constants=exclude_constants,
            codeseg=codeseg,
            constseg=constseg,
            verbose=verbose,
            debug_flag=debug_flag,
            opt_irq=opt_irq,
        )

        received_kept_functions = []
        for function_obj in keep_functions:
            received_kept_functions.append((function_obj.name, function_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_kept_functions)
        received_set = set(received_kept_functions)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in kept functions: {missing_elements}\n"
                f"Extraneous elements in kept functions: {extraneous_elements}"
            )

        expected_removed_functions = []

        for f in ALL_FUNCTIONS_CUSTOM_CODECONSTSEG:
            if f not in expected_kept_functions:
                expected_removed_functions.append(f)

        received_removed_functions = []
        for function_obj in remove_functions:
            received_removed_functions.append((function_obj.name, function_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_removed_functions)
        received_set = set(received_removed_functions)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in removed functions: {missing_elements}\n"
                f"Extraneous elements in removed functions: {extraneous_elements}"
            )

        expected_kept_constants = [
            asmtouple(
                "USED_CONSTANT", "_main.c", output_dir="build/dce_custom_codeconstseg"
            ),
            asmtouple(
                "LOCAL_CONSTANT", "_main.c", output_dir="build/dce_custom_codeconstseg"
            ),
            asmtouple(
                "EXTERNAL_CONST_ARRAY",
                "extra.c",
                output_dir="build/dce_custom_codeconstseg",
            ),
        ]

        received_kept_constants = []
        for constant_obj in keep_constants:
            received_kept_constants.append((constant_obj.name, constant_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_kept_constants)
        received_set = set(received_kept_constants)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in kept constants: {missing_elements}\n"
                f"Extraneous elements in kept constants: {extraneous_elements}"
            )

        expected_removed_constants = []

        for c in ALL_CONSTANTS_CUSTOM_CODECONSTSEG:
            if c not in expected_kept_constants:
                expected_removed_constants.append(c)

        received_removed_constants = []
        for constant_obj in remove_constants:
            received_removed_constants.append((constant_obj.name, constant_obj.path))

        # Check for missing or extraneous elements
        expected_set = set(expected_removed_constants)
        received_set = set(received_removed_constants)

        missing_elements = expected_set - received_set
        extraneous_elements = received_set - expected_set

        if missing_elements or extraneous_elements:
            self.fail(
                f"Missing elements in removed constants: {missing_elements}\n"
                f"Extraneous elements in removed constants: {extraneous_elements}"
            )


if __name__ == "__main__":
    colour_runner.runner.ColourTextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromTestCase(TestDeadCodeElimination)
    )
