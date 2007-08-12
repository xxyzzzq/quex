#! /usr/bin/env python
# Quex is  free software;  you can  redistribute it and/or  modify it  under the
# terms  of the  GNU Lesser  General  Public License  as published  by the  Free
# Software Foundation;  either version 2.1 of  the License, or  (at your option)
# any later version.
# 
# This software is  distributed in the hope that it will  be useful, but WITHOUT
# ANY WARRANTY; without even the  implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the  GNU Lesser General Public License for more
# details.
# 
# You should have received a copy of the GNU Lesser General Public License along
# with this  library; if not,  write to the  Free Software Foundation,  Inc., 59
# Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
################################################################################
import os
import sys
from copy    import copy
from string  import split

temporary_files  = []

def skip_whitespace(fh):
    while 1 + 1 == 2:
        tmp = fh.read(1)

        if tmp in [' ', '\t', '\n']: continue
        elif tmp == "": raise "EOF"

	# -- character was not a whitespace character
	#    => is there a '//' or a '/*' -comment ?
	tmp2 = fh.read(1)
	if tmp2 == "": raise "EOF"

	tmp += tmp2
	if tmp == "//":   
	    # skip until '\n'
	    while tmp != '\n':
		tmp = fh.read(1)
		if tmp == "": raise "EOF"

	elif tmp == "/*":
	    # skip until '*/'
	    previous = " "
	    while tmp != "":
		tmp = fh.read(1)
		if tmp == "": raise "EOF"
		if previous + tmp == "*/":
		    break
		previous = tmp
	else:
	    # no whitespace, no comment --> real character
	    fh.seek(-2, 1)
	    return                


def read_until_whitespace(fh):
    txt = ""
    previous_tmp = ""
    while 1 + 1 == 2:
        tmp = fh.read(1)
        if   tmp == "": raise "EOF"
        elif tmp in [' ', '\t', '\n']:                     fh.seek(-1, 1); return txt
	elif previous_tmp == "/" and (tmp in ["*",  "/"]): fh.seek(-2, 1); return txt[:-1]
        txt += tmp
	previous_tmp = tmp

def read_until_closing_bracket(fh, Opener, Closer,
                               IgnoreRegions = [ ['"', '"'],      # strings
                                                 ["//", "\n"],    # c++ comments
                                                 ["/*", "*/"] ],  # c comments
			       SkipClosingDelimiterF = True):			 
    """This function does not eat the closing bracket from the stream.
    """								    
    # print "# # read_until_closing_bracket: ", Opener, ", ", Closer, ", ", IgnoreRegions

    open_brackets_n = 1
    backslash_f     = False
    txt     = ""
    CacheSz = max(len(Opener), len(Closer))
    if IgnoreRegions != []: 
        # check for correct type, because this can cause terrible errors
        if type(IgnoreRegions) != list:
	    raise "read_until_closing_bracket(): argument 'IgnoreRegions' must be of type '[[]]'"
	for element in IgnoreRegions:					 
            if type(element) != list:
	        raise "read_until_closing_bracket(): argument 'IgnoreRegions' must be of type '[[]]'"
						 
	CacheSz = max(map(lambda delimiter: len(delimiter[0]), IgnoreRegions) + [ CacheSz ])

    cache = ["\0"] * CacheSz

    def match_against_cache(Delimiter):
	"""Determine wether the string 'Delimiter' is flood into the cache or not."""
	if len(Delimiter) > len(cache):
	    raise "error: read_until_closing_bracket() cache smaller than delimiter"

	# delimiter == "" means that it is, in fact, not a delimiter (disabled)    
	if Delimiter == "": return False
	L = len(Delimiter)
	i = -1
	for letter in Delimiter:
	    i += 1
	    if letter != cache[L-i-1]: return False
	return True

    # ignore_start_triggers = map(lamda x: x[0], IgnoreRegions)
    while 1 + 1 == 2:
        tmp = fh.read(1)
        txt += tmp
	cache.insert(0, tmp)  # element 0 last element flood into cache (current)
	cache.pop(-1)         # element N first element                 (oldest)

        if tmp == "":         
	    raise "EOF"

        elif tmp == "\\":       
	    backslash_f = not backslash_f   # every second backslash switches to 'non-escape char'
	    continue


	if not backslash_f:
	    result = match_against_cache(Opener)
	    if   match_against_cache(Opener):
		open_brackets_n += 1
	    elif match_against_cache(Closer):
		open_brackets_n -= 1
		if open_brackets_n == 0: 
		    # stop accumulating text when the closing delimiter is reached. do not 
		    # append the closing delimiter to the text. 
		    txt = txt[:-len(Closer)]
		    break

	backslash_f = False

        for delimiter in IgnoreRegions:
	    # If the start delimiter for ignored regions matches the strings recently in flooded into
	    # the cache, then read until the end of the region that is to be ignored.
	    if match_against_cache(delimiter[0]): 
		## print "##cache = ", cache
		txt += read_until_closing_bracket(fh, "", delimiter[1], IgnoreRegions=[]) 
		txt += delimiter[1]
		# the 'ignore region info' may contain information about with what the
		# closing delimiter is to be replaced
		## print "##ooo", txt
		# flush the cache
		cache = ["\0"] * CacheSz
		break
		
    return txt

def read_until_character(fh, Character):
    open_brackets_n = 1
    backslash_n     = 0
    txt = ""

    # ignore_start_triggers = map(lamda x: x[0], IgnoreRegions)
    # TODO: incorporate "comment ignoring"
    while 1 + 1 == 2:
        tmp = fh.read(1)
        if   tmp == "": raise "EOF"
        elif tmp == "\\": backslash_n += 1
        else:
            backslash_n = 0
            if backslash_n % 2 != 1:
                if tmp == Character:
                    return txt
        txt += tmp

    return txt

def read_until_letter(fh, EndMarkers, Verbose=False):
    txt = ""
    while 1 + 1 == 2:
        tmp = fh.read(1)
        if tmp == "": raise "EOF"
        if tmp in EndMarkers:
            if Verbose: return txt, EndMarkers.index(tmp)
            else:       return txt
        txt += tmp
	
def read_until_line_contains(in_fh, LineContent):
    L = len(LineContent)

    line = in_fh.readline()
    if line == "": return ""

    collector = ""
    while line.find(LineContent) == -1:
        collector += line
        line = in_fh.readline()
        if line == "":  break

    return collector

def get_plain_file_content(FileName):
    fh = open_file_or_die(FileName)
    txt = ""
    for line in fh.readlines(): txt += line
    return txt

def get_current_line_info_number(fh):
    position = fh.tell()
    line_n = 0
    fh.seek(0)
    for i in range(position):
        if fh.read(1) == '\n': line_n += 1

    # just to be sure without having to test this stuff ...
    fh.seek(position)
    return line_n

def clean_up():
    # -- delete temporary files
    for file in temporary_files:
        os.system("rm %s" % file)

def open_file_or_die(FileName, Mode="r"):
    try:
        fh = open(FileName, Mode)
        return fh
    except:
        print "error: opening file '%s' failed" % (FileName)
        sys.exit(-1)

def indented_open(Filename, Indentation = 3):
    """Opens a file but indents all the lines in it. In fact, a temporary
    file is created with all lines of the original file indented. The filehandle
    returned points to the temporary file."""
    
    IndentString = " " * Indentation
    
    try:
        fh = open(Filename, "r")
    except:
        print "%s:error: indented opening of file '%s' " % (this_name, Filename)
        sys.exit(-1)
    new_content = ""
    for line in fh.readlines():
        new_content += IndentString + line
    fh.close()

    tmp_filename = Filename + ".tmp"

    if tmp_filename not in temporary_files:
        temporary_files.append(copy(tmp_filename))

    fh = open(tmp_filename, "w")
    fh.write(new_content)
    fh.close()

    fh = open(tmp_filename)

    return fh

def delete_framing_whitespace(Str):

    if Str == "": return ""
    L = len(Str)
    for i in range(L):
        if Str[i] not in [" ", "\t", "\n"]:
            break
    else:
        # reached end of string --> empty string
        return ""

    for k in range(1, L-i):
        if Str[-k] not in [" ", "\t", "\n"]:
            break

    # note, if k = 1 then we would return Str[i:0]
    if L-i != 1:
        if k == 1:   return Str[i:]
        else:        return Str[i:-k + 1]
    else:            return Str[i:]
    
def read_next_word(fh):
    skip_whitespace(fh)
    word = read_until_whitespace(fh)

    if word == "": raise "EOF"
    return word

def read_word_list(fh, EndMarkers, Verbose=False):
    """reads whitespace separated words until the arrivel
    of a string mentioned in the array 'EndMarkers'. If
    the Verbose flag is set not only the list of found words
    is returned. Moreover the index of the end marker which
    triggered is given as a second return value."""
    word_list = []
    while 1 + 1 == 2:
        skip_whitespace(fh)
        word = read_next_word(fh)        
        if word == "": raise "EOF"
        if word in EndMarkers:
            if Verbose: return word_list, EndMarkers.index(word)
            else:       return word_list
        word_list.append(word)

def verify_next_word(fh, Compare, Quit=True):
    word = read_next_word(fh)
    if word != Compare:
        error_msg("missing token '%s'. found '%s'" % (Compare, word), fh)
    return word
        
def error_msg(ErrMsg, fh=-1, LineN=None, DontExitF=False):
    # fh        = filehandle [1] or filename [2]
    # LineN     = line_number of error
    # DontExitF = True then no exit from program
    #           = False then total exit from program
    #
    # count line numbers (this is a kind of 'dirty' solution for not
    # counting line numbers on the fly. it does not harm at all and
    # is much more direct to be programmed.)

    if fh == -1:
        prefix = "command line"
    if fh == "assert":
        if type(LineN) != str: 
	    error_msg("3rd argument needs to be a string,\n" + \
		      "if message type == 'assert'", "assert", 
		      "file_in.error_msg()")
	file_name = LineN    
	prefix = "internal assert:" + file_name + ":"   
    else:
	if type(fh) == str:
	    line_n = LineN
	    Filename = fh 
	else:
	    if fh != None:
		line_n   = get_current_line_info_number(fh)
		Filename = fh.name
	    else:
		line_n = -1
		Filename = ""
	prefix = "%s:%i:error" % (Filename, line_n + 1)   
	
    for line in split(ErrMsg, "\n"):
	print prefix + ": %s" % line

    if not DontExitF: sys.exit(-1)

def get_include_guard_extension(Filename):
    """Transforms the letters of a filename, so that they can appear in a C-macro."""
    include_guard_extension = ""
    for letter in Filename:
        if letter.isalpha() or letter.isdigit() or letter == "_":
            include_guard_extension += letter.upper()
        else:
            include_guard_extension += "_x%x_" % ord(letter)
    return include_guard_extension


