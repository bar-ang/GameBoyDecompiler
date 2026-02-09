import syntax
import lexer
import sys

def search_inf_loop(tokens, main_start):
    pc = main_start
    while True:
        assert pc - main_start < 10 ** 7
        token = tokens.get(pc, None)
        if token and \
           ((type(token) == syntax.InstAbsJump and token.addr <= pc) or \
            (type(token) == syntax.InstRelJump and token.addr <= 0)):
            return pc
        pc += 1

def extract_func_calling(tokens, start, length):
    res = []

    for i in range(start, start+length):
        tok = tokens.get(i, None)
        if tok and type(tok) in {syntax.InstCall, syntax.InstConitionalCall}:
            res.append(tok.addr)

    return list(set(res))

def identify_func_len(tokens, pc_start):
    pc = pc_start
    while True:
        assert pc - pc_start < 10 ** 7
        tok = tokens.get(pc, None)
        if tok and type(tok) == syntax.InstRet:
            return pc - pc_start
        pc += 1

def map_all_funcs(tokens, calls):
    funcs = {}
    for call in calls:
        flen = identify_func_len(tokens, call)
        more_calls = extract_func_calling(tokens, call, flen)
        funcs.update(map_all_funcs(tokens, more_calls))
        funcs[f"fun_{call:04X}"] = (call, flen)
    return funcs

def handle_entry_point(tokens, pc_start):
    start = tokens[pc_start]
    if start.op not in {"JR", "JP"}:
        pc_start += 1
        start = tokens[pc_start]

    assert start.op in {"JR", "JP"}, f"unexpected of '{str(start)}' on entry point"

    if start.op == "JP":
        return start.addr
    else:
        return start.addr + pc_start


def explore(tokens, pc_start=0x100, main_func="main"):
    funcmap = {}
    calls = []
    buff = []

    main_start = handle_entry_point(tokens, pc_start)

    jr_pos = search_inf_loop(tokens, main_start)

    calls = extract_func_calling(tokens, main_start, jr_pos - main_start)

    funcmap[main_func] = (main_start, jr_pos)
    funcmap.update(map_all_funcs(tokens, calls))

    return funcmap

def main(gb_file):
    with open(gb_file, "rb") as f:
        readed = f.read()
    tokens = lexer.tokenize_code(readed)
    funcmap = explore(tokens)
    print("\n".join([f"{fun}: ${s[0]:04X} (+{s[1]})" for fun, s in funcmap.items()]))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("provide gb file")
        sys.exit(-1)

    sys.exit(main(sys.argv[1]))
