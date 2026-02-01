CHUNK_SIZE = 256

def search_inf_loop(buff):
    for i, opcode in enumerate(buff[:-1]):
        if opcode == 0x18 and buff[i+1] >= 128:
            # absolute JR to previous location
            return i
    return None

def explore(file, pc_start=0x100, main_func="main"):
    funcmap = {}

    f.seek(pc_start)

    jr_pos = None
    while not jr_pos:
        buff = f.read(CHUNK_SIZE)
        assert buff, "EOF and function not identified"
        jr_pos = search_inf_loop(buff)

    print(buff[jr_pos:jr_pos+2])
    end = pc_start + jr_pos
    funcmap[main_func] = (pc_start, end)

    return funcmap


if __name__ == "__main__":
    with open("example.gb", "rb") as f:
        funcmap = explore(f)
    print(funcmap)
