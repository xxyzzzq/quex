"""ABSTRACT:

This module produces an object of class Analyzer. It is a representation of an
analyzer state machine (object of class StateMachine) that is suited for code
generation. In particular, track analysis results in 'decorations' for states
which help to implement efficient code.

Formally an Analyzer consists of a set of states that are related by their
transitions. Each state is an object of class AnalyzerState and has the
following components:

    * entry:          actions to be performed at the entry of the state.

    * input:          what happens to get the next character.

    * transition_map: a map that tells what state is to be entered 
                      as a reaction to the current input character.

    * drop_out:       what has to happen if no character triggers.

For administrative purposes, other data such as the 'state_index' is stored
along with the AnalyzerState object.

The goal of track analysis is to reduce the run-time effort of the lexical
analyzer. In particular, acceptance and input position storages may be spared
depending on the constitution of the state machine.

-------------------------------------------------------------------------------
(C) 2010-2011 Frank-Rene Schaefer
ABSOLUTELY NO WARRANTY
"""

import quex.engine.analyzer.track_analysis        as     track_analysis
import quex.engine.analyzer.optimizer             as     optimizer
from   quex.engine.analyzer.state.core            import AnalyzerState
from   quex.engine.analyzer.state.drop_out        import DropOut
import quex.engine.analyzer.mega_state.analyzer   as     mega_state_analyzer
import quex.engine.analyzer.position_register_map as     position_register_map
import quex.engine.analyzer.engine_supply_factory as     engine
from   quex.engine.misc.tree_walker               import TreeWalker
from   quex.engine.state_machine.core             import StateMachine
from   quex.blackboard  import setup as Setup
from   quex.blackboard  import E_AcceptanceIDs, \
                               E_TransitionN, \
                               E_PreContextIDs, \
                               E_StateIndices

from   collections      import defaultdict
from   itertools        import islice, imap, izip

def do(SM, EngineType=engine.FORWARD):
    # Generate Analyzer from StateMachine
    analyzer = Analyzer(SM, EngineType)

    # Optimize the Analyzer
    analyzer = optimizer.do(analyzer)

    # The language database requires the analyzer for labels etc.
    if Setup.language_db is not None:
        Setup.language_db.register_analyzer(analyzer)

    # If required by the user: Combine some states into mega states.
    mega_state_analyzer.do(analyzer)

    return analyzer

class Analyzer:
    """A representation of a pattern analyzing StateMachine suitable for
       effective code generation.
    """
    def __init__(self, SM, EngineType):
        assert isinstance(EngineType, engine.Base), EngineType.__class__.__name__
        assert isinstance(SM, StateMachine)


        self.__acceptance_state_index_list = SM.get_acceptance_state_index_list()
        self.__init_state_index = SM.init_state_index
        self.__state_machine_id = SM.get_id()
        self.__engine_type      = EngineType

        # (*) From/To Databases
        #
        #     from_db:  state_index --> states from which it is entered.
        #     to_db:    state_index --> states which it enters
        #
        from_db = defaultdict(set)
        to_db   = defaultdict(set)
        for from_index, state in SM.states.iteritems():
            to_db[from_index] = set(state.transitions().get_map().iterkeys())
            for to_index in state.transitions().get_map().iterkeys():
                from_db[to_index].add(from_index)
        self.__from_db = from_db
        self.__to_db   = to_db

        # (*) PathTrace database, Successor database
        self.__trace_db, self.__path_element_db = track_analysis.do(SM, self.__to_db)

        # (*) Prepare AnalyzerState Objects
        self.__state_db = dict([
                (state_index, AnalyzerState(SM.states[state_index], state_index,
                                            state_index == SM.init_state_index, 
                                            EngineType, from_db[state_index])) 
                for state_index in self.__trace_db.iterkeys()])

        if not EngineType.requires_detailed_track_analysis():
            self.__position_register_map = None
            self.__position_info_db      = None
            return

        # (*) Uniform AcceptanceDB
        #
        #         map: state_index --> acceptance pattern
        #
        #     If all paths to a state show the same acceptance pattern, than this
        #     pattern is stored. Otherwise, the state index is related to None.
        self.__uniform_acceptance_db = dict(
                (state_index, self.__multi_path_acceptance_analysis(acceptance_trace_list))
                for state_index, acceptance_trace_list in self.__trace_db.iteritems())

        # (*) Positioning info:
        #
        #     map:  (state_index) --> (pattern_id) --> positioning info
        #
        self.__position_info_db = dict(
                (state_index, self.__multi_path_positioning_analysis(acceptance_trace_list))
                for state_index, acceptance_trace_list in self.__trace_db.iteritems())

        # (*) Drop Out Behavior
        #     The PathTrace objects tell what to do at drop_out. From this, the
        #     required entry actions of states can be derived.
        self.__require_acceptance_storage_db = defaultdict(list)
        self.__require_position_storage_db   = defaultdict(list)
        for state_index, trace_list in self.__trace_db.iteritems():
            self.__state_db[state_index].drop_out = self.configure_drop_out(state_index)

        # (*) Entry Behavior
        #     Implement the required entry actions.
        self.configure_entries(SM)

        if EngineType.requires_position_register_map():
            # (*) Position Register Map (Used in 'optimizer.py')
            self.__position_register_map = position_register_map.do(self)
        else:
            self.__position_register_map = None

    @property
    def trace_db(self):                    return self.__trace_db
    @property
    def state_db(self):                    return self.__state_db
    @property
    def init_state_index(self):            return self.__init_state_index
    @property
    def position_register_map(self):       return self.__position_register_map
    @property
    def state_machine_id(self):            return self.__state_machine_id
    @property
    def engine_type(self):                 return self.__engine_type
    @property
    def position_info_db(self):            return self.__position_info_db
    @property
    def acceptance_state_index_list(self): return self.__acceptance_state_index_list
    @property
    def to_db(self):
        """Map: state_index --> list of states that it enters."""
        return self.__to_db
    @property
    def from_db(self):
        """Map: state_index --> list of states that enter it."""
        return self.__from_db

    def has_transition_to_init_state(self):
        """Determine whether the init state is entered from another state.
        (If not, only the default entry into the init state is generated.)
        """
        if not self.__engine_type.is_FORWARD():                        return False
        if self.__engine_type.requires_buffer_limit_code_for_reload(): return True

        # Is there any state from where the init state is entered?
        source_state_list = self.__from_db.get(self.__init_state_index)

        if source_state_list is None:                                  return False
        if len(source_state_list) == 0:                                return False
        # To be 100% sure (robust against double occurence of NONE)
        for source_state in source_state_list:
            if source_state != E_StateIndices.NONE:                    return True

        # The 'source_state_list' contains only 'NONE'. Thus, the init state is not
        # entered from any other state.
        return False

    def has_successor(self, BeginStateIndex, WantedStateIndex):

        class Walker(TreeWalker):
            def __init__(self, ToDB, WantedStateIndex):
                self.wanted_state_index = WantedStateIndex
                self.to_db              = ToDB
                self.path               = []
                self.success_f          = True
                TreeWalker.__init__(self)

            def on_enter(self, Args):
                state_index = Args
                target_state_index_list = [ x for x in self.to_db[state_index] if x not in self.path ]
                if len(target_state_index_list) == 0:
                    return None

                if self.wanted_state_index in target_state_index_list:
                    self.success_f = True
                    self.abort_f   = True
                    return None

                self.path.append(state_index)

                return target_state_index_list

            def on_finished(self, Args):
                self.path.pop()

        walker = Walker(self.__to_db, WantedStateIndex)
        walker.do(BeginStateIndex)

        ## print "#has_successor:", BeginStateIndex, WantedStateIndex, walker.success_f
        return walker.success_f

    def last_acceptance_variable_required(self):
        """If one entry stores the last_acceptance, then the 
           correspondent variable is required to be defined.
        """
        if not self.__engine_type.is_FORWARD(): 
            return False
        for entry in imap(lambda x: x.entry, self.__state_db.itervalues()):
            if entry.has_accepter(): return True
        return False

    def configure_drop_out(self, StateIndex):
        """____________________________________________________________________
        Every analysis step ends with a 'drop-out'. At this moment it is
        decided what pattern has won. Also, the input position pointer must be
        set so that it indicates the right location where the next step starts
        the analysis. 

        Consequently, a drop-out action contains two elements:

            -- Acceptance Checker: Dependent on the fulfilled pre-contexts a
               winning pattern is determined. 

               If acceptance depends on stored acceptances, a request is raised
               at each accepting state that is has to store its acceptance in 
               variable 'last_acceptance'.

            -- Terminal Router: Dependent on the accepted pattern the input
               position is modified and the terminal containing the pattern
               action is entered.

               If the input position is restored from a position register, 
               then the storing states are requested to store the input
               position.

        _______________________________________________________________________
        HINT:

        A state may be reached via multiple paths. For each path there is a
        separate PathTrace. Each PathTrace tells what has to happen in the
        state depending on the pre-contexts being fulfilled or not (if there
        are even any pre-context patterns).
        _______________________________________________________________________
        """
        result = DropOut()

        # (*) Acceptance Checker
        acceptance_pattern = self.__uniform_acceptance_db[StateIndex]
        if acceptance_pattern is not None:
            # (i) Uniform Acceptance Pattern for all paths through the state.
            # 
            #     Use one trace as prototype. No related state needs to store
            #     acceptance at entry. 
            for x in acceptance_pattern:
                result.accept(x.pre_context_id, x.pattern_id)
                # No further checks after unconditional acceptance necessary
                if     x.pre_context_id == E_PreContextIDs.NONE \
                   and x.pattern_id     != E_AcceptanceIDs.FAILURE: break
        else:
            # (ii) Non-Uniform Acceptance Patterns
            #
            #     Different paths to one state result in different acceptances. 
            #     There is only one way to handle this:
            #
            #       -- The acceptance must be stored in the state where it occurs, and
            #       -- It must be restored here.
            #
            result.accept(E_PreContextIDs.NONE, E_AcceptanceIDs.VOID)

            # Dependency: Related states are required to store acceptance at state entry.
            for acceptance_trace_list in self.__trace_db[StateIndex]:
                for x in acceptance_trace_list:
                    self.__require_acceptance_storage_db[x.accepting_state_index].append(StateIndex)
            # Later on, a function will use the '__require_acceptance_storage_db' to 
            # implement the acceptance storage.

        # (*) Terminal Router
        for pattern_id, info in self.__position_info_db[StateIndex].iteritems():
            result.route_to_terminal(pattern_id, info.transition_n_since_positioning)

            if info.transition_n_since_positioning == E_TransitionN.VOID: 
                # Request the storage of the position from related states.
                for path in info.path_list_since_positioning:
                    position_storing_state_index = path[0]
                    self.__require_position_storage_db[position_storing_state_index].append(
                            (StateIndex, info.pre_context_id, pattern_id))
            # Later on, a function will use the '__require_position_storage_db' to 
            # implement the position storage.

        result.trivialize()
        return result

    def configure_entries(self, SM):
        """DropOut objects may rely on acceptances and input positions being 
           stored. This storage happens at state entries.
           
           Function 'configure_drop_out()' registers which states have to store
           the input position and which ones have to store acceptances. These
           tasks are specified in the two members:

                 self.__require_acceptance_storage_db
                 self.__require_position_storage_db

           It is tried to postpone the storing as much as possible along the
           state paths from store to restore. Thus, some states may not have to
           store, and thus the lexical analyzer becomes a little faster.
        """
        self.implement_required_acceptance_storage(SM)
        self.implement_required_position_storage()

    def detect_on_paths(self, BeginStateIndex, EndStateIndex, break_condition, break_action):

        class DetectorWalker(TreeWalker):
            """Walks all paths from StateIndex0 to StateIndex1, but only until  
            a condition is met. When the condition is met, an action is executed 
            and the path is no longer followed.
            ___________________________________________________________________
            """
            def __init__(self, EndStateIndex, StateDB, ToDB, TraceDB, BreakConditionFunc, ActionFunc):
                self.end_state_index = EndStateIndex

                self.state_db  = StateDB
                self.to_db     = ToDB
                self.trace_db  = TraceDB
                self.done_set  = set()
                self.condition = BreakConditionFunc
                self.action    = ActionFunc
                self.success_f = False
                TreeWalker.__init__(self)

            def on_enter(self, Args):
                PrevStateIndex, StateIndex = Args

                state = self.state_db[StateIndex]
                # Never break-up on the first state (neglect PrevStateIndex is None)
                if PrevStateIndex is not None and self.condition(state):
                    self.action(PrevStateIndex, state, self.trace_db)
                    self.done_set.add(StateIndex)
                    self.success_f = True
                    return None

                if StateIndex in self.done_set:
                    # Even, if the state was done, the entry from PrevStateIndex had
                    # to be consdired. Only then, it can be considered 'done'.
                    return None
                else:
                    # Since, we do a 'depth-first' search, nothing has to be undone.
                    # If a state is registered as 'done', then all of its sub-paths 
                    # can be considered as being treated.
                    self.done_set.add(StateIndex)

                if StateIndex == self.end_state_index:
                    return None

                return [(StateIndex, state_index) for state_index in self.to_db[StateIndex]]

            def on_finished(self, Node):
                pass

        walker = DetectorWalker(EndStateIndex, 
                                self.__state_db, self.__to_db, self.__trace_db,
                                break_condition, break_action)
        walker.do((None, BeginStateIndex))

        # -- True  => that the condition was met and an action has been performed
        # -- False => the condition was not met for any state.
        return walker.success_f

    def implement_required_acceptance_storage(self, SM):
        """
        Storing Acceptance / Postpone as much as possible.
        
        The stored 'last_acceptance' is only needed at the first time
        when it is restored. So, we could walk along the path from the 
        accepting state to the end of the path and see when this happens.
        
        Critical case:
        
          State V --- "acceptance = A" -->-.
                                            \
                                             State Y ----->  State Z
                                            /
          State W --- "acceptance = B" -->-'
        
        That is, if state Y is entered from state V is shall store 'A'
        as accepted, if it is entered from state W is shall store 'B'.
        In this case, we cannot walk the path further, and say that when
        state Z is entered it has to store 'A'. This would cancel the
        possibility of having 'B' accepted here. There is good news:
        
        ! During the 'configure_drop_out()' the last acceptance is restored    !
        ! if and only if there are at least two paths with differing           !
        ! acceptance patterns. Thus, it is sufficient to consider the restore  !
        ! of acceptance in the drop_out as a terminal condition.               !

        EXCEPTION:

        When a state is reached that is part of '__dangerous_positioning_state_set'
        then it is not safe to assume that all sub-paths have been considered.
        The acceptance must be stored immediately.
        """
        # Not Postponed: Collected acceptances to be stored in the acceptance states itself.
        #
        # Here, storing Acceptance cannot be deferred to subsequent states, because
        # the first state that restores acceptance is the acceptance state itself.
        #
        # (1) Restore only happens if there is non-uniform acceptance. See 
        #     function 'configure_drop_out(...)'. 
        # (2) Non-uniform acceptance only happens, if there are multiple paths
        #     to the same state with different trailing acceptances.
        # (3) If there was an absolute acceptance, then all previous trailing 
        #     acceptance were deleted (longest match). This contradicts (2).
        #
        # (4) => Thus, there are only pre-contexted acceptances in such a state.
        #
        # It is possible that a deferred acceptance are already present in the doors. But, 
        # since they all come from trailing acceptances, we know that the acceptance of
        # this state preceeds (longest match). Thus, all the acceptances we add here 
        # preceed the already mentioned ones. Since they all trigger on lexemes of the
        # same length, the only precendence criteria is the pattern_id.
        # 
        for state_index in self.__require_acceptance_storage_db.iterkeys():
            entry = self.__state_db[state_index].entry
            # Only the trace content that concerns the current state is filtered out.
            # It should be the same for all traces through 'state_index'
            prototype = self.__trace_db[state_index][0]
            for x in reversed(prototype):
                if x.accepting_state_index != state_index: continue
                entry.doors_accepter_add(x.pre_context_id, x.pattern_id)

    def implement_required_position_storage(self):
        """
        Store Input Position / Postpone as much as possible.

        Before we do not reach a state that actually restores the position, it
        does make little sense to store the input position. 

                         Critical Point: Loops and Forks

        If a loop is reached then the input position can no longer be determined
        by the transition number. The good news is that during 'configure_drop_out'
        any state that has undetermined positioning restores the input position.
        Thus 'restore_position_f(register)' is enough to catch this case.
        """
        for state_index, info_list in self.__require_position_storage_db.iteritems():
            target_state_index_list = self.__to_db[state_index]
            for end_state_index, pre_context_id, pattern_id in info_list:
                # state_index      --> state that stores the input position
                # end_state_index  --> state that stores the input position
                # pre_context_id   --> pre_context which is concerned
                # pattern_id       --> pattern which is concerned
                # Only consider target states which guide to the 'end_state_index'.
                index_iterable = (i for i in target_state_index_list 
                                    if end_state_index in self.__path_element_db[i])
                for target_index in index_iterable:
                    entry = self.__state_db[target_index].entry
                    entry.doors_store(FromStateIndex   = state_index, 
                                      PreContextID     = pre_context_id, 
                                      PositionRegister = pattern_id, 
                                      Offset           = 0)
                
    def __multi_path_positioning_analysis(self, ThePathTraceList):
        """
        This function draws conclusions on the input positioning behavior at
        drop-out based on different paths through the same state.  Basis for
        the analysis are the PathTrace objects of a state specified as
        'ThePathTraceList'.

        RETURNS: For a given state's PathTrace list a dictionary that maps:

                            pattern_id --> PositioningInfo

        --------------------------------------------------------------------
        
        There are the following alternatives for setting the input position:
        
           (1) 'lexeme_start_p + 1' in case of failure.

           (2) 'input_p + offset' if the number of transitions between
               any storing state and the current state is does not differ 
               dependent on the path taken (and does not contain loops).
        
           (3) 'input_p = position_register[i]' if (1) and (2) are not
               not the case.

        The detection of loops has been accomplished during the construction
        of the PathTrace objects for each state. This function focusses on
        the possibility to have different paths to the same state with
        different positioning behaviors.
        """
        class PositioningInfo(object):
            __slots__ = ("transition_n_since_positioning", 
                         "pre_context_id", 
                         "path_list_since_positioning")
            def __init__(self, PathTraceElement):
                self.transition_n_since_positioning = PathTraceElement.transition_n_since_positioning
                self.path_list_since_positioning    = [ PathTraceElement.path_since_positioning ]
                self.pre_context_id                 = PathTraceElement.pre_context_id

            @property
            def positioning_state_index_set(self):
                return set(path[0] for path in self.path_list_since_positioning)

            def add(self, PathTraceElement):
                self.path_list_since_positioning.append(PathTraceElement.path_since_positioning)

                if self.transition_n_since_positioning != PathTraceElement.transition_n_since_positioning:
                    self.transition_n_since_positioning = E_TransitionN.VOID

            def __repr__(self):
                txt  = ".transition_n_since_positioning = %s\n" % repr(self.transition_n_since_positioning)
                txt += ".positioning_state_index_set    = %s\n" % repr(self.positioning_state_index_set) 
                txt += ".pre_context_id                 = %s\n" % repr(self.pre_context_id) 
                # txt += ".path_since_positioning         = %s\n" % repr(self.path_list_since_positioning)
                return txt

        positioning_info_by_pattern_id = {}
        # -- If the positioning differs for one element in the trace list, or 
        # -- one element has undetermined positioning, 
        # => then the acceptance relates to undetermined positioning.
        for acceptance_trace in ThePathTraceList:
            for element in acceptance_trace:
                assert element.pattern_id != E_AcceptanceIDs.VOID

                prototype = positioning_info_by_pattern_id.get(element.pattern_id)
                if prototype is None:
                    positioning_info_by_pattern_id[element.pattern_id] = PositioningInfo(element)
                else:
                    prototype.add(element)

        return positioning_info_by_pattern_id

    def __multi_path_acceptance_analysis(self, ThePathTraceList):
        """
        This function draws conclusions on the input acceptance behavior at
        drop-out based on different paths through the same state. Basis for
        the analysis are the PathTrace objects of a state specified as
        'ThePathTraceList'.

        Acceptance Uniformity:

            For any possible path to 'this' state the acceptance pattern is
            the same. That is, it accepts exactly the same pattern under the
            same pre contexts and in the same sequence of precedence.

        The very nice thing is that the 'acceptance_trace' of a PathTrace
        object reflects the precedence of acceptance. Thus, one can simply
        compare the acceptance trace objects of each PathTrace.

        RETURNS: list of AcceptInfo() - uniform acceptance pattern.
                 None                 - acceptance pattern is not uniform.
        """
        prototype = ThePathTraceList[0]

        # Check (1) and (2)
        for acceptance_trace in islice(ThePathTraceList, 1, None):
            if len(prototype) != len(acceptance_trace):    return None
            for x, y in izip(prototype, acceptance_trace):
                if   x.pre_context_id != y.pre_context_id: return None
                elif x.pattern_id     != y.pattern_id:     return None

        return prototype

    def __iter__(self):
        for x in self.__state_db.values():
            yield x

    def __repr__(self):
        # Provide some type of order that is oriented towards the content of the states.
        # This helps to compare analyzers where the state identifiers differ, but the
        # states should be the same.
        def order(X):
            side_info = 0
            if len(X.transition_map) != 0: side_info = max(trigger_set.size() for trigger_set, t in X.transition_map)
            return (len(X.transition_map), side_info, X.index)

        txt = [ repr(state) for state in sorted(self.__state_db.itervalues(), key=order) ]
        return "".join(txt)

