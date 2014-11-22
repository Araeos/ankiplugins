# -*- coding: utf-8 -*-
#
# Removes the field formatting of all selected notes.
#
# Author: xelif@icqmail.com


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.hooks import addHook
from aqt import mw
#import sys
import re

def stripFormatting(txt):
    """
    Removes all html tags, except if they begin like this: <img...>
    This allows inserted images to remain.

    Parameters
    ----------
    txt : string
        the string containing the html tags to be filtered
    Returns
    -------
    string
        the modified string as described above
    """
    return re.sub("<(?!img).*?>", "", txt)

def setupMenu(browser):
    """
    Add the button to the browser menu "edit".
    """
    a = QAction("Bulk-Clear Formatting", browser)
    browser.connect(a, SIGNAL("triggered()"), lambda e=browser: onClearFormatting(e))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)

def onClearFormatting(browser):
    """
    Clears the formatting for every selected note.
    Also creates a restore point, allowing a single undo operation.

    Parameters
    ----------
    browser : Browser
        the anki browser from which the function is called
    """
    mw.checkpoint("Bulk-Clear Formatting")
    mw.progress.start()
    for nid in browser.selectedNotes():
        note = mw.col.getNote(nid)
        def clearField(field):
            result = stripFormatting(field);
            # if result != field:
            #     sys.stderr.write("Changed: \"" + field
            #                      + "\" ==> \"" + result + "\"")
            return result
        note.fields = map(clearField, note.fields)
        note.flush()
    mw.progress.finish()
    mw.reset()

addHook("browser.setupMenus", setupMenu)
