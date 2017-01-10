CFLAGS	:= -Wall -g

ROOT    := $(CURDIR)/../..
OBJ	:= edid_test.o $(ROOT)/firmware/edid.o
EXE	:= edid_test

CFLAGS += -I$(ROOT)/firmware

DECODE	:= $(ROOT)/third_party/edid-decode/edid-decode

all: $(EXE)

$(EXE): $(OBJ) | $(ROOT)/firmware/edid.h

$(DECODE):
	$(MAKE) -C $(ROOT)/third_party/edid-decode

check: $(EXE) $(DECODE)
	./$(EXE) | $(DECODE) | less

.PHONY: clean
clean:
	$(RM) $(EXE) $(OBJ)


