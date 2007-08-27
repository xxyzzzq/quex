import quex.core_engine.utf8 as utf8
from copy import deepcopy
backslashed_character_db = { 
        # inside string "..." and outside 
        'a': ord('\a'),   'b': ord('\b'), 'f': ord('\f'),   'n': ord('\n'),
        'r': ord('\r'),   't': ord('\t'), 'v': ord('\v'),   '\\': ord('\\'), '"': ord('"'),
        # only ouside of string
        '+': ord('+'), '*': ord('*'), '?': ord('?'), '/': ord('/'), 
        '|': ord('|'), '$': ord('$'), '^': ord('^'), '-': ord('-'), '\\': ord('\\'),  
        '[': ord('['), ']': ord(']'),    
        '(': ord('('), ')': ord(')'),  
        '{': ord('{'), '}': ord('}'), 
}
        
def do(x, i, ReducedSetOfBackslashedCharactersF=False):
    """x = string containing characters after 'the backslash'
       i = position of the backslash in the given string

       RETURNS: UCS code of the interpreted character,
                index of first element after the treated characters in the string

    """
    if type(x) != str and type(x) != list:       
        raise "expected a string or list of integers (ucs values) as first argument"
    if type(i) != int:       
        raise "expected an integer as second argument"
    if i < -1 or i >= len(x) -1: 
        raise "string '%s' does not have a position %i" % (x, i+1)
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
        # **THIS IS FOR COMPLIANCE WITH FLEX SYNTAX**
        numbe_str = chr(x[i+1])
        u = i + 2
        while u < i + 5 and chr(x[u]).isdigit():
            number_str = chr(x[u])
        number = long(numbe_str, 8)     
        if number > 2^31:
            return False, "octal number > 2^31. Unicode letters have a max. index of 2^31"
        # ATE: until u 
        return number, i

    elif x[i+1] == ord('x'):
        # 1 byte character code point
        number, i = __parse_hex_number(x, i+2, i+4)
        # ATE: until end of hex number 
        return number, i

    elif x[i+1] == ord('X'):
        # 2 byte character code point
        number, i = __parse_hex_number(x, i+2, i+6)
        return number, i

    else:
        return None, i

def __parse_hex_number(x, u, MaxL):
    """x    = string to be parsed
       i    = start position in string to be considered
       MaxL = first position after end of string to be parsed
    """
    Lx = len(x)
    MaxL = max(Lx, MaxL)

    while u < MaxL and \
         (chr(x[u]).isdigit() or 
          chr(x[u]) in ['a', 'A', 'b', 'B', 'c', 'C', 'd', 'D', 'e', 'E', 'f', 'F']):
        number_str += chr(x[u])
        
    return long(number_str, 16), u      
