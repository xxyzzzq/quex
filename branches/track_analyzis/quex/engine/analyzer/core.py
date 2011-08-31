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

import quex.engine.analyzer.track_analysis        as     track_analysis
import quex.engine.analyzer.position_register_map as     position_register_map
from   quex.engine.analyzer.track_analysis        import \
                                                         extract_pre_context_id, \
                                                         E_TransitionN
from   quex.engine.state_machine.state_core_info  import E_PostContextIDs, \
                                                         E_AcceptanceIDs, \
                                                         E_EngineTypes, \
                                                         E_PreContextIDs
from   quex.engine.misc.enum                      import Enum


from quex.blackboard  import E_StateIndices
from collections      import defaultdict
from operator         import attrgetter, itemgetter
from itertools        import islice, ifilter, imap

class Analyzer:
    def __init__(self, SM, EngineType=E_EngineTypes.FORWARD):
        assert EngineType in E_EngineTypes

        acceptance_db = track_analysis.do(SM)

        self.__init_state_index = SM.init_state_index
        self.__state_machine_id = SM.get_id()
        self.__engine_type      = EngineType

        from_db = defaultdict(set)
        for state_index, state in SM.states.iteritems():
            self.transition_map = state.transitions().get_trigger_map()
            for target_index in state.transitions().get_map().keys():
                from_db[target_index].add(state_index)

        self.__state_db = dict([(state_index, AnalyzerState(state_index, SM, EngineType, from_db[state_index])) 
                                 for state_index in acceptance_db.iterkeys()])

        self.__successor_db          = defaultdict(set)
        self.__successor_db_done_set = set()
        self.__successor_db_get(self.__init_state_index, [], self.__successor_db)

        if EngineType == E_EngineTypes.FORWARD:
            for state_index, acceptance_trace_list in acceptance_db.iteritems():
                state = self.__state_db[state_index]
                # acceptance_trace_list: 
                # Trace objects for each path that guides through state.
                state.drop_out = self.get_drop_out_object(state, acceptance_trace_list)

            # -- After the preceding dependency implementation:
            #    If a state has no successor state, or only transitions to itself,
            #    => No accepter check is necessary, done in drop-out
            for state_index, sm_state in SM.states.iteritems():
                transition_map = sm_state.transitions().get_map()
                if     len(transition_map) == 0 \
                   or (len(transition_map) == 1 and transition_map.keys()[0] == state_index):
                   ## self.__state_db[state_index].entry.positioner_db.clear()
                   self.__state_db[state_index].entry.accepter.clear()
        else:
            # NOTE: For backward analysis, drop_out and entry do not require any construction 
            #       beyond what is triggered inside the constructor of 'AnalyzerState'.
            #       This is so, since no dependencies exists between states that require
            #       stored acceptances and stored positions and those state that store it.
            #       
            #       For backward analysis, the behavior of a state can be determined in 
            #       isolation and it is not dependent on other states.
            pass

        if EngineType == E_EngineTypes.FORWARD:
            self.__position_register_map = position_register_map.do(self)
            for entry in imap(lambda x: x.entry, self.__state_db.itervalues()):
                entry.try_unify_positioner_db()
        else:
            self.__position_register_map = None

    @property
    def state_db(self):              return self.__state_db
    @property
    def init_state_index(self):      return self.__init_state_index
    @property
    def position_register_map(self): return self.__position_register_map
    @property
    def state_machine_id(self):      return self.__state_machine_id

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

        # (*) Acceptance Detector
        if self.analyze_acceptance_uniformity(TheAcceptanceTraceList):
            # (1) Uniform Traces
            #     Use one trace as prototype to generate the mapping of 
            #     pre-context flag vs. acceptance.
            prototype = TheAcceptanceTraceList[0]
            checker   = map(lambda x: DropOut_CheckerElement(x[0], x[1].pattern_id), 
                            prototype.get_priorized_list())
            # Note: (1.1) Unconditional Acceptance Exists, and
            #       (1.2) No Unconditional Acceptance 
            #       are already well-handled because the current states acceptance behavior
            #       is already webbed into the traces--and it is conform with the others.
        else:
            # (2) Non-Uniform Traces
            # (2.1) Unconditional Acceptance Exists
            #       => According to AcceptanceTrace.update() all influence from past traces 
            #          is nulled.
            #       => Thus, a state with an unconditional will have **only** the traces
            #          of its own state and is therefore **uniform**.
            #       => This case is impossible for non-uniform traces.
            # (2.2) No Unconditional Acceptance
            #       => past acceptances can be communicated via 'last_acceptance' instead of Failure.
            #          but all current pre-contexts must be checked.
            checker = []
            for origin in sorted(ifilter(lambda x: x.is_acceptance(), state._origin_list),
                                 key=attrgetter("state_machine_id")):
                checker.append(DropOut_CheckerElement(extract_pre_context_id(origin),
                                                      origin.state_machine_id))
                ## Is this right?: According to (2.1) the following must hold
                ## assert origin.pre_context_id() != -1

            # No pre-context --> restore last acceptance
            checker.append(DropOut_CheckerElement(E_PreContextIDs.NONE, E_AcceptanceIDs.VOID))

            # Triggering states need to store acceptance as soon as they are entered
            for trace in TheAcceptanceTraceList:
                for element in trace:
                    accepting_state = self.__state_db[element.accepting_state_index]
                    accepting_state.entry.accepter[element.pre_context_id] = element.pattern_id

        # Terminal Router
        for pattern_id, info in self.analyze_positioning(TheAcceptanceTraceList).iteritems():
            assert pattern_id != E_AcceptanceIDs.VOID
            router.append(DropOut_RouterElement(pattern_id, 
                                                info.transition_n_since_positioning, 
                                                info.post_context_id))

            # If the positioning is all determined, then no 'triggering' state
            # needs to be informed.
            if info.transition_n_since_positioning != E_TransitionN.VOID: continue
            # Pattern 'Failure' is always associated with the init state and the
            # positioning is uniformly 'lexeme_start_p + 1' (and never undefined, i.e. None).
            assert pattern_id != E_AcceptanceIDs.FAILURE

            # Follower states of triggering states need to store the position
            for pos_state_index in info.positioning_state_index_list:
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
                    entry.positioner_db[pos_state_index][info.post_context_id].add(info.pre_context_id)

        # Clean Up the checker and the router:
        # (1) there is no check after the unconditional acceptance
        result = DropOut()
        for i, dummy in ifilter(lambda x:     x[1].pre_context_id == E_PreContextIDs.NONE   \
                                          and x[1].acceptance_id  != E_AcceptanceIDs.FAILURE, 
                                enumerate(checker)):
            result.checker = checker[:i+1]
            break
        else:
            result.checker = checker

        # (2) Acceptances that are not referred do not need to be routed.
        for dummy in ifilter(lambda x: x.acceptance_id == E_AcceptanceIDs.VOID, checker):
            # The 'accept = last_acceptance' appears, thus all possible cases
            # need to be considered.
            result.router = router
            break
        else:
            # Only the acceptances that appear in the checker are considered
            checked_pattern_id_list = map(lambda x: x.acceptance_id, checker)
            result.router = filter(lambda x: x.acceptance_id in checked_pattern_id_list, 
                                   router)

        ##DEBUG:
        result.trivialize()
        return result

    def analyze_positioning(self, TheAcceptanceTraceList):
        """A given state can be reached by (possibly) multiple paths from
           the initial state. Each path relates to an 'AcceptanceTrace'
           object that is determined by passed acceptance states.

           Arrange the information for each acceptance id: It is determined
           if for a given acceptance id, the path to the current state is
           of fixed length or not. Further information is accumulated in 
           PositioningInfo objects. 

           RETURNS:

                     map: acceptance_id --> PositioningInfo

        """
        class PositioningInfo(object):
            __slots__ = ("transition_n_since_positioning", 
                         "post_context_id", 
                         "pre_context_id", 
                         "positioning_state_index_list")
            def __init__(self, TraceElement):
                self.transition_n_since_positioning = TraceElement.transition_n_since_positioning
                self.post_context_id                = TraceElement.post_context_id
                self.positioning_state_index_list   = [ TraceElement.positioning_state_index ]
                self.pre_context_id                 = TraceElement.pre_context_id

            def __repr__(self):
                txt  = ".transition_n_since_positioning = %s\n" % repr(self.transition_n_since_positioning)
                txt += ".post_context_id                = %s\n" % repr(self.post_context_id)                
                txt += ".positioning_state_index_list   = %s\n" % repr(self.positioning_state_index_list) 
                txt += ".pre_context_id                 = %s\n" % repr(self.pre_context_id) 
                return txt

        trace_by_pattern_id = {}
        # -- If the positioning differs for one element in the trace list, or 
        # -- one element has undetermined positioning, 
        # => then the acceptance relates to undetermined positioning.
        for trace in TheAcceptanceTraceList:
            for element in trace:
                info = trace_by_pattern_id.get(element.pattern_id)
                if info is None:
                    trace_by_pattern_id[element.pattern_id] = PositioningInfo(element)
                    continue
                else:
                    # Acceptance-IDs and their Post-Contexts are related 1:1
                    # (Their is no post-contexted 'FAILURE')
                    assert info.post_context_id == element.post_context_id

                    info.positioning_state_index_list.append(element.positioning_state_index)

                    if info.transition_n_since_positioning != element.transition_n_since_positioning:
                        info.transition_n_since_positioning = E_TransitionN.VOID

        return trace_by_pattern_id

    def analyze_acceptance_uniformity(self, TheAcceptanceTraceList):
        """Acceptance Uniformity:

               For each trace in TheAcceptanceTraceList, it holds that for
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
        prototype   = TheAcceptanceTraceList[0]
        id_sequence = prototype.get_priorized_pre_context_id_list()

        # Check (1) and (2)
        for trace in ifilter(lambda trace: id_sequence != trace.get_priorized_pre_context_id_list(),
                             islice(TheAcceptanceTraceList, 1, None)):
            return False

        # If the function did not return yet, then (1) and (2) are negative.

        # Check (3)
        # Pre-Context: 'Begin-of-Line' and 'No-Pre-Context' may trigger
        #              different pattern_ids.

        # -- No Pre-Context (must be in every trace)
        pattern_id = prototype.get(E_PreContextIDs.NONE).pattern_id
        # Iterate over remainder (Prototype is not considered)
        for trace in ifilter(lambda trace: pattern_id != trace[E_PreContextIDs.NONE].pattern_id, 
                             islice(TheAcceptanceTraceList, 1, None)):
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
                                 islice(TheAcceptanceTraceList, 1, None)):
                return False

        # Checks (1), (2), and (3) did not find anything 'bad' --> uniform acceptance.
        return True

    def last_acceptance_variable_required(self):
        """If one entry stores the last_acceptance, then the 
           correspondent variable is required to be defined.
        """
        if self.__engine_type != E_EngineTypes.FORWARD: return False
        for entry in imap(lambda x: x.entry, self.__state_db.itervalues()):
            if len(entry.accepter) != 0: return True
        return False

    def __successor_db_get(self, StateIndex, path, result):
        """Determine for each state the set of successor states.
        """
        state             = self.__state_db[StateIndex]
        target_index_list = state.target_index_list

        path.append(StateIndex)
        for state_index in path:
            result[state_index].update(target_index_list)

        for target_index in ifilter(lambda x: x not in path, target_index_list):
            if target_index in path: continue
            if target_index in self.__successor_db_done_set: continue
            self.__successor_db_get(target_index, path, result)
        path.pop()
        self.__successor_db_done_set.add(StateIndex)

    def _get_equivalent_post_context_id_sets(self):
        """Determine sets of equivalent post context ids, because they
           store the input positions at the exactly same set of states.
        """
        # (1) map: 
        #
        #          post-context-id --> set of states where the positions are stored
        #
        store_constellation_db = defaultdict(set)
        for state in self.state_db.itervalues():
            # Iterate over all post context ids subject to position storage
            for positioner in state.entry.positioner_db.itervalues():
                for post_context_id in positioner.iterkeys():
                    store_constellation_db[post_context_id].add(state.index)

        # (2) inverse map: 
        #             
        #          set of states where the positions are stored --> post context ids that do so
        #
        inverse_db = defaultdict(set)
        for post_context_id, storing_state_set in store_constellation_db.iteritems():
            inverse_db[tuple(sorted(storing_state_set))].add(post_context_id)

        # The grouped post context ids are the set of equivalent post context ids
        # NOTE: An equivalent set of size < 2 does not make any statement.
        #       At least, there must be two elements, so that this means 'A is 
        #       equivalent to B'. Thus, filter anything of size < 2.
        return store_constellation_db.keys(), filter(lambda x: len(x) >= 2, inverse_db.values())

    def _find_state_sets_from_store_to_restore(self):
        """RETURNS: A mapping:

              post-context id --> set of states that lie on the path from store 
                                  to restore of the input position.
        """
        def dive(PostContextID, State, path, collection):
            """Termination Condition: state.target_index_list == empty
                                  or: state_index in path
            """
            for target_index in ifilter(lambda x: x not in path, State.target_index_list):
                collection.add(target_index)
                target_state = self.state_db[target_index]
                for dummy in ifilter(lambda x:     x.positioning     == E_TransitionN.VOID \
                                               and x.post_context_id == PostContextID,
                                     target_state.drop_out.router):
                    collection.update(path)
                    break
                path.append(target_index)
                dive(PostContextID, target_state, path, collection)
                path.pop()

        result = defaultdict(set)
        for state in self.state_db.itervalues():
            # Iterate over all post context ids subject to position storage
            for from_state_index, positioner in ifilter(lambda x: x[0] != E_StateIndices.ALL, 
                                                        state.entry.positioner_db.iteritems()):
                for post_context_id in positioner.iterkeys():
                    dive(post_context_id, state, [], result[post_context_id])

        return result

    def check_state_uniformity(self, StateIndexList):
        assert len(StateIndexList) != 0
        iterable  = [self.state_db[i] for i in StateIndexList].__iter__()
        prototype = iterable.next()
        for dummy in ifilter(lambda state: not state.is_uniform(prototype), iterable):
            return False
        return True

    def __iter__(self):
        for x in self.__state_db.values():
            yield x

InputActions = Enum("INCREMENT_THEN_DEREF", "DEREF", "DECREMENT_THEN_DEREF")

class AnalyzerState(object):
    __slots__ = ("__index", 
                 "__init_state_f", 
                 "__target_index_list", 
                 "__engine_type", 
                 "input", 
                 "entry", 
                 "transition_map", 
                 "drop_out", 
                 "_origin_list")

    def __init__(self, StateIndex, SM, EngineType, FromStateIndexList):
        assert type(StateIndex) in [int, long]
        assert EngineType in E_EngineTypes

        state = SM.states[StateIndex]

        self.__index              = StateIndex
        self.__init_state_f       = SM.init_state_index == StateIndex
        self.__engine_type        = EngineType

        # (*) Input
        if EngineType == E_EngineTypes.FORWARD:
            if StateIndex == SM.init_state_index: self.input = InputActions.DEREF
            else:                                 self.input = InputActions.INCREMENT_THEN_DEREF
        else:                                     self.input = InputActions.DECREMENT_THEN_DEREF

        # (*) Entry Action
        if   EngineType == E_EngineTypes.FORWARD: 
            self.entry = Entry(FromStateIndexList)
        elif EngineType == E_EngineTypes.BACKWARD_PRE_CONTEXT: 
            self.entry = EntryBackward(state.origins())
        elif EngineType == E_EngineTypes.BACKWARD_INPUT_POSITION: 
            self.entry = EntryBackwardInputPositionDetection(state.origins(), SM.core().id())
        else:
            assert False

        # (*) Transition
        if EngineType == E_EngineTypes.BACKWARD_INPUT_POSITION:
            # During backward input detection, an acceptance state triggers a
            # return from the searcher, thus no further transitions are necessary.
            # (orphaned states, also, need to be deleted).
            if state.is_acceptance(): assert state.transitions().is_empty()

        self.transition_map      = state.transitions().get_trigger_map()
        self.__target_index_list = state.transitions().get_map().keys()

        # (*) Drop Out
        if   EngineType == E_EngineTypes.FORWARD: 
            # DropOut and Entry interact and require sophisticated analysis
            # => See "Analyzer.get_drop_out_object(...)"
            self.drop_out = None 
        elif EngineType == E_EngineTypes.BACKWARD_PRE_CONTEXT:
            self.drop_out = DropOut()
            self.drop_out.checker.append(DropOut_CheckerElement(E_PreContextIDs.NONE, 
                                                                E_AcceptanceIDs.VOID))
            self.drop_out.router.append(DropOut_RouterElement(E_AcceptanceIDs.TERMINAL_PRE_CONTEXT_CHECK, 
                                                              E_TransitionN.IRRELEVANT, 
                                                              E_PostContextIDs.IRRELEVANT))
        elif EngineType == E_EngineTypes.BACKWARD_INPUT_POSITION:
            # The drop-out should never be reached, since we walk a path backwards
            # that has been walked forward before.
            self.drop_out = DropOut()

        self._origin_list = state.origins().get_list()

    @property
    def index(self):                return self.__index
    @property
    def init_state_f(self):         return self.__init_state_f
    @property
    def init_state_forward_f(self): return self.__init_state_f and self.__engine_type == E_EngineTypes.FORWARD
    @property
    def engine_type(self):          return self.__engine_type
    @property
    def target_index_list(self):    return self.__target_index_list

    def get_string_array(self, InputF=True, EntryF=True, TransitionMapF=True, DropOutF=True):
        txt = [ "State %i:\n" % self.index ]
        if InputF:         txt.append("  .input: move position %i\n" % self.input.move_input_position())
        if EntryF:         txt.append("  .entry:\n"); txt.append(repr(self.entry))
        if TransitionMapF: txt.append("  .transition_map:\n")
        if DropOutF:       txt.extend(["  .drop_out:\n",    repr(self.drop_out)])
        txt.append("\n")
        return txt

    def get_string(self, InputF=True, EntryF=True, TransitionMapF=True, DropOutF=True):
        return "".join(self.get_string_array(InputF, EntryF, TransitionMapF, DropOutF))

    def __repr__(self):
        return self.get_string()

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
          
               for x in sorted(entry.accepter.iteritems(), key=itemgetter(1)):
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

       Where "post-context-id == -1" stands for no post-context (normal pattern)
       and a "None" in the pre-context-id list stands for the unconditional case.

       NOTE: This type supports being a dictionary key by '__hash__' and '__eq__'.
             Required for the optional 'template compression'.
    """
    __slots__ = ("__uniform_f", "accepter", "positioner_db")

    def __init__(self, FromStateIndexList):
        # By default, we do not do store anything about acceptance at state entry
        self.accepter = {}

        # map:  (from_state_index, pre_context_id) --> post_context_id where to store position
        self.positioner_db = dict([ (i, defaultdict(set)) for i in FromStateIndexList ])

        # Are all positionings uniform?
        # This flag is to be determined after the analyzis by function 'try_unify_positioner_db()'
        self.__uniform_f = None 

    def __hash__(self):
        return hash(len(self.accepter) * 10 + len(positioner_db) * 2 + int(self.__uniform_f))

    def __eq__(self, Other):
        return     self.accepter      == Other.accepter \
               and self.positioner_db == Other.positioner_db

    def is_equal(self, Other):
        # Maybe, we can delete this ...
        return     self.accepter      == Other.accepter \
               and self.positioner_db == Other.positioner_db

    def is_uniform(self): 
        return self.__uniform_f

    def uniform_positioner(self):
        assert self.__uniform_f
        # All positioners are uniform, so simply return the first.
        return self.positioner_db.itervalues().next()

    def get_accepter(self):
        """Returns information about the acceptance sequence. Lines that are dominated
           by the unconditional pre-context are filtered out. Returns pairs of

                          (pre_context_id, acceptance_id)
        """
        result = []
        for pre_context_id, acceptance_id in sorted(self.accepter.iteritems(), key=itemgetter(1)):
            result.append((pre_context_id, acceptance_id))   
            if pre_context_id == E_PreContextIDs.NONE: break
        return result

    def get_positioner_db(self):
        """RETURNS: PositionDB
        
           where PositionDB maps:
        
                   from_state_index  -->   Positioner
 
           where Positioner is a dictionary that maps:

                   post_context_id --> list of pre-context-ids that trigger it 

           Note, that 'PostContextID==None' (Normal Acceptance) can have multiple
           pre-context ids related to it.
        """
        return self.positioner_db

    def try_unify_positioner_db(self):
        """At state entry the positioning might differ dependent on the 
           the state from which it is entered. If the positioning is the
           same for each source state, then the positioning can be unified.

           A unified entry is coded as 'ALL' --> common positioning.
        """
        if len(self.positioner_db) == 0: return
        itervalues = self.positioner_db.itervalues()

        self.__uniform_f = True
        prototype        = itervalues.next()
        for dummy in ifilter(lambda x: x != prototype, itervalues):
            self.__uniform_f = False
            return

    def __repr__(self):
        txt = []
        accepter = self.get_accepter()
        if len(accepter) != 0:
            txt.append("    .accepter:\n")
            if_str = "if     "
            for pre_context_id, acceptance_id in self.get_accepter():
                if pre_context_id != E_PreContextIDs.NONE:
                    txt.append("        %s %s: " % (if_str, repr_pre_context_id(pre_context_id)))
                else:
                    txt.append("        ")
                txt.append("last_acceptance = %s\n" % repr_acceptance_id(acceptance_id))
                if_str = "else if"

        if len(self.positioner_db) != 0:
            txt.append("    .positioner:\n")
        for from_state_index, positioner in self.positioner_db.iteritems():
            txt.append("        .from %i:" % from_state_index)
            if   len(positioner) == 0: txt.append(" <nothing>\n")
            elif len(positioner) != 1: txt.append("\n")
            for post_context_id, pre_context_id_list in positioner.iteritems():
                pre_list = map(repr_pre_context_id, pre_context_id_list)
                if len(positioner) != 1: txt.append("            ")
                if E_PreContextIDs.NONE not in pre_context_id_list:
                    txt.append("if %s: " % repr(pre_list)[1:-1])
                txt.append(" %s = input_p;\n" % repr_position_register(post_context_id))

        return "".join(txt)

class EntryBackwardInputPositionDetection(object):
    """There is not much more to say then: 

       Acceptance State 
       => then we found the input position => return immediately.

       Non-Acceptance State
       => proceed with the state transitions (do nothing here)

       NOTE: This type supports being a dictionary key by '__hash__' and '__eq__'.
             Required for the optional 'template compression'.
    """
    __slots__ = ("__terminated_f", "__detector_sm_id")

    def __init__(self, OriginList, StateMachineID):
        self.__detector_sm_id = StateMachineID
        self.__terminated_f = False
        for origin in ifilter(lambda origin: origin.is_acceptance(), OriginList):
            self.__terminated_f = True
            return

    def __hash__(self):
        return hash(self.__detector_sm_id * 2 + int(self.__terminated_f))

    def __eq__(self, Other):
        return     self.__terminated_f   == Other.__terminated_f \
               and self.__detector_sm_id == Other.__detector_sm_id

    def is_equal(self, Other):
        return self.__eq__(Other)

    @property
    def terminated_f(self): return self.__terminated_f

    @property
    def backward_input_positon_detector_sm_id(self): return self.__detector_sm_id

    def __repr__(self):
        if self.__terminated_f: return "    Terminated (%i)\n" % self.__detector_sm_id
        else:                   return ""

class EntryBackward(object):
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
            self.__pre_context_fulfilled_set.add(origin.state_machine_id)

    def __hash__(self):
        return hash(len(self.__pre_context_fulfilled_set))

    def __eq__(self, Other):
        # NOTE: set([0, 1, 2]) == set([2, 1, 0]) 
        #       ... equal if elements are the same, order not important
        return self.pre_context_fulfilled_set == Other.pre_context_fulfilled_set

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

       The first sub-task is described by the member '.checker' which is a list
       of objects of class 'DropOut_CheckerElement'. An empty list means that
       there is no check and the acceptance has to be restored from 'last_acceptance'.
       
       The second sub-task is described by member '.router' which is a list of 
       objects of class 'DropOut_RouterElement'.

       The exact content of both lists is determined by analysis of the acceptance
       trances.

       NOTE: This type supports being a dictionary key by '__hash__' and '__eq__'.
             Required for the optional 'template compression'.
    """
    __slots__ = ("checker", "router")

    def __init__(self):
        self.checker = []
        self.router  = []

    def __hash__(self):
        return hash(len(self.checker) * 10 + len(self.router))

    def __eq__(self, Other):
        if   len(self.checker) != len(Other.checker): return False
        elif len(self.router)  != len(Other.router):  return False
        for dummy, dummy in ifilter(lambda x: not x[0].is_equal(x[1]), zip(self.checker, Other.checker)):
            return False
        for dummy, dummy in ifilter(lambda x: not x[0].is_equal(x[1]), zip(self.router, Other.router)):
            return False
        return True

    def is_equal(self, Other):
        return self.__eq__(Other)

    def trivialize(self):
        """If there is only one acceptance involved and no pre-context,
           then the drop-out action can be trivialized.

           RETURNS: None                  -- if the drop out is not trivial
                    DropOut_RouterElement -- if the drop-out is trivial
        """
        if E_AcceptanceIDs.TERMINAL_PRE_CONTEXT_CHECK in imap(lambda x: x.acceptance_id, self.router):
            assert len(self.checker) == 1
            assert self.checker[0].pre_context_id == E_PreContextIDs.NONE
            assert self.checker[0].acceptance_id  == E_AcceptanceIDs.VOID
            assert len(self.router) == 1
            return [None, self.router[0]]

        for dummy in ifilter(lambda x: x.acceptance_id == E_AcceptanceIDs.VOID, self.checker):
            # There is a stored acceptance involved, thus need checker + router.
            return None

        result = []
        for check in self.checker:
            for route in self.router:
                if route.acceptance_id == check.acceptance_id: break
            else:
                assert False, \
                       "Acceptance ID '%s' not found in router.\nFound: %s" % \
                       (check.acceptance_id, map(lambda x: x.acceptance_id, self.router))
            result.append((check, route))
            # NOTE: "if check.pre_context_id is None: break"
            #       is not necessary since get_drop_out_object() makes sure that the checker
            #       stops after the first non-pre-context drop-out.

        return result

    def __repr__(self):
        if len(self.checker) == 0 and len(self.router) == 0:
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
                                   (repr_positioning(easy[1].positioning, easy[1].post_context_id),
                                    repr_acceptance_id(easy[1].acceptance_id)))
                    else:
                        txt.append("    %s %s: %s goto %s;\n" % \
                                   (if_str,
                                    repr_pre_context_id(easy[0].pre_context_id),
                                    repr_positioning(easy[1].positioning, easy[1].post_context_id),
                                    repr_acceptance_id(easy[1].acceptance_id)))
                        if_str = "else if"
                return "".join(txt)

        txt = ["    Checker:\n"]
        if_str = "if     "
        for element in self.checker:
            if element.pre_context_id != E_PreContextIDs.NONE:
                txt.append("        %s %s\n" % (if_str, repr(element)))
            else:
                txt.append("        accept = %s\n" % repr_acceptance_id(element.acceptance_id))
                # No check after the unconditional acceptance
                break

            if_str = "else if"

        txt.append("    Router:\n")
        for element in self.router:
            txt.append("        %s\n" % repr(element))

        return "".join(txt)

class DropOut_CheckerElement(object):
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

                         == -1   --> goto terminal 'failure', nothing matched.
                         >= 0    --> goto terminal given by '.terminal_id'

        .positioning      Adaption of the input pointer, before the terminal is entered.

                         >= 0    --> input_p -= .positioning 
                                     (This is possible if the number of transitions since
                                      acceptance is determined beforehand)
                         == None --> restore from position register
                                     (Case of 'failure'. This info is actually redundant.)
                         == -1   --> (Failure) position = lexeme_start_p + 1
                         
        .post_context_id  Registered where the position to be restored is located.

                         == None  --> Nothing (no position is to be stored.)
                                      Case: 'positioning != 1'
                         == -1    --> acceptance without post-context
                         >= 0     --> acceptance with post-context given as integer
    """
    __slots__ = ("acceptance_id", "positioning", "post_context_id")

    def __init__(self, AcceptanceID, TransitionNSincePositioning, PostContextID):
        assert    isinstance(TransitionNSincePositioning, (int, long)) \
               or TransitionNSincePositioning in E_TransitionN
        assert    isinstance(PostContextID, (int, long)) \
               or PostContextID in E_PostContextIDs

        #if    AcceptanceID == E_AcceptanceIDs.TERMINAL_PRE_CONTEXT_CHECK      \
        #   or AcceptanceID == E_AcceptanceIDs.TERMINAL_BACKWARD_INPUT_POSITION: 
        #    assert TransitionNSincePositioning == E_TransitionN.VOID
        #else:   
        #    assert TransitionNSincePositioning != E_TransitionN.VOID
        #if TransitionNSincePositioning == E_TransitionN.VOID:                                 
        #    assert PostContextID != E_PostContextIDs.NONE

        self.acceptance_id   = AcceptanceID
        self.positioning     = TransitionNSincePositioning
        self.post_context_id = PostContextID

    def is_equal(self, Other):
        """Explictly avoid default usage of '__eq__'"""
        return     self.acceptance_id   == Other.acceptance_id   \
               and self.positioning     == Other.positioning     \
               and self.post_context_id == Other.post_context_id

    def __repr__(self):
        if self.acceptance_id == E_AcceptanceIDs.FAILURE: assert self.positioning == E_TransitionN.LEXEME_START_PLUS_ONE
        else:                                             assert self.positioning != E_TransitionN.LEXEME_START_PLUS_ONE

        if self.positioning != 0:
            return "case %s: %s goto %s;" % (repr_acceptance_id(self.acceptance_id, PatternStrF=False),
                                             repr_positioning(self.positioning, self.post_context_id), 
                                             repr_acceptance_id(self.acceptance_id))
        else:
            return "case %s: goto %s;" % (repr_acceptance_id(self.acceptance_id, PatternStrF=False),
                                          repr_acceptance_id(self.acceptance_id))
        
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
