from graphviz import Digraph # type: ignore[import-untyped]
import syntax
import lexer
import sys
import bisect

def find_token_by_pc(tokens, pc) -> int | None:
    dummy = lexer.Token(inst=syntax.Instruction.Empty(), pc=pc)  # inst is unused for comparison
    i = bisect.bisect_left(tokens, dummy)
    if i < len(tokens) and tokens[i].pc == pc:
        return i
    return None

def search_inf_loop(tokens, main_start):
    for i, tok in enumerate(tokens[main_start:]):
        if isinstance(tok.inst, syntax.InstJump) and not tok.inst.cond and \
            (tok.inst.addr <= 0):
                return i + main_start + 1
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


def close_conditions(head_token: lexer.Token) -> None:
    tok: lexer.Token | None = head_token
    while tok is not None:
        if not tok.conditional():
            tok = tok.next_feature
            continue

        assert tok.jump_addr
        assert tok.if_cond_unmet
        assert tok.next_feature

        head = tok
        regmap_met, _ = syntax.create_initial_regmap()
        regmap_unmet, _ = syntax.create_initial_regmap()

        met: lexer.Token = tok.jump_addr
        unmet: lexer.Token = tok.if_cond_unmet
        end: lexer.Token | None = tok.next_feature

        if not met is end:
            while True:
                met.inst.dry_run(regmap_met)
                assert met.next_feature
                if met.next_feature is end:
                    break
                met = met.next_feature
        else:
            met = head

        if not unmet is end:
            while True:
                unmet.inst.dry_run(regmap_unmet)
                assert unmet.next_feature
                if unmet.next_feature is end:
                    break
                unmet = unmet.next_feature
        else:
            unmet = head

        end.inst.dry_run(regmap_met)
        end.inst.dry_run(regmap_unmet)

        if regmap_met != regmap_unmet:
             new_end = end.soft_copy()
             unmet.next_feature = new_end
             head.next_feature = end.next_feature
             close_conditions(head)

        tok = end


def map_all_funcs(tokens, calls):
    funcs = {}
    for call_addr in calls:
        call = find_token_by_pc(tokens, call_addr)
        flen = identify_func_len(tokens, call)
        more_calls = extract_func_calling(tokens, call, flen)
        funcs.update(map_all_funcs(tokens, more_calls))
        con = connect_tokens(tokens[call:call+flen])
        add_nops(con)
        funcs[f"fun_{call:04X}"] = con
        close_conditions(con)
    return funcs

def handle_entry_point(tokens, pc_start):
    i = find_token_by_pc(tokens, pc_start)
    start = tokens[i]
    if not isinstance(start.inst, syntax.InstJump):
        start = tokens[i+1]

    assert isinstance(start.inst, syntax.InstJump), f"unexpected of '{str(start)}' on entry point"
    j = find_token_by_pc(tokens, start.inst.abs_addr(start.pc))
    assert j
    return j

def get_next_feature(token: lexer.Token) -> lexer.Token:
    def intersect(a, b):
        b_ids = {id(x) for x in b}
        return [x for x in a if id(x) in b_ids]
    assert token.jump_addr
    assert token.if_cond_unmet
    left_seen: list[lexer.Token] = [token.jump_addr]
    right_seen: list[lexer.Token] = [token.if_cond_unmet]
    while True:
        sec = intersect(left_seen, right_seen)
        if len(sec):
            return sec[0]
        nl = left_seen[-1].next_feature
        nr = right_seen[-1].next_feature
        assert nl
        assert nr
        left_seen.append(nl)
        right_seen.append(nr)

def connect_tokens(tokens: list[lexer.Token]) -> lexer.Token:
    missing_next_feature = []
    tokens = tokens[:] + [lexer.Token.Empty()]
    for i, tok in enumerate(tokens):
        inst = tok.inst
        if isinstance(inst, syntax.InstRet) or \
           isinstance(inst, syntax.InstReti) or \
           isinstance(inst, syntax.InstConditionalRet):
            raise Exception(f"Token-linking is not supported for instruction: {inst}")

        if isinstance(inst, syntax.InstJump):
            if inst.is_jump_forward():
                t = find_token_by_pc(tokens, tok.inst.addr)
                if not t:
                    import pdb; pdb.set_trace()
                assert t
                tok.jump_addr = tokens[t]
                if inst.cond:
                    tok.if_cond_unmet = tokens[i+1]
                    missing_next_feature.append(tok)
                else:
                    tok.next_feature = tok.jump_addr
            else:
                tok.next_feature = tokens[i+1]
        elif  i < len(tokens) - 1:
            tok.next_feature = tokens[i+1]

    for tok in missing_next_feature[::-1]:
        tok.next_feature = get_next_feature(tok)

    return tokens[0]

def add_nops(head: lexer.Token) -> None:
    curr = head
    while curr is not None:
        if curr.conditional():
            if curr.next_feature is curr.jump_addr:
                nop = lexer.Token(syntax.Instruction.Empty(), 0,
                                  next_feature=curr.next_feature)
                curr.jump_addr = nop
            if curr.next_feature is curr.if_cond_unmet:
                nop = lexer.Token(syntax.Instruction.Empty(), 0,
                                  next_feature=curr.next_feature)
                curr.if_cond_unmet = nop

        curr = curr.next_feature

def explore(tokens, pc_start=0x100, main_func="main"):
    funcmap = {}

    main_start = handle_entry_point(tokens, pc_start)

    jr_pos = search_inf_loop(tokens, main_start)
    if jr_pos is None:
        raise Exception("main function could be detected")

    calls = extract_func_calling(tokens, main_start, jr_pos - main_start)

    connected_tokens = connect_tokens(tokens[main_start: jr_pos])
    funcmap[main_func] = connected_tokens
    close_conditions(connected_tokens)
    add_nops(connected_tokens)
    funcmap.update(map_all_funcs(tokens, calls))

    return funcmap


def main(gb_file):
    with open(gb_file, "rb") as f:
        readed = f.read()
    print("tokenizing code. this can take a few seconds...")
    tokens = lexer.tokenize_code(readed)
    print("exploring function:")
    funcmap = explore(tokens)

    g = Digraph("tokens", strict=True)
    g.attr(rankdir="TD")
    for fun, content in funcmap.items():
        content.to_graph(g)
    g.render("token_graph", format="png", cleanup=True)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("provide gb file")
        sys.exit(-1)

    sys.exit(main(sys.argv[1]))
