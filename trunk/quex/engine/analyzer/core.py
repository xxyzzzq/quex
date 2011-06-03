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

            ## print "##DEBUG", state_index
            ## if state_index in [172]: print "##", state_index, acceptance_trace_list

            state.drop_out = self.get_drop_out_object(state, acceptance_trace_list)
            ## if state_index in [172]: print "##common:", common

    def __iter__(self):
        for x in self.__state_db.values():
            yield x

    def get_drop_out_object(self, state, TheAcceptanceTraceList):
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

        checker = []  # map: pre-context-flag --> acceptance_id
        router  = []  # map: acceptance_id    --> (positioning, 'goto terminal_id')

        # Acceptance Detector
        if analyze_uniformity(self, TheAcceptanceTraceList):
            # Use one trace as prototype to generate the mapping of 
            # pre-context flag vs. acceptance.
            prototype = TheAcceptanceTraceList[0]
            checker   = map(lambda x: DropOutCheckerElement(x.pre_context_id, x.pattern_id), prototype)
        else:
            # 'checker' empty 
            # => Last acceptance is to be restored from past
            # All triggering states must store the acceptance
            for trace in TheAcceptanceTraceList:
                for element in trace:
                    entry = self.__state_db[element.state_index].entry
                    entry.accepter[element.pre_context_id] = element.pattern_id

        # Terminal Router
        for pattern_id, info in analyze_positioning(TheAcceptanceTraceList).iteritems():

            router.append(DropOutRouterElement(info.transition_n_since_positioning, pattern_id))

            if info.transition_n_since_positioning is not None: continue

            # Inform all triggering states that the position needs to be stored
            for element in info.trace_element_list:
                entry = self.__state_db[element.positioning_state_index].entry
                entry.positioner[element.pre_context_id] = element.post_context_id

        drop_out.checker = checker
        drop_out.router  = router
        return drop_out


    def analyze_positioning(self, TheAcceptanceTraceList):
        """Find the pattern for positioning in the traces. Returns a dictionary

           map: acceptance_id --> positioning info

           positioning info == None: positioning is void
        """
        class ResultElement:
            def __init__(self, X, Y):
                self.transition_n_since_positioning = X
                self.trace_element_list             = [Y]

        result = {}
        # If the positioning differs for one element in the trace list, or one
        # element has undetermined positioning, then the acceptance relates to 
        # undetermined positioning.
        for trace in TheAcceptanceTraceList:
            for element in trace:
                entry = result.get(element.pattern_id)
                if info is None:
                    result[element.pattern_id] = ResultElement(element.transition_n_since_positioning,
                                                               element.post_context_id)
                elif entry.transition_n_since_positioning != element.transition_n_since_positioning:
                    entry.transition_n_since_positioning = None
                    entry.trace_element_list.append(element)

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

class AnalyzerState:
    def __init__(self, StateIndex, SM, ForwardF):
        assert type(StateIndex) in [int, long]
        assert type(ForwardF)   == bool

        state = SM.states[StateIndex]

        self.index          = StateIndex
        self.input          = Input(StateIndex == SM.init_state_index, ForwardF)
        self.entry          = Entry(state.origins(), ForwardF)
        self.transition_map = state.transitions().get_trigger_map()
        self.drop_out       = None # See: Analyzer.make_drop_out(...)

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

class Entry(object):
    """An entry has potentially two tasks:
    
          (1) storing information about an acceptance. 
          (2) storing information about positioning.

       Both are pre-context dependent. 
       
       (*) Accepter:

       For the first task mentioned, some 'accepter' sequence needs to be applied, 
       such as

                /* 'Accepter' */
                if     ( pre_context_5_f ) { last_acceptance_id = 15; }
                else if( pre_context_7_f ) { last_acceptance_id = 18; }
                else if( pre_context_9_f ) { last_acceptance_id = 21; }
                else                       { last_acceptance_id = 32; }

       where the last line handles the case that no-pre-context has to be handled. Note,
       that the list is:

                -- sorted by pattern_id (acceptance_id) since this denotes the
                   precedence of the patterns.

                -- it is exclusive, because only one pattern can win.

       The data structure that describes this is the dictionary '.accepter' that maps:

               .accepter:    pre-context-id --> acceptance_id 

       Where 'acceptance_id' >= 0     means a 'real' acceptance_id is to be stored
                             is None  means, that nothing is to be done.

       The sequence is solely determined by the acceptance id, so no further 
       information must be available. At code-construction time the sorted
       list may be used, i.e.
          
               for x in isorted(entry.accepter.iteritems(), key=itemgetter(1)):
                   ...
                   if pre_context_id is None: break

       To facilitate this, the function '.get_accepter' delivers a sorted list
       of accepting entries.

       (*) Positioner

       For the positioning this is different. Depending on the post-context any
       pre-context may later on win. Thus, 

                /* 'Positioner' */
                if( pre_context_5_f ) { last_acceptance_pos   = input_p; }
                if( pre_context_7_f ) { position_register[23] = input_p; }
                if( pre_context_9_f ) { last_acceptance_pos   = input_p; }
                last_acceptance_pos = input_p; 
       
       The list is not sorted and it is not exclusive, line 1 and 2 are redundant
       since the same job is done by line 4 for both in any case. The information
       about position storage is done by a dictionary '.positioner' which maps:

                .positioner:  post-context-id  --> list of pre-context-ids

       Where "post-context-id == None" stands for no post-context (normal pattern)
       and a "None" in the pre-context-id list stands for the unconditional case.

       (*) Backward Lexing

       Backward lexing has the task to find out whether a pre-context is fulfilled.
       But it does not stop, since multiple pre-contexts may still be fulfilled.
       Thus, the set of fulfilled pre-contexts is stored in 

                    ".pre_context_fulfilled_set"

       This list can be determined beforehand from the origin list. For forward lexical 
       analyzis, or when there is no pre-context fulfilled this field must be None. 
       For backward analyzis the fields '.accepter' and '.positioner' must be None. 
    """
    __slots__ = (".accepter", ".positioner", "pre_context_fulfilled_set", "debug_origin_list")
    def __init__(self, OriginList, ForwardF):
        if ForwardF:
            # By default, we do not do store anything about acceptance at state entry
            self.accepter   = {}
            self.positioner = {}
            self.pre_context_fulfilled_set = None
        else:
            # By default, we do not do store anything about acceptance at state entry
            self.accepter   = None
            self.positioner = None
            self.pre_context_fulfilled_set = set([])
            for origin in ifilter(lambda origin: origin.is_acceptance(), OriginList):
                self.pre_context_fulfilled_set.add(origin.state_machine_id)
            if len(self.pre_context_fulfilled_set) == 0:
                self.pre_context_fulfilled_set = None

        # As a reference for some asserts
        self.debug_origin_list = OriginList

    def get_accepter(self):
        """Returns information about the acceptance sequence. Lines that are dominated
           by the unconditional pre-context are filtered out.
        """
        result = []
        for pre_context_id, acceptance_id in isorted(self.accepter.iteritems(), key=itemgetter(1)):
            result.append((pre_context_id, acceptance_id))   
            if pre_context_id is None: break
        return result

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

class DropOut:
    """The general drop-out of a state has the following two 'sub-tasks'

                /* (1) Check pre-contexts to determine acceptance */
                if     ( pre_context_4_f ) acceptance = 26;
                else if( pre_context_3_f ) acceptance = 45;
                else if( pre_context_8_f ) acceptance = 2;
                else                       acceptance = last_acceptance;

                /* (2) Route to terminal / position input pointer. */
                switch( acceptance ) {
                case 2:  input_p -= 10; goto TERMINAL_2;
                case 15: input_p  = post_context_position[4]; goto TERMINAL_15;
                case 26: input_p  = post_context_position[3]; goto TERMINAL_26;
                case 45: input_p  = last_acceptance_position; goto TERMINAL_45;
                }

       The first sub-task is described by the member '.checker' which is a list
       of objects of class 'DropOut_CheckerElement'. An empty list means that
       there is no check and the acceptance has to be restored from 'last_acceptance'.
       
       The second sub-task is described by member '.router' which is a list of 
       objects of class 'DropOut_RouterElement'.

       The exact content of both lists is determined by analysis of the acceptance
       trances.
    """
    __slots__ = (".checker", ".router")

    def __init__(self):
        self.checker = []
        self.router  = []

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

class DropOut_CheckerElement(object):
    """Objects of this class shall describe a check sequence such as

            if     ( pre_condition_5_f ) last_acceptance = 34;
            else if( pre_condition_7_f ) last_acceptance = 67;
            else if( pre_condition_9_f ) last_acceptance = 31;
            else                         last_acceptance = 11;

       by a list such as [(5, 34), (7, 67), (9, 31), (None, 11)]
    
       The values for .pre_context_id and .acceptance_id are carry the 
       following meaning:

       .pre_context_id   PreContextID of concern. 

                         == None --> no pre-context (normal pattern)
                         == -1   --> pre-context 'begin-of-line'
                         >= 0    --> id of the pre-context state machine/flag

       .acceptance_id    Terminal to be targeted (what was accepted).

                         == None --> acceptance determined by stored value in 
                                     'last_acceptance', thus "goto *last_acceptance;"
                         == -1   --> goto terminal 'failure', nothing matched.
                         >= 0    --> goto terminal given by '.terminal_id'

    """
    __slots__ = ("pre_context_id", "acceptance_id") 
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

class DropOut_RouterElement(object):
    """Objects of this class shall be elements to build a router to the terminal
       based on the setting 'last_acceptance', i.e.

            switch( last_acceptance ) {
                case  45: input_p -= 3;                   goto TERMINAL_45;
                case  43:                                 goto TERMINAL_43;
                case  41: input_p -= 2;                   goto TERMINAL_41;
                case  33: input_p = lexeme_start_p - 1;   goto TERMINAL_33;
                case  22: input_p = position_register[2]; goto TERMINAL_22;
            }

       That means, the 'router' actually only tells how the positioning has to happen
       dependent on the acceptance. Then it goes to the action of the matching pattern.
       Following elements are provided:

        .acceptance_id    Terminal to be targeted (what was accepted).

                         == None --> acceptance determined by stored value in 
                                     'last_acceptance', thus "goto *last_acceptance;"
                         == -1   --> goto terminal 'failure', nothing matched.
                         >= 0    --> goto terminal given by '.terminal_id'

        .positioning      Adaption of the input pointer, before the terminal is entered.

                         <= 0    --> input_p -= | .positioning | 
                                     (This is possible if the number of transitions since
                                      acceptance is determined beforehand)
                         == None --> input_p = lexeme_start_p + 1
                                     (Case of 'failure'. This info is actually redundant.)
                         == 1    --> Restore the position given in '.position_register'
                         
        .restore_position_register  Registered where the position to be restored is located.

                            == None  --> Nothing (no position is to be stored.)
                                         Case: 'positioning != 1'
                            == -1    --> position register 'last_acceptance'
                            >= 0     --> position register related to a 'post-context-id'
    """
    __slots__ = ("acceptance_id", "positioning", "restore_position_register")

