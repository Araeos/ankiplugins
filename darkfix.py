# -*- coding: utf-8 -*-
#
# Modifies the default colour scheme in places that conflict with darker
# system colours.
#
# Version: 1.4
#
# Author: xelif@icqmail.com
from anki.hooks import wrap
from aqt import editor, browser, reviewer
from aqt.qt import *
import math
import re

# Query system colours.
p = QPalette()
textcolour = p.color(QPalette.Text)
basecolour = p.color(QPalette.Base)

def getAlternateLightness(values, lower=0, upper=255):
    values = sorted(set(values))
    candidates = []
    if len(values) == 0:
        return (upper - lower) / 2
    if values[0] > lower:
        candidates.append((lower, math.sqrt(values[0]) - math.sqrt(lower)))
    if values[-1] < upper:
        candidates.append((upper, math.sqrt(upper) - math.sqrt(values[-1])))
    for i in range(len(values) - 1):
        a, b = values[i], values[i+1]
        #middle = (values[i+1] - values[i]) / 2
        middle = math.floor((a + b + 2 * math.sqrt(a) * math.sqrt(b)) / 4)
        candidates.append((middle, min(abs(math.sqrt(middle) - math.sqrt(a)), abs(math.sqrt(b) - math.sqrt(middle)))))
    candidates.sort(key=lambda (val, diff): abs(diff))
    return candidates[-1][0]

def hueDiff(a, b):
    return min((a - b) % 360, (b - a) % 360)

def getAlternateHue(values, pref=None):
    def maxMiddle(a, b, h):
        while a != b:
            m = (a + ((b - a) % 360) / 2) % 360
            if h(m) <= h(m+1):
                a = m+1
            else:
                b = m
        return (a, h(a))
    def makeHeuristic(a, b):
        return lambda x: min(hueDiff(a,x), hueDiff(x, b)) * (1 - 0.00045 * (0 if pref is None else hueDiff(x, pref)**2))
    values = sorted(set(values))
    candidates = []
    if len(values) == 0:
        return 0;
    if len(values) == 1:
        a, b = values[0], (values[0] - 1) % 360
        return maxMiddle(a, b, makeHeuristic(a, b))[0]
    for i in range(len(values)):
        a, b = values[i], values[(i + 1) % len(values)]
        candidates.append(maxMiddle(a, b, makeHeuristic(a, b)))
    candidates.sort(key=lambda (val, diff): diff)
    return candidates[-1][0]


# Inject background colour into the browser.
def mySetupTree(self):
    p = self.form.tree.palette()
    p.setColor(QPalette.Base, basecolour)
    self.form.tree.setPalette(p)
browser.Browser.setupTree = wrap(browser.Browser.setupTree, mySetupTree)

# Change suspend and mark colours.
coloursuspended = QColor()
coloursuspended.setNamedColor(browser.COLOUR_SUSPENDED)
colourmarked = QColor()
colourmarked.setNamedColor(browser.COLOUR_MARKED)
lightness_list = [basecolour.lightness()] + range(textcolour.lightness()-25, textcolour.lightness()+26)
hue_list = [basecolour.hue(), textcolour.hue()]
for colour in [coloursuspended, colourmarked]:
    (h, s, l, a) = colour.getHsl()
    l = getAlternateLightness(lightness_list, 30, 210)
    h = getAlternateHue(hue_list, h)
    colour.setHsl(h, s, l, a)
    hue_list.append(h)
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
