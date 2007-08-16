# The 'grammar' of quex's regular expressions:
#
#  complete expression: expression
#                       expression / expression                 = post conditioned expression
#                       expression / expression /               = pre conditioned expression
#                       expression / expression / expression    = pre and post conditioned expression
# 
#  expression: term
#              term | expression
#  
#  term:  primary
#         primary term
#  
#  primary:  " non_double_quote *  "              = character string
#            [ non_rect_bracket_close ]           = set of characters
#            { identifier }                       = pattern replacement
#            ( expression )
#            non_control_character+               = lonely characters
#            primary repetition_cmd
#  
#  non_double_quote: 'anything but an unbackslashed double quote, i.e. \" is ok, 
#                     but " is not.'      
#  non_rect_bracket_close: 'anything but an unbackslashed rectangular bracket, i.e.
#                           \] is ok, but ] is not.'               
#  non_control_character: 'anything but (, ", [, or {'
#       
#  repetition_cmd: 'a repetition command such as +, *, {2}, {,2}, {2,5}'        
#
#########################################################################################       
import sys
import StringIO


from quex.frs_py.string_handling import trim
from quex.core_engine.interval_handling import *
from quex.core_engine.state_machine.core import StateMachine
import quex.core_engine.utf8                                  as utf8
import quex.core_engine.regular_expression.character_set      as map_utf8_set
import quex.core_engine.regular_expression.character_string   as map_utf8_string
import quex.core_engine.state_machine.sequentialize           as sequentialize
import quex.core_engine.state_machine.parallelize             as parallelize
import quex.core_engine.state_machine.repeat                  as repeat
import quex.core_engine.state_machine.setup_post_condition    as setup_post_condition
import quex.core_engine.state_machine.setup_pre_condition     as setup_pre_condition
import quex.core_engine.state_machine.setup_border_conditions as setup_border_conditions


CONTROL_CHARACTERS = [ "+", "*", "\"", "/", "(", ")", "{", "}", "|", "[", "]", "$"] 

__debug_recursion_depth = -1
__debug_output_enabled_f = False 

class something:
    pass

__SETUP = something()

def __debug_print(msg, msg2="", msg3=""):
    global __debug_recursion_depth
    if type(msg2) != str: msg2 = repr(msg2)
    if type(msg3) != str: msg3 = repr(msg3)
    txt = "##" + "  " * __debug_recursion_depth + msg + " " + msg2 + " " + msg3
    txt = txt.replace("\n", "\n    " + "  " * __debug_recursion_depth)
    if __debug_output_enabled_f: print txt
    
def __debug_exit(result, stream):
    global __debug_recursion_depth
    __debug_recursion_depth -= 1

    if __debug_output_enabled_f: 
        pos = stream.tell()
        txt = stream.read()
        stream.seek(pos)    
        __debug_print("##exit: ", txt)
        
    return result

def __debug_entry(function_name, stream):
    global __debug_recursion_depth
    __debug_recursion_depth += 1

    if __debug_output_enabled_f: 
        pos = stream.tell()
        txt = stream.read()
        stream.seek(pos)    
        __debug_print("##entry: %s, remainder = " % function_name, txt)

def __check_for_EOF_or_FAIL_pattern(stream, InitialPosition, EndOfFile_Code):
    # -- is it the <<EOF>> rule?
    if stream.read(len("<<EOF>>")) == "<<EOF>>":  
        return create_EOF_detecting_state_machine(EndOfFile_Code)
    stream.seek(InitialPosition)
    # -- is it the <<FAIL>> rule?
    if stream.read(len("<<FAIL>>")) == "<<FAIL>>":  
        raise "error: '<<FAIL>>' regular expression should not reach regular expression parser"
        # return "<<FAIL>>"

    stream.seek(InitialPosition)
    return None

def do(UTF8_String_or_Stream, PatternDict=None, BeginOfFile_Code=0, EndOfFile_Code=0, 
       DOS_CarriageReturnNewlineF=False):
    global __SETUP

    if type(UTF8_String_or_Stream) == str: stream = StringIO.StringIO(UTF8_String_or_Stream)
    else:                                  stream = UTF8_String_or_Stream    

    __SETUP.EndOfFile_Code   = EndOfFile_Code
    __SETUP.BeginOfFile_Code = BeginOfFile_Code
    __SETUP.BufferLimit_Code = 0x0

    if PatternDict == None: PatternDict = {}

    initial_position = stream.tell()

    # -- special rules EOF, FAIL
    result = __check_for_EOF_or_FAIL_pattern(stream, initial_position, EndOfFile_Code) 
    if result != None: return result

    # -- check for the begin of line condition (BOL)
    if stream.read(1) == '^': begin_of_line_f = True
    else:                     stream.seek(-1, 1); begin_of_line_f = False
    
    # -- MAIN: transform the pattern into a state machine
    sm = snap_conditional_expression(stream, PatternDict)
    if sm == None: 
        stream.seek(initial_position)
        return None
    
    # -- check for end of line condition (EOL)
    if stream.read(1) == '$': end_of_line_f = True
    else:                     stream.seek(-1, 1); end_of_line_f = False
    ## print "##end_of_line_f = ", end_of_line_f

    # -- set begin of line/end of line conditions
    setup_border_conditions.do(sm, begin_of_line_f, end_of_line_f,
                               BeginOfFile_Code, EndOfFile_Code, 
                               DOS_CarriageReturnNewlineF)

    # -- check that pre- and post-conditioning did not mess up the origins
    #if sm.verify_unique_origin() == False:
    #   raise "state machine does not have a unique origin:\n" + repr(sm) 

    if begin_of_line_f or end_of_line_f: sm = __beautify(sm)
    return sm

def snap_conditional_expression(stream, PatternDict):
    """conditional expression: expression
                               expression / expression                 = post conditioned expression
                               expression / expression /               = pre conditioned expression
                               expression / expression / expression    = pre and post conditioned expression
       TODO: <- ($8592) for pre-conditions
             -> ($8594) for post-conditions

    """                     
    __debug_entry("conditional expression", stream)    

    # -- expression
    pattern_0 = snap_expression(stream, PatternDict) 
    if pattern_0 == None: return __debug_exit(None, stream)
    
    # -- '/'
    if stream.read(1) != '/': 
        # (1) expression without pre and post condition
        stream.seek(-1, 1)
        # pattern_0 is already beautified by 'snap_expression()'
        result = __construct(pattern_0)
        return __debug_exit(result, stream)
        
    # -- expression
    pattern_1 = snap_expression(stream, PatternDict) 
    if pattern_1 == None: return __debug_exit(pattern_0, stream)
    
    # -- '/'
    if stream.read(1) != '/': 
        # (2) expression with only a post condition
        stream.seek(-1, 1)
        #     NOTE: setup_post_condition() marks state origins!
        result = __construct(pattern_0, post_condition=pattern_1)
        return __debug_exit(result, stream)

    # -- expression
    pattern_2 = snap_expression(stream, PatternDict) 
    if pattern_2 == None: 
        # (3) expression with only a pre condition
        #     NOTE: setup_pre_condition() marks the state origins!
        result = __construct(pattern_1, pre_condition=pattern_0)
        return __debug_exit(result, stream)

    # (4) expression with post and pre-condition
    result = __construct(pattern_1, pre_condition=pattern_0, post_condition=pattern_2)
    return __debug_exit(result, stream)

def snap_expression(stream, PatternDict):
    """expression:  term
                    term | expression
    """              
    __debug_entry("expression", stream)    
    # -- term
    result = snap_term(stream, PatternDict) 
    if result == None: return __debug_exit(None, stream)

    # -- optional '|'
    if stream.read(1) != '|': 
        stream.seek(-1, 1)
        return __debug_exit(result, stream)
    
    position_1 = stream.tell()
    __debug_print("'|' (in expression)")

    # -- expression
    result_2 = snap_expression(stream, PatternDict) 
    __debug_print("expression(in expression):",  result_2)
    if result_2 == None:
        stream.seek(position_1) 
        return __debug_exit(result, stream)

    result = parallelize.do([result, result_2])    
    return __debug_exit(__beautify(result), stream)
        
def snap_term(stream, PatternDict):
    """term:  primary
              primary term 
    """
    __debug_entry("term", stream)    

    # -- primary
    result = snap_primary(stream, PatternDict) 
    __debug_print("##primary(in term):", result)
    if result == None: return __debug_exit(None, stream)
    position_1 = stream.tell()

    # -- optional 'term' 
    result_2 = snap_term(stream, PatternDict) 
    __debug_print("##term(in term):",  result_2)
    if result_2 == None: 
        stream.seek(position_1)
        return __debug_exit(result, stream)
    
    result = sequentialize.do([result, result_2])    
    return __debug_exit(__beautify(result), stream)
        
def snap_primary(stream, PatternDict):
    """primary:  " non_double_quote *  "              = character string
                 [ non_rect_bracket_close ]           = set of characters
                 { identifier }                       = pattern replacement
                 ( expression )
                 non_control_character+               = lonely characters
                 primary repetition_cmd
    """
    __debug_entry("primary", stream)    
    x = stream.read(1)
    if x == "": return __debug_exit(None, stream)

    def eat_this(supposed_first_char, the_string):
        if len(the_string) < 1 or the_string[0] != supposed_first_char:
            raise "missing '%s'" % supposed_first_char + "\n" + \
                  "remaining string = '%s'" % the_string 
        return the_string[1:]    

    # -- 'primary' primary
    if   x == "\"": result = snap_non_double_quote(stream)
    elif x == "[":  result = snap_non_rect_bracket_close(stream)
    elif x == "{":  result = snap_replacement(stream, PatternDict)
    elif x == ".":  result = create_ALL_BUT_NEWLINE_state_machine()
    elif x == "(": 
        result = snap_expression(stream, PatternDict)
        if stream.read(1) != ")": 
            stream.seek(-1, 1)
            raise "error: missing closing ')' after expression. found '%s'" % stream.read()

    elif x not in CONTROL_CHARACTERS:
        # NOTE: The '\' is not inside the control characters---for a reason.
        #       It is used to define for example character codes using '\x' etc.
        stream.seek(-1, 1)
        result = snap_non_control_characters(stream)

    else:
        # NOTE: This includes the '$' sign which means 'end of line'
        #       because the '$' sign is in CONTROL_CHARACTERS, but is not checked
        #       against. Thus, it it good to leave here on '$' because the
        #       '$' sign is handled on the very top level.
        # this is not a valid primary
        stream.seek(-1, 1)
        return __debug_exit(None, stream)

    # -- optional repetition command? 
    result_repeated = __snap_repetition_range(result, stream) 
    if result_repeated != None: 
        return __debug_exit(__beautify(result_repeated), stream)
    else:                       
        return __debug_exit(__beautify(result), stream)
    
def snap_non_double_quote(stream):
    """Cuts an string that is bracketed by quotes from the start of
      the 'utf8_string. Builds a state machine out of the string that 
      was cut off."""
    character_string = __snap_until(stream, "\"")  

    # transform string into state machine        
    result = map_utf8_string.do(character_string)        

    return result

def snap_non_rect_bracket_close(stream):
    """Cuts a character range bracketed by '[' ']' from the utf8_string and 
       returns the resulting state machine.
    """
    character_string = __snap_until(stream, "]")  

    # transform string into state machine        
    result = map_utf8_set.do(character_string)   

    return result

def snap_non_control_characters(stream):
    """Snaps any 'non_control_character' using UTF8 encoding from the given string. Note, that 
       in UTF8 a character may consist of more than one byte. Creates a state machine 
       than contains solely a trigger from this character to a acceptance state.
    """
    __debug_entry("else characters", stream)

    result = StateMachine()
    #
    state_index = result.init_state_index
    while 1 + 1 == 2: 
        char_code = utf8.map_utf8_to_unicode(stream)
        #
        if char_code == 0xFF: break
        # ask < 0xFF to protect against overflow in char() function
        if char_code < 0xFF and \
           chr(char_code) in CONTROL_CHARACTERS: stream.seek(-1, 1); break 

        # any backslashed character is the character itself, it cannot not be
        # used after that as a command.
        if char_code == ord("\\"):
            char_code = utf8.map_utf8_to_unicode(stream)

        # add new transition from current state to a new state triggering
        # on the given character.
        state_index = result.add_transition(state_index, char_code)

    # last character in the chain triggers an 'acceptance state'
    result.set_acceptance(state_index)
        
    return __debug_exit(result, stream)
    
def snap_replacement(stream, PatternDict):
    """Snaps a predefined pattern from the input string and returns the resulting
       state machine.
    """ 
    pattern_name = __snap_until(stream, "}")  
    pattern_name = trim(pattern_name)    
    if PatternDict.has_key(pattern_name) == False:
        raise "Pattern of name '%s' was not defined" % pattern_name
        
    # transform string into state machine        
    # NOTE: The result may again contain a pattern identifier, etc.     
    regular_expression = StringIO.StringIO(PatternDict[pattern_name])
    result = snap_expression(regular_expression, PatternDict) 
    pos = stream.tell()
    stream.seek(pos)

    return __beautify(result)

def __snap_repetition_range(the_state_machine, stream):    
    """Snaps a string that represents a repetition range. The following 
       syntaxes are supported:
           '?'      one or none repetition
           '+'      one or arbitrary repetition
           '*'      arbitrary repetition (even zero)
           '{n}'    exactly 'n' repetitions
           '{m,n}'  from 'm' to 'n' repetitions
           '{n,}'   arbitrary, but at least 'n' repetitions
    """       
    position_0 = stream.tell()
    x = stream.read(1)
    if   x == "+": result = repeat.do(the_state_machine, 1)
    elif x == "*": result = repeat.do(the_state_machine)
    elif x == "?": result = repeat.do(the_state_machine, 0, 1)
    elif x == "{":
        repetition_range_str = __snap_until(stream, "}")
        if len(repetition_range_str) and not repetition_range_str[0].isdigit():
            # no repetition range, so everything remains as it is
            stream.seek(position_0)
            return the_state_machine
            
        try:
            if repetition_range_str.find(",") == -1:
                # no ',' thus "match exactly a certain number": 
                # e.g. {4} = match exactly four repetitions
                number = int(repetition_range_str)
                result = repeat.do(the_state_machine, number, number)
                return result
            # a range of numbers is given       
            fields = repetition_range_str.split(",")
            fields = map(trim, fields)

            number_1 = int(trim(fields[0]))
            if fields[1] == "": number_2 = -1                    # e.g. {2,}
            else:               number_2 = int(trim(fields[1]))  # e.g. {2,5}  
            # produce repeated state machine 
            result = repeat.do(the_state_machine, number_1, number_2)
            return result
        except:
            raise "error while parsing repetition range expression '%s'" % repetition_range_str 
    else:
        # no repetition range, so everything remains as it is
        stream.seek(position_0)
        return the_state_machine
    
    return result

def __snap_until(stream, ClosingDelimiter, OpeningDelimiter=None):
     """Cuts the first letters of the utf8_string until an un-backslashed
        Delimiter occurs.
     """
     cut_string = ""  
     backslash_f = False
     open_bracket_n = 1 
     while 1 + 1 == 2:
        letter = stream.read(1)
        if letter == "": break

        cut_string += letter    

        if letter == "\\": 
            backslash_f = not backslash_f       
            continue
            
        if letter == ClosingDelimiter and not backslash_f: 
            if open_bracket_n == 1: cut_string = cut_string[:-1]; break
            open_bracket_n -= 1
        elif letter == OpeningDelimiter and not backslash_f: 
            # NOTE: if OpeningDelimiter == None, then this can never be the case!
            open_bracket_n += 1

        # if a backslash would have appeared, we would have 'continue'd (see above)
        backslash_f = False    
     else:
         raise "unable to find closing delimiter '%s'"  % ClosingDelimiter
   
     return cut_string

def __set_end_of_line_post_condition(sm, EndOfFileCode=0):
    """Appends a post condition to the state machine to handle the end of line
       statement. This consists in translating 'EndOfLine' into a state machine
       with 'Newline' or 'EndOfFile'. Thus, when one of both follows the current
       character is at the end of a line.

       If you want to use a different code for end of file, specify it via the
       first argument 'EndOfFile'.

       NOTE: This is fundamentally different from beginning of line (BOL). BOL
             can be achieved by letting the state machine raise the corresponding
             flag. End of line post conditions rely on external algorithms for
             mounting a post-condition.
    """
    post_condition_sm = StateMachine()
    post_condition_sm.add_transition(post_condition_sm.init_state_index, ord('\n'), AcceptanceF=True)
    post_condition_sm.add_transition(post_condition_sm.init_state_index, EndOfFileCode, AcceptanceF=True)

    result = setup_post_condition.do(sm, post_condition_sm)

    return result

def __beautify(the_state_machine):
    the_state_machine.finalize()
    result = the_state_machine.get_DFA()
    result = result.get_hopcroft_optimization()    
    return result

def create_EOF_detecting_state_machine(EndOfFile_Code):
    result = StateMachine()
    result.add_transition(result.init_state_index, EndOfFile_Code, AcceptanceF=True) 
    result.mark_state_origins()
    return result

def create_ALL_BUT_NEWLINE_state_machine():
    global __SETUP
    result = StateMachine()
    trigger_set = NumberSet([Interval(ord("\n")), 
                             Interval(__SETUP.BufferLimit_Code),
                             Interval(__SETUP.EndOfFile_Code),
                             Interval(__SETUP.BeginOfFile_Code)])

    result.add_transition(result.init_state_index, trigger_set.inverse(), AcceptanceF=True) 
    result.mark_state_origins()
    return result
    
def __construct(core_sm, pre_condition=None, post_condition=None):

    if pre_condition == None and post_condition == None:
        core_sm.mark_state_origins()
        result = core_sm
        # -- can't get more beautiful ...
    
    elif pre_condition == None and post_condition != None:
        result = setup_post_condition.do(core_sm, post_condition)
        result = __beautify(result)

    elif pre_condition != None and post_condition == None:
        result = setup_pre_condition.do(core_sm, pre_condition)
        result = __beautify(result)

    elif pre_condition != None and post_condition != None:
        # NOTE: pre-condition needs to be setup **after** post condition, because
        #       post condition deletes all origins!
        #       (is this still so? 07y7m6d fschaef)
        result = setup_post_condition.do(core_sm, post_condition)
        result = setup_pre_condition.do(result, pre_condition)
        result = __beautify(result)

    result.finalized_f = True

    return result
  
