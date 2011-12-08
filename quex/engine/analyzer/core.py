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
import quex.engine.analyzer.position_register_map as     position_register_map
from   quex.engine.state_machine.core             import StateMachine
from   quex.blackboard  import E_StateIndices, \
                               E_PostContextIDs, \
                               E_AcceptanceIDs, \
                               E_EngineTypes, \
                               E_TransitionN, \
                               E_PreContextIDs, \
                               E_InputActions

from   collections      import defaultdict, namedtuple
from   operator         import itemgetter, attrgetter
from   itertools        import islice, ifilter, imap, izip
from   quex.blackboard  import setup as Setup

def do(SM, EngineType=E_EngineTypes.FORWARD):
    # Generate Analyzer from StateMachine
    analyzer = Analyzer(SM, EngineType)

    # Optimize the Analyzer
    analyzer = optimizer.do(analyzer)

    # The language database requires the analyzer for labels etc.
    if Setup.language_db is not None:
        Setup.language_db.register_analyzer(analyzer)

    return analyzer

class Analyzer:
    """A representation of a pattern analyzing StateMachine suitable for
       effective code generation.
    """
    def __init__(self, SM, EngineType):
        assert EngineType in E_EngineTypes
        assert isinstance(SM, StateMachine)

        self.__acceptance_state_index_list = SM.get_acceptance_state_index_list()
        self.__init_state_index = SM.init_state_index
        self.__state_machine_id = SM.get_id()
        self.__engine_type      = EngineType

        # (*) PathTrace database, Successor database
        self.__trace_db, self.__successor_db = track_analysis.do(SM)

        # (*) 'From Database'
        #
        #     map:  state_index --> states from which it is entered.
        #
        from_db = defaultdict(set)
        for from_index, state in SM.states.iteritems():
            for to_index in state.transitions().get_map().iterkeys():
                from_db[to_index].add(from_index)
        self.__from_db = from_db

        # (*) Prepare AnalyzerState Objects
        self.__state_db = dict([(state_index, AnalyzerState(state_index, SM, EngineType, from_db[state_index])) 
                                 for state_index in self.__trace_db.iterkeys()])

        if EngineType != E_EngineTypes.FORWARD:
            # BACKWARD_INPUT_POSITION, BACKWARD_PRE_CONTEXT:
            #
            # DropOut and Entry do not require any construction beyond what is
            # accomplished inside the constructor of 'AnalyzerState'. No positions
            # need to be stored and restored.
            self.__position_register_map = None
            self.__position_info_db      = None
            return

        # (*) Positioning info:
        #
        #     map:  (state_index) --> (pattern_id) --> positioning info
        #
        self.__position_info_db = {}
        for state_index, trace_list in self.__trace_db.iteritems():
            self.__position_info_db[state_index] = self.multi_path_positioning_analysis(trace_list)

        # (*) Drop Out Behavior
        #     The PathTrace objects tell what to do at drop_out. From this, the
        #     required entry actions of states can be derived.
        self.__require_acceptance_storage_list = []
        self.__require_position_storage_list   = []
        for state_index, trace_list in self.__trace_db.iteritems():
            state = self.__state_db[state_index]
            # trace_list: PathTrace objects for each path that guides through state.
            self.configure_drop_out(state, trace_list)

        # (*) Entry Behavior
        #     Implement the required entry actions.
        self.configure_entries()

        # (*) Position Register Map (Used in 'optimizer.py')
        self.__position_register_map = position_register_map.do(self)

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
    def from_db(self):
        """Map: state_index --> list of states that enter it."""
        return self.__from_db
    def last_acceptance_variable_required(self):
        """If one entry stores the last_acceptance, then the 
           correspondent variable is required to be defined.
        """
        if self.__engine_type != E_EngineTypes.FORWARD: return False
        for entry in imap(lambda x: x.entry, self.__state_db.itervalues()):
            if entry.has_accepter(): return True
        return False

    def configure_drop_out(self, state, ThePathTraceList):
        """Every analysis step ends with a 'drop-out'. At this moment it is
           decided what pattern has won. Also, the input position pointer
           must be set so that it indicates the right location where the
           next step starts the analysis. 

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

           --------------------------------------------------------------------
           HINT:
           A state may be reached via multiple paths. For each path there is a
           separate PathTrace. Each PathTrace tells what has to happen in the state
           depending on the pre-contexts being fulfilled or not (if there are
           even any pre-context patterns).
        """
        assert len(ThePathTraceList) != 0
        result = DropOut()

        # (*) Acceptance Checker
        uniform_f = self.multi_path_acceptance_analysis(ThePathTraceList)
        if uniform_f:
            # (i) Uniform Acceptance Pattern for all paths through the state.
            # 
            #     Use one trace as prototype. No related state needs to store
            #     acceptance at entry. 
            prototype = ThePathTraceList[0]
            for x in prototype.acceptance_trace:
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
            #         -- The acceptance must be stored in the state where it occurs, and
            #         -- It must be restored here.
            #
            result.accept(E_PreContextIDs.NONE, E_AcceptanceIDs.VOID)

            # Dependency: Related states are required to store acceptance at state entry.
            for trace in ThePathTraceList:
                self.__require_acceptance_storage_list.extend(trace.acceptance_trace)

        # (*) Terminal Router
        for pattern_id, info in self.__position_info_db[state.index].iteritems():
            result.route_to_terminal(pattern_id, info.transition_n_since_positioning)

            if info.transition_n_since_positioning == E_TransitionN.VOID: 
                # Request the storage of the position from related states.
                self.__require_position_storage_list.append((state.index, pattern_id, info))

        result.trivialize()
        state.drop_out = result

    def configure_entries(self):
        """During the generation of drop-out actions for states the requirements
           for entry actions into states have been derived. This function 
           implements those requirements.

           As an optimization, it tries to postpone the acceptance and input
           position storage as much as possible, so that every lexeme that
           passes only to the non-storing segment profits from not having
           to store the input position.
        """
        for element in self.__require_acceptance_storage_list:
            entry = self.__state_db[element.accepting_state_index].entry
            entry.doors_accept(element.pattern_id, element.pre_context_id)

        for state_index, pattern_id, info in self.__require_position_storage_list:
            for pos_state_index in info.positioning_state_index_set:
                positioning_state = self.__state_db[pos_state_index]

                # Let index be the index of the currently considered state. Then,
                # Let x be one of the target states of the positioning state. 
                # If (index == x) or (index in self.__successor_db[x])
                # => The path from positioning state over x guides to current state
                for target_index in ifilter(lambda x: state_index == x or state_index in self.__successor_db[x],
                                            positioning_state.target_index_list):
                    if target_index == pos_state_index: continue
                    entry = self.__state_db[target_index].entry
                    entry.doors_store(FromStateIndex   = pos_state_index, \
                                      PreContextID     = info.pre_context_id, \
                                      PositionRegister = pattern_id)

    def multi_path_positioning_analysis(self, ThePathTraceList):
        """This function draws conclusions on the input positioning behavior at
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
                         "positioning_state_index_set")
            def __init__(self, PathTraceElement):
                self.transition_n_since_positioning = PathTraceElement.transition_n_since_positioning
                self.positioning_state_index_set    = set([ PathTraceElement.positioning_state_index ])
                self.pre_context_id                 = PathTraceElement.pre_context_id

            def __repr__(self):
                txt  = ".transition_n_since_positioning = %s\n" % repr(self.transition_n_since_positioning)
                txt += ".positioning_state_index_set    = %s\n" % repr(self.positioning_state_index_set) 
                txt += ".pre_context_id                 = %s\n" % repr(self.pre_context_id) 
                return txt

        positioning_info_by_pattern_id = {}
        # -- If the positioning differs for one element in the trace list, or 
        # -- one element has undetermined positioning, 
        # => then the acceptance relates to undetermined positioning.
        for trace in ThePathTraceList:
            for element in trace.acceptance_trace:
                assert element.pattern_id != E_AcceptanceIDs.VOID

                prototype = positioning_info_by_pattern_id.get(element.pattern_id)
                if prototype is None:
                    positioning_info_by_pattern_id[element.pattern_id] = PositioningInfo(element)
                    continue

                prototype.positioning_state_index_set.add(element.positioning_state_index)

                if prototype.transition_n_since_positioning != element.transition_n_since_positioning:
                    prototype.transition_n_since_positioning = E_TransitionN.VOID

        return positioning_info_by_pattern_id

    def multi_path_acceptance_analysis(self, ThePathTraceList):
        """This function draws conclusions on the input positioning behavior at
           drop-out based on different paths through the same state.  Basis for
           the analysis are the PathTrace objects of a state specified as
           'ThePathTraceList'.

           Acceptance Uniformity:

               For any possible path to 'this' state the acceptance pattern is
               the same. That is, it accepts exactly the same pattern under the
               same pre contexts and in the same sequence of precedence.

           The very nice thing is that the 'acceptance_trace' of a PathTrace
           object reflects the precedence of acceptance. Thus, one can simply
           compare the acceptance trace objects of each PathTrace.

           RETURNS: True  - uniform acceptance pattern.
                    False - acceptance pattern is not uniform.

        """
        prototype = ThePathTraceList[0].acceptance_trace

        # Check (1) and (2)
        for path_trace in islice(ThePathTraceList, 1, None):
            acceptance_trace = path_trace.acceptance_trace
            if len(prototype) != len(acceptance_trace):    return False
            for x, y in izip(prototype, acceptance_trace):
                if   x.pre_context_id != y.pre_context_id: return False
                elif x.pattern_id     != y.pattern_id:     return False

        return True

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

class AnalyzerState(object):
    """AnalyzerState consists of the following major components:

       entry -- tells what has to happen at entry to the state (depending 
                on the state from which it is entered).

       input -- determined how to access the character that is used for 
                transition triggering.

       transition_map -- telling what subsequent state is to be entered
                         dependent on the triggering character.

       drop_out -- contains information about what happens when the 
                   transition map cannot trigger on the character.
    """
    __slots__ = ("__index", 
                 "__init_state_f", 
                 "__target_index_list", 
                 "__engine_type", 
                 "__state_machine_id",
                 "input", 
                 "entry", 
                 "map_target_index_to_character_set", 
                 "transition_map", 
                 "drop_out", 
                 "_origin_list")

    def __init__(self, StateIndex, SM, EngineType, FromStateIndexList):
        assert type(StateIndex) in [int, long]
        assert EngineType in E_EngineTypes

        state = SM.states[StateIndex]

        self.__index            = StateIndex
        self.__init_state_f     = SM.init_state_index == StateIndex
        self.__engine_type      = EngineType

        # (*) Input
        self.input = get_input_action(EngineType, self.__init_state_f)

        # (*) Entry Action
        if   EngineType == E_EngineTypes.FORWARD: 
            self.entry = Entry(FromStateIndexList)
        elif EngineType == E_EngineTypes.BACKWARD_PRE_CONTEXT: 
            self.entry = EntryBackward(state.origins())
        elif EngineType == E_EngineTypes.BACKWARD_INPUT_POSITION: 
            self.entry = EntryBackwardInputPositionDetection(state.origins(), state.is_acceptance())
        else:
            assert False

        # (*) Transition
        if EngineType == E_EngineTypes.BACKWARD_INPUT_POSITION:
            # During backward input detection, an acceptance state triggers a
            # return from the searcher, thus no further transitions are necessary.
            # (orphaned states, also, need to be deleted).
            ## if state.is_acceptance(): assert state.transitions().is_empty()
            pass

        self.transition_map                    = state.transitions().get_trigger_map()
        self.__target_index_list               = state.transitions().get_map().keys()
        # Currently, the following is only used for path compression. If the alternative
        # is implemented, then the following is no longer necessary.
        self.map_target_index_to_character_set = state.transitions().get_map()

        # (*) Drop Out
        if   EngineType == E_EngineTypes.FORWARD: 
            # DropOut and Entry interact and require sophisticated analysis
            # => See "Analyzer.get_drop_out_object(...)"
            self.drop_out = None 

        elif EngineType == E_EngineTypes.BACKWARD_PRE_CONTEXT:
            self.drop_out = DropOutBackward()
        elif EngineType == E_EngineTypes.BACKWARD_INPUT_POSITION:
            self.drop_out = DropOutBackwardInputPositionDetection(state.is_acceptance())

        self._origin_list = state.origins().get_list()

    @property
    def index(self):                  return self.__index
    def set_index(self, Value):       assert isinstance(Value, long); self.__index = Value
    @property
    def init_state_f(self):           return self.__init_state_f
    @property
    def init_state_forward_f(self):   return self.__init_state_f and self.__engine_type == E_EngineTypes.FORWARD
    @property
    def engine_type(self):            return self.__engine_type
    def set_engine_type(self, Value): assert Value in E_EngineTypes; self.__engine_type = Value     
    @property
    def target_index_list(self):      return self.__target_index_list
    @property
    def transition_map_empty_f(self): 
        L = len(self.transition_map)
        if   L > 1:  return False
        elif L == 0: return True
        elif self.transition_map[0][1] == E_StateIndices.DROP_OUT: return True
        return False

    def get_string_array(self, InputF=True, EntryF=True, TransitionMapF=True, DropOutF=True):
        txt = [ "State %s:\n" % repr(self.index).replace("L", "") ]
        if InputF:         txt.append("  .input: move position %s\n" % repr(self.input))
        if EntryF:         txt.append("  .entry:\n"); txt.append(repr(self.entry))
        if TransitionMapF: txt.append("  .transition_map:\n")
        if DropOutF:       txt.extend(["  .drop_out:\n",    repr(self.drop_out)])
        txt.append("\n")
        return txt

    def get_string(self, InputF=True, EntryF=True, TransitionMapF=True, DropOutF=True):
        return "".join(self.get_string_array(InputF, EntryF, TransitionMapF, DropOutF))

    def __repr__(self):
        return self.get_string()

class BASE_Entry(object):
    def uniform_doors_f(self):
        assert False, "This function needs to be overloaded for '%s'" % self.__class__.__name__
    def has_special_door_from_state(self, StateIndex):
        """Require derived classes to be more specific, if necessary."""
        return not self.uniform_doors_f()

class EntryAction(object):
    @staticmethod
    def type_id():      assert False
    def priority(self): assert False

# EntryAction_StoreInputPosition: 
#
# Storing the input position is actually dependent on the pre_context_id, if 
# there is one. The pre_context_id is left out for the following reasons:
#
# -- Testing the pre_context_id is not necessary.
#    If a pre-contexted acceptance is reach where the pre-context is required
#    two things can happen: 
#    (i) Pre-context-id is not fulfilled, then no input position needs to 
#        be restored. Storing does no harm.
#    (ii) Pre-context-id is fulfilled, then the position is restored. 
#
# -- Avoiding overhead for pre_context_id test.
#    In case (i) cost = test + jump, (ii) cost = test + assign + jump. Without
#    test (i) cost = assign, (ii) cost = storage. Assume cost for test <= assign.
#    Thus not testing is cheaper.
#
# -- In the process of register economization, some post contexts may use the
#    same position register. The actions which can be combined then can be 
#    easily detected, if no pre-context is considered.
class EntryAction_StoreInputPosition(object):
    __slots__ = ["pre_context_id", "position_register"]
    def __init__(self, PreContextID, PositionRegister):
        self.pre_context_id    = PreContextID
        self.position_register = PositionRegister

    # Require 'type_id' and 'priority' for sorting of entry actions.
    @staticmethod
    def type_id():      return 0
    def priority(self): return - self.position_register

    # Require '__hash__' and '__eq__' to be element of a set.
    def __hash__(self):
        return 1
    def __eq__(self, Other):
        if not isinstance(Other, EntryAction_StoreInputPosition): return False
        return     self.pre_context_id    == Other.pre_context_id \
               and self.position_register == Other.position_register

# EntryAction_AcceptPattern:
# 
# In this case the pre-context-id is essential. We cannot accept a pattern if
# its pre-context is not fulfilled.
EntryAction_AcceptPattern      = namedtuple("EntryAction_AcceptPattern",      ["pre_context_id", "acceptance_id"  ])
class EntryAction_AcceptPattern(object):
    __slots__ = ["pre_context_id", "acceptance_id"]
    def __init__(self, PreContextID, AcceptanceID):
        self.pre_context_id = PreContextID
        self.acceptance_id  = AcceptanceID

    # Require 'type_id' and 'priority' for sorting of entry actions.
    @staticmethod
    def type_id():      return 1
    def priority(self): return - self.acceptance_id

    # Require '__hash__' and '__eq__' to be element of a set.
    def __hash__(self):
        return 1
    def __eq__(self, Other):
        if not isinstance(Other, EntryAction_AcceptPattern): return False
        return     self.pre_context_id == Other.pre_context_id \
               and self.acceptance_id  == Other.acceptance_id

class Entry(BASE_Entry):
    """An entry has potentially two tasks:
    
          (1) Storing information about positioning represented by objects 
              of type 'EntryAction_StoreInputPosition'.

          (2) Storing information about an acceptance. represented by objects
              of type 'EntryAction_StoreInputPosition'.
              
       Entry actions are relative from which state it is entered. Thus, an 
       object of this class contains a dictionary that maps:

                 from_state_index  --> list of entry actions

    """
    __slots__ = ("__uniform_doors_f", "__doors_db")

    def __init__(self, FromStateIndexList):
        # map:  (from_state_index) --> list of actions to be taken if state is entered 
        #                              'from_state_index' for a given pre-context.
        if len(FromStateIndexList) == 0:
            FromStateIndexList = [ E_StateIndices.NONE ]
        self.__doors_db = dict([ (i, set()) for i in FromStateIndexList ])

        # Are the actions for all doors the same?
        self.__uniform_doors_f = None 

    def doors_accept(self, PatternID, PreContextID):
        # Add accepter to every door.
        for door in self.__doors_db.itervalues():
            door.add(EntryAction_AcceptPattern(PreContextID, PatternID))

    def doors_store(self, FromStateIndex, PreContextID, PositionRegister):
        # Add 'store input position' to specific door. See 'EntryAction_StoreInputPosition'
        # comment for the reason why we do not store pre-context-id.
        entry = EntryAction_StoreInputPosition(PreContextID, PositionRegister)
        self.__doors_db[FromStateIndex].add(entry)

    def door_number(self):
        total_size = len(self.__doors_db)
        # Note, that total_size can be '0' in the 'independent_of_source_state' case
        if self.__uniform_doors_f: return min(1, total_size)
        else:                      return total_size

    def door_actions(self, DoorID):
        def criteria(Action):
            return (Action.type_id(), Action.priority())
        action_list = self.__doors_db[DoorID]
        action_list.sort(key=criteria)
        return action_list

    def get_accepter(self):
        """Returns information about the acceptance sequence. Lines that are dominated
           by the unconditional pre-context are filtered out. Returns pairs of

                          (pre_context_id, acceptance_id)
        """
        result = set()
        for door in self.__doors_db.itervalues():
            acceptance_actions = [action for action in door if isinstance(action, EntryAction_AcceptPattern)]
            result.update(acceptance_actions)

        result = list(result)
        result.sort(key=attrgetter("acceptance_id"))
        return result

    def size_of_accepter(self):
        """Count the number of difference acceptance ids."""
        db = set()
        for door in self.__doors_db.itervalues():
            for action in door:
                if not isinstance(action, EntryAction_AcceptPattern): continue
                db.add(action.acceptance_id)
        return len(db)

    def has_accepter(self):
        for door in self.__doors_db.itervalues():
            for action in door:
                if isinstance(action, EntryAction_AcceptPattern): return True
        return False

    def clear_accepter(self):
        for door in self.__doors_db.itervalues():
            for action in list(door):
                if not isinstance(action, EntryAction_AcceptPattern): continue
                door.remove(action)
        return False

    def get_positioner_db(self):
        """RETURNS: PositionDB
        
           where PositionDB maps:
        
                   from_state_index  -->   Positioner
 
           where Positioner is a list of actions to be taken when the state is entered
           from the given 'from_state_index'.
        """
        return self.__doors_db

    def __hash__(self):
        result = 0
        for action_set in self.__doors_db.itervalues():
            result += len(action_set)
        return result

    def __eq__(self, Other):
        if len(self.__doors_db) != len(Other.__doors_db): 
            return False
        for from_state_index, action_list in self.__doors_db.iteritems():
            other_action_list = Other.__doors_db.get(from_state_index)
            if other_action_list is None: return False
            if action_list != other_action_list: return False
        return True

    def is_equal(self, Other):
        # Maybe, we can delete this ...
        return self.__eq__(self, Other)

    def uniform_doors_f(self): 
        return self.__uniform_doors_f

    def get_uniform_door_prototype(self): 
        if not self.__uniform_doors_f: return None
        return self.__doors_db.itervalues().next()

    def get_door_group_tree(self):
        """Grouping and categorizing of entry doors:

           -- All doors which are exactly the same appear in the same group.
           -- Some doors perform actions which are a superset of the actions
              of other doors. The groups of those are organized in hierarchical
              order-from superset to subset. The member '.subset' of each
              group points to the branches of a node.

           Doors are identified by their 'from_state_index'.
        """
        # (1) grouping:
        group_db = defaultdict(list)
        for from_state_index, door in self.__doors_db.iteritems():
            group_db[sorted(door)].append(from_state_index)

    def has_special_door_from_state(self, StateIndex):
        """Determines whether the state has a special entry from state 'StateIndex'.
           RETURNS: False -- if entry is not at all source state dependent.
                          -- if there is no single door for StateIndex to this entry.
                          -- there is one or less door for the given StateIndex.
                    True  -- If there is an entry that depends on StateIndex in exclusion
                             of others.
        """
        if   self.__uniform_doors_f:    return False
        elif len(self.__doors_db) <= 1: return False
        return self.__doors_db.has_key(StateIndex)

    def finish(self, PositionRegisterMap):
        """Once the whole state machine is analyzed and positioner and accepters
           are set, the entry can be 'finished'. That means that some simplifications
           may be accomplished:

           (1) If a position for a post-context is stored in the unconditional
               case, then all pre-contexted position storages of the same post-
               context are superfluous.

           (2) If the entry into the state behaves the same for all 'from'
               states then the entry is independent_of_source_state.
        
        
           At state entry the positioning might differ dependent on the the
           state from which it is entered. If the positioning is the same for
           each source state, then the positioning can be unified.

           A unified entry is coded as 'ALL' --> common positioning.
        """
        if len(self.__doors_db) == 0: 
            self.__uniform_doors_f = True
            return

        # (*) Some post-contexts may use the same position register. Those have
        #     been identified in PositionRegisterMap. Do the replacement.
        for from_state_index, door in self.__doors_db.items():
            if len(door) == 0: continue
            new_door = set()
            for action in door:
                if not isinstance(action, EntryAction_StoreInputPosition):
                    new_door.add(action)
                else:
                    new_door.add(EntryAction_StoreInputPosition(action.pre_context_id, PositionRegisterMap[action.position_register]))
            self.__doors_db[from_state_index] = new_door

        # (*) If a door stores the input position in register unconditionally,
        #     then all other conditions concerning the storage in that register
        #     are nonessential.
        for door in self.__doors_db.itervalues():
            for action in list(x for x in door \
                               if     isinstance(x, EntryAction_StoreInputPosition) \
                                  and x.pre_context_id == E_PreContextIDs.NONE):
                for x in list(x for x in door \
                             if isinstance(x, EntryAction_StoreInputPosition)):
                    if x.position_register == action.position_register and x.pre_context_id != E_PreContextIDs.NONE:
                        door.remove(x)

        # (*) Check whether state entries are independent_of_source_state
        self.__uniform_doors_f = True
        iterable               = self.__doors_db.itervalues()
        prototype              = iterable.next()
        for dummy in ifilter(lambda x: x != prototype, iterable):
            self.__uniform_doors_f = False
            return
        return 

    def __repr__(self):
        txt = []
        if self.has_accepter() != 0:
            txt.append("    .accepter:\n")
            if_str = "if     "
            for action in self.get_accepter():
                if action.pre_context_id != E_PreContextIDs.NONE:
                    txt.append("        %s %s: " % (if_str, repr_pre_context_id(action.pre_context_id)))
                else:
                    txt.append("        ")
                txt.append("last_acceptance = %s\n" % repr_acceptance_id(action.acceptance_id))
                if_str = "else if"


        ptxt = []
        for from_state_index, door in sorted(self.__doors_db.iteritems(), key=itemgetter(0)):
            if from_state_index == E_StateIndices.NONE: continue
            ptxt.append("        .from %s:" % repr(from_state_index).replace("L", ""))
            positioner_action_list = [action for action in door if isinstance(action, EntryAction_StoreInputPosition)]
            positioner_action_list.sort(key=lambda x: (x.pre_context_id, x.position_register))
            if   len(positioner_action_list) == 0: 
                content = " <nothing>\n"
            else:
                content = ""
                for action in positioner_action_list:
                    if action.pre_context_id != E_PreContextIDs.NONE:
                        content += " if '%s': " % repr_pre_context_id(action.pre_context_id)
                    content += " %s = input_p;\n" % repr_position_register(action.position_register)
            if content.count("\n") != 1: 
                ptxt.append("\n")
                content = "            " + content[:-1].replace("\n", "\n            ") + "\n"
            ptxt.append(content)

        if len(ptxt) != 0:
            txt.append("    .positioner:\n")
            txt.extend(ptxt)

        return "".join(txt)

class EntryBackwardInputPositionDetection(BASE_Entry):
    """There is not much more to say then: 

       Acceptance State 
       => then we found the input position => return immediately.

       Non-Acceptance State
       => proceed with the state transitions (do nothing here)

       NOTE: This type supports being a dictionary key by '__hash__' and '__eq__'.
             Required for the optional 'template compression'.
    """
    __slots__ = ("__terminated_f")

    def __init__(self, OriginList, StateMachineID):
        self.__terminated_f = False
        for origin in ifilter(lambda origin: origin.is_acceptance(), OriginList):
            self.__terminated_f = True
            return

    def uniform_doors_f(self):
        # There is no difference from which state we enter
        return True

    def __hash__(self):
        return hash(int(self.__terminated_f))

    def __eq__(self, Other):
        return self.__terminated_f == Other.__terminated_f 

    def is_equal(self, Other):
        return self.__eq__(Other)

    @property
    def terminated_f(self): return self.__terminated_f

    def __repr__(self):
        if self.__terminated_f: return "    Terminated\n"
        else:                   return ""

class EntryBackward(BASE_Entry):
    """(*) Backward Lexing

       Backward lexing has the task to find out whether a pre-context is fulfilled.
       But it does not stop, since multiple pre-contexts may still be fulfilled.
       Thus, the set of fulfilled pre-contexts is stored in 

                    ".pre_context_fulfilled_set"

       This list can be determined beforehand from the origin list. 

       NOTE: This type supports being a dictionary key by '__hash__' and '__eq__'.
             Required for the optional 'template compression'.
    """
    __slots__ = ("__pre_context_fulfilled_set")
    def __init__(self, OriginList):
        self.__pre_context_fulfilled_set = set([])
        for origin in ifilter(lambda origin: origin.is_acceptance(), OriginList):
            self.__pre_context_fulfilled_set.add(origin.pattern_id())

    def __hash__(self):
        return hash(len(self.__pre_context_fulfilled_set))

    def __eq__(self, Other):
        # NOTE: set([0, 1, 2]) == set([2, 1, 0]) 
        #       ... equal if elements are the same, order not important
        return self.pre_context_fulfilled_set == Other.pre_context_fulfilled_set

    def uniform_doors_f(self):
        return True

    def is_equal(self, Other):
        return self.__eq__(Other)

    @property
    def pre_context_fulfilled_set(self):
        return self.__pre_context_fulfilled_set

    def __repr__(self):
        if len(self.pre_context_fulfilled_set) == 0: return ""
        txt = ["    EntryBackward:\n"]
        txt.append("    pre-context-fulfilled = %s;\n" % repr(list(self.pre_context_fulfilled_set))[1:-1])
        return "".join(txt)

class DropOut(object):
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

       The first sub-task is described by the member '.acceptance_checker' which is a list
       of objects of class 'DropOut_AcceptanceCheckerElement'. An empty list means that
       there is no check and the acceptance has to be restored from 'last_acceptance'.
       
       The second sub-task is described by member '.terminal_router' which is a list of 
       objects of class 'DropOut_TerminalRouterElement'.

       The exact content of both lists is determined by analysis of the acceptance
       trances.

       NOTE: This type supports being a dictionary key by '__hash__' and '__eq__'.
             Required for the optional 'template compression'.
    """
    __slots__ = ("acceptance_checker", "terminal_router")

    def __init__(self):
        self.acceptance_checker = []
        self.terminal_router  = []

    def accept(self, PreContextID, PatternID):
        self.acceptance_checker.append(
             DropOut_AcceptanceCheckerElement(PreContextID, PatternID))

    def route_to_terminal(self, PatternID, TransitionNSincePositioning):
        self.terminal_router.append(
             DropOut_TerminalRouterElement(PatternID, TransitionNSincePositioning))

    def __hash__(self):
        return hash(len(self.acceptance_checker) * 10 + len(self.terminal_router))

    def __eq__(self, Other):
        if   len(self.acceptance_checker) != len(Other.acceptance_checker): return False
        elif len(self.terminal_router)  != len(Other.terminal_router):  return False
        for dummy, dummy in ifilter(lambda x: not x[0].is_equal(x[1]), zip(self.acceptance_checker, Other.acceptance_checker)):
            return False
        for dummy, dummy in ifilter(lambda x: not x[0].is_equal(x[1]), zip(self.terminal_router, Other.terminal_router)):
            return False
        return True

    def is_equal(self, Other):
        return self.__eq__(Other)

    def finish(self, PositionRegisterMap):
        for element in self.terminal_router:
            if element.positioning is not E_TransitionN.VOID: continue
            element.position_register = PositionRegisterMap[element.position_register]

    def trivialize(self):
        """If there is only one acceptance involved and no pre-context,
           then the drop-out action can be trivialized.

           RETURNS: None                          -- if the drop out is not trivial
                    DropOut_TerminalRouterElement -- if the drop-out is trivial
        """
        if E_AcceptanceIDs.TERMINAL_PRE_CONTEXT_CHECK in imap(lambda x: x.acceptance_id, self.terminal_router):
            assert len(self.acceptance_checker) == 1
            assert self.acceptance_checker[0].pre_context_id == E_PreContextIDs.NONE
            assert self.acceptance_checker[0].acceptance_id  == E_AcceptanceIDs.VOID
            assert len(self.terminal_router) == 1
            return [None, self.terminal_router[0]]

        for dummy in ifilter(lambda x: x.acceptance_id == E_AcceptanceIDs.VOID, self.acceptance_checker):
            # There is a stored acceptance involved, thus need acceptance_checker + terminal_router.
            return None

        result = []
        for check in self.acceptance_checker:
            for route in self.terminal_router:
                if route.acceptance_id == check.acceptance_id: break
            else:
                assert False, \
                       "Acceptance ID '%s' not found in terminal_router.\nFound: %s" % \
                       (check.acceptance_id, map(lambda x: x.acceptance_id, self.terminal_router))
            result.append((check, route))
            # NOTE: "if check.pre_context_id is None: break"
            #       is not necessary since get_drop_out_object() makes sure that the acceptance_checker
            #       stops after the first non-pre-context drop-out.

        return result

    def __repr__(self):
        if len(self.acceptance_checker) == 0 and len(self.terminal_router) == 0:
            return "    <unreachable code>"
        info = self.trivialize()
        if info is not None:
            if len(info) == 2 and info[0] is None:
                return "    goto PreContextCheckTerminated;"
            else:
                txt = []
                if_str = "if"
                for easy in info:
                    if easy[0].pre_context_id == E_PreContextIDs.NONE:
                        txt.append("    %s goto %s;\n" % \
                                   (repr_positioning(easy[1].positioning, easy[1].position_register),
                                    repr_acceptance_id(easy[1].acceptance_id)))
                    else:
                        txt.append("    %s %s: %s goto %s;\n" % \
                                   (if_str,
                                    repr_pre_context_id(easy[0].pre_context_id),
                                    repr_positioning(easy[1].positioning, easy[1].position_register),
                                    repr_acceptance_id(easy[1].acceptance_id)))
                        if_str = "else if"
                return "".join(txt)

        txt = ["    Checker:\n"]
        if_str = "if     "
        for element in self.acceptance_checker:
            if element.pre_context_id != E_PreContextIDs.NONE:
                txt.append("        %s %s\n" % (if_str, repr(element)))
            else:
                txt.append("        accept = %s\n" % repr_acceptance_id(element.acceptance_id))
                # No check after the unconditional acceptance
                break

            if_str = "else if"

        txt.append("    Router:\n")
        for element in self.terminal_router:
            txt.append("        %s\n" % repr(element))

        return "".join(txt)

class DropOut_AcceptanceCheckerElement(object):
    """Objects of this class shall describe a check sequence such as

            if     ( pre_condition_5_f ) last_acceptance = 34;
            else if( pre_condition_7_f ) last_acceptance = 67;
            else if( pre_condition_9_f ) last_acceptance = 31;
            else                         last_acceptance = 11;

       by a list such as [(5, 34), (7, 67), (9, 31), (None, 11)]. Note, that
       the prioritization is not necessarily by pattern_id. This is so, since
       the whole trace is considered and length precedes pattern_id.
    
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

    def __init__(self, PreContextID, AcceptanceID):
        assert    isinstance(AcceptanceID, (int, long)) \
               or AcceptanceID in E_AcceptanceIDs
        self.pre_context_id = PreContextID
        self.acceptance_id  = AcceptanceID

    def is_equal(self, Other):
        """Explictly avoid default usage of '__eq__'"""
        return     self.pre_context_id == Other.pre_context_id \
               and self.acceptance_id  == Other.acceptance_id

    def __repr__(self):
        txt = []
        txt.append("%s: accept = %s" % (repr_pre_context_id(self.pre_context_id),
                                        repr_acceptance_id(self.acceptance_id)))
        return "".join(txt)

class DropOut_TerminalRouterElement(object):
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

                         == -1   --> goto terminal 'failure', nothing matched.
                         >= 0    --> goto terminal given by '.terminal_id'

        .positioning      Adaption of the input pointer, before the terminal is entered.

                         >= 0    --> input_p -= .positioning 
                                     (This is possible if the number of transitions since
                                      acceptance is determined beforehand)
                         == None --> restore from position register
                                     (Case of 'failure'. This info is actually redundant.)
                         == -1   --> (Failure) position = lexeme_start_p + 1
    """
    __slots__ = ("acceptance_id", "positioning", "position_register")

    def __init__(self, AcceptanceID, TransitionNSincePositioning):
        assert    isinstance(TransitionNSincePositioning, (int, long)) \
               or TransitionNSincePositioning in E_TransitionN

        self.acceptance_id     = AcceptanceID
        self.positioning       = TransitionNSincePositioning
        self.position_register = AcceptanceID                 # May later be adapted.

    def is_equal(self, Other):
        """Explictly avoid default usage of '__eq__'"""
        return     self.acceptance_id     == Other.acceptance_id   \
               and self.positioning       == Other.positioning     \
               and self.position_register == Other.position_register

    def __repr__(self):
        if self.acceptance_id == E_AcceptanceIDs.FAILURE: assert self.positioning == E_TransitionN.LEXEME_START_PLUS_ONE
        else:                                             assert self.positioning != E_TransitionN.LEXEME_START_PLUS_ONE

        if self.positioning != 0:
            return "case %s: %s goto %s;" % (repr_acceptance_id(self.acceptance_id, PatternStrF=False),
                                             repr_positioning(self.positioning, self.position_register), 
                                             repr_acceptance_id(self.acceptance_id))
        else:
            return "case %s: goto %s;" % (repr_acceptance_id(self.acceptance_id, PatternStrF=False),
                                          repr_acceptance_id(self.acceptance_id))
        
class DropOutBackward(DropOut):
    def __init__(self):
        DropOut.__init__(self)

        self.acceptance_checker.append(DropOut_AcceptanceCheckerElement(E_PreContextIDs.NONE, 
                                                                        E_AcceptanceIDs.VOID))
        self.terminal_router.append(DropOut_TerminalRouterElement(E_AcceptanceIDs.TERMINAL_PRE_CONTEXT_CHECK, 
                                                                  E_TransitionN.IRRELEVANT))

class DropOutBackwardInputPositionDetection(object):
    __slots__ = ("__reachable_f")
    def __init__(self, AcceptanceF):
        """A non-acceptance drop-out can never be reached, because we walk a 
           path backward, that we walked forward before.
        """
        self.__reachable_f = AcceptanceF

    @property
    def reachable_f(self):         return self.__reachable_f

    def __hash__(self):            return self.__reachable_f
    def __eq__(self, Other):       return self.__reachable_f == Other.__reachable_f
    def __repr__(self):
        if not self.__reachable_f: return "<unreachable>"
        else:                      return "<backward input position detected>"

def repr_pre_context_id(Value):
    if   Value == E_PreContextIDs.NONE:          return "Always"
    elif Value == E_PreContextIDs.BEGIN_OF_LINE: return "BeginOfLine"
    elif Value >= 0:                             return "PreContext_%i" % Value
    else:                                        assert False

def repr_acceptance_id(Value, PatternStrF=True):
    if   Value == E_AcceptanceIDs.VOID:                       return "last_acceptance"
    elif Value == E_AcceptanceIDs.FAILURE:                    return "Failure"
    elif Value == E_AcceptanceIDs.TERMINAL_PRE_CONTEXT_CHECK: return "PreContextCheckTerminated"
    elif Value >= 0:                                    
        if PatternStrF: return "Pattern%i" % Value
        else:           return "%i" % Value
    else:                                               assert False

def repr_position_register(Register):
    if Register == E_PostContextIDs.NONE: return "position[Acceptance]"
    else:                                 return "position[PostContext_%i] " % Register

def repr_positioning(Positioning, PostContextID):
    if   Positioning == E_TransitionN.VOID: 
        return "pos = %s;" % repr_position_register(PostContextID)
    elif Positioning == E_TransitionN.LEXEME_START_PLUS_ONE: 
        return "pos = lexeme_start_p + 1; "
    elif Positioning > 0:   return "pos -= %i; " % Positioning
    elif Positioning == 0:  return ""
    else: 
        assert False

def get_input_action(EngineType, InitStateF):
    if EngineType == E_EngineTypes.FORWARD:
        if InitStateF: return E_InputActions.DEREF
        else:          return E_InputActions.INCREMENT_THEN_DEREF
    else:              return E_InputActions.DECREMENT_THEN_DEREF

