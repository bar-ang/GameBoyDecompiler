from gb_ast import AST
from explorer import explore
from lr35902dis import lr35902 as disassembler

GB_FILE = "mrdriller.gbc"
CHUNK_SIZE = 1024

def print_debugging_data(code):
    print(" ".join([f"{c:02X}" for c in code]))
    inst = b""
    for c in code:
        inst += bytes([c])
        dis = disassembler.disasm(inst, 0)
        if dis:
            print(dis)
            inst = b""
    if inst:
        print(f"also: {inst}")

def main():

    ast = AST()
    with open(GB_FILE, "rb") as f:
        funcs = explore(f)
        start, len = funcs["main"]
        f.seek(start)
        code = f.read(len)

    try:
        ast.process_all(code)
    except Exception as e:
        print_debugging_data(code)
        raise e
    print(f"main() {{")
    print(ast.decompile())
    print("}\n")


    print("\n".join(f"{k} = {v}" for k, v in ast._data.items()))
#        for fun, pos in funcs.items():
#            ast = AST()
#            start, len = pos
#            f.seek(start)
#            code = f.read(len)
#            ast.process_all(code)
#
#            print(f"{fun}() {{")
#            print(ast.decompile())
#            print("}\n")


if __name__ == "__main__":
    main()
