from quex.blackboard import E_AcceptanceIDs, E_TransitionN

from operator        import attrgetter
from collections     import namedtuple, defaultdict
from itertools       import islice, izip
#______________________________________________________________________________
# Result of the analysis: For each state there is a list of AcceptSequences
# each one representing a path through the state machine to that state. An 
# AcceptSequences is a list of AcceptCondition objects.
# 
AcceptCondition = namedtuple("AcceptCondition", 
                             ["pattern_id", 
                              "pre_context_id", 
                              "accepting_state_index", 
                              "positioning_state_index",
                              "transition_n_since_positioning"])

class AcceptSequence:
    def __init__(self, AcceptanceTrace):
        self.__sequence = [
           AcceptCondition(x.pattern_id, 
                           x.pre_context_id, 
                           x.accepting_state_index, 
                           x.positioning_state_index, 
                           x.transition_n_since_positioning)
           for x in AcceptanceTrace
        ]

    def acceptance_behavior_equal(self, Other):
        if len(self.__sequence) != len(Other.__sequence):    
            return False
        for x, y in izip(self.__sequence, Other.__sequence):
            if   x.pre_context_id != y.pre_context_id: return False
            elif x.pattern_id     != y.pattern_id:     return False
        return True

    def __iter__(self):
        return self.__sequence.__iter__()

    def get_string(self, Indent=0):
        txt = [ " " * (Indent*4) + "p-id     pre-id   as-i     ps-i     tnsp\n"]
        for x in self.__sequence:
            #012345678012345678012345678012345678012345678
            txt.append(" " * (Indent*4) + "%-9s%-9s%-9s%-9s%-9s\n" % ( \
                        x.pattern_id, x.pre_context_id,
                        x.accepting_state_index, x.positioning_state_index,
                        x.transition_n_since_positioning))
        return "".join(txt)

    def __str__(self):
        return self.get_string()

class PositioningInfo(object):
    __slots__ = ("pre_context_id", 
                 "pattern_id",
                 "transition_n_since_positioning", 
                 "positioning_state_index_set")
    def __init__(self, TheAcceptCondition):
        self.pre_context_id                 = TheAcceptCondition.pre_context_id
        self.pattern_id                     = TheAcceptCondition.pattern_id
        self.transition_n_since_positioning = TheAcceptCondition.transition_n_since_positioning
        self.positioning_state_index_set    = set([ TheAcceptCondition.positioning_state_index ])

    def add(self, TheAcceptCondition):
        self.positioning_state_index_set.add(TheAcceptCondition.positioning_state_index)

        if self.transition_n_since_positioning != TheAcceptCondition.transition_n_since_positioning:
            self.transition_n_since_positioning = E_TransitionN.VOID

    def __repr__(self):
        txt  = ".pattern_id                     = %s\n" % repr(self.pattern_id) 
        txt += ".pre_context_id                 = %s\n" % repr(self.pre_context_id) 
        txt += ".transition_n_since_positioning = %s\n" % repr(self.transition_n_since_positioning)
        txt += ".positioning_state_index_set    = %s\n" % repr(self.positioning_state_index_set) 
        return txt

class PathsToState:
    def __init__(self, TraceList):
        self.__list = [ 
            AcceptSequence(x.acceptance_trace) for x in TraceList 
        ]

        # (*) Uniform Acceptance Sequence
        #
        #         map: state_index --> acceptance pattern
        #
        #     If all paths to a state show the same acceptance pattern, than this
        #     pattern is stored. Otherwise, the state index is related to None.
        self.__uniform_acceptance_sequence  = -1 # Undone

        # (*) Acceptance Precedence Matrix
        # 
        #     A matrix that can tell for any two pattern ids A and B:
        #
        #         -- A has always precedence over B
        #         -- B has always precedence over A
        #         -- A and B never occur together in a path.
        #
        #     If there are any two patterns where none of the above 
        #     conditions holds it is considered a 'acceptance precedence clash'.
        self.__acceptance_precedence_matrix = -1 # Undone

        # (*) Set of pattern ids occurring here
        self.__pattern_id_list               = -1 # Undone

        # (*) Positioning info:
        #
        #     map:  (state_index) --> (pattern_id) --> positioning info
        #
        self.__positioning_info             = -1 # Undone

    def get_any_one(self):
        assert len(self.__list) != 0
        return self.__list[0]

    def uniform_acceptance_sequence(self):
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
        if self.__uniform_acceptance_sequence != -1:
            return self.__uniform_acceptance_sequence

        prototype = self.__list[0]

        # Check (1) and (2)
        for accept_sequence in islice(self.__list, 1, None):
            if not accept_sequence.acceptance_behavior_equal(prototype): 
                self.__uniform_acceptance_sequence = None
                break
        else:
            self.__uniform_acceptance_sequence = prototype

        return self.__uniform_acceptance_sequence

    def accepting_state_index_list(self):
        result = []
        for acceptance_sequence in self.__list:
            result.extend(x.accepting_state_index for x in acceptance_sequence)
        return result

    def acceptance_precedence_clash(self):
        # self.__acceptance_precedence_matrix_contruct() is None
        # => there was a clash in the precedence matrix
        return self.acceptance_precedence_matrix() is None

    def acceptance_precedence_get(self, PatternID_A, PatternID_B):
        """RETURNS:
              1   => PatternID_A has always precedence over PatternID_B

              0   => PatternID_A and PatternID_B have always same precedence,
                     only possible of both are the same.

             -1   => PatternID_B has always precedence over PatternID_A

             None => PatternID_A and PatternID_A never occur together.
        """
        # This function should never be called, if there was a acceptance
        # precedence clash.
        assert not self.acceptance_precedence_clash()

        matrix = self.acceptance_precedence_matrix()

        if PatternID_A == PatternID_B:
            return 0

        if PatternID_A > PatternID_B:
            return matrix[PatternID_A][PatternID_B]

        result = matrix[PatternID_B][PatternID_A]
        if result is None:
            return None
        return - result

    def acceptance_precedence_matrix(self):
        """IMPORTANT: The matrix contains only entries [x][y] for x < y.
                      This means, that queries into the matrix need to be 
                      sorted and inverted, if necessary. 

           Consider: acceptance_precedence_get() !
        """
        if self.__acceptance_precedence_matrix == -1:
            self.__acceptance_precedence_matrix = self.__acceptance_precedence_matrix_contruct()

        return self.__acceptance_precedence_matrix

    def pattern_id_list(self):
        if self.__pattern_id_list == -1:
            result = set()
            for accept_sequence in self.__list:
                result.update(x.pattern_id for x in accept_sequence)
            result.sort(key=attrgetter("pattern_id"))
            self.__pattern_id_list = result
        return self.__pattern_id_list

    def positioning_info(self):
        """
        Conclusions on the input positioning behavior at drop-out based on
        different paths through the same state.  Basis for the analysis are the
        PathTrace objects of a state specified as 'ThePathTraceList'.

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
        if self.__positioning_info != -1: 
            return self.__positioning_info

        positioning_info_by_pattern_id = {}
        # -- If the positioning differs for one element in the trace list, or 
        # -- one element has undetermined positioning, 
        # => then the acceptance relates to undetermined positioning.
        for acceptance_sequence in self.__list:
            for x in acceptance_sequence:
                assert x.pattern_id != E_AcceptanceIDs.VOID

                prototype = positioning_info_by_pattern_id.get(x.pattern_id)
                if prototype is None:
                    positioning_info_by_pattern_id[x.pattern_id] = PositioningInfo(x)
                else:
                    prototype.add(x)

        self.__positioning_info = positioning_info_by_pattern_id.values()
        return self.__positioning_info

    def __acceptance_precedence_matrix_contruct(self):
        def matrix_get(matrix, Xid, Yid):
            a = matrix.get(Xid)
            if len(a) == 0: return None
            b = a.get(Yid)
            if b is None: return None
            return b

        # pattern_id_list is sorted by pattern_id
        pattern_id_list = self.pattern_id_list()
        result = defaultdict(dict)
        for i, x_pattern_id in enumerate(pattern_id_list):
            for y_pattern_id in pattern_id_list[i+1:]:
                for accept_sequence in self.__list:
                    value          = accept_sequence.get_precedence(x_pattern_id, y_pattern_id)
                    existing_value = matrix_get(result, x_pattern_id, y_pattern_id)
                    if   existing_value is None:
                        result[x_pattern_id][y_pattern_id] = value 
                    elif existing_value != value:
                        return None
                    else:
                        pass # nothing to be done
        return result

    def __iter__(self):
        return self.__list.__iter__()

def delegate_acceptance_storage(StateIndex, TraceDB, ToDB, DoneSet):
    """A state can potentially carry an acceptance storage command
    further, if all none of its target states inhibits an acceptance
    precedence clash. An acceptance precedence class prohibits that 
    a state can store acceptance without a possible interference.
    """
    target_index_iterable = (x for x in ToDB[StateIndex] if x != StateIndex and x not in DoneSet)

    for target_index in target_index_iterable:
        if TraceDB[target_index].acceptance_precedence_clash():
            return False

    # All target states can store acceptance without 'precedence clash'
    return True

#def get_delegates(StateIndex):
#    """RETURN: 
#       [0] List of target states that can be delegated to store the
#           acceptance storage.
#
#       [1] List of target states that MUST store the acceptance upon
#           the entry from 'StateIndex'.
#
#       None, None means that the state cannot delegate and not store 
#       anything in a subsequent state.
#   """
#   return 
#   #target_index_list = list(x for x in ToDB[StateIndex] if x != StateIndex and x not in DoneSet)
#
#   #if len(target_index_list):
#   #    return [], []
#
#   #for target_index in target_index_list:
#   #    if delegate_acceptance_storage(target_index, TraceDB, ToDB, DoneSet):
#   #        delegate_list.append(target_index)
#   #    else:
#   #        storage_list.append((StateIndex, target_index))
#   #return delegate_list, storage_list
#
#def post_pone_acceptance_storage(AcceptanceStateIndexList, PatternId):
#
#    work_set = set(AcceptanceStateIndexList)
#    done_set = set()
#    while len(work_set) != 0:
#        state_index = work_set.pop()
#        delegate_list, storage_list = get_delegates(state_index)
#        done_set.add(state_index)
#        work_set.update(delegate_list)
#
#        # Perform the storage
#        for from_index, to_index in storage_list:
#            self.state_db[to_index].entry.doors.accepter.add(, compare_func)
#            
#    
#
#
#
