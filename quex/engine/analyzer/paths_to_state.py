from collections     import namedtuple
from itertools       import islice, izip
from quex.blackboard import E_AcceptanceIDs, E_TransitionN
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
        if len(self.__sequence) != len(Other.__sequence):    return None
        for x, y in izip(self.__sequence, Other.__sequence):
            if   x.pre_context_id != y.pre_context_id: return None
            elif x.pattern_id     != y.pattern_id:     return None

    def __iter__(self):
        return self.__sequence.__iter__()

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

    def add(self, PathTraceElement):
        self.positioning_state_index_set.add(PathTraceElement.positioning_state_index)

        if self.transition_n_since_positioning != PathTraceElement.transition_n_since_positioning:
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
        self.__uniform_acceptance_sequence = -1 # Undone

        # (*) Positioning info:
        #
        #     map:  (state_index) --> (pattern_id) --> positioning info
        #
        self.__positioning_info            = -1 # Undone

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
        for acceptance_trace in islice(self.__list, 1, None):
            if acceptance_trace.acceptance_behavior_equal(prototype): 
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
        for acceptance_trace in self.__list:
            for element in acceptance_trace:
                assert element.pattern_id != E_AcceptanceIDs.VOID

                prototype = positioning_info_by_pattern_id.get(element.pattern_id)
                if prototype is None:
                    positioning_info_by_pattern_id[element.pattern_id] = PositioningInfo(element)
                else:
                    prototype.add(element)

        self.__positioning_info = positioning_info_by_pattern_id.values()
        return self.__positioning_info

