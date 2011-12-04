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
from   quex.blackboard              import E_StateIndices, E_PostContextIDs, E_AcceptanceIDs, E_PreContextIDs, E_TransitionN
from   quex.engine.misc.tree_walker import TreeWalker

from   operator    import attrgetter
from   itertools   import ifilter, chain, islice
from   collections import defaultdict
import sys

def do(SM):
    """Determines a database of Trace lists for each state.
    """
    ta = TrackAnalysis(SM)
    return ta.acceptance_trace_db, ta.successor_db

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
        # NOTE: The investigation about loop states must be done **before** the
        #       analysis of traces. The trace analysis requires the loop state set!
        self.__loop_state_set, \
        self.__successor_db    = self.__loop_search() # self.sm.init_state_index, [])

        # (*) Collect Trace Information
        # 
        #    map:  state_index  --> list of Trace objects.
        #
        self.__map_state_to_trace = self.__trace_walk()

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

    @property
    def store_to_restore_path_db(self):
        """A dictionary that maps pattern id to a list of paths which guide from 
           the state where an input position is stored to the position where it 
           is restored. 

           IMPORTANT: This database contains only entries for patterns where the
                      path from store to restore CANNOT be determined from the 
                      number of state transitions (i.e. if there is a 'loop' 
                      involved).
        """
        return self.__store_to_restore_path_db

    @property
    def successor_db(self):
        return self.__successor_db

    def __loop_search(self):
        """Determine the indices of states that are part of a loop. Whenever
           such a state appears in a path from one state A to another state B, 
           then the number of transitions from A to B cannot be determined 
           from the number of transitions between them.

           Recursion Terminal: When a state has no target state that has not
                               yet been handled in the path. This is implemented
                               in the loop itself.
        """
        class LoopSearcher(TreeWalker):
            def __init__(self, SM):
                self.path = []
                self.sm   = SM
                self.done_set             = set()
                self.empty_list           = []
                # set of a all state indices that are on a loop-path
                self.loop_state_index_set = set()
                # map: state_index -> list of all successor state indices
                self.successor_db         = dict([(i, set()) for i in SM.states.iterkeys()])

            def on_enter(self, StateIndex):
                found_f = False # StateIndex found in path?
                for i in self.path:
                    self.successor_db[i].add(StateIndex)
                    if StateIndex == i: 
                        idx = self.path.index(StateIndex)
                        # All states from path[idx] to the current are part of a loop.
                        self.loop_state_index_set.update(self.path[idx:])
                        found_f = True

                # Make sure, that the successor_db has still registered the state_index
                if StateIndex in self.done_set:
                    # All states in the path have the successor states of StateIndex
                    for i in (i for i in self.path if i != StateIndex):
                        self.successor_db[i].update(self.successor_db[StateIndex])
                    return None

                if found_f:
                    return None

                self.path.append(StateIndex)
                propose_list = self.sm.states[StateIndex].transitions().get_map().keys()
                return propose_list

            def on_finished(self, StateIndex):
                self.done_set.add(StateIndex)
                self.path.pop()

        searcher = LoopSearcher(self.sm)
        searcher.do(self.sm.init_state_index)
        return searcher.loop_state_index_set, searcher.successor_db

    def __trace_walk(self):
        """StateIndex -- current state
           path       -- path from init state to current state (state index list)

           Recursion Terminal: When state has no target state that has not yet been
                               handled in the 'path'.
        """
        class TraceFinder(TreeWalker):
            def __init__(self, track_info):
                self.path       = []
                self.sm         = track_info.sm
                self.empty_list = []
                self.result     = dict([(i, []) for i in self.sm.states.iterkeys()])

            def on_enter(self, StateIndex):
                # (*) Update the information about the 'trace of acceptances'
                State = self.sm.states[StateIndex]

                if len(self.path) == 0: 
                    trace = Trace(self.sm.init_state_index)
                else: 
                    trace = self.path[-1][1].next_step(StateIndex, State, self.path) 

                # (*) Mark the current state with its acceptance trace
                #     This automatically handles the case of loops. But it does 
                #     so in a 'considerate manner'. This means, that a loop can
                #     be stepped through multiple times, as long as the resulting
                #     acceptance/storage trace changes.
                existing_trace_list = self.result.get(StateIndex) 
                if trace in existing_trace_list:
                    # If a state has been analyzed before with the same trace as result,  
                    # then it is not necessary dive into deeper investigations again.
                    return None # Refuse further processing of the node
                self.result[StateIndex].append(trace)

                # (*) Add current state to path
                self.path.append((StateIndex, trace))

                # (*) Recurse to all (undone) target states. 
                return self.sm.states[StateIndex].transitions().get_map().keys()

            def on_finished(self, StateIndex):
                # self.done_set.add(StateIndex)
                self.path.pop()

        trace_finder = TraceFinder(self)
        trace_finder.do(self.sm.init_state_index)
        return trace_finder.result

#_DEBUG_counter = 0
class Trace(object):
    """ABSTRACT:
       
       An object of this class documents the impact of actions that happen
       along ONE specific path from the init state to a specific state. 
       ------------------------------------------------------------------------

       EXPLANATION:

       During a path from the init state to 'this state', the following things
       may happen or may have happened:

            -- The input position has been stored in a position register
               (for post context management or on accepting a pattern).

            -- A pattern has been accepted. Acceptance may depend on a
               pre-context being fulfilled.

       Storing the input position can be a costly operation. If the length of
       the path from storing to restoring can be determined from the number of
       transitions, then it actually does not have to be stored. Instead, it
       can be obtained by 'input position -= transition number since
       positioning.' In any case, the restoring of an input position is
       triggered by an acceptance event.

       Acceptance of a pattern occurs, if one drops out of a state, i.e. there
       are no further transitions possible. Later analysis will focus on these
       acceptance events. They are stored in a sorted member '.acceptance_trace'.

       The sort order of the acceptance trace reflects the philosophy of
       'longest match'. That, is that the last acceptance along a path has a
       higher precedence than an even higher prioritized pattern before. 
       Actually, all patterns without any pre-context remove any TraceEntry
       object that preceded along the path.

       For further analysis, this class provides:

            .acceptance_trace -- Sorted list of information about acceptances.
                                 
            .priorized_pre_context_id_list -- Sorted list of pre-context-ids
                                              in the acceptance trace.

       The sort order of '.prioritized_pre_context_id_list' is the same as the
       aforementioned sort order of '.acceptance_trace'.

       During the process of building path traces, the function

            .next_step(...)

       is called. It assumes that the current object represents the path trace
       before 'this state'. Based on the given arguments to this function it 
       modifies itself so that it represents the trace for 'this_state'.

       ------------------------------------------------------------------------

       EXAMPLE:
    
    
           ( 0 )----->(( 1 ))----->( 2 )----->(( 3 ))----->( 4 ) ....
                       8 wins                 pre 4 -> 5 wins                    
                                              pre 3 -> 7 wins

       results in Trace objects for the states as follows:

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
    __slots__ = ("__acceptance_trace",  # List of TraceEntry objects
                 "__storage_db")        # Map: pattern_id --> StoreInfo objects

    def __init__(self, InitStateIndex=None):
        if InitStateIndex is None:
            self.__acceptance_trace = []
        else:
            self.__acceptance_trace = [ 
                  TraceEntry(PreContextID                 = E_PreContextIDs.NONE, 
                             PatternID                    = E_AcceptanceIDs.FAILURE, 
                             AcceptingStateIndex          = InitStateIndex, 
                             TransitionN_SincePositioning = E_TransitionN.LEXEME_START_PLUS_ONE,              
                             PositioningStateIndex        = E_StateIndices.NONE), 
            ]
        self.__storage_db = {}

    def clone(self):
        # global _DEBUG_counter
        # if len(self.__storage_db) == 0 and len(self.__acceptance_trace) == 1:
        #    entry = self.__acceptance_trace.__iter__().next()
        #    if entry.pre_context_id == E_PreContextIDs.NONE                                    \
        #       and entry.pattern_id == E_AcceptanceIDs.FAILURE                                 \
        #       and entry.transition_n_since_positioning == E_TransitionN.LEXEME_START_PLUS_ONE \
        #       and entry.positioning_state_index == E_StateIndices.NONE:
        #         _DEBUG_counter += 1
        #         print "cloning empty counter:", _DEBUG_counter

        result = Trace()
        result.__acceptance_trace = [ x.clone() for x in self.__acceptance_trace ]
        result.__storage_db       = dict(( (i, x.clone()) 
                                         for i, x in self.__storage_db.iteritems() 
                                    ))
        return result

    def next_step(self, StateIndex, State, Path):
        """Assume: 'self.__acceptance_trace' contains accumulated information of passed 
                   states until the current state has been reached. 

           Now, the current state is reached. It contains 'origins', i.e.
           information that witness from what patterns the state evolves and
           what has to happen in the state so that it represents those original
           states. In brief, the origins tell if a pattern is accepted, what
           input position is to be stored and what pre-context has to be
           fulfilled for a pattern to trigger acceptance.
           
           The 'self.__acceptance_trace' contains two types of elements:

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
        # Some experimenting has shown that the number of unnecessary cloning, i.e.
        # when there would be no change, is negligible. So, it is done the safe way:
        # Always clone. The fact that '.transition_n_since_positioning' has to be
        # almost always to be adapted, makes selective cloning meaningless.
        current = self.clone()

        # (*) Update '.transition_n_since_positioning'
        for entry in chain(current.__acceptance_trace, current.__storage_db.itervalues()):
            # 'lexeme_start_p + 1', 'void' --> are not updated
            # Note, if a state is passed the second time, then new entries are 
            # generated in __acceptance_trace and __storage_db. So, the 'transition_n_since_positioning'
            # do not have to be reset to '0' at this point, if a 'no-loop' is detected.
            if not isinstance(entry.transition_n_since_positioning, (int, long)): continue

            # Is there a loop from 'positioning_state_index' to current state?
            if current.__check_loop(Path, entry.positioning_state_index, StateIndex):
                entry.transition_n_since_positioning = E_TransitionN.VOID
            else:
                entry.transition_n_since_positioning += 1

        # (*) Update '.__acceptance_trace' and '.__storage_db'
        for origin in sorted(State.origins(), key=lambda x: x.pattern_id(), reverse=True):
            # Acceptance 
            if origin.is_acceptance():
                if origin.pre_context_id() == E_PreContextIDs.NONE:
                    del current.__acceptance_trace[:]
                current.__add(origin, StateIndex)

            # Store Input Position Information
            if origin.input_position_store_f():
                current.__storage_db[origin.pattern_id()] = StoreInfo(StateIndex)

        assert len(current.__acceptance_trace) >= 1
        return current

    def __add(self, Origin, StateIndex):
        """Add entry to the acceptance trace."""
        pattern_id = Origin.pattern_id()
        if Origin.input_position_restore_f():
            entry = self.__storage_db[pattern_id]
            transition_n_since_positioning = entry.transition_n_since_positioning
            positioning_state_index        = entry.positioning_state_index
        else:
            transition_n_since_positioning = 0
            positioning_state_index        = StateIndex

        for entry_i in (i for i, x in enumerate(self.__acceptance_trace) \
                          if x.pattern_id == pattern_id):
            del self.__acceptance_trace[entry_i]
            # Reoccuring information about an acceptance overwrites
            # => only one entry per pattern_id.
            break

        entry = TraceEntry(Origin.pre_context_id(), pattern_id,
                           AcceptingStateIndex          = StateIndex, 
                           TransitionN_SincePositioning = transition_n_since_positioning,
                           PositioningStateIndex        = positioning_state_index) 

        self.__acceptance_trace.insert(0, entry)

    def __check_loop(self, Path, PositioningStateIndex, StateIndex):
        """Check whether there is a loop between positioning state index to current
           state. Consider the segment from PositioningStateIndex to current state.

           A loop exists if at least one state index appears twice on the path.
           The easiest way to check for that is to compare the size of the unique
           set to the size of the segment. If not equal than state indices appeared
           twice or more often.
        """
        # If the PositioningStateIndex == StateIndex then it does not matter whether there
        # is a loop. The position referes to what is stored in 'StateIndex'. What was before
        # is no longer interesting.
        # if PositioningStateIndex == StateIndex: return False

        # Find the index of the position state index on the path
        L = len(Path)
        for inverse_path_i in (i for i, x in enumerate(reversed(Path)) if x[0] == PositioningStateIndex):
            psi_path_index = L - inverse_path_i
            break
        else:
            assert False

        segment_size = len(Path) - psi_path_index + 1 # '+1' for StateIndex
        unique_set   = set(state_index for state_index, x in islice(Path, psi_path_index, None))
        unique_set.add(StateIndex)
        return len(unique_set) != segment_size

    def get(self, PreContextID):
        for entry in self.__acceptance_trace:
            if entry.pre_context_id == PreContextID: return entry
        return None

    @property
    def acceptance_trace(self):
        return self.__acceptance_trace

    @property
    def prioritized_pre_context_id_list(self):
        return map(lambda x: x.pre_context_id, self.acceptance_trace)

    def __eq__(self, Other):
        if self.__acceptance_trace != Other.__acceptance_trace: return False
        if len(self.__storage_db)  != len(Other.__storage_db):  return False

        for pattern_id, entry in self.__storage_db.iteritems():
            other_entry = Other.__storage_db.get(pattern_id)
            if other_entry is None:                                return False
            if not entry.is_equal(Other.__storage_db[pattern_id]): return False
        
        return True

    def __neq__(self):
        return not self.__eq__(self)

    def __repr__(self):
        return "".join([repr(x) for x in self.__acceptance_trace])

class StoreInfo(object):
    """Informs about a 'positioning action' that happend during the the walk
       along a path before reaching 'this state'.

       A 'positioning action' is the storage of the current input position 
       into a dedicated position register. Objects of class 'StoreInfo'
       are stored in dictionaries where the key represents the pattern-id
       is at the same time the identifier of the position storage register.
       (Note, later the position register is remapped according to required
        entries.)

       'This state' means the state where the trace lead to. 

       The member '.transition_n_since_positioning' is incremented at each
       transition along a path. If a loop is detected it is set to value
       'E_TransitionN.VOID'.

       The member '.positioning_state_index' is the state where the positioning
       happend. If there is a loop along the path from '.positioning_state_index'
       to 'this state, then the '.transition_n_since_positioning' is set to 
       'E_TransitionN.VOID' (see comment above).
    """
    __slots__ = ('transition_n_since_positioning', 'positioning_state_index')
    def __init__(self, PositioningStateIndex, TransitionN_SincePositioning=0):
        self.transition_n_since_positioning = TransitionN_SincePositioning
        self.positioning_state_index        = PositioningStateIndex

    def is_equal(self, Other):
        return     self.transition_n_since_positioning == Other.transition_n_since_positioning \
               and self.positioning_state_index        == Other.positioning_state_index

    def clone(self):
        return StoreInfo(self.positioning_state_index, 
                         self.transition_n_since_positioning)

class TraceEntry(object):
    """Information about a trace element. That is what pre-context is
       required, what pattern id is referred, transition counters etc.
    """
    __slots__ = ("pre_context_id", 
                 "pattern_id", 
                 "accepting_state_index", 
                 "transition_n_since_positioning", 
                 "positioning_state_index")

    def __init__(self, PreContextID, PatternID, 
                 AcceptingStateIndex, 
                 TransitionN_SincePositioning, 
                 PositioningStateIndex): 
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
        """
        self.pre_context_id                 = PreContextID
        self.pattern_id                     = PatternID
        self.transition_n_since_positioning = TransitionN_SincePositioning
        self.accepting_state_index          = AcceptingStateIndex
        self.positioning_state_index        = PositioningStateIndex

    def clone(self):
        result = TraceEntry(self.pre_context_id, 
                            self.pattern_id, 
                            self.accepting_state_index, 
                            self.transition_n_since_positioning, 
                            self.positioning_state_index) 
        return result

    def is_equal(self, Other):
        if   self.pre_context_id                 != Other.pre_context_id:                    return False
        elif self.pattern_id                     != Other.pattern_id:                        return False
        elif self.transition_n_since_positioning != Other.transition_n_since_positioning:    return False
        elif self.accepting_state_index          != Other.accepting_state_index:             return False
        elif self.positioning_state_index        != Other.positioning_state_index:           return False
        return True

    def __eq__(self, Other):
        return self.is_equal(Other)

    def __repr__(self):
        txt = ["---\n"]
        txt.append("    .pre_context_id                 = %s\n" % repr(self.pre_context_id))
        txt.append("    .pattern_id                     = %s\n" % repr(self.pattern_id))
        txt.append("    .transition_n_since_positioning = %s\n" % repr(self.transition_n_since_positioning))
        txt.append("    .accepting_state_index          = %s\n" % repr(self.accepting_state_index))
        txt.append("    .positioning_state_index        = %s\n" % repr(self.positioning_state_index))
        return "".join(txt)

TraceEntry_Void = TraceEntry(PreContextID                 = E_PreContextIDs.NONE, 
                             PatternID                    = E_AcceptanceIDs.VOID, 
                             AcceptingStateIndex          = E_StateIndices.VOID,  
                             TransitionN_SincePositioning = E_TransitionN.VOID, 
                             PositioningStateIndex        = E_StateIndices.NONE) 

