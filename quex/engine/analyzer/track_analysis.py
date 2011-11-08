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

from   itertools   import ifilter, chain, islice
from   collections import defaultdict
import sys

def do(SM):
    """Determines a database of Trace lists for each state.
    """
    ta = TrackAnalysis(SM)
    return ta.acceptance_trace_db, ta.successor_db, ta.store_to_restore_path_db

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
        self.__map_state_to_trace,      \
        self.__store_to_restore_path_db = self.__trace_walk()

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
                self.track_info = track_info
                self.sm         = track_info.sm
                # self.done_set   = set()
                self.empty_list = []
                self.result     = dict([(i, []) for i in self.sm.states.iterkeys()])
                # map: pattern_id --> path from store to restore of input positions 
                #                     where the difference CANNOT be determined by
                #                     the number of transitions.
                self.store_to_restore_path_db = defaultdict(list)

            def on_enter(self, StateIndex):
                # (*) Update the information about the 'trace of acceptances'
                State = self.sm.states[StateIndex]

                if len(self.path) == 0: 
                    trace = Trace(self.sm.init_state_index)
                else: 
                    trace = self.path[-1][1].clone()
                    trace.update(StateIndex, State, self.track_info.loop_state_set, self.path) 

                # (*) Keep track of paths from store to restore
                self.__register_store_restore_paths(trace, StateIndex)

                # (*) Mark the current state with its acceptance trace
                existing_trace_list = self.result.get(StateIndex) 
                if trace in existing_trace_list:
                    # If a state has been analyzed before with the same trace as result,  
                    # then it is not necessary dive into deeper investigations again.
                    return None # Refuse further processing of the node
                self.result[StateIndex].append(trace)

                # if StateIndex in self.done_set: return None

                for dummy in ifilter(lambda x: x[0] == StateIndex, self.path):
                    return None # Refuse further processing of the node

                # (*) Add current state to path
                self.path.append((StateIndex, trace))

                # (*) Recurse to all (undone) target states. 
                return self.sm.states[StateIndex].transitions().get_map().keys()

            def on_finished(self, StateIndex):
                # self.done_set.add(StateIndex)
                self.path.pop()

            def __register_store_restore_paths(self, TheTrace, StateIndex):
                """When a state is reached that:
                       (i) restores the input position and 
                       (ii) the number of transitions from the storage of input position 
                            to here cannot be determined by the number of transitions,
                   then we have a situation where the input position
                       (a) MUST be stored and restored.
                       (b) The path from store to restore must be registered, so that
                           later it can be determine what paths intersect and what not.
                """
                for entry in TheTrace.acceptance_db.itervalues():
                    if entry.transition_n_since_positioning != E_TransitionN.VOID: continue
                    # Find the stretch on the path from the storing state to the current state
                    # where the input position is restored.
                    for path_index, info in enumerate(self.path): 
                        if info[0] == entry.positioning_state_index: break
                    else:
                        assert False, "The positioning_state_index MUST be in the path!"
                    store_to_restore_path = [ state_index for state_index, trace in islice(self.path, path_index, None)] 
                    store_to_restore_path.append(StateIndex)
                    self.store_to_restore_path_db[entry.post_context_id].append(store_to_restore_path)

        trace_finder = TraceFinder(self)
        trace_finder.do(self.sm.init_state_index)
        return trace_finder.result, trace_finder.store_to_restore_path_db

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
    __slots__ = ("__acceptance_db", "__storage_db", "__DEBUG_last_transition_n_to_acceptance")
    # __acceptance_db:   pattern_id --> TraceEntry object 
    #
    #               Information about the acceptance of pattern_id on the trace with 
    #               respect to the state that this object represents.
    #
    # __storage_db: pattern_id --> TraceEntry object 
    #               Information about where input position is stored for given 
    #               pattern_id. This is obviously only important for post-contexted
    #               pattern, i.e. where there is store-restore input position.

    def __init__(self, InitStateIndex=None):
        if InitStateIndex is None:
            self.__acceptance_db = {}
        else:
            self.__acceptance_db = { 
                E_AcceptanceIDs.FAILURE: 
                      TraceEntry(PreContextID                 = E_PreContextIDs.NONE, 
                                 PatternID                    = E_AcceptanceIDs.FAILURE, 
                                 MinTransitionN_ToAcceptance  = 0,
                                 AcceptingStateIndex          = InitStateIndex, 
                                 TransitionN_SincePositioning = E_TransitionN.LEXEME_START_PLUS_ONE,              
                                 PositioningStateIndex        = E_StateIndices.NONE, 
                                 PostContextID                = E_PostContextIDs.NONE),
            }
        self.__storage_db = {}
        self.__DEBUG_last_transition_n_to_acceptance = 0

    def clone(self):
        result = Trace()
        result.__acceptance_db   = dict(( (i, x.clone()) 
                                     for i, x in self.__acceptance_db.iteritems() 
                                  ))
        result.__storage_db = dict(( (i, x.clone()) 
                                     for i, x in self.__storage_db.iteritems() 
                                  ))
        result.__DEBUG_last_transition_n_to_acceptance = self.__DEBUG_last_transition_n_to_acceptance
        return result

    def __len__(self):
        return len(self.__acceptance_db)

    def update(self, StateIndex, State, LoopStateSet, Path):
        """Assume: 'self.__acceptance_db' contains accumulated information of passed 
                   states until the current state has been reached. 

           Now, the current state is reached. It contains 'origins', i.e.
           information that witness from what patterns the state evolves and
           what has to happen in the state so that it represents those original
           states. In brief, the origins tell if a pattern is accepted, what
           input position is to be stored and what pre-context has to be
           fulfilled for a pattern to trigger acceptance.
           
           The 'self.__acceptance_db' contains two types of elements:

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
        CurrentPathLength = len(Path) + 1 # This is the length of the path considered
        #                                 # the current state being added already.

        # It is essential for a meaningful accumulation of the match information
        # that the entries are accumulated from the begin of a path towards its 
        # end. Otherwise, the 'longest match' cannot be applied by overwriting
        # existing entries.
        assert abs(self.__DEBUG_last_transition_n_to_acceptance) < CurrentPathLength
        self.__DEBUG_last_transition_n_to_acceptance = len(Path)

        # Last element of the path is the index of the current state
        # (*) Update all path related Info
        if StateIndex in LoopStateSet:
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
        for entry in chain(self.__acceptance_db.itervalues(), self.__storage_db.itervalues()):
            # 'lexeme_start_p + 1', 'void' --> are not updated
            if     entry.transition_n_since_positioning != E_TransitionN.LEXEME_START_PLUS_ONE \
               and entry.transition_n_since_positioning != E_TransitionN.VOID:
                entry.transition_n_since_positioning = operation(entry.transition_n_since_positioning)

        # (*) Absolute Acceptance 
        acceptance_id = E_AcceptanceIDs.FAILURE
        origin        = State.origins().get_absolute_acceptance_origin()
        if origin is not None:
            self.__acceptance_db.clear()
            self.__add(origin, StateIndex, CurrentPathLength)

        # (*) Conditional Acceptance 
        for origin in State.origins().get_conditional_acceptance_iterable(acceptance_id):
            self.__add(origin, StateIndex, CurrentPathLength)

        # (*) Store Input Position Information
        for origin in State.origins().get_store_iterable():
            # One the StoreInfo object is in __storage_db, it is subject to counting
            # .transition_n_since_positioning each time we advance one step on the path. 
            self.__storage_db[origin.pattern_id()] = StoreInfo(StateIndex)

        assert len(self.__acceptance_db) >= 1

    def __add(self, Origin, StateIndex, CurrentPathLength):
        pattern_id = Origin.pattern_id()
        if Origin.input_position_restore_f():
            entry = self.__storage_db[pattern_id]
            transition_n_since_positioning = entry.transition_n_since_positioning
            positioning_state_index        = entry.positioning_state_index
            post_context_id                = pattern_id
        else:
            transition_n_since_positioning = 0
            positioning_state_index        = StateIndex
            post_context_id                = E_PostContextIDs.NONE

        self.__acceptance_db[pattern_id] = \
                TraceEntry(Origin.pre_context_id(), pattern_id,
                           MinTransitionN_ToAcceptance  = CurrentPathLength,
                           AcceptingStateIndex          = StateIndex, 
                           TransitionN_SincePositioning = transition_n_since_positioning,
                           PositioningStateIndex        = positioning_state_index, 
                           PostContextID                = post_context_id)

    @property
    def acceptance_db(self): return self.__acceptance_db
    @property
    def storage_db(self): return self.__storage_db

    def __getitem__(self, PreContextID):
        return self.get(PreContextID)

    def get(self, PreContextID):
        for entry in self.__acceptance_db.itervalues():
            if entry.pre_context_id == PreContextID: return entry
        return None

    def get_priorized_list(self):
        def my_key(X):
            # Failure always sorts to the bottom ...
            if X.pattern_id == E_AcceptanceIDs.FAILURE: return (sys.maxint, sys.maxint)
            # Longest pattern sort on top
            # Lowest pattern ids sort on top
            return (- X.min_transition_n_to_acceptance, X.pattern_id)

        return sorted(self.__acceptance_db.itervalues(), key=my_key)

    def get_priorized_pre_context_id_list(self):
        return map(lambda x: x.pre_context_id, self.get_priorized_list())

    def __eq__(self, Other):
        """Compare two acceptance trace objects. Note, that __DEBUG_last_transition_n_to_acceptance
           is only for debug purposes.
        """
        if len(self.__acceptance_db)   != len(Other.__acceptance_db):      return False
        if len(self.__storage_db) != len(Other.__storage_db):    return False

        for pattern_id, trace in self.__acceptance_db.iteritems():
            other_trace = Other.__acceptance_db.get(pattern_id)
            if other_trace is None:                              return False
            if not trace.is_equal(Other.__acceptance_db[pattern_id]): return False
        # Here, self.__acceptance_db and Other.__acceptance_db have the same number of entries,
        # thus the same number of unique keys (pattern_ids). Any key in self.__acceptance_db
        # occurs in Other.__acceptance_db, so both have the same key set. Also, Both 
        # have the same trace stored along with their given key.

        for pattern_id, entry in self.__storage_db.iteritems():
            other_entry = Other.__storage_db.get(pattern_id)
            if other_entry is None:                                return False
            if not entry.is_equal(Other.__storage_db[pattern_id]): return False
        # What held for __acceptance_db above holds here for __storage_db
        
        return True

    def __neq__(self):
        return not self.__eq__(self)

    def __repr__(self):
        txt = []
        for x in self.__acceptance_db.itervalues():
            txt.append(repr(x))
        return "".join(txt)

    def __iter__(self):
        for x in self.__acceptance_db.itervalues():
            yield x

class StoreInfo(object):
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
                 "min_transition_n_to_acceptance", 
                 "accepting_state_index", 
                 "transition_n_since_positioning", 
                 "positioning_state_index",
                 "post_context_id",
                 "positioning_state_successor_index")

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
        if PostContextID != E_PostContextIDs.NONE:
            self.post_context_id = PatternID # PostContextID
        else:
            self.post_context_id = E_PostContextIDs.NONE

    def clone(self):
        result = TraceEntry(self.pre_context_id, 
                            self.pattern_id, 
                            self.min_transition_n_to_acceptance, 
                            self.accepting_state_index, 
                            self.transition_n_since_positioning, 
                            self.positioning_state_index, 
                            self.post_context_id)
        result.positioning_state_successor_index = self.positioning_state_successor_index
        return result

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

