CFLAGS	:= -Wall -g

OBJ	:= edid.o edid_test.o
EXE	:= edid_test

DECODE	:= $(CURDIR)/edid-decode/edid-decode

all: $(EXE)

$(EXE): $(OBJ) | edid.h

$(DECODE):
	$(MAKE) -C edid-decode

check: $(EXE) $(DECODE)
	./$(EXE)  | $(DECODE)  | less


.PHONY: clean
clean:
	$(RM) $(EXE) $(OBJ)


