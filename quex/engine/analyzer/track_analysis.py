"""ABSTRACT:

This module analyses paths of a state machine. For each path through a state a
PathTrace object is created. A PathTrace object tells something about the
acceptance behavior of a state in terms of a list of AcceptInfo objects.  As a
basic result of this process a map is generated with the following property:

            map:    state index --> list of PathTrace objects.

Based on the information in the AcceptInfo objects requirements on entry and
drop_out behaviors of a state can be derived, as done by module 'core.py'.

-------------------------------------------------------------------------------

   FURTHER INFO: 

        class TrackAnalysis 
        class PathTrace
        class AcceptInfo

-------------------------------------------------------------------------------
(C) 2010-2011 Frank-Rene Schaefer
ABSOLUTELY NO WARRANTY
"""
from   quex.blackboard              import E_AcceptanceIDs, E_PreContextIDs, E_TransitionN
from   quex.engine.misc.tree_walker import TreeWalker

from   collections import defaultdict
from   itertools   import chain, izip
from   copy        import copy

def do(SM):
    """RETURNS: Acceptance trace database:

                map: state_index --> list of PathTrace objects.
    """
    ta = TrackAnalysis(SM)

    return ta.map_state_to_trace, None # ta.successor_db

class TrackAnalysis:
    """The init function of this class walks down each possible path trough a
       given state machine. During the process of walking down the paths it 
       develops for each state its list of PathTrace objects.
       
       The result of the process is presented by property 'map_state_to_trace'. 
       It delivers for each state of the state machine a trace object that maps:

                   state index --> list of PathTrace objects
       
       Another result of the walk is the 'successor_db' which collects for each
       state all of its successor states.
    """

    def __init__(self, SM):
        """SM -- state machine to be investigated."""
        self.sm = SM

        # (*) Collect PathTrace Information
        self.__map_state_to_trace = self.__trace_walk()

    @property
    def map_state_to_trace(self):
        return self.__map_state_to_trace

    def __trace_walk(self):
        """Determine PathTrace objects for each state. The heart of this function is
           the call to 'PathTrace.next_step()' which incrementally develops the 
           acceptance and position storage history of a path.

           Recursion Terminal: When state has no target state that has not yet been
                               handled in the 'path' in the same manner. That means,
                               that if a state appears again in the path, its trace
                               must be different or the recursion terminates.
        """
        class KnotInfo:
            from_to_db = defaultdict(dict)
            def __init__(self, Pioneer, Rear):
                self.knot_trace = Pioneer

        class TraceFinder(TreeWalker):
            def __init__(self, track_info):
                self.__depth          = 0
                self.sm               = track_info.sm
                self.empty_list       = []
                self.result           = dict((i, []) for i in self.sm.states.iterkeys())
                self.pruned_knot_list = []

            def on_enter(self, Args):
                PreviousTrace = Args[0]
                StateIndex    = Args[1]
                # (*) Update the information about the 'trace of acceptances'
                State = self.sm.states[StateIndex]

                if self.__depth == 0: trace = PathTrace(self.sm.init_state_index)
                else:                 trace = PreviousTrace.next_step(StateIndex, State) 

                # (*) Recursion Termination:
                #
                # If a state has been analyzed before with the same trace as result,  
                # then it is not necessary dive into deeper investigations again. All
                # of its successor paths have been walked along before. This catches
                # two scenarios:
                #   
                # (1) Loops: A state is reached through a loop and nothing 
                #            changed during the walk through the loop since
                #            the last passing.
                # 
                #            There may be connected loops, so it is not sufficient
                #            to detect a loop and stop.
                #parent = trace.parent
                #while parent is not None:
                #    if parent.state_index == StateIndex and parent.is_equivalent(trace): 
                #        # Loop detected which does not add any meaning.
                #        return None
                #    parent = parent.parent
                #
                # (2) Knots: A state is be reached through different branches.
                #            However, the traces through those branches are
                #            indifferent in their positioning and accepting 
                #            behavior. Only one branch needs to consider the
                #            subsequent states.
                #
                #     (There were cases where this blew the computation time
                #      see bug-2257908.sh in $QUEX_PATH/TEST).
                # 
                existing_trace_list = self.result.get(StateIndex) 
                for pioneer in existing_trace_list:
                    if not trace.is_equivalent(pioneer): continue
                    if trace.has_parent(pioneer):
                        # Loop detected -- Continuation unecessary. 
                        # Nothing new happend since last passage.
                        return None
                    else:
                        # Knot detected -- Continuation abbreviated.
                        # A state is reached twice via two separate paths with
                        # the same positioning_states and acceptance states. The
                        # analysis of subsequent states on the path is therefore
                        # complete. Almost: There is now alternative paths from
                        # store to restore that must added later on.
                        # self.knot_branch_db.append(KnotInfo(pioneer, trace))
                        for accept_info in trace.acceptance_trace:
                            self.pruned_knot_list.append((pioneer, accept_info.path_since_positioning))
                        return None
                        # return None # For now, do not further process the node.

                # (*) Mark the current state with its acceptance trace
                self.result[StateIndex].append(trace)

                # (*) Add current state to path
                self.__depth += 1

                # (*) Recurse to all (undone) target states. 
                return [(trace, target_index) 
                        for target_index in self.sm.states[StateIndex].transitions().get_map().iterkeys()
                       ]

            def on_finished(self, Args):
                # self.done_set.add(StateIndex)
                self.__depth -= 1

            def pruned_knot_list_post_process(self):
                for pioneer, acceptance_trace in self.neglected_trace_db:
                    for trace_list in self.result.itervalues():
                        # Consider only traces that originate in the 'pioneer'.
                        for trace in (x for x in trace_list if x.has_parent(pioneer)):
                            sibling_trace_list = trace.generate_siblings_with_alternative_path(acceptance_trace)
                            if sibling_trace_list is not None: 
                                trace_list.extend(sibling_trace_list)

        trace_finder = TraceFinder(self)
        trace_finder.do((None, self.sm.init_state_index))
        class Doodle:
            def __init__(self, X):
                self.acceptance_trace = X.acceptance_trace
        return dict( (key, [Doodle(x) for x in trace_list]) for key, trace_list in trace_finder.result.iteritems())

class PathTrace(object):
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
       Actually, all patterns without any pre-context remove any AcceptInfo
       object that preceded along the path.

       For further analysis, this class provides:

            .acceptance_trace -- Sorted list of information about acceptances.

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

       results in PathTrace objects for the states as follows:

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
    __slots__ = ("__acceptance_trace",  # List of AcceptInfo objects
                 "__storage_db",        # Map: pattern_id --> StoreInfo objects
                 "__parent", 
                 "__state_index")

    def __init__(self, InitStateIndex=None):
        if InitStateIndex is None: # 'None' --> call from '.clone()'
            self.__acceptance_trace = [] 
        else:
            self.__acceptance_trace = [ 
                  AcceptInfo(PreContextID         = E_PreContextIDs.NONE, 
                             PatternID            = E_AcceptanceIDs.FAILURE, 
                             AcceptingStateIndex  = InitStateIndex, 
                             PathSincePositioning = [InitStateIndex])              
            ]
        self.__storage_db  = {}
        self.__state_index = InitStateIndex
        self.__parent      = None

    def reproduce(self, StateIndex):
        result = PathTrace()
        result.__acceptance_trace = [ x.clone() for x in self.__acceptance_trace ]
        result.__storage_db       = dict(( (i, x.clone()) 
                                         for i, x in self.__storage_db.iteritems() 
                                    ))
        # Update '.path_since_positioning'
        for entry in chain(result.__acceptance_trace, result.__storage_db.itervalues()):
            entry.path_since_positioning_append(StateIndex)

        result.__state_index = StateIndex
        result.__parent = self
        return result

    @property 
    def state_index(self):  return self.__state_index
    @property
    def parent(self): return self.__parent
    def has_parent(self, Candidate):
        parent = self.__parent
        while parent is not None:
            if id(parent) == id(Candidate): return True
            parent = parent.parent
        return False

    @property
    def acceptance_trace(self):
        return self.__acceptance_trace

    def next_step(self, StateIndex, State):
        """The present object of PathTrace represents the history of events 
           along a path from the init state to the state BEFORE 'this state'.

           Applying the events of 'this state' on the current history results
           in a PathTrace object that represents the history of events until
           'this state'.

           RETURNS: Altered clone of the present object.
        """
        # Some experimenting has shown that the number of unnecessary cloning,
        # i.e.  when there would be no change, is negligible. The fact that
        # '.path_since_positioning()' has almost always to be adapted,
        # makes selective cloning meaningless. So, it is done the safe way:
        # (update .path_since_positioning during 'reproduction'.)
        result = self.reproduce(StateIndex) # Always clone. 

        # (2) Update '.__acceptance_trace' and '.__storage_db' according to occurring
        #     acceptances and store-input-position events.
        #     Origins must be sorted with the highest priority LAST, so that they will
        #     appear on top of the acceptance trace list.
        for origin in sorted(State.origins(), key=lambda x: x.pattern_id(), reverse=True):
            # Acceptance 
            if origin.is_acceptance():
                result.__acceptance_trace_add_at_front(origin, StateIndex)

            # Store Input Position Information
            if origin.input_position_store_f():
                result.__storage_db[origin.pattern_id()] = StoreInfo([StateIndex])

        assert len(result.__acceptance_trace) >= 1
        return result

    def __acceptance_trace_add_at_front(self, Origin, StateIndex):
        """Assume that the 'Origin' belongs to a state with index 'StateIndex' that
           comes after all states on the before considered path.
           Assume that the 'Origin' talks about 'acceptance'.
        """
        # If there is an unconditional acceptance, it dominates all previous 
        # occurred acceptances (philosophy of longest match).
        if Origin.pre_context_id() == E_PreContextIDs.NONE:
            del self.__acceptance_trace[:]

        # Input Position Store/Restore
        pattern_id = Origin.pattern_id()
        if Origin.input_position_restore_f():
            # Restorage of Input Position (Post Contexts): refer to the 
            # input position at the time when it was stored.
            entry                  = self.__storage_db[pattern_id]
            path_since_positioning = entry.path_since_positioning
        else:
            # Normally accepted patterns refer to the input position at 
            # the time of acceptance.
            path_since_positioning = [StateIndex]

        # Reoccurring information about an acceptance overwrites previous occurrences.
        for entry_i in (i for i, x in enumerate(self.__acceptance_trace) \
                        if x.pattern_id == pattern_id):
            del self.__acceptance_trace[entry_i]
            # From the above rule, it follows that there is only one entry per pattern_id.
            break

        entry = AcceptInfo(Origin.pre_context_id(), pattern_id,
                           AcceptingStateIndex  = StateIndex, 
                           PathSincePositioning = path_since_positioning) 

        # Insert at the beginning, because what comes last has the highest
        # priority.  (Philosophy of longest match). The calling function must
        # ensure that for one step on the path, the higher prioritized patterns
        # appear AFTER the lower prioritized ones.
        self.__acceptance_trace.insert(0, entry)

    def get(self, PreContextID):
        """RETURNS: AcceptInfo object for a given PreContextID."""
        for entry in self.__acceptance_trace:
            if entry.pre_context_id == PreContextID: return entry
        return None

    def is_equivalent(self, Other):
        """This function determines whether the path trace described in Other is
           equivalent to this trace. 
        """
        if   len(self.__acceptance_trace) != len(Other.__acceptance_trace): return False
        elif len(self.__storage_db)       != len(Other.__storage_db):       return False

        for x, y in izip(self.__acceptance_trace, Other.__acceptance_trace):
            if   x.pattern_id                     != y.pattern_id:              return False
            elif x.accepting_state_index          != y.accepting_state_index:   return False
            elif x.positioning_state_index        != y.positioning_state_index: return False
            elif x.transition_n_since_positioning != y.transition_n_since_positioning: return False

        for x, y in izip(sorted(self.__storage_db.iteritems()), sorted(Other.__storage_db.iteritems())):
            x_pattern_id, x_info = x
            y_pattern_id, y_info = y
            if   x_pattern_id                   != y_pattern_id:                   return False
            elif x_info.loop_f                  != y_info.loop_f:                  return False
            elif x_info.positioning_state_index != y_info.positioning_state_index: return False
        return True

    def generate_siblings_with_alternative_path(self, AcceptanceTrace):
        for accept_info in AcceptanceTrace:
            # Is there 'something' like accept_info?
            for mine in self.acceptance_trace:
                if     accept_info.pattern_id              == mine.pattern_id             \
                   and accept_info.accepting_state_index   == mine.accepting_state_index  \
                   and accept_info.positioning_state_index == mine.positioning_state_index:
                       pass

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
        return "".join([repr(x) for x in self.__acceptance_trace]) + "".join([repr(x) for x in self.__storage_db.iteritems()])

class StoreInfo(object):
    """ABSTRACT:
    
       Informs about a 'positioning action' that happened during the walk
       along a specific path from init state to 'this state'. 
       
       Used in function 'PathTrace.next_step()'.
       ------------------------------------------------------------------------
       
       EXPLANATION:

       A 'positioning action' is the storage of the current input position 
       into a dedicated position register. Objects of class 'StoreInfo'
       are stored in dictionaries where the key represents the pattern-id
       is at the same time the identifier of the position storage register.
       (Note, later the position register is remapped according to required
        entries.)

       'This state' means the state where the trace lead to. 

       The member '.path_since_positioning' gets one more state index appended
       at each transition along a path. 
       
       If a loop is detected '.transition_n_since_positioning' returns
       'E_TransitionN.VOID'.

       The member '.positioning_state_index' is the state where the positioning
       happend. If there is a loop along the path from '.positioning_state_index'
       to 'this state, then the '.transition_n_since_positioning' is set to 
       'E_TransitionN.VOID' (see comment above).
    """
    __slots__ = ('path_since_positioning', '__loop_f')
    def __init__(self, PathSincePositioning):
        self.path_since_positioning = PathSincePositioning
        self.__loop_f               = (len(PathSincePositioning) != len(set(PathSincePositioning)))

    def path_since_positioning_append(self, StateIndex):
        if StateIndex in self.path_since_positioning: self.__loop_f = True
        self.path_since_positioning.append(StateIndex)

    @property
    def loop_f(self):                         return self.__loop_f

    @property
    def transition_n_since_positioning(self): return self._transition_n_since_positioning

    def _transition_n_since_positioning(self):
        """The sole purpose for this function is to be callable by a derived class."""
        if self.__loop_f: return E_TransitionN.VOID
        return len(self.path_since_positioning) - 1

    @property
    def positioning_state_index(self):
        return self.path_since_positioning[0]

    def is_equal(self, Other):
        return     self.transition_n_since_positioning == Other.transition_n_since_positioning \
               and self.positioning_state_index          == Other.positioning_state_index

    def clone(self):
        return StoreInfo(copy(self.path_since_positioning))

    def __repr__(self):
        txt = ["---\n"]
        txt.append("    .path_since_positioning         = %s\n" % repr(self.path_since_positioning))
        return "".join(txt)

class AcceptInfo(StoreInfo):
    """ABSTRACT: 
    
       Information about the acceptance behavior in a state which is a result
       of events that happened before on a specific path from the init state
       to 'this_state'.
       ------------------------------------------------------------------------

       EXPLANATION:

       Acceptance of a pattern is something that occurs in case that the 
       state machine can no further proceed on a given input (= philosophy
       of 'longest match'), i.e. on 'drop-out'. 'AcceptInfo' objects tell 
       about the acceptance of a particular pattern (given by '.pattern_id').

       .pattern_id     -- Identifies the pattern that is concerned.

       .pre_context_id -- if E_PreContextIDs.NONE, then '.pattern_id' is
                          always accepted. If not, then the pre-context
                          must be checked before the pattern can be accepted.
       
       .accepting_state_index -- Index of the state that caused the acceptance 
                                 of the pattern somewhere before on the path.
                                 It may, as well be 'this state'.
       
       .transition_n_since_positioning -- Number of transitions since the storage
                                 of the input position needed to be done. If 
                                 it is E_TransitionN.VOID, then the number cannot
                                 be determined from the state machine (loop occurred).
       
       .positioning_state_index -- Identifies the state where the position needed
                                   to be stored. For post-context patterns this is
                                   different from the accepting state.
    """
    __slots__ = ("pre_context_id", 
                 "pattern_id", 
                 "accepting_state_index") 

    def __init__(self, PreContextID, PatternID, 
                 AcceptingStateIndex, 
                 PathSincePositioning): 
        self.pre_context_id        = PreContextID
        self.pattern_id            = PatternID
        self.accepting_state_index = AcceptingStateIndex
        StoreInfo.__init__(self, PathSincePositioning)

    def clone(self):
        result = AcceptInfo(self.pre_context_id, 
                            self.pattern_id, 
                            self.accepting_state_index, 
                            copy(self.path_since_positioning)) 
        return result

    def index_of_last_acceptance_on_path_since_positioning(self):
        L = len(self.path_since_positioning)
        return L - 1 - self.path_since_positioning[::-1].index(self.accepting_state_index)

    @property
    def transition_n_since_positioning(self):
        if self.pattern_id == E_AcceptanceIDs.FAILURE: 
            return E_TransitionN.LEXEME_START_PLUS_ONE
        return StoreInfo._transition_n_since_positioning(self)

    @property
    def positioning_state_index(self):
        return self.path_since_positioning[0]

    def is_equal(self, Other):
        if   self.pre_context_id                 != Other.pre_context_id:                 return False
        elif self.pattern_id                     != Other.pattern_id:                     return False
        elif self.accepting_state_index          != Other.accepting_state_index:          return False
        elif self.transition_n_since_positioning != Other.transition_n_since_positioning: return False
        elif self.positioning_state_index        != Other.positioning_state_index:        return False
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


