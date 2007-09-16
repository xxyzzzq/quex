# GRAMMAR:
#
# set_expression: 
#                 [: set_term :]
#                 '(' set ')'
#                 traditional character set
#                 \P '{' propperty string '}'
#
# set_term:
#                 set_expression
#                 union        '(' set_expression [ ',' set_expression ]+ ')'
#                 intersection '(' set_expression [ ',' set_expression ]+ ')'
#                 difference   '(' set_expression [ ',' set_expression ]+ ')'
#                 inverse      '(' set_expression ')'
# 
import quex.core_engine.regular_expression.traditional_character_set as traditional_character_set
import quex.core_engine.regular_expression.auxiliary                 as aux

def do(stream):
    return snap_set_expression(stream)

def snap_set_expression(stream):
    __debug_entry("set_expression", stream)    
    assert stream.read(1) == "[" 

    skip
    x = stream.read(2)
    y = stream.read(1)
    if   x[0] == ":":  stream.seek(-1, 1); result = snap_set_term(stream)
    elif x[0] == "(":  stream.seek(-1, 1); result = snap_set_expression(stream)
    elif x == "\\P":   result = snap_propperty_string(stream)
    else:              stream.seek(-2, 1); result = snap_traditional_character_set(stream)

    return __debug_exit(result, stream)

def snap_set_term(stream):
    __debug_entry("set_term", stream)    
    word = __read_word(stream)

    if word not in [ "union", "intersection", "difference", "inverse"]: 
        result = __debug_expression(snap_set_expression(stream)
    else:
        set_list = snap_set_list(stream)
        if set_list == None:
            return __debug_exit(None, stream)

        if word == "inverse":
            # The inverse of multiple sets, is to be the inverse of the union
            # of these sets.
            result = set_list[0]
            for set in set_list[1:]:
                result = result.union(set)
            result = result.inverse()
        else:
            # For 'union', 'intersection', and 'difference' the word corresponds
            # to the member function name of NumberSet. So use __dict__[word] to
            # get to the operation function.
            result = set_list[0]
            for set in set_list[1:]:
                result = result.__dict__[word](set)

    return __debug_exit(result, stream)





def snap_set_primary(stream):
    return snap_traditional_character_set(stream)


def snap_traditional_character_set(stream):
    """Cuts a character range bracketed by '[' ']' from the utf8_string and 
       returns the resulting state machine.
    """
    assert stream.read(1) == "[" 

    character_string = aux.__snap_until(stream, "]")  

    # transform traditional character set string 'a-zA-X0-1' ... into a state machine        
    # (traditional in the sense of Unix, POSIX, flex, awk, like character ranges)
    result = traditional_character_set.do(character_string)   

    return result

   
