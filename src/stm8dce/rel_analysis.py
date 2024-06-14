from . import rel_matchers
from . import asm_analysis
from . import debug


class Module:
    def __init__(self, path, line):
        self.path = path
        self.line = line
        self.name = "UNNAMED MODULE"
        self.referenced_symbols = []
        self.defined_symbols = []
        self.referenced_by = []
        self.references = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def print(self):
        print(f"Module: {self.name}")
        print("Referenced Symbols:")
        for symbol in self.referenced_symbols:
            print(f"\t{symbol}")
        print("Defined Symbols:")
        for symbol in self.defined_symbols:
            print(f"\t{symbol}")

    def set_name(self, name):
        self.name = name

    def add_referenced_symbol(self, symbol):
        self.referenced_symbols.append(symbol)

    def add_defined_symbol(self, symbol):
        self.defined_symbols.append(symbol)

    def resolve_references(self, functions, constants):
        for symbol in self.defined_symbols:
            match = asm_analysis.functions_referencing_external(functions, symbol.name)
            if match:
                self.referenced_by.extend(match)
                for function in match:
                    self.referenced_by.append(self)
                    debug.pdbg(
                        f"Function {function.name} in {function.path}:{function.start_line} references external symbol {symbol.name} in {self.path}:{self.line}"
                    )

        # Module isn't imported by linker if it isn't referenced
        # So we don't need to check if it references anything
        if not self.referenced_by:
            return

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
