import syntax
import lexer
import sys

def make_slice(tokens, start, length):
    slice = []
    for i in range(start, start+length):
        tok = tokens.get(i, None)
        if tok:
            slice.append((tok, i))
    return slice

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

def deep_explore(slice):
    gadgets = {}
    res = []

    # first we seek for backward jumps
    for i, (inst, pc) in enumerate(slice):
        if inst.op == "JR" and inst.addr < 0:
            offset = -inst.addr
            j = 0
            count = 2
            while count < offset:
                count += slice[i][1] - slice[i-j][1]
                j += 1

            assert count == offset, (count, offset)
            gadgets[i-j] = (slice[i-j: i], j)

    # now forward jumps
    i = 0
    while i < len(slice):
        inst, pc = slice[i]

        if i in gadgets:
            res.append(({"looppy loop": gadgets[i][0]}, pc))
            i += gadgets[i][1]

        elif inst.op == "JR":
            if inst.addr > 0:
                res.append(({
                    "if something" : deep_explore(slice[i+1 : i+inst.addr])
                }, pc))
                i += inst.addr
            else:
                if inst.addr == 0:
                    res.append(({"if something" : []}))
                i += 1
        else:
            res.append((inst, pc))
            i += 1

    return res

def map_all_funcs(tokens, calls):
    funcs = {}
    for call in calls:
        flen = identify_func_len(tokens, call)
        more_calls = extract_func_calling(tokens, call, flen)
        funcs.update(map_all_funcs(tokens, more_calls))
        funcs[f"fun_{call:04X}"] = deep_explore(make_slice(tokens, call, flen))
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

    main_start = handle_entry_point(tokens, pc_start)

    jr_pos = search_inf_loop(tokens, main_start)

    calls = extract_func_calling(tokens, main_start, jr_pos - main_start)

    funcmap[main_func] = deep_explore(make_slice(tokens, main_start, jr_pos - main_start))
    funcmap.update(map_all_funcs(tokens, calls))

    return funcmap


def funcmap_to_str(funcmap, depth=1):
    def gothrough(cont):
        return "\n".join("\t"*depth + f"{c[0] if type(c[0]) != dict else funcmap_to_str(c[0], depth=depth+1)}" for c in cont)
    return "\n".join([
        f"{fun}:\n{gothrough(cont)}" for fun, cont in funcmap.items()
    ])

def main(gb_file):
    with open(gb_file, "rb") as f:
        readed = f.read()
    print("tokenizing code. this can take a few seconds...")
    tokens = lexer.tokenize_code(readed)
    print("exploring function:")
    funcmap = explore(tokens)
    print(funcmap_to_str(funcmap))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("provide gb file")
        sys.exit(-1)

    sys.exit(main(sys.argv[1]))
