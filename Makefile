# Directories
SRC_DIR := examples
OUT_DIR := roms

# Tools
RGBASM := rgbasm
RGBLINK := rgblink

# Find all .asm files
ASM_FILES := $(wildcard $(SRC_DIR)/*.asm)

# Convert examples/foo.asm -> roms/foo.gb
ROM_FILES := $(patsubst $(SRC_DIR)/%.asm,$(OUT_DIR)/%.gb,$(ASM_FILES))

.PHONY: all clean

examples: $(OUT_DIR) $(ROM_FILES)

# Ensure roms directory exists
$(OUT_DIR):
	mkdir -p $(OUT_DIR)

# Build rule (no intermediate .o file saved)
$(OUT_DIR)/%.gb: $(SRC_DIR)/%.asm | $(OUT_DIR)
	$(RGBASM) -o $*.o $<
	$(RGBLINK) -o $@ $*.o
	rm -f $*.o

clean:
	rm -rf $(OUT_DIR)


