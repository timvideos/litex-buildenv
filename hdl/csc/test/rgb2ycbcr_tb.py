from PIL import Image


def coef(value, cw=None):
    return int(value * 2**cw) if cw is not None else value


def hd_pal_coefs(dw, cw=None):
    d = {
        "ca"      : coef(0.1819, cw),
        "cb"      : coef(0.0618, cw),
        "cc"      : coef(0.6495, cw),
        "cd"      : coef(0.5512, cw),
        "yoffset" : 2**(dw-4),
        "coffset" : 2**(dw-1),
        "ymax"    : 2**dw-1,
        "cmax"    : 2**dw-1,
        "ymin"    : 0,
        "cmin"    : 0
    }
    return d

coefs = hd_pal_coefs(8)


# Model for our implementation
def rgb2ycbcr_model(r, g, b):
    y  = []
    cb = []
    cr = []
    for i in range(len(min(r, g, b))):
        yraw = coefs["ca"]*(r[i]-g[i]) + coefs["cb"]*(b[i]-g[i]) + g[i]
        y.append(yraw + coefs["yoffset"])
        cb.append(coefs["cc"]*(b[i]-yraw) + coefs["coffset"])
        cr.append(coefs["cd"]*(r[i]-yraw) + coefs["coffset"])
    return y, cb, cr


# Wikipedia implementation used as reference
def ycbcr2rgb(y, cb, cr):
    r = []
    g = []
    b = []
    for i in range(len(min(y, cb, cr))):
        r.append(int(y[i] + (cr[i] - 128) *  1.40200))
        g.append(int(y[i] + (cb[i] - 128) * -0.34414 + (cr[i] - 128) * -0.71414))
        b.append(int(y[i] + (cb[i] - 128) *  1.77200))
    return r, g, b


if __name__ == "__main__":
    img_size = 128
    img = Image.open("lena.png")
    img = img.resize((img_size, img_size), Image.ANTIALIAS)
    r, g, b = zip(*list(img.getdata()))
    img_len = len(r)

    y, cb, cr = rgb2ycbcr_model(r, g, b)
    r, g, b = ycbcr2rgb(y, cb, cr)
    img = Image.new("RGB" ,(img_size, img_size))
    img.putdata(list(zip(r,g,b)))
    img.save("lena_tb_model.png")
