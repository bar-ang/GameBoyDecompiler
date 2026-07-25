import sys
from lexer import tokenize_code
from explorer import explore
from gb_ast import build_ast


def main(gb_file):
    with open(gb_file, "rb") as f:
        raw_code = f.read()

    print("tokenizing...")
    tokens = tokenize_code(raw_code)
    print("exploring...")
    explored = explore(tokens)
    print("building AST...")
    import pdb; pdb.set_trace()
    ast = build_ast(explored)

    print(ast)

    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("provide .gb file")
    sys.exit(main(sys.argv[1]))
