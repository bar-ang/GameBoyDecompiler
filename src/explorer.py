from graphviz import Digraph # type: ignore[import-untyped]
from lexer import Token, tokenize_code
import syntax
import sys
import bisect

def handle_entry_point(tokens: list[Token], pc_start: int) -> int:
    i = find_token_by_pc(tokens, pc_start)
    start = tokens[i]
    if not isinstance(start.inst, syntax.InstJump):
        start = tokens[i+1]

    assert isinstance(start.inst, syntax.InstJump), f"unexpected of '{str(start)}' on entry point"
    j = find_token_by_pc(tokens, start.inst.abs_addr(start.pc))
    assert j
    return j

def find_token_by_pc(tokens: list[Token], pc: int) -> int:
    dummy = Token(inst=syntax.Instruction.Empty(), pc=pc)  # inst is unused for comparison
    i = bisect.bisect_left(tokens, dummy)
    if i < len(tokens) and tokens[i].pc == pc:
        return i
    raise Exception(f"no token on addr {pc:04X}")

def search_inf_loop(tokens: list[Token], main_start: int) -> int | None:
    for i, tok in enumerate(tokens[main_start:]):
        if isinstance(tok.inst, syntax.InstJump) and not tok.inst.cond and \
            (tok.inst.addr <= 0):
                return i + main_start + 1
    return None

def connect(tokens: list[Token]) -> None:
    for i, tok in enumerate(tokens[:-1]):
        tok.next_feature = tokens[i+1]

        if isinstance(tok.inst, syntax.InstJump):
            try:
                addr = tok.inst.abs_addr(tok.pc)
                tok.next_feature = tokens[find_token_by_pc(tokens, addr)]
            except:
                tok.jump_addr = None
            if tok.inst.cond:
                tok.if_cond_unmet = tokens[i+1]
        elif isinstance(tok.inst, syntax.InstCall):
            try:
                addr = tok.inst.abs_addr(tok.pc)
                tok.jump_addr = tokens[find_token_by_pc(tokens, addr)]
            except:
                tok.jump_addr = None
        elif isinstance(tok.inst, syntax.InstRet):
            tok.jump_addr = None
            tok.next_feature = None
            tok.if_cond_unmet = None

def explore(tokens: list[Token], pc_start=0x100, main_name="main") -> Token:
    main_start = handle_entry_point(tokens, pc_start)
    main_end = search_inf_loop(tokens, main_start)
    connect(tokens)
    print("connected")
    return {"main" : tokens[main_start]}

def main(gb_file):
    with open(gb_file, "rb") as f:
        readed = f.read()
    print("tokenizing code. this can take a few seconds...")
    tokens = tokenize_code(readed)

    print("exploring functions:")
    connected_tokens = explore(tokens)

    g = Digraph("tokens", strict=True)
    g.attr(rankdir="TD")
    print("graphing")
    for _, func_tokens in connected_tokens.items():
        connected_tokens.to_graph(g)
    print("graphed")
    g.render("token_graph", format="png", cleanup=True)
    print("now render")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("provide gb file")
        sys.exit(-1)

    sys.exit(main(sys.argv[1]))
