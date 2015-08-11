HDLDIR = ../../../
PYTHON = python3

CMD = PYTHONPATH=$(HDLDIR) $(PYTHON)

rgb2ycbcr_tb:
	$(CMD) rgb2ycbcr_tb.py

ycbcr2rgb_tb:
	$(CMD) ycbcr2rgb_tb.py

ycbcr_resampling_tb:
	$(CMD) ycbcr_resampling_tb.py

clean:
	rm -rf *_*.png *.vvp *.v *.vcd

.PHONY: clean