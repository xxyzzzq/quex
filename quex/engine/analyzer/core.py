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

    The track analysis in 'track_analysis.py' provides the basis for the 
    construction of AnalyzerState objects. It produces the 'trace_db'.
    It maps:

                    state index --> list of Trace objects
    
    Each trace object relates to a particular path through the given state. It
    tells how the state should behave, if there was only this particular path. 
    The task of this module is to combine the list of Trace objects and generate
    a AnalyzerState objects with the aforementioned components.
    
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
from   itertools        import islice, ifilter, imap
from   quex.blackboard  import setup as Setup

def do(SM, EngineType=E_EngineTypes.FORWARD):
    analyzer = Analyzer(SM, EngineType)
    analyzer = optimizer.do(analyzer)

    if Setup.language_db is not None:
        Setup.language_db.register_analyzer(analyzer)

    return analyzer

class Analyzer:
    """Objects of class Analyzer contain information for code generation of a
       lexical analyzer. This information is derived from a given state machine
       that is expected to combine all active pattern detectors. 
       
       In the given state machine, information about a states behavior is
       stored along with the states in so called 'origins'. An 'origin' is some
       data that originates in the single pattern detectors before they were
       combined. Those origins are used by the track analysis to determine
       traces. Based on the traces the AnalyzerState objects are created.
    """
    def __init__(self, SM, EngineType):
        assert EngineType in E_EngineTypes
        assert isinstance(SM, StateMachine)

        self.__acceptance_state_index_list = SM.get_acceptance_state_index_list()
        self.__init_state_index = SM.init_state_index
        self.__state_machine_id = SM.get_id()
        self.__engine_type      = EngineType

        # (1) Track Analysis: Get the 'Trace' objects for each state
        trace_db, successor_db = track_analysis.do(SM)

        # (*) Acceptance Traces
        self.__trace_db = trace_db

        # (*) Successor Database
        #     Store for each state the set of all possible successor states.
        self.__successor_db = successor_db

        # (*) 'From Database'
        #     This is calculated on demand: For each state the list of states
        #      which enter it. See: property 'from_db' below.
        from_db = defaultdict(set)
        for from_index, state in SM.states.iteritems():
            for to_index in state.transitions().get_map().iterkeys():
                from_db[to_index].add(from_index)
        self.__from_db = from_db

        # (2) Prepare AnalyzerState Objects
        self.__state_db = dict([(state_index, AnalyzerState(state_index, SM, EngineType, from_db[state_index])) 
                                 for state_index in trace_db.iterkeys()])

        if EngineType != E_EngineTypes.FORWARD:
            # BACKWARD_INPUT_POSITION, BACKWARD_PRE_CONTEXT:
            #
            # DropOut and Entry do not require any construction beyond what is
            # accomplished inside the constructor of 'AnalyzerState'. No positions
            # need to be stored and restored.
            self.__position_register_map = None
            self.__position_info_db      = None
            return

        # Positioning info:
        #
        # map:  (state_index) --> (pattern_id) --> positioning info
        #
        self.__position_info_db = {}
        for state_index, trace_list in trace_db.iteritems():
            self.__position_info_db[state_index] = self.analyze_positioning(trace_list)

        # Store Constellation Database:
        #
        #      map: pattern_id --> set of states where input position is stored for it
        #
        # This database is developed in 'get_drop_out_object(..)' when trace lists are investigated.
        # States that do not need to store post contexts, because the input position difference can
        # be derived from the transition number are not considered.
        self.__store_constellation_db = defaultdict(set)
        for state_index, trace_list in trace_db.iteritems():
            state = self.__state_db[state_index]
            # acceptance_trace_list: 
            # Trace objects for each path that guides through state.
            state.drop_out = self.get_drop_out_object(state, trace_list)

        # What post-contexts are stored in what position register. The following analyzis
        # may spare some space for position registers as well as some unnecessary multiple
        # storage of positions.
        self.__position_register_map = position_register_map.do(self)

    @property
    def trace_db(self): return self.__trace_db
    @property
    def state_db(self):              return self.__state_db
    @property
    def init_state_index(self):      return self.__init_state_index
    @property
    def position_register_map(self): return self.__position_register_map
    @property
    def state_machine_id(self):      return self.__state_machine_id
    @property
    def engine_type(self):           return self.__engine_type
    @property
    def from_db(self):
        """Determines the predecessor of each state, i.e. by

             .predecessor_db[state_index] a list of states is returned that enter
                                          the state of 'state_index'.
        """
        return self.__from_db
    @property
    def acceptance_state_index_list(self):
        return self.__acceptance_state_index_list
    @property
    def position_info_db(self): return self.__position_info_db

    def get_drop_out_object(self, state, TheTraceList):
        """This class computes a 'DropOut' object, i.e. some data that tells
           what has to happen if nothing in the transition map triggers.  It
           does so based on the computed traces produced by the track analysis.

           DropOut objects contain two elements:

               -- An Acceptance Detector: Dependent on the fulfilled 
                  pre-contexts a winning pattern is determined.

               -- Terminal Routing: Dependent on the acceptance the 
                  input position is modified and the terminal containing
                  the pattern action is entered.

           The input position modification may contain a 'restore'. In that
           case the correspondent Entry objects of the storing states are
           modified, so that they store the input position.

           --------------------------------------------------------------------
        
           A state may be reached via multiple paths. For each path there is a
           separate Trace. Each Trace tells what has to happen in the state
           depending on the pre-contexts being fulfilled or not (if there are
           even any pre-context patterns).
        """
        assert len(TheTraceList) != 0

        acceptance_checker = []  # map: pre-context-flag --> acceptance_id
        terminal_router    = []  # map: acceptance_id    --> (positioning, 'goto terminal_id')

        # (*) Acceptance Detector
        if self.analyze_acceptance_uniformity(TheTraceList):
            # (1) Uniform Acceptance Pattern
            #     Use one trace as prototype to generate the mapping of 
            #     pre-context flag vs. acceptance.
            prototype          = TheTraceList[0]
            acceptance_checker = map(lambda x: DropOut_AcceptanceCheckerElement(x.pre_context_id, x.pattern_id), 
                                     prototype.acceptance_trace)
        else:
            # (2) Non-Uniform Acceptance Patterns
            #
            #     Different paths to one state result in different acceptances. There is only one
            #     way to handle this:
            #
            #     -- The acceptance must be stored when it occurs, and
            #     -- It must be restored here.
            acceptance_checker.append(DropOut_AcceptanceCheckerElement(E_PreContextIDs.NONE, E_AcceptanceIDs.VOID))

            # Triggering states need to store acceptance as soon as they are entered
            for trace in TheTraceList:
                for element in trace.acceptance_trace:
                    accepting_state = self.__state_db[element.accepting_state_index]
                    accepting_state.entry.doors_accept(element.pattern_id, element.pre_context_id)

        # Terminal Router
        for pattern_id, info in self.__position_info_db[state.index].iteritems():
            assert pattern_id != E_AcceptanceIDs.VOID
            terminal_router.append(DropOut_TerminalRouterElement(pattern_id, 
                                                                 info.transition_n_since_positioning))

            # If the positioning is all determined, then no 'triggering' state
            # needs to be informed.
            if info.transition_n_since_positioning != E_TransitionN.VOID: continue
    
            # Register the states that store a certain post context. This is only needed
            # later when equivalent storing states are identified.
            self.__store_constellation_db[pattern_id].update(info.positioning_state_index_set)

            # Pattern 'Failure' is always associated with the init state and the
            # positioning is uniformly 'lexeme_start_p + 1' (and never undefined, i.e. None).
            assert pattern_id != E_AcceptanceIDs.FAILURE

            # Follower states of triggering states need to store the position
            for pos_state_index in info.positioning_state_index_set:
                positioning_state = self.__state_db[pos_state_index]

                # Let index be the index of the currently considered state. Then,
                # Let x be one of the target states of the positioning state. 
                # If (index == x) or (index in self.__successor_db[x])
                # => The path from positioning state over x guides to current state
                for target_index in ifilter(lambda x: state.index == x or state.index in self.__successor_db[x],
                                            positioning_state.target_index_list):
                    if target_index == pos_state_index: continue
                    entry = self.__state_db[target_index].entry
                    # from state: pos_state_index (the state before)
                    entry.doors_store(pos_state_index, \
                                      PreContextID     = info.pre_context_id, \
                                      PositionRegister = pattern_id)

        # Clean Up the acceptance_checker and the terminal_router:
        # (1) there is no check after the unconditional acceptance
        result = DropOut()
        for i, dummy in ifilter(lambda x:     x[1].pre_context_id == E_PreContextIDs.NONE   \
                                          and x[1].acceptance_id  != E_AcceptanceIDs.FAILURE, 
                                enumerate(acceptance_checker)):
            result.acceptance_checker = acceptance_checker[:i+1]
            break
        else:
            result.acceptance_checker = acceptance_checker

        # (2) Acceptances that are not referred do not need to be routed.
        for dummy in ifilter(lambda x: x.acceptance_id == E_AcceptanceIDs.VOID, acceptance_checker):
            # The 'accept = last_acceptance' appears, thus all possible cases
            # need to be considered.
            result.terminal_router = terminal_router
            break
        else:
            # Only the acceptances that appear in the acceptance_checker are considered
            checked_pattern_id_list = map(lambda x: x.acceptance_id, acceptance_checker)
            result.terminal_router  = filter(lambda x: x.acceptance_id in checked_pattern_id_list, 
                                             terminal_router)

        ##DEBUG:
        result.trivialize()
        return result

    def analyze_positioning(self, TheTraceList):
        """A given state can be reached by (possibly) multiple paths from the
           initial state. Each path relates to an 'Trace' object that is
           determined by passed acceptance states.

           Arrange the information for each acceptance id: It is determined if
           for a given acceptance id, the path to the current state is of fixed
           length or not. Further information is accumulated in PositioningInfo
           objects. 

           RETURNS:

                     map: acceptance_id --> PositioningInfo

        """
        class PositioningInfo(object):
            __slots__ = ("transition_n_since_positioning", 
                         "pre_context_id", 
                         "positioning_state_index_set")
            def __init__(self, TraceElement):
                self.transition_n_since_positioning = TraceElement.transition_n_since_positioning
                self.positioning_state_index_set    = set([ TraceElement.positioning_state_index ])
                self.pre_context_id                 = TraceElement.pre_context_id

            def __repr__(self):
                txt  = ".transition_n_since_positioning = %s\n" % repr(self.transition_n_since_positioning)
                txt += ".positioning_state_index_set    = %s\n" % repr(self.positioning_state_index_set) 
                txt += ".pre_context_id                 = %s\n" % repr(self.pre_context_id) 
                return txt

        positioning_info_by_pattern_id = {}
        # -- If the positioning differs for one element in the trace list, or 
        # -- one element has undetermined positioning, 
        # => then the acceptance relates to undetermined positioning.
        for trace in TheTraceList:
            for element in trace.acceptance_trace:
                prototype = positioning_info_by_pattern_id.get(element.pattern_id)
                if prototype is None:
                    positioning_info_by_pattern_id[element.pattern_id] = PositioningInfo(element)
                    continue

                prototype.positioning_state_index_set.add(element.positioning_state_index)

                if prototype.transition_n_since_positioning != element.transition_n_since_positioning:
                    prototype.transition_n_since_positioning = E_TransitionN.VOID

        return positioning_info_by_pattern_id

    def analyze_acceptance_uniformity(self, TheTraceList):
        """Acceptance Uniformity:

               For each trace in TheTraceList, it holds that for
               any given pre-context: The trace accepts the same pattern.
        
           Consequently, the following cases cancel uniformity:

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
        prototype   = TheTraceList[0]
        id_sequence = prototype.get_priorized_pre_context_id_list()

        # Check (1) and (2)
        for trace in ifilter(lambda trace: id_sequence != trace.get_priorized_pre_context_id_list(),
                             islice(TheTraceList, 1, None)):
            return False

        # If the function did not return yet, then (1) and (2) are negative.

        # Check (3)
        # Pre-Context: 'Begin-of-Line' and 'No-Pre-Context' may trigger
        #              different pattern_ids.

        # -- No Pre-Context (must be in every trace)
        pattern_id = prototype.get(E_PreContextIDs.NONE).pattern_id
        # Iterate over remainder (Prototype is not considered)
        for trace in ifilter(lambda trace: pattern_id != trace[E_PreContextIDs.NONE].pattern_id, 
                             islice(TheTraceList, 1, None)):
            return False

        # -- Begin-of-Line 
        x = prototype.get(E_PreContextIDs.BEGIN_OF_LINE)
        if x is None:
            # According to (1) no other trace will have a Begin-of-Line pre-context
            pass
        else:
            # According to (1) every trace will contain 'begin-of-line' pre-context
            acceptance_id = x.pattern_id
            for trace in ifilter(lambda trace: trace[E_PreContextIDs.BEGIN_OF_LINE].pattern_id != acceptance_id,
                                 islice(TheTraceList, 1, None)):
                return False

        # Checks (1), (2), and (3) did not find anything 'bad' --> uniform acceptance.
        return True

    def last_acceptance_variable_required(self):
        """If one entry stores the last_acceptance, then the 
           correspondent variable is required to be defined.
        """
        if self.__engine_type != E_EngineTypes.FORWARD: return False
        for entry in imap(lambda x: x.entry, self.__state_db.itervalues()):
            if entry.has_accepter(): return True
        return False

    def __iter__(self):
        for x in self.__state_db.values():
            yield x

    def __repr__(self):
        # Provide some type of order that is oriented vs. the content of the states.
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
    def transition_map_empty_f(self): 
        L = len(self.transition_map)
        if   L > 1:  return False
        elif L == 0: return True
        elif self.transition_map[0][1] == E_StateIndices.DROP_OUT: return True
        return False
    @property
    def index(self):                return self.__index
    def set_index(self, Value):     assert isinstance(Value, long); self.__index = Value
    @property
    def init_state_f(self):         return self.__init_state_f
    @property
    def init_state_forward_f(self): return self.__init_state_f and self.__engine_type == E_EngineTypes.FORWARD
    @property
    def engine_type(self):            return self.__engine_type
    def set_engine_type(self, Value): assert Value in E_EngineTypes; self.__engine_type = Value     
    @property
    def target_index_list(self):    return self.__target_index_list

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

# EntryAction_StoreInputPosition: 
#
# Storing the input position is actually dependent of the pre_context_id, if 
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
    # Require '__hash__' and '__eq__' to be element of a set.
    def __hash__(self):
        return 1
    def __eq__(self, Other):
        if not isinstance(Other, EntryAction_AcceptPattern): return False
        return     self.pre_context_id == Other.pre_context_id \
               and self.acceptance_id  == Other.acceptance_id

class Entry(BASE_Entry):
    """An entry has potentially two tasks:
    
          (1) Storing information about positioning. This action may depend
              on the state where we come from. There are two possibilities:

              (i) The entries to the state differ in their 'position storage 
                  behavior'. In this case, the origin of the states must be
                  mentioned, i.e.

                     _4711_from_815:  position[34] = input_p; goto _4711;
                     _4711_from_17:   position[3]  = input_p; goto _4711;
                     _4711_from_147:  position[41] = input_p; goto _4711;
                     _4711_from_461:  position[71] = input_p; goto _4711;
                     _4711:
                         ...
                        (it follows: accepter)

              (ii) All states enter with the same 'position storage behavior'.
                    
                    _4711:
                        position[3] = _input_p;
                        position[7] = _input_p;
                        ...
                        (it follows: accepter)

              The positioner may also be pre-context dependent, i.e. something like

                       if( pre_context_34_f ) position[12] = _input_p;
                       ...
                  
          (2) Storing information about an acceptance. This action is independent
              from the state that we come from. It may depend, though, on the 
              pre-context, i.e.

                    (positioning terminated)
                    ...
                    if( pre_context_341_f ) last_acceptance = 34;
                    if( pre_context_12_f )  last_acceptance = 31;
                    if( pre_context_55_f )  last_acceptance = 34;

       (*) Positioner

       Depending on the post-context any pre-context may later on win. Thus, 

                /* 'Positioner' */
                if( pre_context_5_f ) { position[LastAcceptance] = input_p; }
                if( pre_context_7_f ) { position_register[23]    = input_p; }
                if( pre_context_9_f ) { position[LastAcceptance] = input_p; }
                position[LastAcceptance] = input_p; 
       
       The list is not sorted and it is not exclusive, line 1 and 2 are redundant
       since the same job is done by line 4 for both in any case. The information
       about position storage is done by a dictionary '.positioner' which maps:

                .positioner:  post-context-id  --> list of pre-context-ids

       Note: 
       
       "post-context-id == E_PostContextIDs.NONE" stands for no post-context 
                           ('normal' pattern)  
       "pre-context-id == E_PreContextIDs.NONE" in the pre-context-id list 
                          stands for the unconditional case (also 'normal').

       (*) Accepter:

       For the second task mentioned, some 'accepter' sequence needs to be applied, 
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
          
               for x in sorted(entry.accepter.iteritems(), key=itemgetter(1)):
                   ...
                   if pre_context_id is None: break

       To facilitate this, the function '.get_accepter' delivers a sorted list
       of accepting entries.

       NOTE: This type supports being a dictionary key by '__hash__' and '__eq__'.
             Required for the optional 'template compression'.

       MEMBERS:

          .positioner_db[from_state_index] = (pattern_id, pre_context_id_set)
  
          When the state is entered via 'from_state_index' and one of the pre-contexts
          in the 'pre_context_id_set' is fullfilled, then the position of 'pattern_id'
          must be stored.
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
        else:                                    return total_size

    def _positioner_eq(self, Other):
        if not self.__uniform_doors_f:
            return self.__doors_db == Other.__doors_db
        if len(self.__doors_db) == 0: return True
        prototype_A = self.__doors_db.itervalues().next()
        prototype_B = Other.__doors_db.itervalues().next()
        return prototype_A == prototype_B

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
        if   self.__uniform_doors_f: return False
        elif len(self.__doors_db) <= 1:            return False
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

           RETURNS: None                  -- if the drop out is not trivial
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
    def reachable_f(self): return self.__reachable_f

    def __hash__(self):      return self.__reachable_f
    def __eq__(self, Other): return self.__reachable_f == Other.__reachable_f

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

