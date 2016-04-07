opsis_minisoc:
	rm -rf build
	./opsis_base.py --with-ethernet --build --nocompile-gateware
	cd firmware && make clean all
	./opsis_base.py --with-ethernet --build

opsis_video:
	rm -rf build
	./opsis_video.py --build --nocompile-gateware
	cd firmware && make clean all
	./opsis_video.py --build
