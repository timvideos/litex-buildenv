#!/usr/bin/env python3

"""
Script for loading an image into the pattern buffer via Etherbone.
"""

import shutil
import subprocess
import tempfile
import time

import numpy
import progressbar

from common import *


def send_int32_data(wb, base, data, b=128):
    l = len(data)
    batches = l/b
    print("Data is {} bytes (need {} batches)".format(l*4, batches))

    bar = progressbar.ProgressBar(max_value=l).start()
    for pos in range(0, l, b):
        mem_loc = base+pos*4
        wb.write(mem_loc, [int(x) for x in data[pos:pos+b]])
        bar.update(pos)

    bar.finish()


def add_args(parser):
    parser.add_argument(
        "--file",
        default="third_party/litevideo/litevideo/csc/test/lena.png",
        help="File to send to the pattern buffer.")

    parser.add_argument(
        "--pattern-offset",
        default=None,
        help="Manually set the pattern offset.")

    parser.add_argument(
        "--delay",
        default=30,
        type=float,
        help="Number of seconds between sending each frame of the input."
        )

    parser.add_argument(
        "--pattern",
        default=None,
        help="Send a gstreamer pattern, use 'gst-inspect-1.0 videotestsrc' to see possible options.")


def main():
    args, wb = connect(__doc__, add_args=add_args)
    print_memmap(wb)
    print()

    if args.pattern_offset is not None:
        pattern_offset = args.pattern_offset
    else:
        # Find pattern memory location
        define = "#define PATTERN_FRAMEBUFFER_BASE "
        pattern_offset = 0
        for l in open("firmware/pattern.c").readlines():
            if not l.startswith(define):
                continue

            pattern_offset = eval(l[len(define):-1])
        assert pattern_offset != 0

    pattern_mem = wb.mems.main_ram.base + pattern_offset

    width = wb.regs.hdmi_out0_core_initiator_hres.read()
    height = wb.regs.hdmi_out0_core_initiator_vres.read()
    print()
    print("Pattern Information")
    print("-"*75)
    print("   Offset: 0x{:x}".format(pattern_offset))
    print(" Location: 0x{:x}".format(pattern_mem))
    print("     Size: {}x{}".format(width, height))
    print("-"*75)
    print()

    if args.pattern:
        src = "videotestsrc pattern={} num-buffers=5".format(args.pattern)
    else:
        infile = os.path.realpath(os.path.expanduser(args.file))
        assert os.path.exists(infile), "{} ({}) does not exist!".format(infile, args.file)
        src = "filesrc location={} ! decodebin ! videoscale".format(infile)

    # Use gstreamer to convert input
    tempdir = None
    try:
        tempdir = tempfile.mkdtemp(prefix='hdmi2usb-litex-load_pattern.')

        assert os.listdir(tempdir) == []
        print("Generating raw frames in {}".format(tempdir))
        print("-"*75)

        pipeline = """
gst-launch-1.0 -v \
    {src} ! \
    videoconvert ! \
    video/x-raw,format=UYVY,height={height},width={width},colorimetry=1:4:0:0 ! \
    multifilesink location="{tempdir}/%05d.yuv422.raw" max-files={max}
""".format(src=src,
           width=width,
           height=height,
           tempdir=tempdir,
           max=1024)
        print(pipeline)
        subprocess.check_call(pipeline, shell=True)
        print("-"*75)

        files = os.listdir(tempdir)
        assert len(files) > 0, "gstreamer generated no files!"

        print()
        print("Input Information")
        print("-"*75)
        print(" Source: {}".format(src))
        print(" Frames: {}".format(len(files)))
        print("-"*75)
        print()

        for i, fn in enumerate(files):
            pn = os.path.join(tempdir, fn)
            print("Sending {}".format(pn))
            data = numpy.fromfile(open(pn, 'rb'), '>4I')
            send_int32_data(wb, pattern_mem, data.flat)

            if i != len(files)-1:
                print("Sleeping for {} seconds".format(args.delay))
                time.sleep(args.delay)

    finally:
        if tempdir:
            shutil.rmtree(tempdir)


if __name__ == "__main__":
    main()
