"""
_______________________________________________________________________________

This module produces an object of class Analyzer. It is a representation of an
analyzer state machine (object of class StateMachine) that is suited for code
generation. In particular, track analysis results in 'decorations' for states
which help to implement efficient code.

_______________________________________________________________________________
EXPLANATION:

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

_______________________________________________________________________________
(C) 2010-2013 Frank-Rene Schaefer
ABSOLUTELY NO WARRANTY
_______________________________________________________________________________
"""

import quex.engine.analyzer.track_analysis        as     track_analysis
import quex.engine.analyzer.optimizer             as     optimizer
from   quex.engine.analyzer.state.core            import AnalyzerState, ReloadState
from   quex.engine.analyzer.state.drop_out        import DropOut
from   quex.engine.analyzer.state.entry_action    import TransitionID, \
                                                         TransitionAction
from   quex.engine.analyzer.commands              import InputPDereference, \
                                                         InputPIncrement, \
                                                         InputPDecrement,  \
                                                         PreContextOK
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
from   itertools        import imap
from   operator         import attrgetter

def do(SM, EngineType=engine.FORWARD):

    analyzer = __main_analysis(SM, EngineType)
    # AnalyzerState.transition_map:    Interval --> DoorID

    # [Optional] Combination of states into MegaState-s.
    if len(Setup.compression_type_list) != 0:
        __mega_state_analysis(analyzer)
        # MegaState.transition_map:    Interval --> TargetByStateKey
        #                           or Interval --> DoorID

    return analyzer

def __main_analysis(SM, EngineType):
    # Generate Analyzer from StateMachine
    analyzer = Analyzer(SM, EngineType)

    # Optimize the Analyzer
    analyzer = optimizer.do(analyzer)

    # Assign DoorID-s to transition actions and relate transitions to DoorID-s.
    # ('.prepare_for_reload()' requires DoorID-s.)
    for state in analyzer.state_db.itervalues():
        state.entry.action_db.categorize(state.index)

    # Implement the infrastructure for 'reload':
    # -- Transition maps goto the 'reload procedure' upon 'buffer limit' code
    # -- The 'reload state' does certain things dependent on the from what state
    #    it is entered.
    # -- The states have a dedicated entry from after the reload procedure.
    for state in analyzer.state_db.itervalues():
        state.prepare_for_reload(analyzer)
    analyzer.reload_state.entry.action_db.categorize(analyzer.reload_state.index)

    for state in analyzer.state_db.itervalues():
        state.transition_map = state.transition_map.relate_to_door_ids(analyzer, state.index)

    return analyzer

def __mega_state_analysis(analyzer):
    """Tries to find MegaStates which combine multiple states into one.
    """
    mega_state_analyzer.do(analyzer)

    for mega_state in analyzer.mega_state_list:
        mega_state.prepare_for_reload(analyzer)
    analyzer.reload_state.entry.action_db.categorize(analyzer.reload_state.index)


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
        #     from_db:  state_index --> states reachable from state_index
        #     to_db:    state_index --> states having a path to state_index
        #
        self.__from_db, self.__to_db = SM.get_from_to_db()

        # (*) PathTrace database, Successor database
        self.__trace_db,       \
        self.__path_element_db = track_analysis.do(SM, self.__to_db)

        # (*) Prepare AnalyzerState Objects
        self.__state_db = dict([
            (state_index, self.prepare_state(SM.states[state_index], state_index))
            for state_index in self.__trace_db.iterkeys()]
        )

        self.reload_state = ReloadState(EngineType=self.__engine_type)

        self.__mega_state_list          = []
        self.__non_mega_state_index_set = set(state_index for state_index in SM.states.iterkeys())

        if not EngineType.requires_detailed_track_analysis():
            self.__position_register_map = None
            return
        else:
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

    def add_mega_states(self, MegaStateList):
        """Add MegaState-s into the analyzer and remove the states which are 
        represented by them.
        """
        for mega_state in MegaStateList:
            state_index_set = mega_state.implemented_state_index_set()
            for state_index in state_index_set:
                del self.__state_db[state_index]
            self.reload_state.remove_states(state_index_set)
            self.reload_state.add_state(mega_state, InitStateForwardF=False)

        self.__mega_state_list          = MegaStateList
        self.__non_mega_state_index_set = set(self.__state_db.iterkeys())

        self.__state_db.update(
           (mega_state.index, mega_state) for mega_state in MegaStateList
        )

    @property
    def mega_state_list(self):             return self.__mega_state_list
    @property
    def non_mega_state_index_set(self):    return self.__non_mega_state_index_set
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
    def acceptance_state_index_list(self): return self.__acceptance_state_index_list
    @property
    def to_db(self):
        """Map: state_index --> list of states which can be reached starting from state_index."""
        return self.__to_db
    @property
    def from_db(self):
        """Map: state_index --> list of states which which lie on a path to state_index."""
        return self.__from_db

    def iterable_target_state_indices(self, StateIndex):
        for i in self.__state_db[StateIndex].map_target_index_to_character_set.iterkeys():
            yield i
        yield None

    def prepare_state(self, OldState, StateIndex):
        """REQUIRES: 'self.init_state_forward_f', 'self.engine_type', 'self.__from_db'.
        """
        init_state_forward_f  = self.is_init_state_forward(StateIndex)

        state = AnalyzerState.from_State(OldState, StateIndex, set(), self.engine_type)

        ta = TransitionAction()
        cl = ta.command_list
        if self.engine_type.is_BACKWARD_PRE_CONTEXT():
            cl.extend(
                 PreContextOK(origin.pattern_id()) for origin in OldState.origins() \
                 if origin.is_acceptance() 
            )

        if state.transition_map.is_empty() and False: 
            # NOTE: We need a way to disable this exception for PathWalkerState-s(!)
            #       It safe, not to allow it, in general.
            #------------------------------------------------------------------------
            # If the state has no further transitions then the input character does 
            # not have to be read. This is so, since without a transition map, the 
            # state immediately drops out. The drop out transits to a terminal. 
            # Then, the next action will happen from the init state where we work
            # on the same position. If required the reload happens at that moment,
            # NOT before the empty transition block.
            #
            # This is not true for Path Walker States, so we offer the option 
            # 'ForceInputDereferencingF'
            assert StateIndex != self.init_state_index # Empty state machine! --> impossible

            if self.engine_type.is_FORWARD(): cl.append(InputPIncrement())
            else:                             cl.append(InputPDecrement())
        else:
            if self.engine_type.is_FORWARD(): cl.extend([InputPIncrement(), InputPDereference()])
            else:                             cl.extend([InputPDecrement(), InputPDereference()])

        # NOTE: The 'from reload transition' is implemented by 'prepare_for_reload()'
        for source_state_index in self.__from_db[StateIndex]: 
            assert source_state_index != E_StateIndices.NONE
            tid = TransitionID(StateIndex, source_state_index, TriggerId=0)
            state.entry.action_db.enter(tid, ta.clone())

        if StateIndex == self.init_state_index:
            tid_at_entry = TransitionID(StateIndex, E_StateIndices.NONE, TriggerId=0)
            if self.engine_type.is_FORWARD():
                ta = TransitionAction()
                ta.command_list.append(InputPDereference())
            state.entry.action_db.enter(tid_at_entry, ta)

        return state
                                      
    def get_action_at_state_machine_entry(self):
        assert self.engine_type.is_FORWARD()
        ##print "#action_db:", self.init_state_index
        ##for key, value in self.state_db[self.init_state_index].entry.action_db.iteritems():
        ##    print "#key:", key
        ##    print "#value:", value.door_id
        return self.state_db[self.init_state_index].entry.action_db.get_action(self.init_state_index, E_StateIndices.NONE)

    def get_depth_db(self):
        """Determine a database which tells about the minimum distance to the initial state.

            map: state_index ---> min. number of transitions from the initial state.

        """
        depth_db = { self.__init_state_index: 0, }

        work_set   = set(self.__state_db.keys())
        work_set.remove(self.__init_state_index)
        last_level = set([ self.__init_state_index ])
        level_i    = 1
        while len(work_set):
            len_before = len(work_set)
            this_level = set()
            for state_index in last_level:
                for i in self.iterable_target_state_indices(state_index):
                    if   i not in work_set: continue
                    elif i in depth_db:     continue 
                    depth_db[i] = level_i
                    this_level.add(i)
                    work_set.remove(i)
            assert len_before != len(work_set), "There are orphaned states!" 
            last_level = this_level
            level_i += 1

        return depth_db

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
        # => not only consider len(source_state_list) >= 2, but iterate
        for source_state in source_state_list:
            if source_state != E_StateIndices.NONE:                    return True

        # The 'source_state_list' contains only 'NONE'. Thus, the init state is not
        # entered from any other state.
        return False

    def last_acceptance_variable_required(self):
        """If one entry stores the last_acceptance, then the 
           correspondent variable is required to be defined.
        """
        if not self.__engine_type.is_FORWARD(): 
            return False
        for entry in imap(lambda x: x.entry, self.__state_db.itervalues()):
            if entry.action_db.has_Accepter(): return True
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
        accept_sequence = self.__trace_db[StateIndex].uniform_acceptance_sequence()
        if accept_sequence is not None:
            # (i) Uniform Acceptance Pattern for all paths through the state.
            # 
            #     Use one trace as prototype. No related state needs to store
            #     acceptance at entry. 
            for x in accept_sequence:
                result.accept(x.pre_context_id, x.pattern_id)
                # No further checks necessary after unconditional acceptance
                if     x.pre_context_id == E_PreContextIDs.NONE \
                   and x.pattern_id     != E_AcceptanceIDs.FAILURE: break
        else:
            # (ii) Non-Uniform Acceptance Patterns
            #
            #     Different paths to one state result in different acceptances. 
            #     There is only one way to handle this:
            #
            #     -- The acceptance must be stored in the state where it occurs, 
            #     -- and it must be restored here.
            #
            result.accept(E_PreContextIDs.NONE, E_AcceptanceIDs.VOID)

            # Dependency: Related states are required to store acceptance at state entry.
            for accepting_state_index in self.__trace_db[StateIndex].accepting_state_index_list():
                self.__require_acceptance_storage_db[accepting_state_index].append(StateIndex)

            # Later, a function will use the '__require_acceptance_storage_db' to 
            # implement the acceptance storage.

        # (*) Terminal Router
        for x in self.__trace_db[StateIndex].positioning_info():
            result.route_to_terminal(x.pattern_id, x.transition_n_since_positioning)

            if x.transition_n_since_positioning != E_TransitionN.VOID: continue

            # Request the storage of the position from related states.
            for state_index in x.positioning_state_index_set:
                self.__require_position_storage_db[state_index].append(
                        (StateIndex, x.pre_context_id, x.pattern_id))

            # Later, a function will use the '__require_position_storage_db' to 
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
        def add_Accepter(entry, PreContextId, PatternId):
            entry.action_db.add_Accepter_on_all(PreContextId, PatternId)

        for state_index in self.__require_acceptance_storage_db.iterkeys():
            entry = self.__state_db[state_index].entry
            # Only the trace content that concerns the current state is filtered out.
            # It should be the same for all traces through 'state_index'
            prototype = self.__trace_db[state_index].get_any_one()
            for x in sorted(prototype, key=attrgetter("pattern_id", "pre_context_id")):
                if x.accepting_state_index != state_index: 
                    continue
                add_Accepter(entry, x.pre_context_id, x.pattern_id)

    def acceptance_storage_post_pone_do(self, StateIndex, PatternId):

        pass 

    def acceptance_storage_post_pone_can_be_delegate(self, StateIndex, PatternId, MotherAcceptSequence):
        pass
            
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
                                    if i in self.__path_element_db[end_state_index])
                for target_index in index_iterable: # target_state_index_list: # index_iterable:
                    if target_index == state_index: # Position is stored upon entry in *other*
                        continue                    # state--not the state itself. 
                    entry = self.__state_db[target_index].entry

                    entry.action_db.add_StoreInputPosition(StateIndex       = target_index, 
                                                           FromStateIndex   = state_index, 
                                                           PreContextID     = pre_context_id, 
                                                           PositionRegister = pattern_id, 
                                                           Offset           = 0)

    def is_init_state_forward(self, StateIndex):
        return StateIndex == self.init_state_index and self.engine_type.is_FORWARD()     
                
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

