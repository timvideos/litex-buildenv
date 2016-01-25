HDLDIR = ../../../
PYTHON = python3

CMD = PYTHONPATH=$(HDLDIR) $(PYTHON)

buffer_tb:
	$(CMD) buffer_tb.py

dma_tb:
	$(CMD) dma_tb.py	

clean:
	rm -rf *.vvp *.v *.vcd

.PHONY: clean