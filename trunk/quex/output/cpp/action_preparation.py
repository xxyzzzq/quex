"""Action Preparation:

Functions to prepare a source code fragment to be sticked into the lexical
analyzer. This includes the following:

-- pattern matches: 

   (optional) line and column counting based on the character content of the
   lexeme. Many times, the character or line number count is determined by the
   pattern, so counting can be replaced by an addition of a constant (or even
   no count at all).
                        
-- end of file/stream action:

   If not defined by the user, send 'TERMINATION' token and return.

-- failure action (no match):

   If not defined by the user, abort program with a message that tells that the
   user did not define an 'on_failure' handler.

(C) 2005-2012 Frank-Rene Schaefer
"""
from   quex.engine.generator.action_info           import CodeFragment, \
                                                          PatternActionInfo
from   quex.engine.analyzer.door_id_address_label  import Label
from   quex.blackboard                             import setup as Setup, E_IncidenceIDs
import quex.output.cpp.counter_for_pattern         as     counter_for_pattern
from   quex.engine.analyzer.state.core             import ReloadState, \
                                                          TerminalState


LanguageDB   = None
def do(Mode, IndentationSupportF, BeginOfLineSupportF):
    """The module 'quex.output.cpp.core' produces the code for the 
   state machine. However, it requires a certain data format. This function
   adapts the mode information to this format. Additional code is added 

       -- for counting newlines and column numbers. This happens inside
          the function ACTION_ENTRY().
       -- (optional) for a virtual function call 'on_action_entry()'.
       -- (optional) for debug output that tells the line number and column number.
    """
    global LanguageDB
    global variable_db
    LanguageDB = Setup.language_db

    assert Mode.__class__.__name__ == "Mode"

    # -- 'on after match' action
    on_after_match, \
    require_terminating_zero_preparation_f = __prepare_on_after_match_action(Mode)

    # -- 'end of stream' action
    on_end_of_stream_action = __prepare_on_end_of_stream_action(Mode, IndentationSupportF, BeginOfLineSupportF)

    # -- 'on failure' action (on the event that nothing matched)
    on_failure_action = __prepare_on_failure_action(Mode, BeginOfLineSupportF, require_terminating_zero_preparation_f)

    # -- pattern-action pairs
    pattern_action_pair_list = Mode.get_pattern_action_pair_list()

    # Assume pattern-action pairs (matches) are sorted and their pattern state
    # machine ids reflect the sequence of pattern precedence.
    terminal_state_list = []
    for pattern_info in pattern_action_pair_list:
        action  = pattern_info.action()
        pattern = pattern_info.pattern()

        prepared_action = self.prepare_CodeFragment(Mode, action, pattern) 

        pattern_info.set_action(prepared_action)
    
    for action in (end_of_stream_action, on_failure_action, on_after_match):
        if action is None: continue
        pattern_action_pair_list.append(action)

    return pattern_action_pair_list

def pretty_code(Code, Base):
    """-- Delete empty lines at the beginning
       -- Delete empty lines at the end
       -- Strip whitespace after last non-whitespace
       -- Propper Indendation based on Indentation Counts

       Base = Min. Indentation
    """
    class Info:
        def __init__(self, IndentationN, Content):
            self.indentation = IndentationN
            self.content     = Content
    info_list           = []
    no_real_line_yet_f  = True
    indentation_set     = set()
    for line in Code.split("\n"):
        line = line.rstrip() # Remove trailing whitespace
        if len(line) == 0 and no_real_line_yet_f: continue
        else:                                     no_real_line_yet_f = False

        content     = line.lstrip()
        if len(content) != 0 and content[0] == "#": indentation = 0
        else:                                       indentation = len(line) - len(content) + Base
        info_list.append(Info(indentation, content))
        indentation_set.add(indentation)

    # Discretize indentation levels
    indentation_list = list(indentation_set)
    indentation_list.sort()

    # Collect the result
    result              = []
    # Reverse so that trailing empty lines are deleted
    no_real_line_yet_f  = True
    for info in reversed(info_list):
        if len(info.content) == 0 and no_real_line_yet_f: continue
        else:                                             no_real_line_yet_f = False
        indentation_level = indentation_list.index(info.indentation)
        result.append("%s%s\n" % ("    " * indentation_level, info.content))

    return "".join(reversed(result))

