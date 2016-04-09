opsis_minisoc:
	rm -rf build
	./opsis_base.py --with-ethernet --nocompile-gateware
	cd firmware && make clean all
	./opsis_base.py --with-ethernet

opsis_video:
	rm -rf build
	./opsis_video.py --nocompile-gateware
	cd firmware && make clean all
	./opsis_video.py

load:
	./load.py
