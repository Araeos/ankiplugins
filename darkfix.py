# -*- coding: utf-8 -*-
#
# Fixed the browser tree background to use the system colour.
#
# Author: xelif@icqmail.com
from anki.hooks import wrap
from aqt.browser import Browser
from aqt.qt import *

def mySetupTree(self):
    p = QPalette()
    #p = self.form.tree.palette()
    #p.setColor(QPalette.Base, QColor("#101010"))
    self.form.tree.setPalette(p)

Browser.setupTree = wrap(Browser.setupTree, mySetupTree)
