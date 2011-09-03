"""
Track Analysis

(C) 2010-2011 Frank-Rene Schaefer
===============================================================================

The goal of track analysis is to reduce the run-time effort of the lexical
analyzer. In particular, acceptance and input position storages may be 
spared depending on the constitution of the state machine.

The result of the track analysis is a list of 'Trace' objects for each state. 
That is at the end there is a dictionary:

            map:    state index --> list of Trace objects.

A Trace object contains for one path through a state a set of TraceEntry 
objects. The set of TraceEntry-s tells what has to happen in a state, if 
there was only the currently considered path.

The consideration of effects from multiple path in a state happens in upper
layer: the 'core.py' module of this directory.

Further Info:   class TrackAnalysis 
                class Trace
                class TraceEntry

-------------------------------------------------------------------------------
EXAMPLE:

            (0)--- a --->(1)--- b --->(2)--- c --->(3)
                           A12                       A3/Restore7
                           Store7
                           A5

The annotations originate from states that were combined during the
construction of a single state machine from multiple pattern detectors.
For state 0, it can only be said that, in case of drop out the 
analyzer needs to notify 'Failure'. 

       State 0 --> [ TraceEntry(Failure) ]

State 1 accepts pattern 12 and 5, pattern 5, though has precedence (lower
pattern id). Further the input position for post-context 7 needs to be stored.

       State 1 --> [ TraceEntry(Accept Pattern 5), 
                     TraceEntry(Store Input Position in '7') ]

If the state machine drops out in State 2, then the last acceptance is
restored which was pattern 5. It lies now one position backwards. So
the input position needs to be decremented by one.

       State 2 --> [ TraceEntry(Accept Pattern 5, input_p -= 1) ]

In state 3, finally pattern 3 is accepted. However, it is a post-context
so that the input position needs to be set to what was stored in '7'. 
Since the distance from storage to restore can be determined from the
number of transitions, the adaption of the input position can happen
without actual storing of input positions:

       State 3 --> [ TraceEntry(Accept Pattern 7, input_p -= 2) ]

===============================================================================
"""
from   quex.blackboard        import E_StateIndices, E_PostContextIDs, E_AcceptanceIDs, E_PreContextIDs, E_TransitionN
from   quex.engine.misc.enum  import Enum

from   collections import defaultdict
from   copy        import deepcopy
from   operator    import attrgetter
from   itertools   import ifilter
import sys

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

                   state index --> list of Trace objects
       
       The acceptance_trace_db is basically the accumulated trace information 
       which is cleaned of auxiliary information from the analysis process.
    """

    def __init__(self, SM):
        """SM -- state machine to be investigated."""
        self.sm = SM

        # (*) Determined Set of 'Loop States'.
        #
        #    Collect states that are part of a loop in the state machine.  If a
        #    path from state A to state B contains one of those states, then the
        #    number of transitions that appear between A and B can only be
        #    determined at run-time.
        #
        #    set of state indices that are part of a loop.
        #
        self.__loop_state_set = set([])
        # NOTE: The investigation about loop states must be done **before** the
        #       analysis of traces. The trace analysis requires the loop state set!
        self.__loop_search_done_set = set()
        self.__loop_search(self.sm.init_state_index, [])

        # (*) Collect Trace Information
        # 
        #    map:  state_index  --> list of Trace objects.
        #
        self.__map_state_to_trace = dict([(i, []) for i in self.sm.states.iterkeys()])
        self.__trace_walk(self.sm.init_state_index, 
                          path  = [], 
                          trace = Trace(self.sm.init_state_index))

        # (*) Clean-Up
        # 
        #    Now, for the outer user only the traces are relevant which contain 
        #    information about acceptances.
        for trace_list in self.__map_state_to_trace.itervalues():
            for trace in trace_list:
                trace.delete_non_accepting_traces()

    @property
    def loop_state_set(self):
        """A set of indices of those states which are part of a loop 
           in the given state machine. Whenever such a state appears
           on a path, the length of the path cannot be determined from
           the state machine structure itself.

           Result of "self.__loop_search(...)"
        """
        return self.__loop_state_set

    @property
    def acceptance_trace_db(self):
        """A dictionary that maps 

                    state index --> object of class Trace

           All auxiliary trace objects for positioning have been deleted at this 
           point in time. So, the traces concern only acceptance information.

           Result of self.__trace_walk(...)
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
                self.__loop_state_set.update(path[idx:])
                continue # Do not dive into done states

            self.__loop_search(state_index, path)

        # (3) Remove current state index --> path is as before
        x = path.pop()
        self.__loop_search_done_set.add(StateIndex)
        assert x == StateIndex

    def __trace_walk(self, StateIndex, path, trace):
        """StateIndex -- current state
           path       -- path from init state to current state (state index list)

           Recursion Terminal: When state has no target state that has not yet been
                               handled in the 'path'.
        """
        # (1) Add current state to path
        path.append(StateIndex)

        # (2) Update the information about the 'trace of acceptances'
        trace.update(self, path) 

        # (3) Mark the current state with its acceptance trace
        #     NOTE: When this function is called, trace is already
        #           an independent object, i.e. constructed or deepcopy()-ed.
        if     self.__map_state_to_trace.has_key(StateIndex):
            if trace in self.__map_state_to_trace[StateIndex]:
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
            self.__trace_walk(target_index, path, deepcopy(trace))

        self.__map_state_to_trace[StateIndex].append(trace)

        # (5) Remove current state index --> path is as before
        x = path.pop()
        assert x == StateIndex

class Trace(object):
    """For one particular STATE that is reached via one particular PATH an
       Trace accumulates information about what pattern 'ACCEPTS' and where the
       INPUT POSITION is to be placed.

       This behavior may depend on pre-contexts being fulfilled.

       In other words, a Trace of a state provides information about what
       pattern would be accepted and what the input positioning should be if
       the current path was the only path to the state.

       The acceptance information is **prioritized**. That means, that it is
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
        """Assume: 'self.__trace_db' contains accumulated information of passed 
                   states until the current state has been reached. 

           Now, the current state is reached. It contains 'origins', i.e. information
           that witness from what patterns the state evolves and what has to happen
           in the state so that it represents those original states. In brief, 
           the origins tell if a pattern is accepted, what input position is to
           be stored and what pre-context has to be fulfilled for a pattern
           to trigger acceptance.
           
           The 'self.__trace_db' contains two types of elements:

              -- TraceEntry objects that tell about an acceptance.
                 => .accepting_state_index = index of the accepting state

                 The remaining members tell about what state stores the
                 position, how many transitions it lies backwards, the 
                 min. number of transitions until an acceptance is reached
                 etc.

              -- TraceEntry objects that tell about an input position to be stored.
                 => .accepting_state_index = E_StateIndices.VOID

                 There no information about an acceptance yet--only information
                 about a input position storage for a certain post context. 
                 Inside these objects the counters are incremented during 
                 further development, so that the distance between positioning 
                 state and accepting state can be determined as soon as the 
                 accepting state arrives that belongs to the storage info.
        """
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
        """Delete the additional traces from the analysis procedure. Now, only
           traces are required that tell about acceptances.
        """
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
            if X.pattern_id == E_AcceptanceIDs.FAILURE: return (sys.maxint, sys.maxint)
            # Longest pattern sort on top
            # Lowest pattern ids sort on top
            return (- X.min_transition_n_to_acceptance, X.pattern_id)

        return sorted(self.__trace_db.itervalues(), key=my_key)

    def get_priorized_pre_context_id_list(self):
        return map(lambda x: x.pre_context_id, self.get_priorized_list())

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

    def __neq__(self):
        return not self.__eq__(self)

    def __repr__(self):
        txt = []
        for x in self.__trace_db.itervalues():
            txt.append(repr(x))
        return "".join(txt)

    def __iter__(self):
        for x in self.__trace_db.itervalues():
            yield x

class TraceEntry(object):
    """Information about a trace element. That is what pre-context is
       required, what pattern id is referred, transition counters etc.
    """
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

