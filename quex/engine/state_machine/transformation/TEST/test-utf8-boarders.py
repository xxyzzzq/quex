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
import quex.engine.state_machine.index                            as     index
import quex.engine.state_machine.TEST.helper_state_machine_shapes as     sms
import quex.engine.state_machine.algorithm.beautifier             as     beautifier
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

boarders = [ 
    0x00000080, 0x000007FF, 0x00000800, 0x0000FFFF, 
    0x00010000, 0x001FFFFF, 0x00200000, 0x03FFFFFF,
    0x04000000, 0x7FFFFFFF
]

good_sequences = [
    unicode_to_utf8(x) for x in boarders
]

def get_bad_sequences():
    """Take each good sequence and implant a codec error at any possible byte
    position.

    RETURNS: List of bad sequences.
    """
    global good_sequences
    bad_byte0s = [ 0x80, 0xBF, 0xFE, 0xFF ] # boarders of disallowed Byte[0]
    bad_byteNs = [ 0x00, 0x7F, 0xC0, 0xFF ] # boarders of disallowed Byte[>0]
    result     = []
    for sequence in good_sequences:
        # Implement a couple of bad sequences based on the good sequence.
        for i, lexatom in enumerate(sequence):
            if i == 0: bad_lexatoms = bad_byte0s
            else:      bad_lexatoms = bad_byteNs
            for bad in bad_lexatoms:
                bad_copy    = copy(sequence)
                bad_copy[i] = bad
                result.append(bad_copy)
    return result

def generate_sm():
    sm = StateMachine()
    for ucs_char in boarders:
        target_idx = index.get() 
        sms.line(sm, sm.init_state_index, 
                 (ucs_char, target_idx), (ucs_char, target_idx))
        sm.states[target_idx].set_acceptance()

    verdict_f, result = EncodingTrafoUTF8().do_state_machine(sm, beautifier)
    assert verdict_f
    return result

def sequence_string(Sequence):
    return "".join("%02X." % x for x in Sequence)[:-1]

def result_string(state):
    if state is None:
        return "None"
    elif state.has_acceptance_id(E_IncidenceIDs.BAD_LEXATOM):
        return "Bad Lexatom"
    elif state.is_acceptance():
        return "Accept"
    else:
        return "No Accept"

sm = generate_sm()

if True:
    print
    print "Good Sequences: ________________________________________________________"
    print
    for sequence in good_sequences:
        state = sm.apply_sequence(sequence, StopAtBadLexatomF=True)
        print "%s: %s" % (result_string(state), sequence_string(sequence))
           
    print
    print "Bad Sequences: _________________________________________________________"
    print
    for sequence in get_bad_sequences():
        state = sm.apply_sequence(sequence, StopAtBadLexatomF=True)
        print "%s: %s" % (result_string(state), sequence_string(sequence))

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
