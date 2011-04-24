from quex.engine.generator.track_info import TrackInfo

from quex.input.setup import setup as Setup
from copy             import copy, deepcopy
from collections      import defaultdict
from operator         import attrgetter
from exceptions       import AssertionError

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

        common = TheAcceptanceTraceList[0]
        common_pre_context_id_list = common.get_pre_context_id_list()

        # If any acceptance trace differs from the prototype in accepting or positioning
        # => it needs to be stored and restored.
        # Loop: 'first falsifies'
        for acceptance_trace in islice(TheAcceptanceTraceList, 1, None):
            common_pre_context_id_list.update(acceptance_trace.get_pre_context_id_list())
            for pre_context_id in common_pre_context_id_list:
                common_entry = common.get_pre_context_id_entry(pre_context_id)
                other_entry  = acceptance_trace.get_pre_context_id_entry(pre_context_id)
                if common_entry == None:
                    acceptance = None; positioning = None # Cannot be determined beforehand
                    if other_entry != None:
                        self.__state_db[other_entry.accepting_state_index].entry.set_store_acceptance_f(pre_context_id)
                        self.__state_db[other_entry.accepting_state_index].entry.set_store_acceptance_position_f(pre_context_id)

                if other_entry == None:
                    acceptance = None; positioning = None # Cannot be determined beforehand
                    if common_entry != None:
                        self.__state_db[common_entry.accepting_state_index].entry.set_store_acceptance_f(pre_context_id)
                        self.__state_db[common_entry.accepting_state_index].entry.set_store_acceptance_position_f(pre_context_id)

                # pre_context_id present in both maps
                if acceptance != None:
                    if common_entry.pattern_id != other_entry.pattern_id:
                        acceptance = None
                        # Inform related states about the task to store acceptance
                        self.__state_db[other_entry.accepting_state_index].entry.set_store_acceptance_f(pre_context_id)
                        self.__state_db[common_entry.accepting_state_index].entry.set_store_acceptance_f(pre_context_id)
                    if common_entry.positioning != other_entry.positioning:
                        positioning = None
                        # Inform related states about the task to store acceptance position
                        self.__state_db[other_entry.accepting_state_index].entry.set_store_acceptance_position_f(pre_context_id)
                        self.__state_db[common_entry.accepting_state_index].entry.set_store_acceptance_position_f(pre_context_id)

                common[pre_context_id].pattern_id  = acceptance
                common[pre_context_id].positioning = positioning

        state.drop_out.set_sequence(common)

class AnalyzerState:
    def __init__(self, StateIndex, SM, InitStateF, ForwardF):
        assert type(StateIndex) in [int, long]
        assert type(TheDropOut) == list

        state = SM.states[StateIndex]

        self.index       = StateIndex
        self.input       = Input(StateIndex == SM.init_state_index, ForwardF)
        self.entry       = Entry(state.origins(), ForwardF)
        self.trigger_map = state.transitions().get_trigger_map()
        self.drop_out    = DropOut()

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
                if( 'self.store_acceptance_f' )          last_acceptance            = 'self.pattern_id';
                if( 'self.store_acceptance_position_f' ) last_acceptance_position_f = input_p;
           }

        The 'self.*' variables are computed off-line, so the actual code 
        will look a little more gentle.
    """
    def __init__(self, PreContextID, PatternID):
        self.pre_context_id              = PreContextID
        self.pattern_id                  = PatternID    
        self.store_acceptance_f          = False
        self.store_acceptance_position_f = False

def extract_pre_context_id(Origin):
    if   origin.pre_context_begin_of_line_f(): return -1
    elif origin.pre_context_id() == -1:        return None
    else:                                      return origin.pre_context_id()

class Entry:
    def __init__(self, OriginList, ForwardF):
        self.__origin_list                 = sorted(OriginList, key=attrgetter("state_machine_id"))
        self.__sequence                    = None

        if ForwardF:
            self.__pre_context_fulfilled_set = None
            self.__sequence                  = []
            for origin in self.__origin_list:
                entry = ConditionalEntryAction(extract_pre_context_id(origin), pattern_id)
                self.__sequence.append(entry)
                # If an unconditioned acceptance occurred, then no further consideration!
                # (Rest of acceptance candidates is dominated).
                if pre_context_id != None: break
        else:
            self.__pre_context_fulfilled_set = set([])
            self.__sequence                  = None
            for origin in self.__origin_list:
                if not origin.store_input_position_f(): continue
                assert origin.is_acceptance()
                self.__pre_context_fulfilled_set.add(origin.state_machine_id)

        # List of post context begin positions that need to be stored at state entry
        self.__store_position_begin_of_post_context_id_set = set([])

    def get_sequence(self):
        assert self__sequence != None
        return self.__sequence

    def set_store_acceptance_f(self):
        for x in self.__sequence: 
            x.store_acceptance_f = True

    def set_store_acceptance_position_f(self):
        for x in self.__sequence: 
            x.store_acceptance_position_f = True

    def set_store_begin_of_post_context_position(self, PostContextID):
        if __debug__:
            for origin in self.__origin_list:
                if origin.post_context_id() == PostContextID: break
            else:
                assert AssertionError, "PostContextID not mentioned in state"

        self.__store_position_begin_of_post_context_id_set.add(PostContextID)

    def pre_context_fulfilled_list(self):
        """This is only relevant during backward lexical analyzis while
           searching for pre-contexts. The list that is returned tells
           that the given pre-contexts are fulfilled in the current state
           and must be set, e.g.

                    pre_context_fulfilled[i] = true; 
        """
        assert self.__pre_context_fulfilled_set != None
        return self.__pre_context_fulfilled_set

class ConditionalDropOutAction:
    """Objects of this class describe what has to happen, if a pre-context
       is fulfilled. The related action may be written in pseudo code:

           if( 'self.pre_context_id' fulfilled ) {
                if( 'self.restore_acceptance_position_f' ) {
                    input_p = last_acceptance_position;
                }
                else if( 'self.post_context_id' != None ) {
                    input_p = position_register['self.post_context_id'];
                }
                if( 'self.pattern_id' == None ) {
                    goto ROUTER(last_acceptance);
                }
                else  {
                    goto 'self.pattern_id' terminal;
                }
           }
            
       Alternatives:

           input_p = position_register[i];
           goto TERMINAL_X;gt

    """
    def __init__(self):
        self.pre_context_id  = PreContextID
        self.pattern_id      = PatternID
        self.post_context_id = PostContextID

class DropOut:
    def __init__(self):
        pass

    def set_restore_last_acceptance_f(self):
        for x in self._sequence:
            x.pattern_id = None


