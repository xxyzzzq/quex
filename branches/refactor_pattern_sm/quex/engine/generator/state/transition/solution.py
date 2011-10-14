from   quex.engine.misc.enum import Enum
from   math                  import log

E_Type = Enum("SWITCH_CASE", "BISECTION", "COMPARISON_SEQUENCE", "UPPER_ONLY", "TRANSITION", "OUTSTANDING")

def get(TriggerMap, 
        size_all_intervals=None, 
        size_all_drop_out_intervals=None):
    """Let P be the preferably of a switch statement over bisection or linear if-else
       blocks. The following heuristics may be applied:
    
       -- The more ranges are involved in a trigger map, the more 'if-else' we need,
          thus:
                   P increases with len(trigger_map)

          Since only for bisection only log2(N) comparisons are necessary (and if linear
          if-else blocks are used, then only if N/2 < log2(N)), it may be assumed that

              (1)  P increases with log2(len(trigger_map))            

       -- The look-up tables used for switches can potentially grow large, so that

                   P decreases wit== E_Type.SWITCH_CASE
          where size(trigger_map) = all characters minus the ones that 'drop-out', thus
           
              (2)  P decreases with size(all intervals) - size(all drop out intervals)
               

       The following heuristic is proposed:

              P = log2(len(trigger_map)) / sum(all interval) - sum(drop_out_intervals) 
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

