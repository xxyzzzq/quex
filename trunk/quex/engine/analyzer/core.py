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
            print "##DEBUG", state_index
            if state_index in [172]: print "##", state_index, acceptance_trace_list

            common = self.__horizontal_analysis(state, acceptance_trace_list)
            if state_index in [172]: print "##common:", common
            self.__vertical_analysis(state, common)

    def __iter__(self):
        for x in self.__state_db.values():
            yield x

    def __horizontal_analysis(self, state, TheAcceptanceTraceList):
        """A state may be reached via multiple paths. For each path there is 
           a separate AcceptanceTrace. Each AcceptanceTrace tells what has to
           happen in the state depending on the pre-contexts being fulfilled 
           or not (if there are even any pre-context patterns).

           This function computes a single object that indicates what has to
           happen in the current state based on the given list of acceptance
           traces. And, the two rule are simple:

             (1) If there is the slightest difference between the acceptances
                 of the acceptance traces, then the acceptance depends on the 
                 path.

                 -- all pre-context-ids must be the same
                 -- the precedence of the pre-context-ids must be the same

                 Note, that precedence is first of all subject to length
                 of the match, then it is subject to the pattern id.

             (2) For a given pre-context, if the positioning backwards differs
                 for one entry, or is undetermined, then the positions must be
                 stored by the related state and restored in the current state.
        """
        assert len(TheAcceptanceTraceList) != 0

        prototype = TheAcceptanceTraceList[0]
        remainder = islice(TheAcceptanceTraceList, 1, None)

        what about the precendence of checks in common drop out?

        # (1) Acceptance
        # The un-common pre-contexts are subject to 'store_acceptance' anyway.
        # For the common pre-contexts, if they do not appear with the same
        # precedence (due to length), then the whole state must rely on 'store_acceptance'.
        prototype_seq = map(lambda x: x.pre_context_id, prototype.get_sorted_sequence())
        for trace in remainder:
            seq = map(lambda x: x.pre_context_id, trace.get_sorted_sequence())
            if seq == prototype_seq: continue

            # Acceptance depends on path --> must be stored
            self.store_acceptance(TheAcceptanceTraceList)
            break

        else:
            # All traces have the same pre-context-ids and they are equal in precedence
            # It holds:  pre-context-id <---> acceptance (anyways)
            # except for: pre-context-id == -1   (begin of line)
            # and         pre-context-id == None (no pre context)
            prototype_acceptance_id = prototype.get(None).pattern_id
            for trace in remainder:
                entry = trace.get(None)
                if entry.pattern_id != prototype_acceptance_id:
                    self.store_acceptance_specific(TheAcceptanceTraceList, None)
                    break

            entry = prototype.get(-1)
            if entry is None:
                for trace in ifilter(lambda x: x.get(-1) is not None, remainder):
                    self.store_acceptance_specific(TheAcceptanceTraceList, -1)
            else:
                for trace in ifilter(lambda x: x.get(-1) is not None, remainder):
                    if trace.pattern_id != prototype_acceptance_id:
                        self.store_acceptance_specific(TheAcceptanceTraceList, -1)
                        break

        # (2) Positioning
        #     For positioning it is not necessary what the precedence is, only 
        #     (1) all pre-contexts are present
        #     (2) all have the same 'transition_n_since_positioning'
        #     (3) no 'transition_n_since_positioning' = None
        prototype_transition_n_since_positioning = prototype.get(None).transition_n_since_positioning
        if prototype_transition_n_since_positioning is None:
            self.store_position(TheAcceptanceTraceList)
            return 

        prototype_set = set(prototype_seq)
        for trace in remainder:
            pre_context_set = map(lambda x: x.pre_context_id, trace.get_sequence())
            if pre_context_set != prototype_set:
                self.store_position(TheAcceptanceTraceList)
                return

        # All have the same set of 
        for pre_context_id in prototype_set:
            if    trace.get(pre_context_id).transition_n_since_positioning \
               != prototype.get(pre_context_id).transition_n_since_positioning:
                self.store_position_specific(TheAcceptanceTraceList, pre_context_id)
    
    def store_acceptance_specific(self, TheAcceptanceTraceList, PreContextID):
        for entry in imap(lambda x: x.get(PreContextID), TheAcceptanceTraceList):
            if entry is None: continue
            self.__state_db[entry.accepting_state_index].entry.set_store_acceptance_f()
            state.drop_out.set_restore_acceptance_f(entry.pre_context_id)

    def store_acceptance(self, TheAcceptanceTraceList):
        for trace in TheAcceptanceTraceList:
            for x in trace:
                self.__state_db[x.accepting_state_index].entry.set_store_acceptance_f()
        state.drop_out.set_restore_acceptance_always()

    def store_position_specific(self, TheAcceptanceTraceList, PreContextID):
        for entry in imap(lambda x: x.get(PreContextID), TheAcceptanceTraceList):
            if entry is None: continue
            self.__state_db[entry.positioning_state_index].entry.set_store_position_f()
            state.drop_out.set_restore_position_f(x.pre_context_id)

    def store_position(self, TheAcceptanceTraceList):
        for trace in TheAcceptanceTraceList:
            for x in trace:
                self.__state_db[x.accepting_state_index].entry.set_store_acceptance_f()
        state.drop_out.set_restore_position_always()

    def __vertical_analysis(self, state, Common):
        """Takes a 'common' acceptance trace as a result from the horizontal 
           analysis and sorts and filters its elements. 
        """
        assert len(Common) != 0

        def __voidify(trace):
            for x in ifilter(lambda x: x.accepting_state_index != -1, trace):
                print "##voidify", x.accepting_state_index, x.positioning_state_index, x.pre_context_id
                self.store_acceptance(x.accepting_state_index, x.pre_context_id)
                self.store_position(x.positioning_state_index, x.pre_context_id)
            # Set a totally undetermined acceptance trace, that is:
            # restore acceptance and acceptance position
            state.drop_out.set_sequence([AcceptanceTraceEntry_Void])
            return

        trace = Common.values()
        if len(trace) == 1: 
            ## assert trace[0].pre_context_id is None
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
            if x.pre_context_id is None: break

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
        if self.pre_context_id is not None:
            if self.pre_context_id == -1:    txt.append("BOF, ")
            else:                            txt.append("PreContext_%i, " % self.pre_context_id)

        if self.pattern_id is not None and self.store_acceptance_f:        
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
            for origin in ifilter(lambda x: x.is_acceptance(), OriginList):
                entry = ConditionalEntryAction(track_analysis.extract_pre_context_id(origin), 
                                               origin.state_machine_id)
                self.__sequence.append(entry)
                # If an unconditioned acceptance occurred, then no further consideration!
                # (Rest of acceptance candidates is dominated).
                if origin.pre_context_id is None: break
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
        if self.__pre_context_fulfilled_set is not None:
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
        assert self__sequence is not None
        return self.__sequence

    def set_store_acceptance_f(self, PreContextID):
        for x in ifilter(lambda x: x.pre_context_id == PreContextID, self.__sequence): 
            x.store_acceptance_f = True
            return
        assert False, "PostContextID not mentioned in state"

    def set_store_position_f(self, PreContextID):
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
        assert self.__pre_context_fulfilled_set is not None
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

       Special Case: if .transition_n_since_positioning is None and .post_context_id != -1
                     => restore post_context_position[.post_context_id]
    """
    def __init__(self):
        self.__sequence = []

    def __repr__(self):
        assert len(self.__sequence) != 0

        def write(txt, X):
            if   X.transition_n_since_positioning is None: 
                if X.post_context_id == -1:
                    txt.append("pos = Position[Acceptance]; ")
                else:
                    txt.append("pos = Position[PostContext_%i]; " % X.post_context_id)
            elif X.transition_n_since_positioning == -1:   txt.append("pos = lexeme_start + 1; ")
            elif X.transition_n_since_positioning == 0:    pass # This state is an acceptance state
            else:                           txt.append("pos -= %i; " % X.transition_n_since_positioning) 
            if   X.pattern_id is None:      txt.append("goto StoredAcceptance;")
            elif X.pattern_id == -1:        txt.append("goto Failure;")
            else:                           txt.append("goto Pattern%i;" % X.pattern_id)

        txt = []
        L = len(self.__sequence)
        for i, x in enumerate(self.__sequence):
            if len(txt) != 0: txt.append("             ")
            if x.pre_context_id is None: 
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

