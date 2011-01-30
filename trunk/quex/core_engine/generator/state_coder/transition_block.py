import sys
import quex.core_engine.generator.state_coder.transition as transition
from   quex.input.setup                                  import setup as Setup
from   quex.core_engine.interval_handling                import Interval
from   quex.core_engine.generator.languages.core         import label_db_unregister_usage

__DEBUG_CHECK_ACTIVE_F = False # Use this flag to double check that intervals are adjacent

class TriggerAction:
    def __init__(self, Code, DropOutF=False):
        assert type(DropOutF) == bool

        self.__code       = Code
        self.__drop_out_f = DropOutF

    def get_code(self):
        return self.__code

    def is_drop_out(self):
        return self.__drop_out_f

def __interpret(TriggerMap, CurrentStateIdx, DSM):
    result = [None] * len(TriggerMap)
    for i, entry in enumerate(TriggerMap):
        interval = entry[0]
        target   = entry[1]

        if   target == None:
            # Classical Drop-Out: no further state transition
            target = TriggerAction(transition.get_transition_to_drop_out(CurrentStateIdx, ReloadF=False),
                                   DropOutF=True)

        elif target == -1:
            # Limit Character Detected: Reload
            # NOTE: Reload != Drop Out!
            target = TriggerAction(transition.get_transition_to_drop_out(CurrentStateIdx, ReloadF=True),
                                   DropOutF=False)

        elif type(target) in [int, long]:
            # Classical State Transition: transit to state with given id
            target = TriggerAction(transition.get_transition_to_state(target, DSM),
                                   DropOutF=False)

        else:
            isinstance(target, TriggerAction)
            # No change necessary

        result[i] = (interval, target)
    return result

def do(TriggerMap, StateIdx, DSM):
    """Target == None           ---> Drop Out
       Target == -1             ---> Buffer Limit Code; Require Reload
                                     (this one is added by '__separate_buffer_limit_code_transition()'
       Target == Integer >= 0   ---> Transition to state with index 'Target'
       Target == string         ---> past code fragment 'Target' for given Interval
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

    # The 'buffer-limit-code' always needs to be identified separately.
    # This helps to generate the reload procedure a little more elegantly.
    __separate_buffer_limit_code_transition(TriggerMap)

    # Interpret the trigger map.
    # The actions related to intervals become code fragments (of type 'str')
    TriggerMap = __interpret(TriggerMap, StateIdx, DSM)

    if len(TriggerMap) > 1:
        # Check whether some things might be pre-checked before the big trigger map
        # starts working. This includes likelyhood and 'assembler-switch' implementations.
        # The TriggerMap has now been adapted to reflect that some transitions are
        # already implemented in the priorized_code
        code = __get_code(TriggerMap)
        # No transition to 'drop-out' shall actually occur in the map
        label_db_unregister_usage(transition.get_label_of_drop_out(StateIdx, ReloadF=False))
        return [ code ]

    else:
        # We can actually be sure, that the Buffer Limit Code is filtered
        # out, since this is the task of the regular expression parser.
        # In case of backward lexing in pseudo-ambiguous post conditions,
        # it makes absolutely sense that there is only one interval that
        # covers all characters (see the discussion there).
        assert TriggerMap[0][0].begin == -sys.maxint
        assert TriggerMap[0][0].end   == sys.maxint
        return ["    ", TriggerMap[0][1].get_code(), "\n"]

def __get_code(TriggerMap):
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
        for interval, target_state_index in TriggerMap[1:]:
            assert interval.begin == previous_interval.end, \
                   "Non-adjacent intervals in TriggerMap\n" + \
                   "TriggerMap = " + repr(TriggerMap)
            assert interval.end > interval.begin, \
                   "Interval of size zero in TriggerMap\n" + \
                   "TriggerMap = " + repr(TriggerMap)
            previous_interval = interval

    #________________________________________________________________________________

    if TriggerSetN == 1 :
        # (*) Only one interval 
        #     (all boundaring cases must have been dealt with already => case is clear)
        #     If the input falls into this interval the target trigger is identified!
        txt = [ __create_transition_code(TriggerMap[0]) ]
        
    else:    
        simple_txt = None # __try_very_simplest_case(TriggerMap)
        if simple_txt != None: 
            txt = ["    ", simple_txt]
        else:
            # two or more intervals => cut in the middle
            MiddleTrigger_Idx = int(TriggerSetN / 2)
            middle            = TriggerMap[MiddleTrigger_Idx]

            # input < 0 is impossible, since unicode codepoints start at 0!
            if middle[0].begin == 0: 
                code = [ __get_code(TriggerMap[MiddleTrigger_Idx:]) ]
            else: 
                code = __get_switch(TriggerMap)
                if code == None:
                    code = __get_bisection(MiddleTrigger_Idx, TriggerMap)
            txt = ["    "] + code
        

    # (*) indent by four spaces (nested blocks are correctly indented)
    #     delete the last newline, to prevent additional indentation
    result = "".join(txt)
    if result[-1] == "\n": result = result[:-1]
    result = result.replace("\n", "\n    ") + "\n"
    return result 

def __get_bisection(MiddleTrigger_Idx, TriggerMap):
    LanguageDB = Setup.language_db

    middle = TriggerMap[MiddleTrigger_Idx]
    lower  = TriggerMap[:MiddleTrigger_Idx]
    higher = TriggerMap[MiddleTrigger_Idx:]

    assert middle[0].begin >= 0, \
           "code generation: error cannot split intervals at negative code points."

    # Note, that an '<' does involve a subtraction. A '==' only a comparison.
    # The latter is safe to be faster (or at least equally fast) on any machine.
    if len(higher) == 1 and higher[0][1].is_drop_out():
        
        # If the size of one interval is 1, then replace the '<' by an '=='.
        if   len(lower)  == 1 and lower[0][0].size() == 1:
            comparison = LanguageDB["$if =="](repr(lower[0][0].begin))
        elif higher[0][0].size() == 1:
            comparison = LanguageDB["$if !="](repr(higher[0][0].begin))
        else:
            comparison = LanguageDB["$if <"](repr(higher[0][0].begin))

        # No 'else' case for what comes BEHIND middle
        if_block_txt   = __get_code(lower)
        else_block_txt = ""

    elif len(lower) == 1 and lower[0][1].is_drop_out():
        if   lower[0][0].size() == 1:
            comparison = LanguageDB["$if !="](repr(lower[0][0].begin))
        elif len(higher) == 1 and higher[0][0].size() == 1:
            comparison = LanguageDB["$if =="](repr(higher[0][0].begin))
        else:
            comparison = LanguageDB["$if >="](repr(lower[0][0].end))

        # No 'else' case for what comes BEFORE middle
        if_block_txt   = __get_code(higher)
        else_block_txt = ""

    else:
        # If the size of one interval is 1, then replace the '<' by an '=='.
        if   len(lower)  == 1 and lower[0][0].size() == 1:
            comparison = LanguageDB["$if =="](repr(lower[0][0].begin))
        elif len(higher) == 1 and higher[0][0].size() == 1:
            comparison = LanguageDB["$if !="](repr(higher[0][0].begin))
        else:
            comparison = LanguageDB["$if <"](repr(middle[0].begin))

        if_block_txt   = __get_code(lower)
        else_block_txt =   LanguageDB["$endif-else"] \
                         + __get_code(higher)

    return [ 
                comparison,
                if_block_txt,
                else_block_txt, 
                LanguageDB["$endif"]
           ]

def __create_transition_code(TriggerMapEntry):
    """Creates the transition code to a given target based on the information in
       the trigger map entry.
    """
    LanguageDB = Setup.language_db
    comment_function = LanguageDB["$comment"]
    comment          = lambda interval: comment_function(interval.get_utf8_string())

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
    txt =  "    " + target_state_index.get_code() 
    assert interval != None
    if interval != None:
        # if Setup.buffer_codec != "":
        txt += "    " + comment(interval) + "\n"
    else:
        txt += "\n"

    txt = txt[:-1].replace("\n", "\n    ") + "\n" # don't replace last '\n'
    return txt

def __get_switch(TriggerMap):
    LanguageDB = Setup.language_db

    non_drop_out_range_n   = 0
    character_n            = 0
    #white_space_target     = None
    for interval, target in TriggerMap:
        if target.is_drop_out(): continue
        non_drop_out_range_n += 1
        character_n          += interval.size()
    #    if interval.contains(ord(' ')):
    #        white_space_target = target

    if non_drop_out_range_n == 0: 
        return None

    if character_n == 1:
        return None

    case_density = character_n / non_drop_out_range_n 
    if case_density > 10: 
        return None

    #if white_space_target != None:
    #    result.append(LanguageDB["$if =="]("0x32"))
    #    result.append(white_space_target.get_code())
    #    result.append(LanguageDB["$endif"])

    case_code_list = []
    for interval, target in TriggerMap:
        if target.is_drop_out(): continue
        target_code = target.get_code()
        for i in range(interval.begin, interval.end):
            case_code_list.append(("0x%X" % i, target_code))

    return LanguageDB["$switch-block"]("input", case_code_list)

    #    occurence_db = {}
    #    for interval, target in TriggerMap:
    #        target_code = target.get_code()
    #        if not occurence_db.has_key(target_code): occurence_db[target_code] = 0
    #        occurence_db[target_code] += 1
    #
    #    best_target_code, occurence_n = max(occurence_db.iteritems(), key=itemgetter(1))
    #
    #    # If the remaining intervals are either 'small' then a 'switch' catcher can be implemented
    #    # 
    #    # (1) max. size of an interval --> if too big, do not implement a switch
    #    max_interval_size = max(TriggerMap, key=lambda x: x[0].size)
    #    #
    #    # (2) compute total amount of switch cases
    #    sum_switch_case_n = 0
    #    for interval, target in TriggerMap:
    #        if target.get_code() == best_target_code: continue
    #        sum_switch_case_n += interval.size()

def __separate_buffer_limit_code_transition(TriggerMap):
    """This function ensures, that the buffer limit code is separated 
       into a single value interval. Thus the transition map can 
       transit immediate to the reload procedure.
    """
    for i, entry in enumerate(TriggerMap):
        interval, target_index = entry

        if   target_index == -1:   
            assert interval.contains_only(Setup.buffer_limit_code) 
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

#__likely_char_list = [ ord(' ') ]
#def __get_priorized_code(trigger_map, info):
#    """-- Write code to trigger on likely characters.
#       -- Use that fact that assemblers can do 'switch-case indexing'
#          which is much faster than N comparisons.
#    """
#    LanguageDB = Setup.language_db
#
#    if len(trigger_map) <= 1: return ""
#
#    # -- Very likely characters
#    result  = []
#    first_f = True
#    for character_code in __likely_char_list:
#        first_f, txt = __extract_likely_character(trigger_map, character_code, first_f, info)
#        result.extend(txt)
#    if len(result) != 0: 
#        result.append(LanguageDB["$endif"])
#
#    # -- Adjacent tiny domains --> Assembler might use fast indexing.
#    #    Setup 'TinyNeighborTransitions' objects as targets so that transition
#    #    code generator can generate 'switch' statements.
#    tiny_neighbour_list = __filter_tiny_neighours(trigger_map)
#
#    if len(tiny_neighbour_list):
#        result.append("    ")
#        result.append(LanguageDB["$switch"]("input"))
#        for entry in tiny_neighbour_list:
#            result.extend(__tiny_neighbour_transitions(entry, info.state_index, info.dsm))
#        result.append("    ")
#        result.append(LanguageDB["$switchend"])
#        result.append("\n")
#
#    return "".join(result)
#
#def __tiny_neighbour_transitions(Info, CurrentStateIdx, DSM):
#    LanguageDB = Setup.language_db
#    assert Info.__class__.__name__ == "TinyNeighborTransitions"
#
#    result = []
#    for number, target in Info.get_mapping():
#        assert target.__class__.__name__ != "TinyNeighborTransitions"
#        result.append("       ")
#        result.append(LanguageDB["$case"]("0x%X" % number))
#        result.append(target.get_code())
#        result.append("\n")
#
#    return result
#    
#class TinyNeighborTransitions:
#    def __init__(self):
#        self.__list = []
#
#    def append(self, Interval, Target):
#        self.__list.append((Interval, Target))
#
#    def get_mapping(self):
#        mapping = []
#        for interval, target in self.__list:
#            for i in range(interval.begin, interval.end):
#                mapping.append((i, target))
#        return mapping
#
#def __filter_tiny_neighours(trigger_map):
#    result    = []
#
#    Tiny      = 20
#    MinExtend = 4
#    i = 0
#    L = len(trigger_map)
#    while i != L:
#        interval, target = trigger_map[i]
#
#        if interval.size() > Tiny: 
#            i += 1
#            continue
#
#        # Collect tiny neighbours
#        k                = i
#        candidate        = TinyNeighborTransitions()
#        candidate_extend = 0
#        while 1 + 1 == 2:
#            assert target.__class__ != TinyNeighborTransitions
#
#            candidate.append(interval, target)
#            candidate_extend += interval.size()
#
#            k += 1
#            if k == L: break 
#
#            interval, target = trigger_map[k]
#            if interval.size() > Tiny: break
#
#        if candidate_extend < MinExtend: 
#            i = k 
#            continue
#
#        else:
#            # User trigger_map[i], adapt it to reflect that from
#            # trigger_map[i][0].begin to trigger_map[k-1][0].end all becomes
#            # a 'tiny neighbour region'.
#            Begin = trigger_map[i][0].begin
#            End   = trigger_map[k-1][0].end
#            result.append(candidate)
#            del trigger_map[i:k] # Delete (k - i) elements
#            if i != 0: trigger_map[i][0].begin = trigger_map[i-1][0].end
#            else:      trigger_map[i][0].begin = - sys.maxint
#            L -= (k - i)
#            if i == L: break
#
#    return result
#
#def code_this(result, Letter, Target, first_f, info):
#    LanguageDB = Setup.language_db
#
#    if first_f: result += LanguageDB["$if =="]("0x%X" % Letter)    
#    else:       result += LanguageDB["$elseif =="]("0x%X" % Letter)
#    result.append("    ")
#    result.append(transition.do(Target, info.state_index, Interval(Letter), info.dsm))
#    result.append("\n")
#
#def __extract_likely_character(trigger_map, CharacterCode, first_f, info):
#    LanguageDB = Setup.language_db
#
#    i      = 0
#    L      = len(trigger_map)
#    result = []
#    while i != L:
#        interval, target = trigger_map[i]
#
#        if not interval.contains(CharacterCode): 
#            i += 1
#            continue
#
#        elif interval.size() != 1: 
#            # (0.a) size(Interval) != 1
#            #       => no need to adapt the trigger map.
#            # 
#            #     x[     ]   --> trigger map catches on 'x' even
#            #                    though, it has been catched on the
#            #                    priorized map --> no harm.
#            #     [  x   ]   --> same
#            #     [     ]x   --> same
#            code_this(result, CharacterCode, target, first_f, info)
#            first_f = False
#            i += 1
#            continue
#
#        elif L == 1:
#            # (0.b) If there's only one transition remaining (which
#            #       is of size 1, see above). Then no preference needs
#            #       to be given to the likely character.
#            break   # We are actually done!
#
#        else:
#            # (1) size(Interval) == 1
#            #     => replace trigger with adjacent transition
#            code_this(result, CharacterCode, target, first_f, info)
#            first_f = False
#        
#            del trigger_map[i]
#            # Intervals **must** be adjacent
#            assert trigger_map[i][0].begin == CharacterCode + 1
#            trigger_map[i][0].begin = CharacterCode
#            # Once the letter has been found, we are done
#            break
#
#    return first_f, result
