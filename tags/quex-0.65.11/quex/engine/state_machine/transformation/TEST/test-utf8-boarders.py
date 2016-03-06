#! /usr/bin/env python
# 
# PURPOSE: Check transition generation at 'codec boarder'.
#
# UTF8 codes unicode characters in byte sequences of different length. The
# length of a byte sequence is determined by the range in the Unicode
# representation.
#
#    0x00000080 - 0x000007FF: 1 byte: 0xxxxxxx
#    0x00000800 - 0x0000FFFF: 2 byte: 110xxxxx 10xxxxxx
#    0x00010000 - 0x001FFFFF: 3 byte: 1110xxxx 10xxxxxx 10xxxxxx
#    0x00200000 - 0x03FFFFFF: 4 byte: 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
#    0x04000000 - 0x7FFFFFFF: 5 byte: 111110xx 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxx
#                             6 byte: 1111110x 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxxx
#
# From the above mapping 10 boarders (the first column) are extracted and coded
# in a state machine. The state machine is double-checked by stimulating it
# with:
#        (i)  code sequences that represent the boarders.
#        (ii) code sequences that lie outside the codec range.
#
# The implemented state machine inhabit repetition to challenag the robustness
# of the coder.
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________

import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine                       as     regex
from   quex.engine.misc.interval_handling                         import NumberSet, Interval
from   quex.engine.state_machine.transformation.utf8_state_split  import EncodingTrafoUTF8
from   quex.engine.state_machine.core                             import StateMachine
from   quex.engine.misc.utf8                                      import unicode_to_utf8
import quex.engine.state_machine.transformation.TEST.helper       as     helper


from   quex.blackboard import setup as Setup, \
                              E_IncidenceIDs

if "--hwut-info" in sys.argv:
    print "UTF8 Split: Repetition at Codec Boarders"
    print "CHOICES:    error-detect, plain;"
    sys.exit()

if "error-detect" in sys.argv:
    Setup.bad_lexatom_detection_f = True
else:
    Setup.bad_lexatom_detection_f = False

boarders = [ 
    0x00000080, 0x000007FF, 0x00000800, 0x0000FFFF, 
    0x00010000, 0x001FFFFF, 0x00200000, 0x03FFFFFF,
    0x04000000, 0x7FFFFFFF
]

good_sequences = [
    unicode_to_utf8(x) for x in boarders
]

# Boarders of code unit ragnes which are encoding errors:
bad_byte0s = [ 0x80, 0xBF, 0xFE, 0xFF ] # boarders of disallowed Byte[0]
bad_byteNs = [ 0x00, 0x7F, 0xC0, 0xFF ] # boarders of disallowed Byte[>0]

sm = helper.generate_sm_for_boarders(boarders, EncodingTrafoUTF8())

bad_sequence_list = helper.get_bad_sequences(good_sequences, bad_byte0s, bad_byteNs)

if True:
    helper.test_good_and_bad_sequences(sm, good_sequences, bad_sequence_list)

else:
    # Check on isolated sequence (debugging)
    sequence = [ 0x80, 0x80 ]
    si       = sm.init_state_index
    print "#si:", si, sm.states[si]
    for lexatom in sequence:
        print "#tm:", sm.states[si].target_map
        si = sm.states[si].target_map.get_resulting_target_state_index(lexatom)
        if si is None: break
        print "#si:", si, sm.states[si]

#helper.show_graphviz(sm)
