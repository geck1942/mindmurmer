"""
This file contains several utility functions that can be imported
from other scripts, through the standard python import mechanism.
"""

import itertools, fr0stlib

def calculate_colors(xforms):
    """Distribute color values evenly among xforms. You can pass the entire
    xform list as an argument, or just a slice of it."""
    len_ = len(xforms) - 1.0 or 1.0
    for i, xf in enumerate(xforms):
        xf.color = i / len_


def normalize_weights(flame, norm=1.0):
    if(flame.xform is None or len(flame.xform) == 0):
        return
    """Normalize the weights of the xforms so that they total 1.0"""
    ws = sum(xf.weight for xf in flame.xform) / norm
    for xf in flame.xform:
        xf.weight /= ws

        
def batch(func, nflames, *a, **k):
    """Takes a flame-generating function, and calls it multiple
    times to generate a batch."""
    name = func.__name__ + "%03d"
    lst = []
    for i in range(nflames):
        flame = func(*a, **k)
        flame.name = name % i
        lst.append(flame)
    return lst


def animation_preview(flames, repeat=True):
    """ animate flames in an infinite loop."""
    assert fr0stlib.GUI # guard against command line scripts.
    itr = itertools.cycle(flames) if repeat else flames
    for f in itr:
        fr0stlib.preview(f)
        fr0stlib.show_status("previewing %s" %f)

def get_scriptpath():
    import os
    return os.path.dirname(os.path.realpath(__file__))
               
# static math methods:
def reduceAndClamp(inrange_value, inrange_min, inrange_max, outrange_min = 0, outrange_max = 1, overflow = False):
    inpct = (inrange_value - inrange_min) / (inrange_max - inrange_min)
    return clamp(inpct, outrange_min, outrange_max, overflow)

def clamp(percent, outrange_min = 0, outrange_max = 1, overflow = False):
    delta = outrange_max - outrange_min
    if (overflow == False and percent > 1): percent = 1
    if (overflow == False and percent < 0): percent = 0
    return (percent * delta) + outrange_min

def easing_cubic(percent, minvalue = 0, maxvalue = 1):
    percent *= 2.
    if(percent < 1) : return ((maxvalue - minvalue) / 2.) * percent * percent * percent + minvalue
    percent -= 2
    return ((maxvalue - minvalue) / 2.) * (percent * percent * percent + 2) + minvalue

def easing_square(percent, minvalue = 0, maxvalue = 1):
    percent *= 2.
    if(percent < 1) : return ((maxvalue - minvalue) / 2.) * percent * percent + minvalue
    percent -= 2
    return ((maxvalue - minvalue) / 2.) * (percent * percent + 2) + minvalue