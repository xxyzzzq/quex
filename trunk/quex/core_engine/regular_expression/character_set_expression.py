# GRAMMAR:
#
# set_expression: 
#                 [: set_term :]
#                 traditional character set
#                 \P '{' propperty string '}'
#
# set_term:
#                 "alnum" 
#                 "alpha" 
#                 "blank" 
#                 "cntrl" 
#                 "digit" 
#                 "graph" 
#                 "lower" 
#                 "print" 
#                 "punct" 
#                 "space" 
#                 "upper" 
#                 "xdigit"
#                 "union"        '(' set_term [ ',' set_term ]+ ')'
#                 "intersection" '(' set_term [ ',' set_term ]+ ')'
#                 "difference"   '(' set_term [ ',' set_term ]+ ')'
#                 "inverse"      '(' set_term ')'
#                 set_expression
# 
import quex.core_engine.regular_expression.traditional_character_set as traditional_character_set
import quex.core_engine.regular_expression.auxiliary                 as aux
#
from quex.core_engine.state_machine.core import StateMachine
from quex.exception                      import RegularExpressionException
from quex.frs_py.string_handling         import trim
from quex.frs_py.file_in                 import read_until_letter, \
                                                read_until_non_letter, \
                                                skip_whitespace
from quex.core_engine.regular_expression.auxiliary import __snap_until, \
                                                          __debug_entry, \
                                                          __debug_exit

special_character_set_db = {
        "alnum":  traditional_character_set.do("[a-zA-Z0-9]"),
        "alpha":  traditional_character_set.do("[a-zA-Z]"),
        "blank":  traditional_character_set.do("[ \\t]"),
        "cntrl":  traditional_character_set.do("[\\x00-\\x1F\\x7F]"), 
        "digit":  traditional_character_set.do("[0-9]"),
        "graph":  traditional_character_set.do("[\\x21-\\x7E]"),
        "lower":  traditional_character_set.do("[a-z]"),
        "print":  traditional_character_set.do("[\\x20-\\x7E]"), 
        "punct":  traditional_character_set.do("[!\"#$%&'()*+,-./:;?@[\\]_`{|}~\\\\]"),
        "space":  traditional_character_set.do("[ \\t\\r\\n]"),
        "upper":  traditional_character_set.do("[A-Z]"),
        "xdigit": traditional_character_set.do("[a-fA-F0-9]"),
}

def do(stream):
    trigger_set = snap_set_expression(stream)

    if trigger_set == None: 
        raise RegularExpressionException("Regular Expression: character_set_expression called for something\n" + \
                                         "that does not start with ']' or '\\P'")

    # create state machine that triggers with the trigger set to SUCCESS
    # NOTE: The default for the ELSE transition is FAIL.
    sm = StateMachine()
    sm.add_transition(sm.init_state_index, trigger_set, AcceptanceF=True)

    return __debug_exit(sm, stream)

def snap_set_expression(stream):
    __debug_entry("set_expression", stream)

    x = stream.read(2)
    if   x == "[:":
        result = snap_set_term(stream)
    elif x[0] == "[":
        stream.seek(-1, 1)
        result = snap_traditional_character_set(stream)
    elif x == "\\P": 
        result = snap_property_string.do(stream)
    elif x == "\\N": 
        result = snap_property_string.do_name(stream)
    elif x == "\\G": 
        result = snap_property_string.do_general_category(stream)
    else:
        result = None

    return __debug_exit(result, stream)

def snap_set_term(stream):
    __debug_entry("set_term", stream)    

    skip_whitespace(stream)
    position = stream.tell()

    # if there is no following '(', then enter the 'snap_expression' block below
    try:    
        word = read_until_non_letter(stream)
        stream.seek(-1, 1)  # putback the non-letter
    except: 
        word = "not a valid word"

    word = trim(word)

    if word in [ "union", "intersection", "difference", "inverse"]: 
        set_list = snap_set_list(stream, word)
        # if an error occurs during set_list parsing, an exception is thrown about syntax error

        L      = len(set_list)
        result = set_list[0]

        if word == "inverse":
            # The inverse of multiple sets, is to be the inverse of the union of these sets.
            if L > 1:
                for set in set_list[1:]:
                    result = result.union(set)
            result = result.inverse()
            return __debug_exit(result, stream)

        if L < 2:
            raise RegularExpressionException("Regular Expression: A %s operation needs at least\n" % word + \
                                             "two sets to operate on them.")
            
        if   word == "union":
            for set in set_list[1:]:
                result = result.union(set)
        elif word == "intersection":
            for set in set_list[1:]:
                result = result.intersection(set)
        elif word == "difference":
            for set in set_list[1:]:
                result = result.difference(set)

    elif word in special_character_set_db.keys():
        result = special_character_set_db[word]

    else:
        # try to snap an expression out of it
        stream.seek(position)
        result = snap_set_expression(stream)

    return __debug_exit(result, stream)

def __snap_word(stream):
    try:    the_word = read_until_letter(stream, ["("]) 
    except: 
        raise RegularExpressionException("Missing opening bracket.")
    stream.seek(-1,1)
    return trim(the_word)

def snap_set_list(stream, set_operation_name):
    __debug_entry("set_list", stream)

    skip_whitespace(stream)
    if stream.read(1) != "(": 
        raise RegularExpressionException("Missing opening bracket '%s' operation." % set_operation_name)

    set_list = []
    while 1 + 1 == 2:
        skip_whitespace(stream)
        result = snap_set_term(stream)
        if result == None: 
            raise RegularExpressionException("Missing set expression list after '%s' operation." % set_operation_name)
        set_list.append(result)
        skip_whitespace(stream)
        tmp = stream.read(1)
        if tmp != ",": 
            if tmp != ")":
                stream.seek(-1, 1)
                raise RegularExpressionException("Missing closing ')' after after '%s' operation." % set_operation_name)
            return __debug_exit(set_list, stream)

def snap_set_primary(stream):
    __debug_entry("set_primary", stream)

    return __debug_entry(snap_traditional_character_set(stream), stream)

def snap_traditional_character_set(stream):
    """Cuts a character range bracketed by '[' ']' from the utf8_string and 
       returns the resulting state machine.
    """
    character_string = aux.__snap_until(stream, "]")  

    # transform traditional character set string 'a-zA-X0-1' ... into a state machine        
    # (traditional in the sense of Unix, POSIX, flex, awk, like character ranges)
    result = traditional_character_set.do(character_string)   

    return result

   
