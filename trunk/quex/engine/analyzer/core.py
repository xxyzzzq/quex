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
from   quex.engine.analyzer.track_analysis import AcceptanceTraceEntry, \
                                                  AcceptanceTraceEntry_Void


from quex.input.setup import setup as Setup
from copy             import copy, deepcopy
from collections      import defaultdict
from operator         import attrgetter
from exceptions       import AssertionError
from itertools        import islice, ifilter, takewhile
import sys

class Analyzer:
    def __init__(self, SM, ForwardF):

        acceptance_db = track_analysis.do(SM, ForwardF)

        self.__state_db = dict([(state_index, AnalyzerState(state_index, SM, ForwardF)) 
                                 for state_index in acceptance_db.iterkeys()])

        for state_index, acceptance_trace_list in acceptance_db.iteritems():
            state = self.__state_db[state_index]
            ## print "##DEBUG", state_index
            ## if state_index in [43]: print "##", state_index, acceptance_trace_list

            common = self.__horizontal_analysis(state, acceptance_trace_list)
            self.__vertical_analysis(state, common)

    def __iter__(self):
        for x in self.__state_db.values():
            yield x

    def __horizontal_analysis(self, state, TheAcceptanceTraceList):
        """For a given state, there might be multiple paths through it. For
           each of those paths there exists an 'acceptance trace' that has been
           accumulated since the init state. An acceptance trace tells what
           happens if a pre-context is fulfilled. The horizontal analysis
           combines the multiple acceptance traces into a single 'common'
           acceptance trace, i.e.

           Trace[0]       Trace[1]       Trace[2]           Common
           
           (pre 0 => A)   (pre 0 => A)                      (pre 0 => A)  
                          (pre 1 => B)                      (pre 1 => B)                    
           (pre 2 => C)                  (pre 4 => C)  --\  (pre 2 => C)  
           (pre 3 => D)                  (pre 5 => E)  --/  (pre 3 => None)  
                                                            (pre 4 => E)              
           (None  => F)   (None  => H)   (None  => G)       (None  => None)  
        """
                   
        if len(TheAcceptanceTraceList) == 0: return 

        pre_context_id_set = set([])
        for acceptance_trace in TheAcceptanceTraceList:
            pre_context_id_set.update(acceptance_trace.get_pre_context_id_list())

        common = {}
        # If any acceptance trace differs from the prototype in accepting or positioning
        # => it needs to be stored and restored.
        # Loop: 'first falsifies'
        ##print "##common 0:", common
        for pre_context_id in pre_context_id_set:

            entry_list = map(lambda x: x.get(pre_context_id), TheAcceptanceTraceList)
            # If a 'pre_context_id' is in 'pre_context_id_set' this means that at least one
            # path triggers on the given 'pre_context_id' to acceptance. If on the other hand
            # one single trace does not trigger on the given pre-context to acceptance, then
            # this means that the acceptance and positioning depends on the path taken at
            # runtime.
            if None in entry_list:
                # One path does not trigger on given pre-context-id
                common[pre_context_id] = AcceptanceTraceEntry(pre_context_id, 
                                                              PatternID                    = None, # Undetermined
                                                              TransitionN_ToAcceptance     = -1,
                                                              AcceptingStateIndex          = -1, 
                                                              TransitionN_SincePositioning = -1,   # Undetermined
                                                              PositioningStateIndex        = -1, 
                                                              PostContextID                = -1)
                for that in ifilter(lambda x: x != None, entry_list):
                    if that.accepting_state_index == -1: continue
                    self.__state_db[that.accepting_state_index].entry.set_store_acceptance_f(pre_context_id)
                    self.__state_db[that.accepting_state_index].entry.set_store_acceptance_position_f(pre_context_id)
                continue

            this = entry_list[0]
            common[pre_context_id] = this
            for that in islice(entry_list, 1, None):

                # (1) If both maps have an entry, then determine whether the pattern ids 
                #     and the positioning differs.
                if pre_context_id == None:
                    if this.pattern_id != that.pattern_id:
                        # Inform related states about the task to store acceptance
                        if that.accepting_state_index != -1:
                            self.__state_db[that.accepting_state_index].entry.set_store_acceptance_f(pre_context_id)
                        if this.accepting_state_index != -1:
                            self.__state_db[this.accepting_state_index].entry.set_store_acceptance_f(pre_context_id)
                        common[pre_context_id].pattern_id = None # Winner determined at run-time
                else:
                    # Same pre-context-ids must refer the same patterns.
                    assert this.pattern_id == that.pattern_id

                if this.transition_n_since_positioning != that.transition_n_since_positioning:
                    # Inform related states about the task to store acceptance position
                    if that.positioning_state_index != -1:
                        self.__state_db[that.positioning_state_index].entry.set_store_acceptance_position_f(pre_context_id)
                    if this.positioning_state_index != -1:
                        self.__state_db[this.positioning_state_index].entry.set_store_acceptance_position_f(pre_context_id)
                    this.transition_n_since_positioning = None # Distance determined at run-time

        # Even, if there is only one trace: If the backward position is undetermined
        # then it the 'positioning state' must store the input position.
        for x in common.itervalues():
            if x.transition_n_since_positioning != None: continue
            if x.post_context_id == -1:                  continue
            if x.positioning_state_index == -1:          continue
            self.__state_db[x.positioning_state_index].entry.set_store_begin_of_post_context_position(x.post_context_id)

        return common

    def __vertical_analysis(self, state, Common):
        """Takes a 'common' acceptance trace as a result from the horizontal 
           analysis and sorts and filters its elements. 
        """
        assert len(Common) != 0

        def __voidify(trace):
            for x in ifilter(lambda x: x.accepting_state_index != -1, trace):
                self.__state_db[x.accepting_state_index].entry.set_store_acceptance_f(x.pre_context_id)
                self.__state_db[x.positioning_state_index].entry.set_store_acceptance_f(x.pre_context_id)
            # Set a totally undetermined acceptance trace, that is:
            # restore acceptance and acceptance position
            state.drop_out.set_sequence([AcceptanceTraceEntry_Void])
            return

        trace = Common.values()
        if len(trace) == 1: 
            assert trace[0].pre_context_id == None
            state.drop_out.set_sequence(trace)
            return 

        # (1) Length of the Match
        #
        # -- If length of match cannot be determined for more than one entry
        #    then no comparison can be made at all. Thus, acceptance can only
        #    be determined at run-time.
        # -- If all entries are of undetermined length, but they all accept
        #    at the same state, then the trace can still be treated before
        #    run-time.
        x_min_transition_n      = -1
        x_accepting_state_index = -1
        for x in ifilter(lambda x: x.transition_n_to_acceptance < 0, trace):
            if x_accepting_state_index == -1: 
                # 'count == 0' there was no element with 'n < 0' before.
                x_min_transition_n      = - x.transition_n_to_acceptance
                x_accepting_state_index = x.accepting_state_index
            elif    x_accepting_state_index != x.accepting_state_index \
                 or x_min_transition_n      != - x.transition_n_to_acceptance:
                # 'count > 0' there was an element with 'n < 0' before and the
                # accepting state was different.
                return __voidify(trace)

        if x_min_transition_n != -1:
            # The 'min_transition_n' must dominate all others, otherwise, 
            # no sorting can happen.
            for x in ifilter(lambda x: x.transition_n_to_acceptance >= 0, trace):
                if x_min_transition_n <= x.transition_n_to_acceptance:
                    return __voidify(trace)

        # (2) Sort Entries
        #     Since we know that the min. accepted distance for the undetermined
        #     case dominates all others, we can put them all on the same scale.
        #     Longer patterns must sort 'higher', thus me must make sure that 
        #     all entries are negative.
        # 
        #     (Equal race: make sure that 'at least N' enters the race as 'N' 
        #                  'n < 0' means 'at least n', 'n >= 0' means exactly 'n')
        for x in ifilter(lambda x: x.transition_n_to_acceptance >= 0, trace):
            x.transition_n_to_acceptance = - x.transition_n_to_acceptance

        trace.sort(key=attrgetter("transition_n_to_acceptance", "pattern_id"))

        # (3) Filter anything that is dominated by the unconditional acceptance
        result = []
        for x in trace:
            result.append(x)
            if x.pre_context_id == None: break

        state.drop_out.set_sequence(result)

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
        if EntryF:         txt.extend(["  .entry:    ",         repr(self.entry)])
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
            else:                            txt.append("PreContext_%i, " % self.pre_context_id)

        if self.pattern_id != None and self.store_acceptance_f:        
            txt.append("StoreAcceptance %i, " % self.pattern_id)
        if self.store_acceptance_position_f: 
            txt.append("Position[Acceptance] = pos, ")

        return "".join(txt)

class Entry:
    def __init__(self, OriginList, ForwardF):
        self.__sequence    = None

        if ForwardF:
            self.__pre_context_fulfilled_set  = None
            self.__sequence                   = []
            for origin in OriginList:
                entry = ConditionalEntryAction(track_analysis.extract_pre_context_id(origin), 
                                               origin.state_machine_id)
                self.__sequence.append(entry)
                # If an unconditioned acceptance occurred, then no further consideration!
                # (Rest of acceptance candidates is dominated).
                if origin.pre_context_id == None: break
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
        txt = []
        if self.__pre_context_fulfilled_set != None:
            # (only possible in backward lexical analysis)
            if len(txt): txt.append("          ") 
            for x in self.__pre_context_fulfilled_set:
                txt.append("\npre context id %i fulfilled\n" % x)
        else:
            for x in self.__sequence:
                element = repr(x)
                if element == "": continue
                if len(txt): txt.append("             ") 
                txt.append(element + "\n")
            for x in self.__store_position_begin_of_post_context_id_set:
                if len(txt): txt.append("             ") 
                txt.append("Position[PostContext_%i] = pos\n" % x)

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
                .transition_n_since_positioning  # Positioning of the input pointer
                .pattern_id       # Goto this particular terminal

       are of interest.

       Special Case: if .transition_n_since_positioning == None and .post_context_id != -1
                     => restore post_context_position[.post_context_id]
    """
    def __init__(self):
        self.__sequence = []

    def __repr__(self):
        assert len(self.__sequence) != 0

        def write(txt, X):
            if   X.transition_n_since_positioning == None: 
                if X.post_context_id == -1:
                    txt.append("pos = Position[Acceptance]; ")
                else:
                    txt.append("pos = Position[PostContext_%i]; " % X.post_context_id)
            elif X.transition_n_since_positioning == -1:   txt.append("pos = lexeme_start + 1; ")
            elif X.transition_n_since_positioning == 0:    pass # This state is an acceptance state
            else:                           txt.append("pos -= %i; " % X.transition_n_since_positioning) 
            if   X.pattern_id == None:      txt.append("goto StoredAcceptance;")
            elif X.pattern_id == -1:        txt.append("goto Failure;")
            else:                           txt.append("goto Pattern%i;" % X.pattern_id)

        txt = []
        L = len(self.__sequence)
        for i, x in enumerate(self.__sequence):
            if len(txt) != 0: txt.append("             ")
            if x.pre_context_id == None: 
                write(txt, x)
            else: 
                txt.append("if pre_context_%i: " % x.pre_context_id)
                write(txt, x)
            if i != L - 1:
                txt.append("\n")

        return "".join(txt)

    def set_sequence(self, CommonTrace):
        """This function receives a 'common trace', that means that it receives (something)
           like a list of pairs (pre_context_id, AcceptanceTraceEntry) for every pre-
           context that ever appeared in any path for a given state.
        """
        assert len(CommonTrace) != 0
        for x in CommonTrace:
            assert isinstance(x, AcceptanceTraceEntry)
        self.__sequence = CommonTrace

    def get_sequence(self):
        return self.__sequence

