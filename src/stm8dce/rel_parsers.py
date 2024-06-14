from . import rel_matchers
from . import rel_analysis
from . import debug

from .FileIterator import FileIterator


def parse_file(file_path):
    debug.pdbg()
    debug.pdbg(f"Parsing file: {file_path}")
    debug.pseperator()

    with open(file_path, "r", errors="replace") as file_obj:
        file_iterator = FileIterator(file_obj)
        return parse(file_iterator)


def parse(file_iterator):
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
            modules.append(rel_analysis.Module(file_iterator.path, file_iterator.index))

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
