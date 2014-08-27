# (C) Frank-Rene Schaefer
from   quex.engine.state_machine.core                  import StateMachine
import quex.engine.state_machine.utf8_state_split      as utf8_state_split
import quex.engine.state_machine.utf16_state_split     as utf16_state_split
import quex.engine.state_machine.algorithm.beautifier  as beautifier
from   quex.engine.analyzer.transition_map             import TransitionMap
from   quex.engine.misc.file_in                        import error_msg
from   quex.engine.interval_handling                   import NumberSet
from   quex.blackboard                                 import setup as Setup

from   quex.engine.tools import typed

@typed(X=(StateMachine,None))
def do_state_machine(X):
    """Transforms a given state machine from 'Unicode Driven' to another
       character encoding type.
    
       RETURNS: 
       [0] Transformation complete (True->yes, False->not all transformed)
       [1] Transformed state machine. It may be the same as it was 
           before if there was no transformation actually.

       It is ensured that the result of this function is a DFA compliant
       state machine.
    """
    def ensure_dfa_compliance(SM):
        if   SM is None:            return None
        elif SM.is_DFA_compliant(): return SM
        else:                       return beautifier.do(SM)

    if X is None: 
        return True, ensure_dfa_compliance(X)

    assert X.is_DFA_compliant()
    TrafoInfo = Setup.buffer_codec_transformation_info

    if TrafoInfo is None: 
        complete_f = True
        result     = X
    elif isinstance(TrafoInfo, (str, unicode)):
        if   TrafoInfo == "utf8-state-split":  
            complete_f = True
            result     = utf8_state_split.do(X)
        elif TrafoInfo == "utf16-state-split": 
            complete_f = True
            result     = utf16_state_split.do(X)
        else:                                  
            assert False
    else:
        # Pre-condition SM is transformed inside the member function
        complete_f = X.transform(TrafoInfo) # All uncovered characters => 'DoorID.incidence(E_IncidenceIDs.CODEC_ERROR)'
        result     = X

    return complete_f, ensure_dfa_compliance(result)

def do_set(number_set, TrafoInfo, fh=-1):
    """RETURNS: True  transformation successful
                False transformation failed, number set possibly in inconsistent state!
    """
    assert TrafoInfo is not None
    assert isinstance(number_set, NumberSet)

    if isinstance(TrafoInfo, (str, unicode)):
        if TrafoInfo == "utf8-state-split": 
            result = utf8_state_split.do_set(number_set)
            if result is None:
                error_msg("Operation 'number set transformation' failed 'utf8'.\n" + \
                          "The given number set results in a state sequence not a single transition.", fh) 
            return result
        elif TrafoInfo == "utf16-state-split": 
            result = utf16_state_split.do_set(number_set)
            if result is None:
                error_msg("Operation 'number set transformation' failed 'utf16'.\n" + \
                          "The given number set results in a state sequence not a single transition.", fh) 
            return result
        # Other transformations are not supported
        assert False
    
    return number_set.transform(TrafoInfo)

def do_character(Character, TrafoInfo, fh=-1):
    """The current implementation is, admitably, not very fast. 
    Improve upon detection of speed issues.

    RETURNS: A list of integers which represent the character in the 
             given TrafoInfo.
    """
    if TrafoInfo is None:
        return [ Character ]
    return do_set(NumberSet(Character), TrafoInfo, fh).get_intervals()

def do_sequence(Sequence, TrafoInfo=None, fh=-1):
    if TrafoInfo is None:
        TrafoInfo = Setup.buffer_codec_transformation_info
    result = []
    for x in Sequence:
        result.extend(do_character(x, TrafoInfo, fh))
    return result

def homogeneous_chunk_n_per_character(Thing, TrafoInfo):
    assert isinstance(TrafoInfo, (str, unicode))

    def _core(module, SM_or_CharacterSet):
        """Consider a given state machine (pattern). If all characters involved in the 
        state machine require the same number of chunks (2 bytes) to be represented 
        this number is returned. Otherwise, 'None' is returned.

        RETURNS:   N > 0  number of chunks (2 bytes) required to represent any character 
                          in the given state machine.
                   None   characters in the state machine require different numbers of
                          chunks.
        """
        if isinstance(SM_or_CharacterSet, NumberSet):
            return module.homogeneous_chunk_n_per_character(SM_or_CharacterSet)
        else:
            chunk_n = None
            for state in SM_or_CharacterSet.states.itervalues():
                for number_set in state.target_map.get_map().itervalues():
                    candidate_chunk_n = module.homogeneous_chunk_n_per_character(number_set)
                    if   candidate_chunk_n is None:    return None
                    elif chunk_n is None:              chunk_n = candidate_chunk_n
                    elif chunk_n != candidate_chunk_n: return None
            return chunk_n

    if   TrafoInfo == "utf8-state-split":  return _core(utf8_state_split, Thing)
    elif TrafoInfo == "utf16-state-split": return _core(utf16_state_split, Thing)
    else:                                  assert False


