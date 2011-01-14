import sys
import quex.core_engine.generator.state_coder.transition as transition
from   quex.input.setup                                  import setup as Setup
from   quex.core_engine.interval_handling                import Interval

__DEBUG_CHECK_ACTIVE_F = False # Use this flag to double check that intervals are adjacent

class __info:
    def __init__(self, StateIdx, IsInitStateF, DSM):
        assert DSM == None or DSM.__class__.__name__ == "StateMachineDecorator"

        self.state_index     = StateIdx
        self.is_init_state_f = IsInitStateF
        self.dsm             = DSM

def do(TriggerMap, StateIdx, DSM):
    """Target == None  ---> Drop Out
       Target == -1    ---> Buffer Limit Code; Require Reload
                            (this one is added by '_separate_buffer_limit_code_transition()'
    """
    assert type(TriggerMap) == list
    assert DSM == None or DSM.__class__.__name__ == "StateMachineDecorator"
    # If a state has no transitions, no new input needs to be eaten => no reload.
    #
    # NOTE: The only case where the buffer reload is not required are empty states,
    #       AND states during backward input position detection!
    #       Empty states do not exist any longer, the backward input position is
    #       essential though for pseudo ambiguous post contexts.
    assert TriggerMap != [] # states with empty trigger maps are 'dead end states'. those
    #                       # are not to be coded at this place.
    if DSM == None: InitStateF = False
    else:           InitStateF = (StateIdx == DSM.sm().init_state_index)

    info = __info(StateIdx=StateIdx, IsInitStateF=InitStateF, DSM=DSM)

    # The 'buffer-limit-code' always needs to be identified separately.
    # This helps to generate the reload procedure a little more elegantly.
    _separate_buffer_limit_code_transition(TriggerMap)

    if len(TriggerMap) > 1:
        # Check whether some things might be pre-checked before the big trigger map
        # starts working. This includes likelyhood and 'assembler-switch' implementations.
        priorized_code = "" # __get_priorized_code(TriggerMap, info)
        # The TriggerMap has now been adapted to reflect that some transitions are
        # already implemented in the priorized_code
        block_code     = __get_code(TriggerMap, info)
        return [priorized_code, "\n", 
                block_code, "\n"]

    else:
        # We can actually be sure, that the Buffer Limit Code is filtered
        # out, since this is the task of the regular expression parser.
        # In case of backward lexing in pseudo-ambiguous post conditions,
        # it makes absolutely sense that there is only one interval that
        # covers all characters (see the discussion there).
        assert TriggerMap[0][0].begin == -sys.maxint
        assert TriggerMap[0][0].end   == sys.maxint
        return ["    ", transition.do(TriggerMap[0][1], StateIdx, TriggerMap[0][0], DSM), "\n"]

__likely_char_list = [ ord(' ') ]
def __get_priorized_code(trigger_map, info):
    """-- Write code to trigger on likely characters.
       -- Use that fact that assemblers can do 'switch-case indexing'
          which is much faster than N comparisons.
    """
    LanguageDB = Setup.language_db

    if len(trigger_map) <= 1: return ""

    # -- Very likely characters
    result  = []
    first_f = True
    for character_code in __likely_char_list:
        first_f, txt = __extract_likely_character(trigger_map, character_code, first_f, info)
        result.extend(txt)
    if len(result) != 0: 
        result.append(LanguageDB["$endif"])

    # -- Adjacent tiny domains --> Assembler might use fast indexing.
    #    Setup 'TinyNeighborTransitions' objects as targets so that transition
    #    code generator can generate 'switch' statements.
    tiny_neighbour_list = __filter_tiny_neighours(trigger_map)

    if len(tiny_neighbour_list):
        result.append("    ")
        result.append(LanguageDB["$switch"]("input"))
        for entry in tiny_neighbour_list:
            result.extend(__tiny_neighbour_transitions(entry, info.state_index, info.dsm))
        result.append("    ")
        result.append(LanguageDB["$switchend"])
        result.append("\n")

    return "".join(result)

def __tiny_neighbour_transitions(Info, CurrentStateIdx, DSM):
    LanguageDB = Setup.language_db
    assert Info.__class__.__name__ == "TinyNeighborTransitions"

    result = []
    for number, target in Info.get_mapping():
        assert target.__class__.__name__ != "TinyNeighborTransitions"
        result.append("       ")
        result.append(LanguageDB["$case"]("0x%X" % number))
        result.append(transition.do(target, CurrentStateIdx, Interval(number), DSM))
        result.append("\n")

    return result
    
class TinyNeighborTransitions:
    def __init__(self):
        self.__list = []

    def append(self, Interval, Target):
        self.__list.append((Interval, Target))

    def get_mapping(self):
        mapping = []
        for interval, target in self.__list:
            for i in range(interval.begin, interval.end):
                mapping.append((i, target))
        return mapping

def __filter_tiny_neighours(trigger_map):
    result    = []

    Tiny      = 20
    MinExtend = 4
    i = 0
    L = len(trigger_map)
    while i != L:
        interval, target = trigger_map[i]

        if interval.size() > Tiny: 
            i += 1
            continue

        # Collect tiny neighbours
        k                = i
        candidate        = TinyNeighborTransitions()
        candidate_extend = 0
        while 1 + 1 == 2:
            assert target.__class__ != TinyNeighborTransitions

            candidate.append(interval, target)
            candidate_extend += interval.size()

            k += 1
            if k == L: break 

            interval, target = trigger_map[k]
            if interval.size() > Tiny: break

        if candidate_extend < MinExtend: 
            i = k 
            continue

        else:
            # User trigger_map[i], adapt it to reflect that from
            # trigger_map[i][0].begin to trigger_map[k-1][0].end all becomes
            # a 'tiny neighbour region'.
            Begin = trigger_map[i][0].begin
            End   = trigger_map[k-1][0].end
            result.append(candidate)
            del trigger_map[i:k] # Delete (k - i) elements
            if i != 0: trigger_map[i][0].begin = trigger_map[i-1][0].end
            else:      trigger_map[i][0].begin = - sys.maxint
            L -= (k - i)
            if i == L: break

    return result

def code_this(result, Letter, Target, first_f, info):
    LanguageDB = Setup.language_db

    if first_f: result += LanguageDB["$if =="]("0x%X" % Letter)    
    else:       result += LanguageDB["$elseif =="]("0x%X" % Letter)
    result.append("    ")
    result.append(transition.do(Target, info.state_index, Interval(Letter), info.dsm))
    result.append("\n")

def __extract_likely_character(trigger_map, CharacterCode, first_f, info):
    LanguageDB = Setup.language_db

    i      = 0
    L      = len(trigger_map)
    result = []
    while i != L:
        interval, target = trigger_map[i]

        if not interval.contains(CharacterCode): 
            i += 1
            continue

        elif interval.size() != 1: 
            # (0.a) size(Interval) != 1
            #       => no need to adapt the trigger map.
            # 
            #     x[     ]   --> trigger map catches on 'x' even
            #                    though, it has been catched on the
            #                    priorized map --> no harm.
            #     [  x   ]   --> same
            #     [     ]x   --> same
            code_this(result, CharacterCode, target, first_f, info)
            first_f = False
            i += 1
            continue

        elif L == 1:
            # (0.b) If there's only one transition remaining (which
            #       is of size 1, see above). Then no preference needs
            #       to be given to the likely character.
            break   # We are actually done!

        else:
            # (1) size(Interval) == 1
            #     => replace trigger with adjacent transition
            code_this(result, CharacterCode, target, first_f, info)
            first_f = False
        
            del trigger_map[i]
            # Intervals **must** be adjacent
            assert trigger_map[i][0].begin == CharacterCode + 1
            trigger_map[i][0].begin = CharacterCode
            # Once the letter has been found, we are done
            break

    return first_f, result

def __get_code(TriggerMap, info):
    """Creates code for state transitions from this state. This function is very
       similar to the function creating code for a 'NumberSet' condition 
       (see 'interval_handling').
    
       Writes code that does a mapping according to 'binary search' by
       means of if-else-blocks.
    """
    TriggerSetN = len(TriggerMap)

    if TriggerSetN > 1 and __DEBUG_CHECK_ACTIVE_F:
        # -- check that the trigger map consist of sorted adjacent intervals 
        #    This assumption is critical because it is assumed that for any isolated
        #    interval the bordering intervals have bracketed the remaining cases!
        previous_interval = TriggerMap[0][0] 
        for trigger_interval, target_state_index in TriggerMap[1:]:
            assert trigger_interval.begin == previous_interval.end, \
                   "non-adjacent intervals in TriggerMap\n" + \
                   "TriggerMap = " + repr(TriggerMap)
            assert trigger_interval.end > previous_interval.begin, \
                   "unsorted intervals in TriggerMap\n" + \
                   "TriggerMap = " + repr(TriggerMap)
            previous_interval = deepcopy(trigger_interval)

    #________________________________________________________________________________

    if TriggerSetN == 1 :
        # (*) Only one interval 
        #     (all boundaring cases must have been dealt with already => case is clear)
        #     If the input falls into this interval the target trigger is identified!
        txt = [ __create_transition_code(TriggerMap[0], info) ]
        
    else:    
        simple_txt = __try_very_simplest_case(TriggerMap, info)
        if simple_txt != None: 
            txt = ["    ", simple_txt]
        else:
            # two or more intervals => cut in the middle
            MiddleTrigger_Idx = int(TriggerSetN / 2)
            middle = TriggerMap[MiddleTrigger_Idx]

            # input < 0 is impossible, since unicode codepoints start at 0!
            if middle[0].begin == 0: code = [ __get_code(TriggerMap[MiddleTrigger_Idx:], info) ]
            elif TriggerSetN == 2:   code = __bracket_two_intervals(TriggerMap, info) 
            elif TriggerSetN == 3:   code = __bracket_three_intervals(TriggerMap, info)
            else:                    code = __bracket_normally(MiddleTrigger_Idx, TriggerMap, info)
            txt = ["    "] + code
        

    # (*) indent by four spaces (nested blocks are correctly indented)
    #     delete the last newline, to prevent additional indentation
    result = "".join(txt)
    if result[-1] == "\n": result = result[:-1]
    result = result.replace("\n", "\n    ") + "\n"
    return result 

def __create_transition_code(TriggerMapEntry, info):
    """Creates the transition code to a given target based on the information in
       the trigger map entry.
    """
    LanguageDB = Setup.language_db

    interval           = TriggerMapEntry[0]
    target_state_index = TriggerMapEntry[1]       
    #  target state != None, then the machine is still eating
    #                        => transition to subsequent state.
    #
    #  target state == None, drop into a terminal state (defined by origins).
    #
    #  for details about $transition, see the __transition() function of the
    #  respective language module.
    #
    txt =  "    " + transition.do(target_state_index, info.state_index, interval, info.dsm)
    if interval != None:
        # if Setup.buffer_codec != "":
        txt += "    " + LanguageDB["$comment"](interval.get_utf8_string()) + "\n"
    else:
        txt += "\n"

    txt = txt[:-1].replace("\n", "\n    ") + "\n" # don't replace last '\n'
    return txt

def __try_very_simplest_case(TriggerMap, info):
    """Assume the following setup:

           if( input == Char1 ) goto X;
           if( input == Char2 ) goto X;
               ...
           if( input == CharN ) goto X;

       If the input is equally distributed over the characters 1 to N then the
       average number of comparisons for N = 3 will be 2,333. For N = 4, the 
       everage number of comparisons will be 2,75. Binary bracketing requires
       ld(N), so for N = 4 the number of comparisons is 2. Thus until N = 3
       it is advantegous to compare step by step. Also, for N = 1 a simple 
       comparison is, most likely, more efficient that an 'or' operation over
       a list of length '1'. 
       
       This function is trying to identify the case where there are only two or
       three characters that trigger to the same target state. 
       
       RETURNS:  'None' if the very simple implementation does not make sense.
                 A string if it could be implemented that way
    """
    LanguageDB = Setup.language_db

    character_list            = []
    common_target_state_index = None # Something Impossible for a state
    for trigger in TriggerMap:
        interval           = trigger[0]
        target_state_index = trigger[1]

        if target_state_index == None: continue

        # All must have the same target state
        if common_target_state_index == None:
            common_target_state_index = target_state_index
        # Make sure, you call the target_state_index's comparison operator.
        # (The index might actually be a real object, e.g. an IndentationCounter)
        elif target_state_index != common_target_state_index: 
            return None

        # Because of memory reasons, it is not wise to try to extend sys.maxint number
        # of characters. Since, we do not allow for more than three characters, let's
        # do a little sanity pre-check:
        if interval.size() > 3: return None
        character_list.extend(range(interval.begin, interval.end))

        # More than three characters does not make sense
        if len(character_list) > 3: return None

    if len(character_list) < 2: return None
    assert common_target_state_index != -1

    txt0 = LanguageDB["$if in-set"](character_list)    
    return "".join([
                    txt0,
                    # TriggerInfo = [None, TargetStateIndex] because the interval does not matter.
                    __create_transition_code([None, common_target_state_index], info),
                    LanguageDB["$endif-else"],
                    __create_transition_code([None, None], info),
                    LanguageDB["$end-else"]
                   ])

def __bracket_two_intervals(TriggerMap, info):
    assert len(TriggerMap) == 2
    LanguageDB = Setup.language_db

    first  = TriggerMap[0]
    second = TriggerMap[1]

    # If the first interval causes a 'drop out' then make it the second.
    ## If the second interval is a 'drop out' the 'goto drop out' can be spared,
    ## since it lands there anyway.
    ## if second[0] < 0: # target state index < 0 ==> drop out
    ##    tmp = first; first = second; second = tmp

    # find interval of size '1'
    first_interval  = first[0]
    second_interval = second[0]

    # We only need one comparison at the border between the two intervals
    if   first_interval.size() == 1:  txt0 = LanguageDB["$if =="](repr(first_interval.begin))
    elif second_interval.size() == 1: txt0 = LanguageDB["$if !="](repr(second_interval.begin))
    else:                             txt0 = LanguageDB["$if <"](repr(second_interval.begin))

    return [
                txt0,
                __create_transition_code(first, info),
                LanguageDB["$endif-else"],
                __create_transition_code(second, info),
                LanguageDB["$end-else"]
           ]

def __bracket_three_intervals(TriggerMap, info):
    assert len(TriggerMap) == 3
    LanguageDB = Setup.language_db

    # does one interval have the size '1'?
    size_one_map = [False, False, False]   # size_on_map[i] == True if interval 'i' has size '1'
    for i in range(len(TriggerMap)):
        interval = TriggerMap[i][0]
        if interval.size() == 1: size_one_map[i] = True

    target_state_0 = TriggerMap[0][1]
    target_state_2 = TriggerMap[2][1]
    if target_state_0 == target_state_2:
        if TriggerMap[1][0].size() == 1:
            # (1) Special Trick I only holds for one single case:
            #     -- the interval in the middle has size 1
            #     -- the outer two intervals trigger to the same target state
            #     if inner character is matched: goto its target
            #     else:                          goto alternative target
            txt0  = LanguageDB["$if =="](repr(TriggerMap[1][0].begin))
        else:
            # (2) Special Trick II only holds for:
            #     -- the outer two intervals trigger to the same target state
            #     if character in inner interval: goto its target
            #     else:                           goto alternative target
            txt0  = LanguageDB["$if in-interval"](TriggerMap[1][0])

        return [
                    txt0,
                    __create_transition_code(TriggerMap[1], info),
                    LanguageDB["$endif-else"],
                    # TODO: Add somehow a mechanism to report that here the 
                    #       intervals 0 **and** 1 are triggered
                    #       (only for the comments in the generated code)
                    __create_transition_code(TriggerMap[0], info),
                    LanguageDB["$end-else"]
               ]

    # (*) Non special case --> bracket normally
    return __bracket_normally(1, TriggerMap, info)

def __bracket_normally(MiddleTrigger_Idx, TriggerMap, info):
    LanguageDB = Setup.language_db

    middle = TriggerMap[MiddleTrigger_Idx]
    lower  = TriggerMap[:MiddleTrigger_Idx]
    higher = TriggerMap[MiddleTrigger_Idx:]

    assert middle[0].begin >= 0, \
           "code generation: error cannot split intervals at negative code points."

    # If the size of one interval is 1, then replace the '<' by an '=='.
    # Note, that an '<' does involve a subtraction. A '==' only a comparison.
    # The latter is safe to be faster (or at least equally fast) on any machine.
    if   len(lower)  == 1 and lower[0][0].size() == 1:
        comparison = LanguageDB["$if =="](repr(lower[0][0].begin))
    elif len(higher) == 1 and higher[0][0].size() == 1:
        comparison = LanguageDB["$if !="](repr(higher[0][0].begin))
    else:
        comparison = LanguageDB["$if <"](repr(middle[0].begin))

    return [ 
                comparison,
                __get_code(lower, info),
                LanguageDB["$endif-else"],
                __get_code(higher, info),
                LanguageDB["$end-else"]
           ]

def _separate_buffer_limit_code_transition(TriggerMap):
    """This function ensures, that the buffer limit code is separated 
       into a single value interval. Thus the transition map can 
       transit immediate to the reload procedure.
    """
    for i, entry in enumerate(TriggerMap):
        interval, target_index = entry

        if   target_index == -1:   
            assert interval.contains(Setup.buffer_limit_code) 
            assert interval.size() == 1
            # Transition 'buffer limit code --> -1' has been setup already
            return

        elif target_index != None: 
            continue

        elif not interval.contains(Setup.buffer_limit_code): 
            continue

        # Found the interval that contains the buffer limit code.
        # If the interval's size is alread 1, then there is nothing to be done
        if interval.size() == 1: return

        before_begin = interval.begin
        before_end   = Setup.buffer_limit_code 
        after_begin  = Setup.buffer_limit_code + 1
        after_end    = interval.end

        # Replace Entry with (max.) three intervals: before, buffer limit code, after
        del TriggerMap[i]

        if after_end > after_begin:
            TriggerMap.insert(i, (Interval(after_begin, after_end), None))

        # "Target == - 1" ==> Buffer Limit Code
        TriggerMap.insert(i, (Interval(Setup.buffer_limit_code, Setup.buffer_limit_code + 1), -1))

        if before_end > before_begin and before_end > 0:
            TriggerMap.insert(i, (Interval(before_begin, before_end), None))

        return

    # It is conceivable, that the transition does not contain a 'None' transition
    # on buffer limit code. This happens for example, during backward detection
    # where it is safe to assume that the buffer limit code may not occur.
    return


