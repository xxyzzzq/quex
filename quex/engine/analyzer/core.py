"""Analyzer:

   An object of class Analyzer is a representation of an analyzer state machine
   (object of class StateMachine) that is suited for code generation. In
   particular, track analysis results in 'decorations' for states which help to
   implement efficient code.

   Formally an Analyzer consists of a set of states that are related by their
   transitions. Each state is an object of class AnalyzerState and has the 
   following components:

        * input:          what happens to get the next character.
        * entry:          actions to be performed at the entry of the state.
        * transition_map: a map that tells what state is to be entered 
                          as a reaction to the current input character.
        * drop_out:       what has to happen if no character triggers.

    For administrative purposes, other data such as the 'state_index' is 
    stored along with the AnalyzerState object.
"""

import quex.engine.analyzer.track_analysis as track_analysis

from quex.input.setup import setup as Setup
from copy             import copy, deepcopy
from collections      import defaultdict
from operator         import attrgetter
from exceptions       import AssertionError
from itertools        import islice

class Analyzer:
    def __init__(self, SM, ForwardF):

        acceptance_db = track_analysis.do(SM, ForwardF)

        self.__state_db = dict([(state_index, AnalyzerState(state_index, SM, ForwardF)) 
                                 for state_index in acceptance_db.iterkeys()])

        for state_index, acceptance_trace_list in acceptance_db.iteritems():
            state = self.__state_db[state_index]
            self.__analyze(state, acceptance_trace_list)

    def __iter__(self):
        for x in self.__state_db.values():
            yield x

    def __analyze(self, state, TheAcceptanceTraceList):
                   
        if len(TheAcceptanceTraceList) == 0: return 

        common = {} 
        for x in TheAcceptanceTraceList[0]:
            common[x.pre_context_id] = x
        common_pre_context_id_set = set(common.keys())

        # If any acceptance trace differs from the prototype in accepting or positioning
        # => it needs to be stored and restored.
        # Loop: 'first falsifies'
        for acceptance_trace in islice(TheAcceptanceTraceList, 1, None):
            common_pre_context_id_set.update(acceptance_trace.get_pre_context_id_list())
            for pre_context_id in common_pre_context_id_set:
                
                common_entry = common.get(pre_context_id)
                other_entry  = acceptance_trace.get(pre_context_id)

                # (0) If one of the two does not contain the pre_context_id then the 
                #     common entry must 'void' the entry totally.
                if common_entry == None:
                    common[pre_context_id] = track_analysis.AcceptanceTraceEntry(pre_context_id, None, None, -1, -1, -1)
                    if other_entry != None:
                        self.__state_db[other_entry.accepting_state_index].entry.set_store_acceptance_f(pre_context_id)
                        self.__state_db[other_entry.accepting_state_index].entry.set_store_acceptance_position_f(pre_context_id)
                    continue

                elif other_entry == None:
                    common[pre_context_id].pattern_id  = None # accepting pattern unknown
                    common[pre_context_id].positioning = None # positioning unknown
                    # Here: common_entry != None
                    self.__state_db[common_entry.accepting_state_index].entry.set_store_acceptance_f(pre_context_id)
                    self.__state_db[common_entry.accepting_state_index].entry.set_store_acceptance_position_f(pre_context_id)
                    continue

                # (1) If both maps have an entry, then determine whether the pattern ids 
                #     and the positioning differs.
                if common_entry.pattern_id != other_entry.pattern_id:
                    # Inform related states about the task to store acceptance
                    self.__state_db[other_entry.accepting_state_index].entry.set_store_acceptance_f(pre_context_id)
                    self.__state_db[common_entry.accepting_state_index].entry.set_store_acceptance_f(pre_context_id)
                    common[pre_context_id].pattern_id = None

                if common_entry.move_backward_n != other_entry.move_backward_n:
                    # Inform related states about the task to store acceptance position
                    self.__state_db[other_entry.accepting_state_index].entry.set_store_acceptance_position_f(pre_context_id)
                    self.__state_db[common_entry.accepting_state_index].entry.set_store_acceptance_position_f(pre_context_id)
                    common[pre_context_id].move_backward_n = None

        state.drop_out.set_sequence(common)

class AnalyzerState:
    def __init__(self, StateIndex, SM, ForwardF):
        assert type(StateIndex) in [int, long]
        assert type(ForwardF)   == bool

        state = SM.states[StateIndex]

        self.index          = StateIndex
        self.input          = Input(StateIndex == SM.init_state_index, ForwardF)
        self.entry          = Entry(state.origins(), ForwardF)
        self.transition_map = state.transitions().get_trigger_map()
        self.drop_out       = DropOut()

    def get_string_array(self, InputF=True, EntryF=True, TransitionMapF=True, DropOutF=True):
        txt = [ "State %i:\n" % self.index ]
        if InputF:         txt.append("  .input: move position %i\n" % self.input.move_input_position())
        if EntryF:         txt.extend(["  .entry: ",         repr(self.entry)])
        if TransitionMapF: txt.append("  .transition_map:\n")
        if DropOutF:       txt.extend(["  .drop_out: ",    repr(self.drop_out)])
        txt.append("\n")
        return txt

    def get_string(self, InputF=True, EntryF=True, TransitionMapF=True, DropOutF=True):
        return "".join(self.get_string_array(InputF, EntryF, TransitionMapF, DropOutF))

    def __repr__(self):
        return self.get_string()

class Input:
    def __init__(self, InitStateF, ForwardF):
        if ForwardF: # Rules (1), (2), and (3)
            self.__move_input_position = + 1 if not InitStateF else 0
        else:        # Backward lexing --> rule (3)
            self.__move_input_position = - 1

    def move_input_position(self):
        """+1 --> increment by one before dereferencing
           -1 --> decrement by one before dereferencing
            0 --> neither increment nor decrement.
        """
        return self.__move_input_position

    def immediate_drop_out_if_not_pre_context_list(self):
        """If all successor states require the list of given pre-contexts, then 
           the state can check whether at least one of them is hit. Otherwise, it 
           could immediately drop out.
        """
        return self.__immediate_drop_out_if_not_pre_context_list

class ConditionalEntryAction:
    """Objects of this class describe what has to happen, if a pre-context
       is fulfilled. The related action may be written in pseudo code:

           if( 'self.pre_context_id' fulfilled ) {
                if( 'self.store_acceptance_f' )          last_acceptance            = 'self.pattern_id';
                if( 'self.store_acceptance_position_f' ) last_acceptance_position_f = input_p;
           }

        The 'self.*' variables are computed off-line, so the actual code 
        will look a little more gentle.
    """
    def __init__(self, PreContextID, PatternID):
        self.pre_context_id              = PreContextID
        self.pattern_id                  = PatternID    
        self.store_acceptance_f          = False
        self.store_acceptance_position_f = False

    def __repr__(self):
        if self.store_acceptance_f == False and self.store_acceptance_position_f == False:
            return ""

        txt = []
        if self.pre_context_id != None:
            if self.pre_context_id == -1:    txt.append("BOF, ")
            else:                            txt.append("PreContext%i, " % self.pre_context_id)
        if self.pattern_id == None:          txt.append("Failure, ")
        else:                                txt.append("Pattern%i, " % self.pattern_id)
        if self.store_acceptance_f:          txt.append("StoreAcceptance, ")
        if self.store_acceptance_position_f: txt.append("StoreAcceptancePosition, ")

        return "".join(txt)

class Entry:
    def __init__(self, OriginList, ForwardF):
        self.__sequence    = None

        if ForwardF:
            self.__pre_context_fulfilled_set = None
            self.__sequence                  = []
            for origin in OriginList:
                entry = ConditionalEntryAction(self.__extract_pre_context_id(origin), 
                                               origin.state_machine_id)
                self.__sequence.append(entry)
                # If an unconditioned acceptance occurred, then no further consideration!
                # (Rest of acceptance candidates is dominated).
                if origin.pre_context_id != None: break
        else:
            self.__pre_context_fulfilled_set = set([])
            self.__sequence                  = None
            for origin in OriginList:
                if not origin.store_input_position_f(): continue
                assert origin.is_acceptance()
                self.__pre_context_fulfilled_set.add(origin.state_machine_id)

        # List of post context begin positions that need to be stored at state entry
        self.__store_position_begin_of_post_context_id_set = set([])

        # Only for 'assert' see member functions below
        self.__origin_list = set(filter(lambda x: x != -1, 
                                        map(lambda x: x.post_context_id(), OriginList)))

    def __repr__(self):
        txt     = []
        first_f = True
        if self.__pre_context_fulfilled_set != None:
            # (only possible in backward lexical analysis)
            if first_f: first_f = False
            else:       txt.append("          ") 
            for x in self.__pre_context_fulfilled_set:
                txt.append("\npre context id %i fulfilled\n" % x)
        else:
            for x in self.__sequence:
                if first_f: first_f = False
                else:       txt.append("          ") 
                txt.append(repr(x))
                txt.append("\n")
            for x in self.__store_position_begin_of_post_context_id_set:
                if first_f: first_f = False
                else:       txt.append("          ") 
                txt.append("post context id %i begin\n" % x)

        if len(txt) == 0: txt.append("\n")
        return "".join(txt)

    def get_sequence(self):
        assert self__sequence != None
        return self.__sequence

    def set_store_acceptance_f(self, PreContextID):
        for x in self.__sequence: 
            if x.pre_context_id == PreContextID: 
                x.store_acceptance_f = True
                return
        assert False, "PostContextID not mentioned in state"

    def set_store_acceptance_position_f(self, PreContextID):
        for x in self.__sequence: 
            if x.pre_context_id == PreContextID: 
                x.store_acceptance_position_f = True
                return
        assert False, "PostContextID not mentioned in state"

    def set_store_begin_of_post_context_position(self, PostContextID):
        assert PostContextID in self.__post_context_id_list

        self.__store_position_begin_of_post_context_id_set.add(PostContextID)

    def pre_context_fulfilled_list(self):
        """This is only relevant during backward lexical analyzis while
           searching for pre-contexts. The list that is returned tells
           that the given pre-contexts are fulfilled in the current state
           and must be set, e.g.

                    pre_context_fulfilled[i] = true; 
        """
        assert self.__pre_context_fulfilled_set != None
        return self.__pre_context_fulfilled_set

    def __extract_pre_context_id(self, Origin):
        """This function basically describes how pre-context-ids and 
           'begin-of-line' pre-context are expressed by an integer.
        """
        if   Origin.pre_context_begin_of_line_f(): return -1
        elif Origin.pre_context_id() == -1:        return None
        else:                                      return Origin.pre_context_id()

class DropOut:
    """The drop out has to do (at maximum) two things:

       -- positioning the input pointer of the analyzer.
       -- goto the related terminal.

       This may happen depending on fulfilled pre_context's. Thus, there
       is actually a sequence of checks:
        
            if     ( pre_context_0 ) { input_p = ... ; goto ...; }
            else if( pre_context_1 ) { input_p = ... ; goto ...; }
            else if( pre_context_2 ) { input_p = ... ; goto ...; }
            else                     { input_p = ... ; goto ...; }

       This is what is returned by 'get_sequence()' the elements are of class
       'AcceptanceTraceEntry' where now only the members:

                .pre_context_id   # The pre context id for which it is valid
                .move_backward_n  # Positioning of the input pointer
                .pattern_id       # Goto this particular terminal

       are of interest.
    """
    def __init__(self):
        self.__sequence = []

    def __repr__(self):
        if len(self.__sequence) == 0: return "Failure"

        def write(txt, X):
            if   X.move_backward_n == None: txt.append("pos = restore(StoredAcceptancePosition); ")
            elif X.move_backward_n == 1:    txt.append("pos = lexeme_start + 1; ")
            elif X.move_backward_n == 0:    pass # This state is an acceptance state
            else:                           txt.append("pos -= %i; " % X.move_backward_n) 
            if   X.pattern_id == None:      txt.append("goto StoredAcceptance;")
            else:                           txt.append("goto Pattern%i;" % X.pattern_id)

        txt = []
        first_f = True
        L = len(self.__sequence)
        for i, x in enumerate(self.__sequence):
            if first_f: first_f = False
            else:       txt.append("             ")
            if x.pre_context_id == None: 
                write(txt, x)
            else: 
                txt.append("if pre_context_%i: " % x.pre_context_id)
                write(txt, x)
            if i != L - 1:
                txt.append("\n")

        return "".join(txt)

    def set_sequence(self, CommonTrace):
        for x in sorted(CommonTrace.itervalues(), key=attrgetter("pattern_id")):
            assert x.__class__ == track_analysis.AcceptanceTraceEntry
            self.__sequence.append(copy(x))
            if x.pre_context_id == None: break

    def get_sequence(self):
        return self.__sequence

