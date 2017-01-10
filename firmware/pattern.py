def rgb2ycbcr(r, g, b):
    y = int(0.299*r + 0.587*g + 0.114*b)
    cb = int(-0.1687*r - 0.3313*g + 0.5*b + 128)
    cr = int(0.5*r - 0.4187*g - 0.0813*b + 128)
    return y, cb, cr

def ycbcr_pack(y, cb, cr):
    value  = y
    value |= cr << 8
    value |= y  << 16
    value |= cb << 24
    return value

color_bars_rgb = [
    [255, 255, 255],
    [255, 255,   0],
    [0,   255, 255],
    [0,   255,   0],
    [255,   0, 255],
    [255,   0,   0],
    [0,     0, 255],
    [0,     0,   0],
]

color_bars_ycbcr = []
for color_bar_rgb in color_bars_rgb:
    r, g, b = color_bar_rgb
    y, cb, cr = rgb2ycbcr(r, g, b)
    color_bars_ycbcr.append([y, cb, cr])

for color_bar_ycbcr in color_bars_ycbcr:
    value = ycbcr_pack(*color_bar_ycbcr)
    print("%08x" %value)
