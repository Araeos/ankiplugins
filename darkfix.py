# -*- coding: utf-8 -*-
#
# Modifies the default colour scheme in places that conflict with darker
# system colours.
#
# Author: Felix Esch
# VCS+issues: https://github.com/Araeos/ankiplugins
# Licence: GNU General Public Licence (GNU GPL), version 3
#
# Version: 1.5.0                                                [2015-08-22 Sat]
# - Improved colours in browser; suspended and marked cards are better
#   integrated in the user's colour theme.
# - Refactored colour selection code.
# Version: 1.4.3, Patch by: flan                                [2015-08-19 Wed]
# - Fixed infinite loop on start when one of the palette hues is not in the
#   [0, 360] range
# Version: 1.4.2                                                [2015-02-05 Thu]
# - Fixed invalid colour values in range lightness_list.

from anki.hooks import wrap
from aqt import editor, browser, reviewer
from aqt.qt import QPalette, QColor
import math
import re

def main():
    # Query system colours.
    p = QPalette()
    textcolour = p.color(QPalette.Text)
    basecolour = p.color(QPalette.Base)

    # Inject background colour into the browser.
    def tree_colour_hook(self):
        p = self.form.tree.palette()
        p.setColor(QPalette.Base, basecolour)
        self.form.tree.setPalette(p)
    browser.Browser.setupTree = wrap(browser.Browser.setupTree, tree_colour_hook)

    # Change suspend and mark colours.
    coloursuspended = QColor()
    coloursuspended.setNamedColor(browser.COLOUR_SUSPENDED)
    colourmarked = QColor()
    colourmarked.setNamedColor(browser.COLOUR_MARKED)
    lightness_blacklist = [textcolour.lightness()]
    hue_blacklist = [basecolour.hue(), textcolour.hue()]
    lightness_preference = max(basecolour.lightness(), 40)
    for colour in [coloursuspended, colourmarked]:
        (h, s, l, a) = colour.getHsl()
        new_lightness = get_new_lightness(lightness_blacklist, lightness_preference)
        # print("Considering {0} with preference {2} choose lightness {1}\n".format(
        #     lightness_blacklist, new_lightness, lightness_preference))
        new_hue = get_new_hue(hue_blacklist, h)
        # print("Considering {0} with preference {2} choose hue {1}\n".format(
        #     hue_blacklist, new_hue, h))
        hue_blacklist.append(new_hue)
        colour.setHsl(new_hue, s, new_lightness, a)
    browser.COLOUR_SUSPENDED = coloursuspended.name()
    browser.COLOUR_MARKED = colourmarked.name()

    # Inject colouring into the web view.
    editor._html = re.sub(
        "(\\.fname\s*\\{)",
        "\\1 color: {0};".format(textcolour.name()),
        editor._html)
    # Fix the default text colour for type answer edit elements.
    reviewer.Reviewer._css = re.sub(
        "(#typeans\s*\\{)",
        "\\1 color: {0};".format(textcolour.name()),
        reviewer.Reviewer._css)

def get_new_lightness(existing, pref):
    """Given a list of existing lightness return a new, different value.

    Args:
        existing (List[int]): List of existing values to avoid.
        pref (Optional[int]): Preferred value. May be none.

    Returns:
        int: The best value."""
    # Filter input of duplicates and sort it (required below).
    existing = sorted(set(existing))
    if len(existing) == 0:
        return 0;
    else:
        a, b = None, None
        candidates = []
        for exist_value in existing + [None]:
            a, b = b, exist_value
            # From low(inclusive) to high(exclusive).
            low, high = (0 if a is None else a + 1), (256 if b is None else b)
            diff =  high - low
            for offset in range(0, diff):
                val = low + offset
                if   a is None: space = diff - offset
                elif b is None: space = offset
                else:           space = min(diff - offset, offset)
                if pref is None: distance = None
                else:            distance = abs(pref - val)
                r = rating(space, distance, 256, crit_range=50, crit_value=0.85)
                candidates.append((val, r))
        candidates.sort(key=lambda (val, diff): diff)
        return candidates[-1][0]


def get_new_hue(existing, pref):
    """Given a list of existing hues return a new, different value.

    Args:
        existing (List[int]): List of existing values to avoid.
        pref (Optional[int]): Preferred value. May be none.

    Returns:
        int: The best value."""
    def choose_best_between(low, high):
        """Rate all hues from low(exclusive) to high(exclusive).

        When a == b is true, this will scan all other 359 hues.
        """
        diff = (high - low - 1) % 360
        best_val = (None, 0)
        for offset in range(1, diff + 1):
            val = (low + offset) % 360
            space = min(offset, diff - offset + 1)
            if pref is None: distance = None
            else:            distance = min((pref - val) % 360,
                                            (val - pref) % 360)
            r = rating(space, distance, 360, crit_range=40, crit_value=0.8)
            if r > best_val[1]:
                best_val = (val, r)
        return best_val
    # Filter input of duplicates and sort it (required below).
    existing = sorted(set(existing))
    if len(existing) == 0:
        return 0;
    else:
        candidates = []
        for i in range(len(existing)):
            a, b = existing[i], existing[(i + 1) % len(existing)]
            candidates.append(choose_best_between(a, b))
        candidates.sort(key=lambda (val, diff): diff)
        return candidates[-1][0]

#-------------------------------------------------------------------------------
# Helper methods
#-------------------------------------------------------------------------------
def recenter_interval(center, inverse = False):
    """Returns a function that maps values from (0, 1) to (0, 1).

    Center is the position where previous values are mapped to below 0.5
    and following values above 0.5.
    The properties of the returned function `f` in the interval [0, 1] are:
     - f is increasing (monotonic)
     - f is continuous (gaps are subject to floating point precision)
     - f(0.) = 0.
     - f(1.) = 1.
     - Main critera depends on `inverse`:
         - f(center) = 0.5, if False or omitted
         - f(0.5) = center, if True
    The returned function is undefined outside the (closed) interval [0, 1].

    To satisfy the above properties, center must be within (0, 1), but neither
    0 nor 1 is allowed.
    Args:
        center (float): The value within the domain (0, 1) which will be mapped
            to 0.5.
        inverse (bool): When False or omitted map `center` to 0.5. Else map 0.5
            to `center` (inverse function).

    Returns:
        Callable[[float], float]: The function with the above properties.
            May be None when `center` is not well within (0, 1)."""
    max_error = 0.0000001
    if abs(center - 0) < max_error or abs(center - 1) < max_error:
        raise RuntimeError("center ({0}) must be within open interval (0, 1)".format(center))
    if abs(center - 0.5) < max_error:
        return lambda x: x
    elif center < 0.5:
        a = 1 / (2 * math.log(1 / center - 1))
        b = 1
        c = center**2 / (1 - 2*center)
        d = -a * math.log(c)
    else:
        a = -1 / (2 * math.log(1 / (1 - center) - 1))
        b = -1
        c = - center**2 / (1 - 2*center)
        d = 1 - a * math.log(c - 1)
    if inverse:
        return lambda x: b * (math.e**((x - d) / a) - c)
    else:
        return lambda x: a * math.log(b*x + c) + d

def rating_comp_undesired(maximum, undesired):
    """Helper for the rating function."""
    return 0.5 * (1 + math.cos(math.pi * undesired / maximum))
    return 1 - 1. / maximum * undesired

def rating_comp_required(maximum, required, crit_range, crit_value):
    """Helper for the rating function."""
    f_x = recenter_interval(float(crit_range) / maximum)
    f_y = recenter_interval(crit_value, True)
    return f_y(0.5 * (1 - math.cos(f_x(float(required) / maximum) * math.pi)))

def rating(required, undesired, maximum, crit_range = None, crit_value = 0.8):
    """Calculate a rating based on given parameters heuristically.

    A higher rating means a good compromise of values 'required' and
    'undesired'.

    Args:
        required (float): A value between 0 and 'maximum' which should not
            not be too low. Higher is better, but undesired may win out
            quickly depending on the values of 'crit_range' and 'crit_value'.
            Within (0, crit_range) slopes to reach `crit_value` influence
            and then more slowly again until it reaches 1 at `maximum`.
        undesired (float): A value between 0 and 'maximum' which
            is desired to be low.
        maximum (float): Maximum value that 'undesired'/'required' will
            have. The minimum is always 0.
        crit_range (Optional[int]): The range in which the required value's
            importance is lower than indicated by `crit_value`.
        crit_value (Optional[float]): The quotient of importance that
            'required' will have when equal to 'crit_range'.
            Must be between 0 and 1 (exclusive).
    Returns:
        int: Rating that shows the quality of compromise between 'required'
            and 'undesired'."""
    if crit_range is None:
        crit_range = 0.1 * maximum
    r_s =  rating_comp_required(maximum, required, crit_range, crit_value)
    r_d =  rating_comp_undesired(maximum, undesired)
    return 0.5 * (r_s + r_d)


#-------------------------------------------------------------------------------
# Entry point
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    print("This python script should be run as an anki addon.")
else:
    main()
