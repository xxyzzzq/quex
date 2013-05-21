#! /usr/bin/env python
# - * - coding : utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.analyzer.state.entry            import *
from   quex.engine.analyzer.state.entry_action     import *
import quex.engine.generator.state.entry_door_tree as     entry_door_tree

from   collections import namedtuple
from   copy import copy
from   random import randint

if "--hwut-info" in sys.argv:
    print "Build Tree of Entry Door Commands"
    print "CHOICES: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, set_state_key, set_path_iterator;" #, clear_door_tree;"
    sys.exit()

choice = sys.argv[1]

A1   = [AccepterElement(x, y) for x, y in [(1, 10), (2, 20)]]
A2   = [AccepterElement(x, y) for x, y in [(2, 20), (1, 10)]]
S000 = StoreInputPosition(0, 0, 0) # 1
S001 = StoreInputPosition(0, 0, 1) # 2
S002 = StoreInputPosition(0, 0, 2) # 3
S100 = StoreInputPosition(1, 0, 0) # 4
S101 = StoreInputPosition(1, 0, 1) # 5
S102 = StoreInputPosition(1, 0, 2) # 6
S010 = StoreInputPosition(0, 1, 0) # 7
S011 = StoreInputPosition(0, 1, 1) # 8
S012 = StoreInputPosition(0, 1, 2) # 9

def make_action_db(DoorDb):
    result = {}
    for transition_id, door_id in DoorDb.iteritems():
        ta = TransitionAction(transition_id.state_index, transition_id.from_state_index, 
                              CommandList(), transition_id.trigger_id)
        ta.door_id = door_id
        result[transition_id]   = ta

def test(ActionDB):
    state_index = 0
    entry = Entry(state_index, ActionDB.keys())
    for from_state_index, action_list in ActionDB.iteritems():
        for element in action_list:
            if isinstance(element, list):
                entry.action_db.add_specific_Accepter(from_state_index, element)
            else:
                entry.action_db.add_StoreInputPosition(from_state_index, 
                                                       element.pre_context_id, 
                                                       element.position_register, 
                                                       element.offset)
    entry.action_db.categorize(state_index)
    door_db, door_tree_root = entry_door_tree.do(state_index, entry.action_db)
    print door_tree_root.get_string(entry.action_db)

if "1" in sys.argv:
    # All three states have exactly the same entry actions
    action_db = {
        0: [ A1 ],
        1: [ A1 ],
        2: [ A1 ],
    }
elif "2" in sys.argv:
    # Two different entry actions
    action_db = { 
        0: [ A2 ],
        1: [ A1 ],
    }
elif "3" in sys.argv:
    # One entry action is shared. 
    # Each door has a special action.
    action_db = {
        0: [ A1, S000 ],
        1: [ A1, S001 ],
        2: [ A1, S002 ],
    }
elif "4" in sys.argv:
    # One entry action is shared. 
    # Each two doors share an action.
    action_db = {
        0: [ A1, S000 ],
        1: [ A1, S000 ],
        2: [ A1, S001 ],
        3: [ A1, S001 ],
        4: [ A1, S002 ],
        5: [ A1, S002 ],
    }
elif "5" in sys.argv:
    # One entry action is shared. 
    # Each two doors share an action.
    # Each door has a special action.
    action_db = {
        0: [ A1, S000, S100 ],
        1: [ A1, S000, S101 ],
        2: [ A1, S001, S102 ],
        3: [ A1, S001, S010 ],
    }
elif "6" in sys.argv:
    # One entry action is shared. 
    # Each two doors share an action.
    # Each door has a special action.
    action_db = {
        0: [ A1, S000, S100 ],
        1: [ A1, S000, S101 ],
        2: [ A2, S001, S102 ],
        3: [ A2, S001, S010 ],
    }
elif "7" in sys.argv:
    actions   = [A1, A2, S000, S001, S002, S100, S101, S102, S010, S011, S012]
    action_db = dict((i, [x]) for i, x in enumerate(actions))

elif "8" in sys.argv:
    actions   = [A1, S000, S001, S002, S100, S101, S102, S010, S011, S012]
    action_db = dict((i, actions) for i in xrange(100))

elif "9" in sys.argv:
    action_db = dict((i, []) for i in xrange(1000))

elif "10" in sys.argv:
    actions   = [A1, S000, S001, S002, S100, S101, S102, S010, S011, S012]
    L         = len(actions)
    def get_actions(Index):
        result = copy(actions)
        del result[Index % L]
        return result

    print "ActionDB:"
    action_db = {}
    for i in xrange(10):
        action_list = get_actions(i)
        print "(0<-%i):" % i
        txt = []
        for action in action_list:
            txt.append("    %s\n" % repr(action).replace("\n", ""))
        txt.sort()
        print "".join(txt)
        action_db[i] = action_list
    print "-----------------------------------"

elif "11" in sys.argv:
    from quex.blackboard import setup as Setup
    Setup.state_entry_analysis_complexity_limit = 5
    action_db = dict((i, [StoreInputPosition(0, 0, i)]) for i in xrange(10))

elif "set_state_key" in sys.argv:
    action_list = [
        TransitionAction(1, 1, CommandList([ SetTemplateStateKey(1) ])),
        TransitionAction(2, 1, CommandList([ SetTemplateStateKey(2) ])),
        TransitionAction(3, 1, CommandList([ SetTemplateStateKey(2) ])),
        TransitionAction(4, 1, CommandList([ SetTemplateStateKey(2) ])),
        TransitionAction(1, 2, CommandList([ SetTemplateStateKey(3) ])),
        TransitionAction(2, 2, CommandList([ SetTemplateStateKey(3) ])),
        TransitionAction(3, 2, CommandList([ SetTemplateStateKey(3) ])),
        TransitionAction(4, 2, CommandList([ SetTemplateStateKey(4) ])),
    ]
    door_db, door_tree_root = build_door_tree(4711, action_list)
    print door_tree_root.get_string(make_action_db(door_db))
    sys.exit(0)

elif "set_path_iterator" in sys.argv:
    action_list = [
        TransitionAction(1, 1, CommandList([ SetPathIterator(0, 1, 1) ])),
        TransitionAction(2, 1, CommandList([ SetPathIterator(0, 1, 1) ])),
        TransitionAction(3, 1, CommandList([ SetPathIterator(0, 1, 1) ])),
        TransitionAction(4, 1, CommandList([ SetPathIterator(1, 1, 1) ])),
        TransitionAction(1, 2, CommandList([ SetPathIterator(1, 1, 1) ])),
        TransitionAction(2, 2, CommandList([ SetPathIterator(2, 1, 1) ])),
        TransitionAction(3, 2, CommandList([ SetPathIterator(1, 2, 1) ])),
        TransitionAction(4, 2, CommandList([ SetPathIterator(1, 1, 2) ])),
    ]
    door_db, door_tree_root = build_door_tree(4711, action_list)
    print door_tree_root.get_string(make_action_db(door_db))
    sys.exit(0)

elif "clear_door_tree" in sys.argv:
    Door.init()
    # Create an empty tree of nodes --> should totally collapse to one node.
    ti   = 0
    #    def generate_childs(parent, Depth=0):
    #        global ti
    #        child_n    = randint(1, 3 - Depth)
    #        if Depth == 1:
    #            parent.child_list = [ Door(parent, CommandList(), [TransitionAction(ti + i)]) \
    #                                for i in xrange(child_n) ]
    #            ti += child_n
    #        else:
    #            parent.child_list = [ Door(parent, CommandList(), []) for i in xrange(child_n) ]
    #            for child in parent.child_list:
    #                generate_childs(child, Depth + 1)
    # root = Door(None, CommandList(), [])
    # generate_childs(root)

    root = Door(None, CommandList(), [])
    node = root
    for i in xrange(10):
        node.child_list = [ Door(node, CommandList(), []) ]
        node = node.child_list[0]

    node.child_list = [ Door(node, CommandList(), [TransitionAction(0, 0)]) ]
    print root
    print clear_door_tree(root)
    sys.exit()
        
elif "X" in sys.argv:
    actions   = [A1, S000, S001, S002, S100, S101, S102, S010, S011, S012]
    L         = len(actions)
    def get_actions(Index):
        result = copy(actions)
        del result[Index % L]
        return result
    action_db = dict((i, get_actions(i)) for i in xrange(1000))

test(action_db)


