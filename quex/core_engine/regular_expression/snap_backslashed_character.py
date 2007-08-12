import quex.core_engine.utf8 as utf8
from copy import deepcopy

quex_backslashed_characters = deepcopy(utf8.backslashed_characters)
# extra characters
quex_backslashed_characters['^']  = ord('^'), 
quex_backslashed_characters['-']  = ord('-'),  
quex_backslashed_characters['[']  = ord('['),
quex_backslashed_characters['(']  = ord('('),
quex_backslashed_characters[']']  = ord(']'), 
quex_backslashed_characters[')']  = ord(')'), 
quex_backslashed_characters['\\'] = ord('\\')  
quex_backslashed_characters['"']  = ord('"')  
	      

def do(x, i):
    if quex_backslashed_characters.has_key(chr(x[i+1])):
	# a backslashed letter, e.g. \n, \a, \-, etc.
	value = quex_backslashed_characters[chr(x[i+1])]
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
	raise "unknown backslashed character"

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
