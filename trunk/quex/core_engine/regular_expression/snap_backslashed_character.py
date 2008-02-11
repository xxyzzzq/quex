from copy import deepcopy
from quex.exception        import  RegularExpressionException


backslashed_character_db = { 
        # inside string "..." and outside 
        'a': ord('\a'),   'b': ord('\b'), 'f': ord('\f'),   'n': ord('\n'),
        'r': ord('\r'),   't': ord('\t'), 'v': ord('\v'),   '\\': ord('\\'), '"': ord('"'),
        # only ouside of string
        '+': ord('+'), '*': ord('*'), '?': ord('?'), '/': ord('/'), 
        '|': ord('|'), '$': ord('$'), '^': ord('^'), '-': ord('-'), 
        '[': ord('['), ']': ord(']'),    
        '(': ord('('), ')': ord(')'),  
        '{': ord('{'), '}': ord('}'), 
}
        
def do(x, i, ReducedSetOfBackslashedCharactersF=False):
    """All backslashed characters shall enter this function. In particular 
       backslashed characters appear in:
        
             "$50"     -- quoted strings
             [a-zA-Z]  -- character sets
             for       -- lonestanding characters 
    
       x = string containing characters after 'the backslash'
       i = position of the backslash in the given string

       ReducedSetOfBackslashedCharactersF indicates whether we are outside of a quoted
       string (lonestanding characters, sets, etc.) or inside a string. Inside a quoted
       string there are different rules, because not all control characters need to be
       considered.

       RETURNS: UCS code of the interpreted character,
                index of first element after the treated characters in the string
    """
    assert type(x) == str or type(x) == list       
    assert type(i) == int       
    assert i >= -1 and i < len(x) -1

    if type(x) == str:
        x = map(ord, x)  # transform string into a list of ASCII values (UCS page 0)

    if ReducedSetOfBackslashedCharactersF:
        backslashed_character_list = [ 'a', 'b', 'f', 'n', 'r', 't', 'v', '\\', '"' ]
    else:
        backslashed_character_list = backslashed_character_db.keys()

    tmp = sh.read(1)
       
    if   tmp in backslashed_character_list: return backslashed_character_db[tmp]
    elif tmp.isdigit():                     return __parse_octal_number(sh, 5)
    elif tmp == 'x':                        return __parse_hex_number(sh, 4)
    elif tmp == 'X':                        return __parse_hex_number(sh, 6)
    elif tmp == 'U':                        return __parse_hex_number(sh, 8)
    else:                                   return None

def __parse_octal_number(x, u, MaxL):
    """MaxL = Maximum length of number to be parsed.
    """
    tmp = sh.read(1)
    while len(number_str) < MaxL and tmp.isdigit() and ord(tmp) < ord("8"): 
        number_str += tmp
        tmp.read(1)
        
    if number_str == "":
        raise RegularExpressionException("Missing octal number.")

    return long(number_str, 8), u      

def __parse_hex_number(sh, MaxL):
    """MaxL = Maximum length of number to be parsed.
    """
    number_str = ""
    tmp        = sh.read(1)
    while len(number_str) < MaxL and 
          (tmp.isdigit() or tmp in ['a', 'A', 'b', 'B', 'c', 'C', 'd', 'D', 'e', 'E', 'f', 'F']):
        number_str += tmp
        tmp.read(1)
        
    if number_str == "": 
        raise RegularExpressionException("Missing hexadecimal number.")

    return long(number_str, 16)
