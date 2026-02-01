from analyzer import AST
from lr35902dis import lr35902 as disassembler

GB_FILE = "example.gb"
CHUNK_SIZE = 1024

def main():
    ast = AST()
    with open(GB_FILE, "rb") as f:
        f.seek(0x100)
        chunk = f.read(CHUNK_SIZE)
        ast.process_all(chunk)
    print(ast.decompile())


if __name__ == "__main__":
    main()
