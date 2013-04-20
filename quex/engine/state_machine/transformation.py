# (C) 2009 Frank-Rene Schaefer
import os
import sys
from   quex.engine.state_machine.core                  import StateMachine
import quex.engine.state_machine.utf8_state_split      as utf8_state_split
import quex.engine.state_machine.utf16_state_split     as utf16_state_split
import quex.engine.state_machine.algorithm.beautifier  as beautifier
import quex.engine.analyzer.transition_map             as     transition_map_tool
from   quex.engine.misc.file_in                        import error_msg
from   quex.engine.interval_handling                   import NumberSet
from   quex.blackboard                                 import setup as Setup

sys.path.append(os.environ["QUEX_PATH"])

def do_state_machine(X, TrafoInfo=None):
    """Transforms a given state machine from 'Unicode Driven' to another
       character encoding type.
    
       RETURNS: 
       [0] Transformation complete (True->yes, False->not all transformed)
       [1] Transformed state machine. It may be the same as it was 
           before if there was no transformation actually.
    """
    if X is None: 
        return True, X

    assert isinstance(X, StateMachine)
    assert X.is_DFA_compliant()

    if TrafoInfo is None:
        TrafoInfo = Setup.buffer_codec_transformation_info

    if TrafoInfo is None: 
        return True, X

    if isinstance(TrafoInfo, (str, unicode)):
        if   TrafoInfo == "utf8-state-split":  return True, __DFA(utf8_state_split.do(X))
        elif TrafoInfo == "utf16-state-split": return True, __DFA(utf16_state_split.do(X))
        else:                                  assert False
    
    # Pre-condition SM is transformed inside the member function
    complete_f = X.transform(TrafoInfo)
    return complete_f, __DFA(X)

def __DFA(SM):
    if   SM is None:            return None
    elif SM.is_DFA_compliant(): return SM

    result = beautifier.do(SM)
    return result

def do_set(number_set, TrafoInfo, fh=-1):
    """RETURNS: True  transformation successful
                False transformation failed, number set possibly in inconsistent state!
    """
    assert TrafoInfo is not None
    assert TrafoInfo.__class__.__name__ == "NumberSet"

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

def do_sequence(Sequence, TrafoInfo, fh):
    result = []
    for x in Sequence:
        result.extend(do_character(x))
    return result

def do_transition_map(TM, TrafoInfo=None):
    """RETURNS: verdict, tm

       verdict == True, if the transformation has been made without any 
       complaints or missing characters. It is 'False' if not. 'tm' is 
       the resulting transition map.
    """
    if TrafoInfo is None:
        TrafoInfo = Setup.buffer_codec_transformation_info
    if TrafoInfo is None:
        return True, TM

    assert not isinstance(TrafoInfo, (str, unicode)) or TrafoInfo.find("-state-split") == -1

    total_verdict = True
    result        = []
    for interval, target in TM:
        verdict, transformed = interval.transform(TrafoInfo)
        if not verdict: total_verdict = False
        result.extend((x, target) for x in transformed)

    transition_map_tool.clean_up(result)
    # DO NOT:  "transition_map_tool.fill_gaps(result, [])!"
    # BECAUSE: This adds an action which is not in the original transition map!
    # EXAMPLE: A loop every action contains a '++p' and the loop ends on 
    #          'p == End'. Then an additional empty action [] would mean that 
    #          for some cases '++p' would not occur and the loop will be endless! 

    return total_verdict, result    

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
                for number_set in state.transitions().get_map().itervalues():
                    candidate_chunk_n = module.homogeneous_chunk_n_per_character(number_set)
                    if   candidate_chunk_n is None:    return None
                    elif chunk_n is None:              chunk_n = candidate_chunk_n
                    elif chunk_n != candidate_chunk_n: return None
            return chunk_n

    if   TrafoInfo == "utf8-state-split":  return _core(utf8_state_split, Thing)
    elif TrafoInfo == "utf16-state-split": return _core(utf16_state_split, Thing)
    else:                                  assert False


