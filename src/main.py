from gb_ast import AST
from explorer import explore
from lr35902dis import lr35902 as disassembler

GB_FILE = "example.gb"
CHUNK_SIZE = 1024

def main():
    with open(GB_FILE, "rb") as f:
        funcs = explore(f)

        for fun, pos in funcs.items():
            ast = AST()
            start, len = pos
            f.seek(start)
            code = f.read(len)
            ast.process_all(code)

            print(f"{fun}() {{")
            print(ast.decompile())
            print("}\n")


if __name__ == "__main__":
    main()
