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

            common = self.analysis(state, acceptance_trace_list)
            if state_index in [172]: print "##common:", common

    def __iter__(self):
        for x in self.__state_db.values():
            yield x

    def analysis(self, state, TheAcceptanceTraceList):
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

                 ===========================================================
                 | Note, that precedence is first of all subject to length |
                 | of the match, then it is subject to the pattern id.     |
                 ===========================================================

             (2) For a given pre-context, if the positioning backwards differs
                 for one entry, or is undetermined, then the positions must be
                 stored by the related state and restored in the current state.
        """
        assert len(TheAcceptanceTraceList) != 0

        if analyze_uniformity(self, TheAcceptanceTraceList):
            return self.build_pre_determined_drop_out(TheAcceptanceTraceList)
        else:
            return self.build_not_pre_determined_drop_out(TheAcceptanceTraceList)

    def build_pre_determined_drop_out(self, TheAcceptanceTraceList):
        """Assume that analysis of the traces has shown that the acceptance
           of the state can be determined from the state machine structure
           before run-time. Then, this function enters the ball park.
           --------------------------------------------------------------------
           Still, the positioning needs to be checked. If for one acceptance
           there are either two paths or an undefined path length, then the
           triggering states must store the position and the drop-out relies
           on the stored acceptance position.
        """
        pass

    def build_not_pre_determined_drop_out(self, TheAcceptanceTraceList):
        """Assume that analysis of the traces has shown, that they are not
           uniform. In this case, the acceptance is determined at run-time
           and stored in the 'last_acceptance' variable. The entry objects
           of the triggering states need to be notified.
           --------------------------------------------------------------------
        """

    def analyze_positioning(self, TheAcceptanceTraceList):
        """Find the pattern for positioning in the traces. Returns a dictionary

           map: acceptance_id --> positioning info

           positioning info == None: positioning is void
        """
        result = {}
        for trace in TheAcceptanceTraceList:
            for condition in trace:
                transition_n = result.get(condition.pattern_id)
                if info is None:
                    result[condition.pattern_id] = condition.transition_n_since_positioning
                elif transition_n != condition.transition_n_since_positioning:
                    result[condition.pattern_id] = None
        return result

    def analyze_uniformity(self, TheAcceptanceTraceList):
        """Following cases cancel uniformity:

           (1) There is a pre-context that is not present in another trace.
           
           Assumed (1) does not hold than every trace has the same set of
           pre-contexts. 

           (2) The precedence of the pre-contexts differs.

           Assumed (2) does not hold then all traces check the pre-contexts
           with the same precedence (Precedence first depends on path-length, 
           then on pattern-id).

           (3) A pre-context that may accept more than one pattern, accepts
               different patterns. This is possible for the 'begin-of-line'
               pattern that may prefix multiple patterns, and the 'no-pre-context'
               of normal patterns.

           If the checks (1), (2), and (3) are passed negative, then the traces
           are indeed uniform. This means, that the drop-out does not have to
           rely on stored acceptances.

           RETURNS: True  -- uniform.
                    False -- not uniform.
        """
        prototype   = TheAcceptanceTraceList[0]
        id_sequence = prototype.get_priorized_pre_context_id_list()

        # Check (1) and (2)
        for trace in ifilter(lambda trace: id_sequence != trace.get_priorized_pre_context_id_list(),
                             islice(TheAcceptanceTraceList, 1, None):
            return False

        # If the function did not return yet, then (1) and (2) are negative.

        # Check (3)
        # Pre-Context: 'Begin-of-Line' and 'No-Pre-Context' may trigger
        #              different pattern_ids.

        # -- No Pre-Context (must be in every trace)
        acceptance_id = Prototype.get(None).pattern_id
        # Iterate over remainder (Prototype is not considered)
        for trace in ifilter(lambda trace: acceptance_id != trace[None].pattern_id, 
                             islice(TheAcceptanceTraceList, 1, None)):
            return False

        # -- Begin-of-Line (pre-context-id == -1)
        x = Prototype.get(-1)
        if x is not None:
            # According to (1) no other trace will have a Begin-of-Line pre-context
            pass
        else:
            # According to (1) every trace will contain 'begin-of-line' pre-context
            acceptance_id = x.pattern_id
            for trace in ifilter(lambda trace: trace[-1].pattern_id != acceptance_id,
                                 islice(TheAcceptanceTraceList, 1, None)):
                return False

        # Checks (1), (2), and (3) did not find anything 'bad' --> uniform.
        return True

    def analyse_acceptance(self, state, Prototype, UniformF, TheAcceptanceTraceList):
        # (1) Acceptance
        if not uniform_f:
            # If the pre-contexts and their precedences is not totally uniform, 
            # then the acceptance cannot be determined beforehand.
            self.handle_acceptance_void(state, TheAcceptanceTraceList)
            return

        # (*) All pre-context-ids are the same and have the same precedence

        # -- drop_out: There is a common precedence scheme, follow it.
        state.drop_out.set_precontext_precedence(prototype_id_seq)

        # It holds:   pre-context-id <-1:1-> acceptance (anyways)
        # except for: -1 (begin of line) or 'None' (no pre context)

        # -- drop_out:      if pattern_id differs, the acceptance must be restored
        # -- other entries: if pattern_id differs, the acceptance must be stored

        # 'None' -- no pre-context (must be defined for every trace)
        prototype_acceptance_id = Prototype.get(None).pattern_id
        # Iterate over remainder (Prototype is not considered)
        for trace in imap(lambda trace: trace[None].pattern_id != prototype_acceptance_id, 
                          islice(TheAcceptanceTraceList, 1, None)):
            # If there is one trace with a differing acceptance, then:
            self. handle_acceptance_void_specific(TheAcceptanceTraceList, None)
            break

        # '-1' -- begin of line (not necessarily present in every trace)
        x = Prototype.get(-1)
        if x is None:
            for trace in ifilter(lambda x: x.get(-1) is not None, 
                                 islice(TheAcceptanceTraceList, 1, None)):
                # If there is one trace with 'begin of line' condition
                self.handle_acceptance_void_specific(TheAcceptanceTraceList, -1)
                break
        else:
            prototype_acceptance_id = x.pattern_id
            for trace in ifilter(lambda trace: trace.get(-1) is None or trace[-1].pattern_id != prototype_acceptance_id,
                                 islice(TheAcceptanceTraceList, 1, None)):
                # If there is one trace with a different 'begin of line' condition
                self.handle_acceptance_void_specific(TheAcceptanceTraceList, -1)
                break

    def analyse_positioning(self, state, Prototype, PrototypeIDSet, UniformF, HomogenousF, TheAcceptanceTraceList):
        # If traces are not uniform, but homogenous and all have the transition_n_since_positioning
        # then the transition_n can still be determined.
        if UniformF:
            for pre_context_id in PrototypeIDSet:
                n = prototype.get(pre_context_id).transition_n_since_positioning
                # In the uniform case trace[pre_context_id] always works.
                for trace in ifilter(lambda trace: \
                                     n != trace[pre_context_id].transition_n_since_positioning, \
                                     TheAcceptanceTraceList):
                    self.handle_positioning_void_specific(TheAcceptanceTraceList, pre_context_id)
                    break
            return

        if not HomogenousF:
            self.handle_positioning_void(state, TheAcceptanceTraceList)
            return

        # Here: not uniform, but homogeneous.
        #       If for all cases the positioning is the same backwards, then
        #       it is determined. If one diverges, then it cannot be determined at run-time.
        # NOTE: trace[pre_context_id] works for all pre-contexts, since we are 'homogeneous'.
        n = prototype[None].transition_n_since_positioning
        if n is None:
            self.handle_positioning_void(TheAcceptanceTraceList)
            return

        for trace in TheAcceptanceTraceList:
            for condition in ifilter(lambda condition: n != condition.transition_n_since_positioning, trace):
                self.handle_positioning_void(state, TheAcceptanceTraceList)
                return

        # Precedence does not matter
        state.drop_out.set_positioning(n)
        return
    
    def handle_acceptance_void_specific(self, state, TheAcceptanceTraceList, PreContextID):
        """For the case of no-pre-context or begin-of-line pre-context the acceptance
           may differ (all other normal pre-contexts are related 1:1 with an acceptance).
        """
        assert PreContextID is None or PreContextID == -1
        for condition in imap(lambda trace: trace.get(PreContextID), TheAcceptanceTraceList):
            if condition is None: continue
            entry = self.__state_db[condition.accepting_state_index].entry
            x = entry.access(PreContextID)
            x.store_acceptance_id = condition.pattern_id

        state.dropout.set_terminal_id(None, PreContextID)

    def handle_acceptance_void(self, state, TheAcceptanceTraceList):
        """If the acceptance is void for a state, then all states that trigger
           acceptance in the past trace must store the acceptance, and the current
           state must restore it.  
        """
        for trace in TheAcceptanceTraceList:
            for condition in trace:
                state_index               = condition.accepting_state_index
                entry                     = self.__state_db[state_index].entry
                x = entry.access(condition.pre_context_id)
                x.store_acceptance_id = condition.pattern_id

        state.dropout.set_terminal_id(None)

    def handle_positioning_void_specific(self, state, TheAcceptanceTraceList, PreContextID):
        """If the positioning of the input pointer for a particular pre-context 
           cannot be determined beforehand, then the triggering states need to
           store the position, and the drop out handler of the current state
           needs restore the position in case of this pre-context.
        """
        for condition in imap(lambda trace: trace.get(PreContextID), TheAcceptanceTraceList):
            if condition is None: continue
            entry = self.__state_db[condition.accepting_state_index].entry
            x = entry.access(PreContextID)
            x.store_position_register = condition.post_context_id

        state.drop_out.set_positioning(Positioning, Register, PreContextID)

    def handle_positioning_void(self, state, TheAcceptanceTraceList):
        """If the positioning for a state is totally void then the current state needs
           to restore the stored position and all triggering states need to store 
           the input position that is to be restored.
        """
        for trace in TheAcceptanceTraceList:
            for condition in trace:
                state_index = trace.positioning_state_index
                entry                           = self.__state_db[state_index].entry
                x = entry.access(PreContextID)
                x.store_position_register = condition.post_context_id

        state.drop_out.set_positioning(Positioning, Register)

class AnalyzerState:
    def __init__(self, StateIndex, SM, ForwardF):
        assert type(StateIndex) in [int, long]
        assert type(ForwardF)   == bool

        state = SM.states[StateIndex]

        self.index          = StateIndex
        self.input          = Input(StateIndex == SM.init_state_index, ForwardF)
        self.entry          = Entry(state.origins(), ForwardF)
        self.transition_map = state.transitions().get_trigger_map()
        self.drop_out       = DropOut(state.origins())

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

class EntryElement:
    """Objects of this class tell what has to be done at entry of a state
       for a specific pre-context.

       .pre_context_id   PreContextID of concern. 

                         == None --> no pre-context (normal pattern)
                         == -1   --> pre-context 'begin-of-line'
                         >= 0    --> id of the pre-context state machine/flag

       .store_acceptance_id  AcceptanceID to be stored

                             == None --> nothing to be done      
                             == -1   --> store 'failure'         
                             >= 0    --> store acceptance id     

       .store_position_register  'Register' where the current position is to be stored. 
                                 == None  --> No position is to be stored.
                                 == -1    --> store in 'last_acceptance_position'
                                 >= 0     --> store in 'post-context-id' related position.
    """
    __slots__ = ("pre_context_id", "store_acceptance_id", "store_position_register")

    def __repr__(self):
        txt == []

        # Pre-Context
        if   self.pre_context_id is None: txt.append("Always,        ")
        elif self.pre_context_id == -1:   txt.append("BOF,           ")
        else:                             txt.append("PreContext %i, " % self.pre_context_id)

        # Store Acceptance (?)
        if   self.store_acceptance_id is None: txt.append("(nothing),              ")
        elif self.store_acceptance_id == -1:   txt.append("last_acceptance = FAIL, ")
        else:                                  txt.append("last_acceptance = %i,   " % self.store_acceptance_id)

        # Store Position (?)
        if   self.store_position_register is None: txt.append("(nothing);")
        elif self.store_position_register == -1:   txt.append("last_acceptance_pos = input_p;")
        else:                                      txt.append("post_context_pos[%i] = input_p;" % self.store_position_register)

class Entry:
    __slots__ = ("sequence", "pre_context_fulfilled_set")
    def __init__(self, OriginList, ForwardF):
        # By default, we do not do anything at state entry
        self.__sequence = []

        # For backward analysis (pre-context detection) some flag may have to be raised
        # as soon as a pre-context is fulfilled.
        if ForwardF:
            self.pre_context_fulfilled_set = None
        else:
            self.__pre_context_fulfilled_set = set([])
            for origin in ifilter(lambda origin: origin.is_acceptance(), OriginList):
                self.__pre_context_fulfilled_set.add(origin.state_machine_id)

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

class DropOutElement:
    """Objects of this class tell what has to be done at drop-out of a state
       for a specific pre-context.

       .pre_context_id   PreContextID of concern. 

                         == None --> no pre-context (normal pattern)
                         == -1   --> pre-context 'begin-of-line'
                         >= 0    --> id of the pre-context state machine/flag

       .terminal_id      Terminal to be targeted (what was accepted).

                         == None --> acceptance determined by stored value in 
                                     'last_acceptance', thus "goto *last_acceptance;"
                         == -1   --> goto terminal 'failure', nothing matched.
                         >= 0    --> goto terminal given by '.terminal_id'

       .positioning      Adaption of the input pointer, before the terminal is entered.

                         <= 0    --> input_p -= .positioning
                                     (This is possible if the number of transitions since
                                      acceptance is clear)
                         == None --> input_p = lexeme_start_p + 1
                                     (Case of 'failure'. This info is actually redundant.)
                         == 1    --> Restore the position given in '.position_register'
                         
        .restore_position_register  Registered where the position to be restored is located.

                            == None  --> Nothing (no position is to be stored.)
                                         Case: 'positioning != 1'
                            == -1    --> position register 'last_acceptance'
                            >= 0     --> position register related to a 'post-context-id'
    """
    __slots__ = ("pre_context_id", 
                 "terminal_id", 
                 "positioning", 
                 "restore_position_register")

    def __repr__(self):
        txt = []

        # Pre-Context
        if   self.pre_context_id is None: txt.append("Always,        ")
        elif self.pre_context_id == -1:   txt.append("BOF,           ")
        else:                             txt.append("PreContext %i, " % self.pre_context_id)

        # Positioning
        if self.positioning is None:      txt.append("input_p  = lexeme_start_p + 1,  ")
        elif self.positioning == 0:       txt.append("input_p (no change),            ")
        elif self.positioning <  0:       txt.append("input_p -= %i,                  " % self.positioning)
        else:           
            assert self.positioning == 1
            assert self.restore_position_register is not None
            if self.restore_position_register == -1:
                txt.append("input_p = post_context_pos[%i], " % self.restore_position_register)
            else:
                txt.append("input_p = last_acceptance_pos,  ")

        # Terminal 
        if   self.terminal_id is None:   txt.append("goto last_acceptance;")
        elif self.terminal_id == -1:     txt.append("goto Failure;")
        else:                            txt.append("goto TERMINAL_%i;" % self.terminal_id)

        return "".join(txt)

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

    def set_restore_acceptance(self):
    def set_restore_acceptance_always(self):
    def set_restore_position(self):
    def set_restore_position_always(self):

