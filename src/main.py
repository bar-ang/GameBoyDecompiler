from gb_ast import AST
from explorer import explore, identify_flow_control
from lr35902dis import lr35902 as disassembler

GB_FILE = "example2.gb"
CHUNK_SIZE = 1024

def insert_scope(code, tab_size=4):
    prefix = " " * tab_size
    return "{\n" + "\n".join(prefix + line for line in code.splitlines()) + "\n}"

def convert_to_scope_data(scopes):
    opens = [t[0] for v in scopes.values() for t in v]
    closes = [sum(t) for v in scopes.values() for t in v]
    return dict(opens=opens, closes=closes)

def main():
    with open(GB_FILE, "rb") as f:
        funcs = explore(f)

        for fun, pos in funcs.items():
            start, len = pos
            f.seek(start)
            code = f.read(len)
            flow = identify_flow_control(code, pc_start=start)
            ast = AST(code, pc_start=start, scope_data=convert_to_scope_data(flow))
            print(f"{fun}() {insert_scope(ast.decompile())}")
            print(flow, convert_to_scope_data(flow))


if __name__ == "__main__":
    main()
