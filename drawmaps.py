#!/usr/bin/python3
# based on https://sourceforge.net/p/omgifol/code/HEAD/tree/demo/drawmaps.py
# original by Fredrik Johansson, 2006-12-11
# updated  by Frans P. de Vries, 2016-04-26/2018-09-05/2018-10-04
# utilized by doom_map_scope InZane84 1/13/2025

import sys, getopt
from omg import *
from PIL import Image, ImageDraw, ImageFont

verbose   = False
dmspawns  = False
ctfspawns = False
scales = 0
total  = 0

# configuration
alias  = 3
border = 4

# spot & text dimensions
sptdim = 10
txtdim = 16
# spot & text colors
dmtcol = (0,   176,   0) # deathmatch green
blucol = (0,   112, 255) # CTF team blue
redcol = (240,   0,   0) # CTF team red
grncol = (0,   176,   0) # CTF team green
txtcol = (255, 216,   0) # yellow text
whtcol = (255, 255, 255) # white border


def drawmap(wad, name, filename, maxpixels, reqscale):
    global scales, total
    try:
        edit = UMapEditor(wad.udmfmaps[name])
    except KeyError:
        edit = UMapEditor(wad.maps[name])

    # set default linedef id
    if edit.namespace.lower() in ('zdoom', 'hexen'):
        defid = -1
    else:
        defid = 0

    # determine scale = map area unit / pixel
    xmin = min([v.x for v in edit.vertexes])
    xmax = max([v.x for v in edit.vertexes])
    ymin = min([-v.y for v in edit.vertexes])
    ymax = max([-v.y for v in edit.vertexes])
    xsize = xmax - xmin
    ysize = ymax - ymin
    scale = (maxpixels - border*2) / float(max(xsize, ysize))

    # tally for average scale or compare against requested scale
    if reqscale == 0:
        scales += scale
        total += 1
    else:
        if scale > 1.0 / reqscale:
            scale = 1.0 / reqscale

    # size up if anti-aliasing
    ascale = scale * alias
    aborder = border * alias

    # convert all numbers to (aliased) image space
    axmin = int(xmin * ascale)
    aymin = int(ymin * ascale)
    xmin  = int(xmin * scale)
    ymin  = int(ymin * scale)
    axsize = int(xsize * ascale) + aborder*2;
    aysize = int(ysize * ascale) + aborder*2;
    xsize  = int(xsize * scale) + border*2;
    ysize  = int(ysize * scale) + border*2;
    for v in edit.vertexes:
        v.x = int(v.x * scale); v.y = int(v.y * -scale)
    if dmspawns or ctfspawns:
        for t in edit.things:
            t.x = int(t.x * ascale); t.y = int(t.y * -ascale)

    # initiate new map image
    if verbose:
        flag = ""
        if xsize * ysize > 12500000:
            flag = " !"
        print("\t%0.2f: %d x %d%s" % (1.0 / scale, xsize, ysize, flag))

    im = Image.new('RGB', (xsize, ysize), (255,255,255))
    draw = ImageDraw.Draw(im)

    # draw 1s lines after 2s lines so 1s lines are never obscured
    edit.linedefs.sort(key=lambda a: not a.twosided)

    # draw all lines from their vertexes
    for line in edit.linedefs:
        p1x = edit.vertexes[line.v1].x - xmin + border
        p1y = edit.vertexes[line.v1].y - ymin + border
        p2x = edit.vertexes[line.v2].x - xmin + border
        p2y = edit.vertexes[line.v2].y - ymin + border
        color = (0, 0, 0)
        if line.twosided:   color = (144, 144, 144)
        if line.special:    color = (220, 130, 50)
        if line.id > defid: color = (200, 110, 30)

        # draw multiple lines to simulate thickness
        draw.line((p1x, p1y,   p2x, p2y),   fill=color)
        draw.line((p1x+1, p1y, p2x+1, p2y), fill=color)
        draw.line((p1x-1, p1y, p2x-1, p2y), fill=color)
        draw.line((p1x, p1y+1, p2x, p2y+1), fill=color)
        draw.line((p1x, p1y-1, p2x, p2y-1), fill=color)

    # scale up to anti-alias
    if alias > 1:
        im = im.resize((axsize, aysize))
        del draw
        draw = ImageDraw.Draw(im)

    # draw DM spawns
    if dmspawns:
        drawspawns(edit, draw, axmin, aymin, aborder, 11, dmtcol, False)
    # draw CTF spawns & flags
    if ctfspawns:
        drawspawns(edit, draw, axmin, aymin, aborder, 5080, blucol, False) # blue spawn
        drawspawns(edit, draw, axmin, aymin, aborder, 5130, blucol, True)  # blue flag
        drawspawns(edit, draw, axmin, aymin, aborder, 5081, redcol, False) # red spawn
        drawspawns(edit, draw, axmin, aymin, aborder, 5131, redcol, True)  # red flag
        drawspawns(edit, draw, axmin, aymin, aborder, 5083, grncol, False) # green spawn
        drawspawns(edit, draw, axmin, aymin, aborder, 5133, grncol, True)  # green flag

    # scale down to anti-alias
    if alias > 1:
        im = im.resize((xsize, ysize), Image.ANTIALIAS)

    del draw
    im.save(filename)

def plotmap(wad, name, maxpixels, reqscale):
    """ Draw a map to a DearPyGui window"""
    pass

def drawspawns(edit, draw, xmin, ymin, border, thtype, sptcol, flag):

    spawn = 1;
    for thing in edit.things:
        if thing.type == thtype:
            # define spot string
            if flag:
                spstr = 'F'
            else:
                spstr = str(spawn)
            # size up if anti-aliasing
            radius = sptdim * alias
            # larger spot for 2 digits
            if len(spstr) > 1:
                radius *= 1.3
            size = font.getsize(spstr)
            # compute bounding box
            p1x = (thing.x - radius) - xmin + border
            p1y = (thing.y - radius) - ymin + border
            p2x = (thing.x + radius) - xmin + border
            p2y = (thing.y + radius) - ymin + border

            # draw spawn spot
            draw.ellipse((p1x, p1y, p2x, p2y), outline=sptcol, fill=sptcol)

            if not flag:
                # draw arrow at thing angle
                draw.arc((p1x-12, p1y-12, p2x+12, p2y+12), 360-thing.angle- 2, 360-thing.angle+ 2, fill=sptcol)
                draw.arc((p1x-11, p1y-11, p2x+11, p2y+11), 360-thing.angle- 4, 360-thing.angle+ 4, fill=sptcol)
                draw.arc((p1x-10, p1y-10, p2x+10, p2y+10), 360-thing.angle- 6, 360-thing.angle+ 6, fill=sptcol)
                draw.arc((p1x- 9, p1y- 9, p2x+ 9, p2y+ 9), 360-thing.angle- 8, 360-thing.angle+ 8, fill=sptcol)
                draw.arc((p1x- 8, p1y- 8, p2x+ 8, p2y+ 8), 360-thing.angle-10, 360-thing.angle+10, fill=sptcol)
                draw.arc((p1x- 7, p1y- 7, p2x+ 7, p2y+ 7), 360-thing.angle-11, 360-thing.angle+11, fill=sptcol)
                draw.arc((p1x- 6, p1y- 6, p2x+ 6, p2y+ 6), 360-thing.angle-12, 360-thing.angle+12, fill=sptcol)
                draw.arc((p1x- 5, p1y- 5, p2x+ 5, p2y+ 5), 360-thing.angle-13, 360-thing.angle+13, fill=sptcol)
                draw.arc((p1x- 4, p1y- 4, p2x+ 4, p2y+ 4), 360-thing.angle-14, 360-thing.angle+14, fill=sptcol)
                draw.arc((p1x- 2, p1y- 2, p2x+ 2, p2y+ 2), 360-thing.angle-15, 360-thing.angle+15, fill=sptcol)

                # draw border around arrow
                draw.arc((p1x-15, p1y-15, p2x+15, p2y+15), 360-thing.angle- 3, 360-thing.angle+ 3, fill=whtcol)
                draw.arc((p1x-14, p1y-14, p2x+14, p2y+14), 360-thing.angle- 4, 360-thing.angle+ 4, fill=whtcol)
                draw.arc((p1x-13, p1y-13, p2x+13, p2y+13), 360-thing.angle- 5, 360-thing.angle+ 5, fill=whtcol)
                draw.arc((p1x-12, p1y-12, p2x+12, p2y+12), 360-thing.angle+ 3, 360-thing.angle+ 7, fill=whtcol)
                draw.arc((p1x-12, p1y-12, p2x+12, p2y+12), 360-thing.angle- 7, 360-thing.angle- 3, fill=whtcol)
                draw.arc((p1x-11, p1y-11, p2x+11, p2y+11), 360-thing.angle+ 5, 360-thing.angle+ 9, fill=whtcol)
                draw.arc((p1x-11, p1y-11, p2x+11, p2y+11), 360-thing.angle- 9, 360-thing.angle- 5, fill=whtcol)
                draw.arc((p1x-10, p1y-10, p2x+10, p2y+10), 360-thing.angle+ 7, 360-thing.angle+11, fill=whtcol)
                draw.arc((p1x-10, p1y-10, p2x+10, p2y+10), 360-thing.angle-11, 360-thing.angle- 7, fill=whtcol)
                draw.arc((p1x- 9, p1y- 9, p2x+ 9, p2y+ 9), 360-thing.angle+ 9, 360-thing.angle+13, fill=whtcol)
                draw.arc((p1x- 9, p1y- 9, p2x+ 9, p2y+ 9), 360-thing.angle-13, 360-thing.angle- 9, fill=whtcol)
                draw.arc((p1x- 8, p1y- 8, p2x+ 8, p2y+ 8), 360-thing.angle+11, 360-thing.angle+15, fill=whtcol)
                draw.arc((p1x- 8, p1y- 8, p2x+ 8, p2y+ 8), 360-thing.angle-15, 360-thing.angle-11, fill=whtcol)
                draw.arc((p1x- 7, p1y- 7, p2x+ 7, p2y+ 7), 360-thing.angle+12, 360-thing.angle+16, fill=whtcol)
                draw.arc((p1x- 7, p1y- 7, p2x+ 7, p2y+ 7), 360-thing.angle-16, 360-thing.angle-12, fill=whtcol)

                # draw border around rest of spot
                draw.arc((p1x- 6, p1y- 6, p2x+ 6, p2y+ 6), 360-thing.angle+12, 360-thing.angle-12, fill=whtcol)
                draw.arc((p1x- 4, p1y- 4, p2x+ 4, p2y+ 4), 360-thing.angle+14, 360-thing.angle-14, fill=whtcol)
                draw.arc((p1x- 2, p1y- 2, p2x+ 2, p2y+ 2), 360-thing.angle+15, 360-thing.angle-15, fill=whtcol)

            else:
                # draw border around entire spot
                draw.ellipse((p1x- 4, p1y- 4, p2x+ 4, p2y+ 4), outline=whtcol)
                draw.ellipse((p1x- 2, p1y- 2, p2x+ 2, p2y+ 2), outline=whtcol)

            # shift top-left corner by 'size/2' to center text in spot
            draw.text((thing.x - xmin + border - size[0]/2,
                       thing.y - ymin + border - size[1]/2 - 5),
                      spstr, txtcol, font=font)
            spawn += 1


if len(sys.argv) < 3:
    print("\n    Omgifol script: draw maps to image files\n")
    print("    Usage:")
    print("    drawmaps.py [-v] [-d] [-f] source.wad pattern [size [scale]]\n")
    print("    Draw all maps whose names match the given pattern (eg E?M4 or MAP*).")
    print("    If no 'size' is specified, default size is 1000 px.")
    print("    With 'scale' specified, all maps are rendered at that same scale,")
    print("    but still capped to 'size' if needed.")
    print("    With verbose flag '-v', log actual scale & dimensions per map and,")
    print("    without 'scale', also log the average scale for all maps.")
    print("    With DM spawns flag '-d' or CTF spawns flag '-f', draw numbered")
    print("    spawn spots.")
    print("    Wiki images can be max. 12,500,000 pixels, larger is flagged with !")
else:
    # process optional flags
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vdf')
        for o, a in opts:
            if o == '-v':
                verbose = True
            if o == '-d':
                dmspawns = True
            if o == '-f':
                ctfspawns = True
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)

    # don't use anti-aliasing without spawn spots
    if not dmspawns and not ctfspawns:
        alias = 1
    font = ImageFont.truetype('arial.ttf', txtdim * alias)

    # process optional limits
    try:
        maxpixels = int(args[2])
        try:
            reqscale = float(args[3])
        except:
            reqscale = 0
    except:
        maxpixels = 1000  # default size
        reqscale = 0

    # load WAD and draw map(s)
    print("Loading %s ..." % args[0])
    inwad = WAD()
    inwad.from_file(args[0])

    for name in inwad.maps.find(args[1]) + inwad.udmfmaps.find(args[1]):
        print("Drawing %s" % name, end='')
        drawmap(inwad, name, name + ".png", maxpixels, reqscale)
        if not verbose:
            print("")

    if verbose and total > 1:
        print("\nAvg scale: %0.2f" % (1.0 / (scales / total)))