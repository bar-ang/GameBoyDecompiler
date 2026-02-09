import syntax
import lexer
import sys

CHUNK_SIZE = 256

def search_inf_loop(tokens, main_start):
    pc = main_start
    while True:
        token = tokens.get(pc, None)
        print(pc, token)
        if token and \
           ((type(token) == syntax.InstAbsJump and token.addr <= pc) or \
            (type(token) == syntax.InstRelJump and token.addr <= 0)):
            return pc
        pc += 1

def extract_func_calling(buff):
    res = []
    call_opcodes = (0xC4, 0xCC, 0xCD, 0xD4, 0xDC)
    for i, opcode in enumerate(buff[:-2]):
        if opcode in call_opcodes:
            res.append(buff[i+1] | (buff[i+2] << 8))

    return list(set(res))

def identify_func(file, pc_start):
    ret_opcodes = (0xC0, 0xC8, 0xC9, 0xD0, 0xD8, 0xD9)
    file.seek(pc_start)
    buff = b""

    ret_idx = None
    while not ret_idx:
        r = file.read(CHUNK_SIZE)
        assert r, "EOF and RET not identified"
        buff += r
        ret_idx = next(
            (i for i, op in enumerate(buff) if op in ret_opcodes),
            None
        )

    return buff[:ret_idx+1]

def map_all_funcs(file, calls):
    funcs = {}
    for call in calls:
        code = identify_func(file, call)
        more_calls = extract_func_calling(code)
        funcs.update(map_all_funcs(file, more_calls))
        funcs[f"fun_{call:04X}"] = (call, len(code))
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

    calls = extract_func_calling(buff)

    funcmap[main_func] = (main_start, jr_pos)
    funcmap.update(map_all_funcs(file, calls))

    return funcmap

def main(gb_file):
    with open(gb_file, "rb") as f:
        f.seek(0x100)
        tokens = lexer.tokenize_code(f.read())
    funcmap = explore(tokens)
    print("\n".join([f"{fun}: ${s[0]:04X} (+{s[1]})" for fun, s in funcmap.items()]))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("provide gb file")
        sys.exit(-1)

    sys.exit(main(sys.argv[1]))
