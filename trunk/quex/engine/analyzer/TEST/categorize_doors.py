#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.analyzer.state_entry             import *
import help
from   collections import namedtuple

if "--hwut-info" in sys.argv:
    print "Categorize Entry Door Actions"
    print "CHOICES: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10;"
    sys.exit()

choice = sys.argv[1]

AcceptInfo = namedtuple("AcceptInfo", ("pre_context_id", "pattern_id"))
StoreInfo  = namedtuple("StoreInfo",  ("pre_context_id", "position_register", "offset"))

def test(ActionDB):
    entry = Entry(ActionDB.keys())
    for from_state_index, action_list in ActionDB.iteritems():
        for element in action_list:
            if isinstance(element, list):
                for info in element:
                    entry.doors_accept(from_state_index, info)
            else:
                entry.doors_accept(from_state_index, 
                                   element.pre_context_id, 
                                   element.position_register, 
                                   element.offset)
    print entry.categorize_doors()

if "1" in sys.argv:
    action_db = {
        0: [ [AcceptInfo(x, y) for x, y in [(1, 10), (2, 20)]] ],
        1: [ [AcceptInfo(x, y) for x, y in [(1, 10), (2, 20)]] ],
        2: [ [AcceptInfo(x, y) for x, y in [(1, 10), (2, 20)]] ],
    }
elif "2" in sys.argv:
    action_db = { 
        0: [ AcceptInfo(x, y) for x, y in [(2, 20), (1, 10)] ],
        1: [ AcceptInfo(x, y) for x, y in [(1, 10), (2, 20)] ],
    }
if "1" in sys.argv:
    action_db = {
        0: [ AcceptInfo(x, y) for x, y in [(1, 10), (2, 20)] ],
        1: [ AcceptInfo(x, y) for x, y in [(1, 10), (2, 20)] ],
        2: [ AcceptInfo(x, y) for x, y in [(1, 10), (2, 20)] ],
    }

test(action_db)


