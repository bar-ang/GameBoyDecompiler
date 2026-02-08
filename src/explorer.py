CHUNK_SIZE = 256

def search_inf_loop(buff):
    for i, opcode in enumerate(buff[:-1]):
        if opcode == 0x18 and buff[i+1] >= 128:
            # absolute JR to previous location
            return i
    return None

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

def handle_entry_point(file, pc_start, entry_point_size_bytes=4):
    file.seek(pc_start)
    entry = file.read(entry_point_size_bytes)
    return entry[2] | (entry[3] << 8)


def explore(file, pc_start=0x100, main_func="main"):
    funcmap = {}
    calls = []
    buff = b""

    main_start = handle_entry_point(file, pc_start)

    file.seek(main_start)

    jr_pos = None
    while not jr_pos:
        r = file.read(CHUNK_SIZE)
        assert r, "EOF and function not identified"
        buff += r
        jr_pos = search_inf_loop(buff)

    calls = extract_func_calling(buff)

    funcmap[main_func] = (main_start, jr_pos)
    funcmap.update(map_all_funcs(file, calls))

    return funcmap

def main(gb_file):
    with open(gb_file, "rb") as f:
        funcmap = explore(f)
    print("\n".join([f"{fun}: ${s[0]:04X} (+{s[1]})" for fun, s in funcmap.items()]))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("provide gb file")
        sys.exit(-1)

    sys.exit(main(sys.argv[1]))
