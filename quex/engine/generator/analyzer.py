from quex.engine.generator.track_info import TrackInfo

from quex.input.setup import setup as Setup
from copy             import copy, deepcopy
from collections      import defaultdict
from operator         import attrgetter

def do(sm, ForwardF):
    track_info = TrackInfo(sm, ForwardF)

    for state_index, acceptance_info in track.acceptance_db.iteritems():
            
        state._i_ = AnalyzerState(state_index,
                                  acceptance_info,
                                  EntryActions(state_index, acceptance_info, [], []),
                                  Input(state_index, track_info),
                                  DropOut(state_index, acceptance_info, track_info))

    return sm.values()

class Input:
    def __init__(self, InitStateF, ForwardF):
        if ForwardF: # Rules (1), (2), and (3)
            self.__move_input_position = + 1 if not InitStateF else 0
        else:        # Backward lexing --> rule (3)
            self.__move_input_position = - 1

    def move_input_position(self):
        return self.__move_input_position


    def move_input_position(self):
        """+1 --> increment by one before dereferencing
           -1 --> decrement by one before dereferencing
            0 --> neither increment nor decrement.
        """
        return self.__move_input_position

    def immediate_drop_out_if_not_pre_context_list(self):
        """If all successor states require the list of given pre-contexts, then 
           the state can check whether at least one of them is hit. Otherwise, it 
           could immediately drop out.
        """
        return self.__immediate_drop_out_if_not_pre_context_list

class ConditionalEntryAction:
    """Objects of this class describe what has to happen, if a pre-context
       is fulfilled. The related action may be written in pseudo code:

           if( 'self.pre_context_id' fulfilled ) {
                if( 'self.pattern_id' != None ) 
                    last_acceptance = 'self.pattern_id';
                if( 'self.store_acceptance_f' != None ) 
                    last_acceptance_position_f = input_p;
                if( 'self.post_context_id_list' not empty   ) {
                    for i in 'self.post_context_id_list':
                        position_register[i] = input_p;
                }
           }

       Since StoreAcceptanceF and StorePositionF are determined offline, the 
       actually generated code looks much more gentle.
    """
    def __init__(self):
        self.pre_context_id              = PreContextID
        self.pattern_id                  = AcceptedPatternID    
        self.store_acceptance_position_f = StoreAcceptancePositionF
        self.post_context_begin_list     = PostContextBeginList

def extract_pre_context_id(Origin):
    if   origin.pre_context_begin_of_line_f(): return -1
    elif origin.pre_context_id() == -1:        return None
    else:                                      return origin.pre_context_id()

class Entry:
    def __init__(self, OriginList):

        self.__store_acceptance_f          = False
        self.__store_acceptance_position_f = False
        self.__origin_list                 = sorted(OriginList, key=attrgetter("state_machine_id"))
        self.__sequence                    = None
        self.__post_context_id_list        = []
        self.__pre_context_fulfilled_list  = []

    def finalize(self):
        """Once, the information about storing acceptance etc. has been set 
           the entry actions can be finalized.
        """
        self.__sequence = []
        for origin in self.__origin_list:
            pattern_id = origin.state_machine_id if self.__store_acceptance_f else None
            self.__sequence.append(
                    ConditionalEntryAction(extract_pre_context_id(origin),
                                           pattern_id, 
                                           self.__store_acceptance_f))
            # If an unconditioned acceptance occurred, then no further consideration!
            # (Rest of acceptance candidates is dominated).
            if pre_context_id != None: break

        if self.__store_acceptance_position_f:
            for origin in self.__origin_list:
                if origin.post_context_id() != -1 and origin.store_input_position_f():
                    self.__post_context_id_list.append(origin.post_context_id())
            


    def get_sequence(self):
        assert self.__sequence != None, "Function 'finalize()' has not been called yet."
        return self.__sequence

    def store_acceptance_f_set(self):
        self.__store_acceptance_f = True

    def store_acceptance_f(self):
        return self.__store_acceptance_f

    def store_acceptance_position_f_set(self):
        self.__store_acceptance_position_f = True

    def store_acceptance_position_f(self):
        return self.__store_acceptance_position_f
        
    def store_post_context_position_list(self):
        """What post context positions have to be stored. Return list of
           register indices. That is for each element 'i' in the list the
           position needs to be stored:

                    post_context_position[i] = input_p;
        """
        return self.__store_post_context_position_list

    def mark_pre_context_fulfilled_list(self):
        """This is only relevant during backward lexical analyzis while
           searching for pre-contexts. The list that is returned tells
           that the given pre-contexts are fulfilled in the current state
           and must be set, e.g.

                    pre_context_fulfilled[i] = true; 
        """
        return self.__pre_context_fulfilled_list

class ConditionalDropOutAction:
    """Objects of this class describe what has to happen, if a pre-context
       is fulfilled. The related action may be written in pseudo code:

           if( 'self.pre_context_id' fulfilled ) {
                if( 'self.post_context_id' != None ) {
                    input_p = position_register['self.post_context_id'];
                }
                if( 'self.pattern_id' == None ) {
                    goto ROUTER(last_acceptance);
                }
                goto 'self.pattern_id' terminal;
           }

       Since StoreAcceptanceF and StorePositionF are determined offline, the 
       actually generated code looks much more gentle.
    """
    def __init__(self):
        self.pre_context_id  = PreContextID
        self.pattern_id      = PatternID
        self.post_context_id = PostContextID

class DropOut:
    def __init__(self):
        pass

    def acceptance_pattern_set(self, X)
        pass

    def positioning_pattern_set(self, X)
        pass

class AnalyzerState:
    def __init__(self, StateIndex, SM, InitStateF, ForwardF):
        assert type(StateIndex) in [int, long]
        assert type(TheDropOut) == list

        self.index    = StateIndex
        self.input    = Input(StateIndex == SM.init_state_index, ForwardF)
        self.entry    = Entry(SM.states[StateIndex].origins())
        self.drop_out = DropOut()

class Analyzer:
    def __init__(self, SM, ForwardF):

        track_info = TrackInfo(SM)
        acceptance_db = track_info.acceptance_db

        self.__state_db = dict([(i, AnalyzerState(i, SM, ForwardF)) 
                                 for i in acceptance_db.iterkeys()])

        for state_index, acceptance_trace_list in acceptance_db.iteritems():
            state = self.__state_db[state_index]
            self.__analyze(state, acceptance_trace_list)

    def __analyze(self, state, TheAcceptanceTraceList):
                   
        if len(TheAcceptanceTraceList) == 0: return 

        prototype = TheAcceptanceTraceList[0]

        # In a first approach: If the acceptance is conditional then the states need
        #                      to store acceptance and acceptance position
        same_acceptance_pattern_f  = not prototype.is_conditional()
        same_positioning_pattern_f = not (prototype.is_conditional() or prototype.is_positioning_void())
        # If any acceptance trace differs from the prototype in accepting or positioning
        # => it needs to be stored and restored.
        # Loop: 'first falsifies'
        for acceptance_trace in islice(TheAcceptanceTraceList, 1, None):
            if prototype.has_same_acceptance_pattern(x)  == False: same_acceptance_pattern_f  = False
            if prototype.has_same_positioning_pattern(x) == False: same_positioning_pattern_f = False

        state.drop_out.acceptance_pattern_set(prototype if same_acceptance_pattern_f else None)
        state.drop_out.positioning_pattern_set(prototype if same_positioning_pattern_f else None)

        # If a storage of acceptance is required, 
        # => notify all related states they must store acceptance ids
        if not same_acceptance_pattern_f:
            state_index_list = chain(map(lambda x: x.accepting_state_index_list(), TheAcceptanceTraceList))
            for state in map(lambda x: self.__states[x], state_index_list):
                state.entry.store_acceptance_f_set()

        if not same_positioning_pattern_f:
            state_index_list = chain(map(lambda x: x.positioning_state_index_list(), TheAcceptanceTraceList))
            for state in map(lambda x: self.__states[x], state_index_list):
                state.entry.store_acceptance_position_f_set()


