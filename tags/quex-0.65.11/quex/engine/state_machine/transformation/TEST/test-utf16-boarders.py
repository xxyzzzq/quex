#! /usr/bin/env python
# 
# PURPOSE: Check transition generation at 'codec boarder'.
#
# UTF16 codes unicode characters in byte sequences of different length. The
# length of a byte sequence is determined by the range in the Unicode
# representation.
#
#    0x000000 - 0x00D7FF: 1 code unit = 2 byte = original UCS code
#    0x00E000 - 0x00FFFF: (same)
#    0x010000 - 0x110000: 2 code units = 4 byte = constructed from UCS code
#                         Range of 1st code unit: 0xD800..0xDBFF
#                                  2nd code unit: 0xDC00..0xDFFF
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
from   quex.engine.state_machine.transformation.utf16_state_split import EncodingTrafoUTF16
from   quex.engine.state_machine.core                             import StateMachine
from   quex.engine.misc.utf16                                     import unicode_to_utf16
import quex.engine.state_machine.index                            as     index
import quex.engine.state_machine.TEST.helper_state_machine_shapes as     sms
import quex.engine.state_machine.transformation.TEST.helper       as     helper


from   quex.blackboard import setup as Setup, \
                              E_IncidenceIDs
from   copy            import copy

if "--hwut-info" in sys.argv:
    print "UTF8 Split: Repetition at Codec Boarders"
    print "CHOICES:    error-detect, plain;"
    sys.exit()

if "error-detect" in sys.argv:
    Setup.bad_lexatom_detection_f = True
else:
    Setup.bad_lexatom_detection_f = False

#   0x000000 - 0x00D7FF: 1 code unit = 2 byte = original UCS code
#   0x00E000 - 0x00FFFF: (same)
#   0x010000 - 0x110000: 2 code units = 4 byte = constructed from UCS code
#                        Range of 1st code unit: 0xD800..0xDBFF
#                                 2nd code unit: 0xDC00..0xDFFF
boarders = [ 
    0x000080, 0x00D7FF, 0x00E000, 0x00FFFF, 
    0x010000, 0x10FFFF
]

good_sequences = [
    unicode_to_utf16(x) for x in boarders
]

# Boarders of code unit ragnes which are encoding errors:
bad_1st_s = [ 0xDC00, 0xDFFF ]                   # boarders of disallowed CodeUnit[0]
bad_2nd_s = [ 0x0000, 0xDBFF, 0xE000, 0x110000 ] # boarders of disallowed CodeUnit[1]

good_sequences = [
    unicode_to_utf16(x) for x in boarders
]

trafo = EncodingTrafoUTF16()
trafo.adapt_source_and_drain_range(LexatomByteN=4)
sm = helper.generate_sm_for_boarders(boarders, EncodingTrafoUTF16())

bad_sequence_list = helper.get_bad_sequences(good_sequences, bad_1st_s, bad_2nd_s)


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


# helper.show_graphviz(sm)
