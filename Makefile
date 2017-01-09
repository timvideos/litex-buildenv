TESTDIR	:= test/edid

all:
	$(MAKE) -C $(TESTDIR)

check:
	$(MAKE) -C $(TESTDIR) check

clean:
	$(MAKE) -C $(TESTDIR) clean
