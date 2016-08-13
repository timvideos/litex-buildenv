CFLAGS	:= -Wall -g

OBJ	:= edid.o edid_test.o
EXE	:= edid_test

all: $(EXE)

$(EXE): $(OBJ) | edid.h

.PHONY: clean
clean:
	$(RM) $(EXE) $(OBJ)


