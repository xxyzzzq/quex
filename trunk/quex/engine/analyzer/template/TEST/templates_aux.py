import quex.engine.analyzer.template.core  as templates 
from   quex.engine.analyzer.template.state import TargetScheme, TemplateState
from   operator import attrgetter

def clean_transition_map(tm):
    for i, element in enumerate(tm):
        x = element[1]
        if isinstance(element[1], list): 
            x = tuple(x)
        if isinstance(x, tuple):
            tm[i] = (element[0], TargetScheme(0, x))

class TestTemplateState(TemplateState):
    def __init__(self, TriggerMap, StateIndexList):
        self.__transition_map   = TriggerMap
        clean_transition_map(self.__transition_map)
        self.__state_index_list = StateIndexList

    @property 
    def transition_map(self): return self.__transition_map
    @property
    def state_index_list(self): return self.__state_index_list
    @property
    def index(self): return None


class TestState:
    def __init__(self, TM, Index=None, StateIndexList=None):
        self.transition_map   = TM
        self.index            = Index
        self.state_index_list = StateIndexList

def get_combination(TriggerMap, StateList):
    """Creates A Template Combination Object for the given Trigger Map
       and States. The trigger map is a list of objects

            [ interval, State Index to which interval triggers ] 

       The generated object of type 'TemplateCombination' will contain
       the 'StateList' as '__involved_state_list' and the trigger map
       as '__trigger_map'.
    """

    result = templates.TemplateCombination(map(long, StateList), [])

    for info in TriggerMap: 
        result.append(info[0].begin, info[0].end, info[1])

    return result

def print_tm(TM):
    """Prints a trigger map. That is, character ranges are aligned horizontally, 
       and target states, or respectively involved state lists are printed 
       inside the cells. E.g.

       |         |         |         |        |    [1L, 2L, 3L], 1, [7L, 4L, 3L], 7;

       Means, that there are four intervals. The first is a TemplateCombination
       and triggers to '[1, 2, 3]', the second is a pure state and triggers to 
       state '1', the third is a TemplateCombination and triggers to '[7, 4, 3]'
       and the forth interval triggers to '7'.

       NOTE: The first state in an involved state list is always state index of 
             the TemplateCombination. 
    """
    cursor = 0
    txt    = [" "] * 40
    for info in TM[1:]:
        x = max(0, min(40, info[0].begin))
        txt[x] = "|"

    txt[0]  = "|"
    txt[39] = "|"
    print "".join(txt),

    txt = ""
    for info in TM:
        if not isinstance(info[1], TargetScheme): txt += "%s, " % repr(info[1]).replace("L", "")
        else:                                     txt += "%s, " % repr(info[1].scheme).replace("L", "")
    txt = txt[:-2] + ";"
    print "   " + txt

def print_metric(TM):
    def get_target_scheme_list(TM):
        result = []
        for interval, target in TM:
            if isinstance(target, TargetScheme):
                result.append(target)
        return result

    SL = get_target_scheme_list(TM)
    SL.sort(key=attrgetter("scheme"))

    print "BorderN    = %i" % (len(TM) - 1)
    print "TargetComb = %s" % str(SL)[1:-1].replace("[", "(").replace("]", ")").replace("L", "")

