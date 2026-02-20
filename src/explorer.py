import syntax
import lexer
import sys
import bisect

def find_token_by_pc(tokens, pc) -> int | None:
    dummy = lexer.Token(inst=syntax.Instruction(), pc=pc)  # inst is unused for comparison
    i = bisect.bisect_left(tokens, dummy)
    if i < len(tokens) and tokens[i].pc == pc:
        return i
    return None

def search_inf_loop(tokens, main_start):
    for i, tok in enumerate(tokens[main_start:]):
        if isinstance(tok.inst, syntax.InstJump) and not tok.inst.cond and \
            ((tok.inst.is_relative() and tok.inst.addr < 0) or \
            (not tok.inst.is_relative() and tok.inst.addr < tok.pc)):
                return i + main_start
    return None

def extract_func_calling(tokens, start, length):
    res = []

    for i in range(start, start+length):
        inst = tokens[i].inst
        if isinstance(inst, syntax.InstCall) or \
           isinstance(inst, syntax.InstConditionalCall):
            res.append(inst.addr)

    return list(set(res))

def identify_func_len(tokens, start):
    for i, tok in enumerate(tokens[start:]):
        inst = tok.inst
        if isinstance(inst, syntax.InstRet) or \
           isinstance(inst, syntax.InstReti) or \
           isinstance(inst, syntax.InstConditionalRet):
            return i
    raise Exception("unfortunate CALL without a following RET")

def map_all_funcs(tokens, calls):
    funcs = {}
    for call_addr in calls:
        call = find_token_by_pc(tokens, call_addr)
        flen = identify_func_len(tokens, call)
        more_calls = extract_func_calling(tokens, call, flen)
        funcs.update(map_all_funcs(tokens, more_calls))
        funcs[f"fun_{call:04X}"] = tokens[call:call+flen]
        connect_tokens(tokens[call:call+flen])
    return funcs

def handle_entry_point(tokens, pc_start):
    i = find_token_by_pc(tokens, pc_start)
    start = tokens[i].inst
    if not isinstance(start, syntax.InstJump):
        start = tokens[i+1].inst

    assert isinstance(start, syntax.InstJump), f"unexpected of '{str(start)}' on entry point"
    j = find_token_by_pc(tokens, start.addr)
    assert j
    return j

def connect_tokens(tokens):
    for i, tok in enumerate(tokens):
        inst = tok.inst
        if isinstance(inst, syntax.InstRet) or \
           isinstance(inst, syntax.InstReti) or \
           isinstance(inst, syntax.InstConditionalRet):
            raise Exception(f"Token-linking is not supported for instruction: {inst}")

        if i < len(tokens) - 1:
            tok.next_token = tokens[i+1]

        if isinstance(inst, syntax.InstJump) and inst.cond:
            tok.next_cond_token = tokens[find_token_by_pc(tokens, inst.addr)]


def explore(tokens, pc_start=0x100, main_func="main"):
    funcmap = {}

    main_start = handle_entry_point(tokens, pc_start)

    jr_pos = search_inf_loop(tokens, main_start)
    if jr_pos is None:
        raise Exception("main function could be detected")

    calls = extract_func_calling(tokens, main_start, jr_pos - main_start)

    funcmap[main_func] = tokens[main_start: jr_pos]
    connect_tokens(tokens[main_start: jr_pos])
    funcmap.update(map_all_funcs(tokens, calls))

    return funcmap


def main(gb_file):
    with open(gb_file, "rb") as f:
        readed = f.read()
    print("tokenizing code. this can take a few seconds...")
    tokens = lexer.tokenize_code(readed)
    print("exploring function:")
    funcmap = explore(tokens)
    print("\n".join([f"{fun}:\n{"\n".join([f"\t{c}" for c in cont])}" for fun, cont in funcmap.items()]))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("provide gb file")
        sys.exit(-1)

    sys.exit(main(sys.argv[1]))
