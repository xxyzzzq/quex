from   quex.engine.misc.enum import Enum
from   math                  import log

E_Type = Enum("SWITCH_CASE", "BISECTION", "COMPARISON_SEQUENCE", "UPPER_ONLY", "TRANSITION", "OUTSTANDING")

def get(TriggerMap, 
        size_all_intervals=None, 
        size_all_drop_out_intervals=None):
    """(i) Cost of Bisectioning 
    
       Let 'B' be the cost of bisectioning a given trigger map devided by the number
       of involved characters. It holds:
    
       -- The more ranges are involved in a trigger map, the more 'if-else' we need,
          thus:
                   B increases with len(trigger_map)

          Since for bisection only log2(N) comparisons are necessary (and if linear
          if-else blocks are used, then only if N/2 < log2(N)), it may be assumed that

                           log2(len(trigger_map))            
              (1)  B  = ---------------------------
                           extend(trigger_map)

       (ii) Cost of Switch-Case-ing
        
       Let 'S' be the cost of a switch-case sectioning of a given trigger map, i.e.
       "goto constant * (character - offset)". It holds

       -- The look-up tables used for switches can potentially grow large, so that

                    S = C0 * extend(trigger_map)

          where extend(trigger_map) = all characters in trigger_map.
           
       (*) Decision

       A switch case is preferrable to a bisectioning, if S < B, that is

                                 log2(len(trigger_map))
                          C0 < --------------------------
                                 extend(trigger_map) ** 2

       The magic lies in determining the constant C0, but equation (2) gives a hint.
    """
    TriggerSetN       = len(TriggerMap)
    MiddleTrigger_Idx = int(TriggerSetN / 2)
    middle            = TriggerMap[MiddleTrigger_Idx]

    if TriggerSetN == 1:
        return E_Type.TRANSITION

    # input < 0 is impossible, since unicode codepoints start at 0!
    if middle[0].begin == 0:  
        return E_Type.UPPER_ONLY

    if size_all_intervals is None:
        size_all_intervals          = 0
        size_all_drop_out_intervals = 0
        for interval, target in TriggerMap:
            if target.drop_out_f: size_all_drop_out_intervals += interval.size()
            size_all_intervals += interval.size()

    if size_all_intervals - size_all_drop_out_intervals == 0:
        return E_Type.BISECTION

    p = log(len(TriggerMap), 2) / (size_all_intervals - size_all_drop_out_intervals)

    if p > 0.03: 
        return E_Type.SWITCH_CASE

    if len(TriggerMap) > 5: 
        return E_Type.BISECTION
    else:
        return E_Type.COMPARISON_SEQUENCE

