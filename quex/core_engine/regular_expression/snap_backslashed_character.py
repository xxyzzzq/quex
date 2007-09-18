import quex.core_engine.utf8 as utf8
from copy import deepcopy
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

       
    if chr(x[i+1]) in backslashed_character_list:
        # a backslashed letter, e.g. \n, \a, \-, etc.
        value = backslashed_character_db[chr(x[i+1])]
        # ATE: two characters
        return value, i+2

    elif chr(x[i+1]).isdigit():
        # octal number 
        number, i = __parse_octal_number(x, i+1, i+5)
        # ATE: until u 
        return number, i

    elif x[i+1] == ord('x'):
        print "## obacht"
        # 1 byte character code point
        number, i = __parse_hex_number(x, i+2, i+4)
        # ATE: until end of hex number 
        return number, i

    elif x[i+1] == ord('X'):
        # 2 byte character code point
        number, i = __parse_hex_number(x, i+2, i+6)
        return number, i

    elif x[i+1] == ord('U'):
        # 2 byte character code point
        number, i = __parse_hex_number(x, i+2, i+8)
        return number, i

    else:
        return None, i

def __parse_octal_number(x, u, MaxL):
    """x    = string to be parsed
       i    = start position in string to be considered
       MaxL = first position after end of string to be parsed
    """
    Lx = len(x)
    MaxL = min(Lx, MaxL)
    number_str = ""

    while u < MaxL and chr(x[u]).isdigit() and x[u] < ord("8"): 
        number_str += chr(x[u])
        u += 1
        
    return long(number_str, 8), u      

def __parse_hex_number(x, u, MaxL):
    """x    = string to be parsed
       i    = start position in string to be considered
       MaxL = first position after end of string to be parsed
    """
    Lx = len(x)
    MaxL = min(Lx, MaxL)
    number_str = ""

    while u < MaxL and \
         (chr(x[u]).isdigit() or 
          chr(x[u]) in ['a', 'A', 'b', 'B', 'c', 'C', 'd', 'D', 'e', 'E', 'f', 'F']):
        number_str += chr(x[u])
        u += 1
        
    return long(number_str, 16), u      
