"""
Track Analysis

(C) 2010-2011 Frank-Rene Schaefer
===============================================================================

The goal of track analysis is to reduce the run-time effort of the lexical
analyzer. In particular, acceptance and input position storages may be 
spared depending on the constitution of the state machine.

The result of the track analysis is a 'Trace' objects for each state. That is
at the end there is a dictionary:

            map:    state index --> Trace

The Trace object contains for each path through the state a TraceEntry object.
The TraceEntry tells what has to happen in a state, if there was only the
currently considered path. The consideration of effects from multiple path in a
state happens in upper layer, the 'core.py' module of this directory.

Further Info:   class TrackAnalysis 
                class Trace
                class TraceEntry

===============================================================================
"""
from   quex.engine.state_machine.state_core_info import E_PostContextIDs, E_AcceptanceIDs, E_PreContextIDs
from   quex.blackboard                           import E_StateIndices
from   quex.engine.misc.enum                     import Enum

from   collections import defaultdict
from   copy        import deepcopy
from   operator    import attrgetter
from   itertools   import ifilter
import sys

E_TransitionN = Enum("VOID", 
                     "LEXEME_START_PLUS_ONE",
                     "IRRELEVANT",
                     "_DEBUG_NAME_TransitionNs")

def do(SM):
    """Determines a database of Trace lists for each state.
    """
    return TrackAnalysis(SM).acceptance_trace_db

class TrackAnalysis:
    """The init function of this class walks down each possible path trough a
       given state machine. During this walk it determines all possible trace
       information. 
       
       The result of the process is presented by property 'acceptance_trace_db'. 
       It delivers for each state of the state machine a trace object that maps:

                   state index --> object of class Trace
       
       The acceptance_trace_db is basically the accumulated trace information 
       which is cleaned of auxiliary information from the analysis process.
    """

    def __init__(self, SM):
        """SM -- state machine to be investigated."""
        self.sm = SM

        # -- Determined Set of 'Loop States'.
        #
        #    Collect states that are part of a loop in the state machine.  If a
        #    path from state A to state B contains one of those states, then the
        #    number of transitions that appear between A and B can only be
        #    determined at run-time.
        #
        #    set of state indices that are part of a loop.
        #
        self.loop_state_set = set([])
        #    NOTE: The investigation about loop states must be done **before**
        #          the analysis of the acceptance traces. The acceptance trace
        #          analysis requires the loop state set to be complete!
        self.__loop_search_done_set = set()
        self.__loop_search(self.sm.init_state_index, [])

        # -- Collect Trace Information
        # 
        #    map:  state_index  --> list of Trace objects.
        #
        self.__map_state_to_trace = dict([(i, []) for i in self.sm.states.iterkeys()])
        self.__trace_walk(self.sm.init_state_index, 
                          path             = [], 
                          acceptance_trace = Trace(self.sm.init_state_index))

        # For further treatment the storage informations are not relevant
        for trace_list in self.__map_state_to_trace.itervalues():
            for trace in trace_list:
                trace.delete_non_accepting_traces()

    @property
    def acceptance_trace_db(self):
        """RETURNS: A dictionary that maps 

                    state index --> object of class Trace

           All auxiliary trace objects for positioning have been deleted at this 
           point in time. So, the traces concern only acceptance information.
        """
        return self.__map_state_to_trace

    def __loop_search(self, StateIndex, path):
        """Determine the indices of states that are part of a loop. Whenever
           such a state appears in a path from one state A to another state B, 
           then the number of transitions from A to B cannot be determined 
           from the state machine itself.

           Recursion Terminal: When a state has no target state that has not
                               yet been handled in the path. This is implemented
                               int the loop itself.
        """
        # if StateIndex in path: return

        # (1) Add current state index to path
        path.append(StateIndex)

        state = self.sm.states[StateIndex]

        # (2) Iterate over all target states
        for state_index in state.transitions().get_target_state_index_list():
            if state_index in self.__loop_search_done_set:
                continue
            elif state_index in path: 
                # Mark all states that are part of a loop. The length of a path that 
                # contains such a state can only be determined at run-time.
                idx = path.index(StateIndex)
                self.loop_state_set.update(path[idx:])
                continue # Do not dive into done states

            self.__loop_search(state_index, path)

        # (3) Remove current state index --> path is as before
        x = path.pop()
        self.__loop_search_done_set.add(StateIndex)
        assert x == StateIndex

    def __trace_walk(self, StateIndex, path, acceptance_trace):
        """StateIndex -- current state
           path       -- path from init state to current state (state index list)

           last_acceptance_i -- index in 'path' of the last acceptance state. 
                                path[last_acceptance_i] == state index of 
                                last acceptance state.

           last_post_context_i_db[k] -- index in 'path' of the last state where post context 
                                        'k' begins. 
                                        path[last_post_context_i_db[k] == state index 
                                        of last state where post context k begins.

           Recursion Terminal: When state has no target state that has not yet been
                               handled in the 'path'.
        """
        # (1) Add current state to path
        path.append(StateIndex)

        # (2) Update the information about the 'trace of acceptances'
        acceptance_trace.update(self, path) 

        # (3) Mark the current state with its acceptance trace
        #     NOTE: When this function is called, acceptance_trace is already
        #           an independent object, i.e. constructed or deepcopy()-ed.
        if     self.__map_state_to_trace.has_key(StateIndex):
            if acceptance_trace in self.__map_state_to_trace[StateIndex]:
                # If a state has been analyzed and we pass it a second time:
                # If the acceptance trace is already in there, we do not need 
                # further investigations.
                #x = path.pop()
                #assert x == StateIndex
                #return
                pass
        
        # (4) Recurse to all (undone) target states. 
        for target_index in self.sm.states[StateIndex].transitions().get_target_state_index_list():
            # Do not dive into done states / prevents recursion along loops.
            if target_index in path: continue 
            self.__trace_walk(target_index, path, deepcopy(acceptance_trace))

        self.__map_state_to_trace[StateIndex].append(acceptance_trace)

        # (5) Remove current state index --> path is as before
        x = path.pop()
        assert x == StateIndex

class Trace(object):
    """For one particular STATE that is reached via one particular PATH an
       Trace accumulates information about what pattern 'ACCEPTS' and where the
       INPUT POSITION is to be placed.

       This behavior may depend on pre-contexts being fulfilled.

       In other words, an Trace of a state provides information about what
       pattern would be accepted and what the input positioning should be if
       the current path was the only path to the state.

       The acceptance information is **priorized**. That means, that it is
       important in what order the pre-contexts are checked. 

       Example:

       ( 0 )----->(( 1 ))----->( 2 )----->(( 3 ))----->( 4 )------>( 5 ) ....
                   8 wins                 pre 4 -> 5 wins                    
                                          pre 3 -> 7 wins

       Trace-s for each state:

       State 0: has no acceptance trace, only '(no pre-context, failure)'.
       State 1: (pattern 8 wins, input position = current)
       State 2: (pattern 8 wins, input position = current - 1)
       State 3: (if pre context 4 fulfilled: 5 wins, input position = current)
                (if pre context 3 fulfilled: 7 wins, input position = current)
                (else,                       8 wins, input position = current - 2)
       State 4: (if pre context 4 fulfilled: 5 wins, input position = current - 1)
                (if pre context 3 fulfilled: 7 wins, input position = current - 1)
                (else,                       8 wins, input position = current - 3)
       ...
    """
    __slots__ = ("__trace_db", "__last_transition_n_to_acceptance")

    def __init__(self, InitStateIndex):
        self.__trace_db = { 
            E_AcceptanceIDs.FAILURE: 
                  TraceEntry(PreContextID                 = E_PreContextIDs.NONE, 
                             PatternID                    = E_AcceptanceIDs.FAILURE, 
                             MinTransitionN_ToAcceptance  = 0,
                             AcceptingStateIndex          = InitStateIndex, 
                             TransitionN_SincePositioning = E_TransitionN.LEXEME_START_PLUS_ONE,              
                             PositioningStateIndex        = E_StateIndices.NONE, 
                             PostContextID                = E_PostContextIDs.NONE),
        }
        self.__last_transition_n_to_acceptance = 0

    def __len__(self):
        return len(self.__trace_db)

    def update(self, track_info, Path):
        # It is essential for a meaningful accumulation of the match information
        # that the entries are accumulated from the begin of a path towards its 
        # end. Otherwise, the 'longest match' cannot be applied by overwriting
        # existing entries.
        assert abs(self.__last_transition_n_to_acceptance) < len(Path)
        self.__last_transition_n_to_acceptance = len(Path)

        # Last element of the path is the index of the current state
        StateIndex        = Path[-1]
        CurrentPathLength = len(Path)
        Origins           = track_info.sm.states[StateIndex].origins()

        # (*) Update all path related Info
        if StateIndex in track_info.loop_state_set:
            # -- Touching a loop ...
            #    => The number of transitions starting from the current state cannot 
            #       be determined by the number of state transitions. 
            #    => Positioning becomes 'void'
            operation = lambda transition_n: E_TransitionN.VOID
        else:
            # -- One transition, one character ...
            #    => Increment count of transitions by '1'.
            operation = lambda transition_n: transition_n + 1

        # Loop controlled by 'operation'
        for entry in self.__trace_db.itervalues():
            # 'lexeme_start_p + 1', 'void' --> are not updated
            if     entry.transition_n_since_positioning != E_TransitionN.LEXEME_START_PLUS_ONE \
               and entry.transition_n_since_positioning != E_TransitionN.VOID:
                entry.transition_n_since_positioning = operation(entry.transition_n_since_positioning)

        for origin in Origins:
            pre_context_id  = extract_pre_context_id(origin)
            pattern_id      = origin.state_machine_id
            post_context_id = origin.post_context_id()

            # (1) Acceptance:
            #     -- dominates any acceptance of same pre-context with 
            #        'transition_n_since_positioning != 0'
            # (1.1) No Position Restore (normal pattern)
            # (1.2) With Position Restore (end of post-context)
            #         -- dominates any acceptance of same pre-context with 
            #            'transition_n_since_positioning != 0'
            #         -- turn position store object in trace into an 
            #            accepting trace (accepting_state_index != VOID).
            # (2) Non-Acceptance:
            # (2.1) Store input position
            #         -- Enter in database: store position info object
            # (2.2) Non input position storage
            #         -- Unimportant
            if origin.is_acceptance():
                if not self.__sift(StateIndex, origin): 
                    continue
                if origin.post_context_id() != E_PostContextIDs.NONE:  # Restore --> adapt the 'store trace'
                    self.__trace_db[pattern_id].pre_context_id                 = pre_context_id
                    self.__trace_db[pattern_id].accepting_state_index          = StateIndex
                    self.__trace_db[pattern_id].min_transition_n_to_acceptance = CurrentPathLength
                    continue
                accepting_state_index          = StateIndex
                min_transition_n_to_acceptance = CurrentPathLength
            else:
                if not origin.store_input_position_f(): continue
                pre_context_id                 = E_PreContextIDs.NONE
                accepting_state_index          = E_StateIndices.VOID
                min_transition_n_to_acceptance = E_TransitionN.VOID

            # Add entry to the Database 
            self.__trace_db[pattern_id] = \
                    TraceEntry(pre_context_id, 
                               pattern_id,
                               MinTransitionN_ToAcceptance  = min_transition_n_to_acceptance,
                               AcceptingStateIndex          = accepting_state_index, 
                               TransitionN_SincePositioning = 0,
                               PositioningStateIndex        = StateIndex, 
                               PostContextID                = post_context_id)

        assert len(self.__trace_db) >= 1

    def __sift(self, StateIndex, Origin):
        """StateIndex -- index of the current state.
           Origin     -- information about what happens in the current state.

           This functions sifts out elements in the trace of the current path
           which are dominated by the influence of the Origin. On the other
           hand, if the Origin contains information which is dominated by 
           existing traces it is returned 'False' which indicates that 
           the origin does not need to be considered further.

           The origin carries information about acceptances of patterns and 
           storage of input positions. An unconditional acceptance means,
           that it does not depend on any pre-context of any kind. 

           RETURNS:
               True  -- Origin is subject to further treatment.
               False -- Origin is dominated by other content of the trace.
        """
        assert Origin.is_acceptance()
        ThePatternID = Origin.state_machine_id

        # NOTE: There are also traces, which are only 'position storage infos'.
        #       Those have accepting state index == VOID.
        if Origin.is_unconditional_acceptance():
            # Abolish:
            # -- all previous traces (accepting_state_index != StateIndex)
            # -- traces of same state, if they are dominated (pattern_id > ThePatternID)
            for entry in ifilter(lambda x: x.accepting_state_index != E_StateIndices.VOID, 
                                 self.__trace_db.values()):
                if   entry.accepting_state_index != StateIndex:
                    del self.__trace_db[entry.pattern_id]
                elif entry.pattern_id == E_AcceptanceIDs.FAILURE or entry.pattern_id >= ThePatternID:
                    del self.__trace_db[entry.pattern_id]
                elif entry.pre_context_id == E_PreContextIDs.NONE:
                    return False
        else:
            # Abolish ONLY TRACES WITH THE SAME PRE-CONTEXT ID:
            ThePreContextID = extract_pre_context_id(Origin)
            # -- all previous traces (accepting_state_index != StateIndex)
            # -- traces of same state, if they are dominated (pattern_id > ThePatternID)
            for entry in ifilter(lambda x:     x.pre_context_id        == ThePreContextID \
                                           and x.accepting_state_index != E_StateIndices.VOID,
                                 self.__trace_db.values()):
                if entry.accepting_state_index != StateIndex:
                    del self.__trace_db[entry.pattern_id]
                elif entry.pattern_id >= ThePatternID:
                    del self.__trace_db[entry.pattern_id]
                else:
                    return False

        return True

    def delete_non_accepting_traces(self):
        for pattern_id in self.__trace_db.keys():
            if self.__trace_db[pattern_id].accepting_state_index == E_StateIndices.VOID:
                del self.__trace_db[pattern_id]
    
    def __getitem__(self, PreContextID):
        return self.get(PreContextID)

    def get(self, PreContextID):
        for entry in self.__trace_db.itervalues():
            if entry.pre_context_id == PreContextID: return entry
        return None

    def get_priorized_list(self):
        def my_key(X):
            # Failure always sorts to the bottom ...
            if X[1].pattern_id == E_AcceptanceIDs.FAILURE: return (sys.maxint, sys.maxint)
            # Longest pattern sort on top
            # Lowest pattern ids sort on top
            return (- X[1].min_transition_n_to_acceptance, X[1].pattern_id)

        result = map(lambda x: (x[1].pre_context_id, x[1]), self.__trace_db.iteritems())
        result.sort(key=my_key)
        return result

    def get_priorized_pre_context_id_list(self):
        return map(lambda x: x[0], self.get_priorized_list())

    def __repr__(self):
        txt = []
        for x in self.__trace_db.itervalues():
            txt.append(repr(x))
        return "".join(txt)

    def __eq__(self, Other):
        """Compare two acceptance trace objects. Note, that __last_transition_n_to_acceptance
           is only for debug purposes.
        """
        if set(self.__trace_db.iterkeys()) != set(Other.__trace_db.iterkeys()):
            return False
        for pattern_id, trace in self.__trace_db.iteritems():
            if not trace.is_equal(Other.__trace_db[pattern_id]):
                return False
        return True

    def __iter__(self):
        for x in self.__trace_db.itervalues():
            yield x

class TraceEntry(object):
    __slots__ = ("pre_context_id", 
                 "pattern_id", 
                 "transition_n_since_positioning", 
                 "min_transition_n_to_acceptance", 
                 "accepting_state_index", 
                 "positioning_state_index",
                 "positioning_state_successor_index",
                 "post_context_id")

    def __init__(self, PreContextID, PatternID, 
                 MinTransitionN_ToAcceptance, 
                 AcceptingStateIndex, 
                 TransitionN_SincePositioning, 
                 PositioningStateIndex, 
                 PostContextID):
        """PreContextID  --
           PatternID     -- 
           TransitionN_SincePositioning -- Number of transitions since the 'positioning'
                                           state has been reached.
           AcceptingStateIndex -- Index of the state that accepts the mentioned
                                  pattern. This is used when we need to inform
                                  the state that it needs to store the acceptance
                                  information.
           PositioningStateIndex -- Index of the state that positions the input pointer
                                    in the case of acceptance. This is usually the 
                                    acceptance state. For post-context patterns it is 
                                    the state where the post context begins.

           PostContextID   = -1  acceptance has nothing to do with post context
                          != -1  acceptance is related to post context with given id.
        """
        self.pre_context_id  = PreContextID
        self.pattern_id      = PatternID
        self.transition_n_since_positioning = TransitionN_SincePositioning
        # Transitions To Acceptance 
        # 
        # This basically means how many transitions happened since the init
        # state when the pattern was accepted. For non-post-context patterns
        # this is the lexeme length; For post-context patterns this is the 
        # length of the core pattern plus the length of the post context.
        #
        #  N >= 0 :   distance(init state, acceptance) == exactly 'N' characters
        #  N <  0 :   distance(init state, acceptance) >= 'N' characters
        self.min_transition_n_to_acceptance = MinTransitionN_ToAcceptance

        # 
        self.accepting_state_index             = AcceptingStateIndex
        self.positioning_state_index           = PositioningStateIndex
        self.positioning_state_successor_index = None
        #
        self.post_context_id         = PostContextID

    def is_equal(self, Other):
        if   self.pre_context_id                    != Other.pre_context_id:                    return False
        elif self.pattern_id                        != Other.pattern_id:                        return False
        elif self.transition_n_since_positioning    != Other.transition_n_since_positioning:    return False
        elif self.min_transition_n_to_acceptance    != Other.min_transition_n_to_acceptance:    return False
        elif self.accepting_state_index             != Other.accepting_state_index:             return False
        elif self.positioning_state_index           != Other.positioning_state_index:           return False
        elif self.positioning_state_successor_index != Other.positioning_state_successor_index: return False
        elif self.post_context_id                   != Other.post_context_id:                   return False
        return True

    def __repr__(self):
        txt = ["---\n"]
        txt.append("    .pre_context_id                 = %s\n" % repr(self.pre_context_id))
        txt.append("    .pattern_id                     = %s\n" % repr(self.pattern_id))
        txt.append("    .transition_n_since_positioning = %s\n" % repr(self.transition_n_since_positioning))
        txt.append("    .min_transition_n_to_acceptance     = %s\n" % repr(self.min_transition_n_to_acceptance))
        txt.append("    .accepting_state_index          = %s\n" % repr(self.accepting_state_index))
        txt.append("    .positioning_state_index        = %s\n" % repr(self.positioning_state_index))
        txt.append("    .post_context_id                = %s\n" % repr(self.post_context_id))
        return "".join(txt)

TraceEntry_Void = TraceEntry(PreContextID                 = E_PreContextIDs.NONE, 
                             PatternID                    = E_AcceptanceIDs.VOID, 
                             MinTransitionN_ToAcceptance  = 0,
                             AcceptingStateIndex          = E_StateIndices.VOID,  
                             TransitionN_SincePositioning = E_TransitionN.VOID, 
                             PositioningStateIndex        = E_StateIndices.NONE, 
                             PostContextID                = E_PostContextIDs.NONE)

def extract_pre_context_id(Origin):
    """This function basically describes how pre-context-ids and 
       'begin-of-line' pre-context are expressed by an integer.
    """
    if   Origin.pre_context_begin_of_line_f(): return E_PreContextIDs.BEGIN_OF_LINE
    elif Origin.pre_context_id() == -1:        return E_PreContextIDs.NONE
    else:                                      return Origin.pre_context_id()

