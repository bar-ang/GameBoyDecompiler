CHUNK_SIZE = 256

def search_inf_loop(buff):
    for i, opcode in enumerate(buff[:-1]):
        if opcode == 0x18 and buff[i+1] >= 128:
            # absolute JR to previous location
            return i+2
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

def identify_flow_control(buff, pc_start=0):
    assert not any([ret_op in buff for ret_op in (0xC0, 0xC8, 0xC9, 0xD0, 0xD8, 0xD9)])
    jr_opcodes = {
        0x20: "!= 0",
        0x30: ">= 0",
        0x28: "== 0",
        0x38: "< 0",
        0x18: "uncond"
    }
    assert buff[-1] not in jr_opcodes.keys()

    ifs = []
    loops = []

    for i, op in enumerate(buff[:-1]):
        if op in jr_opcodes.keys():
            if buff[i+1] < 128:
                ifs.append((i+pc_start, buff[i+1]))
            else:
                neg = buff[i+1] - 256
                loops.append((i+ buff[i+1] - 254 + pc_start, 256 - buff[i+1]))

    return dict(ifs=ifs, loops=loops)

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

def main():
    with open("example2.gb", "rb") as f:
        funcmap = explore(f)
        pos, len = funcmap["main"]
        f.seek(pos)
        buff = f.read(len)
        print(" ".join([f"{i}:{c:02X}" for i, c in enumerate(buff)]))
        print(identify_flow_control(buff))

    print("\n".join([f"{fun}: ${s[0]:04X} (+{s[1]})" for fun, s in funcmap.items()]))

if __name__ == "__main__":
    main()
