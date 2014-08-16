import quex.engine.generator.state.transition_map.transition as     transition
from quex.blackboard import setup as Setup, \
                            Lng
def do(txt, TriggerMap):
    """Transitions of characters that lie close to each other can be very efficiently
       be identified by a switch statement. For example:

           switch( Value ) {
           case 1: ..
           case 2: ..
           ...
           case 100: ..
           }

       If SwitchFrameF == False, then no 'switch() { ... }' frame is produced.

       Is implemented by the very few lines in assembler (i386): 

           sall    $2, %eax
           movl    .L13(%eax), %eax
           jmp     *%eax

       where 'jmp *%eax' jumps immediately to the correct switch case.
    
       It is therefore of vital interest that those regions are **identified** and
       **not split** by a bisection. To achieve this, such regions are made a 
       transition for themselves based on the character range that they cover.
    """
    global Lng

    case_code_list = []
    for interval, target in TriggerMap:
        target_code = []
        transition.do(target_code, (interval, target))
        case_code_list.append((range(interval.begin, interval.end), target_code))

    txt.extend(Lng.SELECTION("input", case_code_list))
    txt.append("\n")
    return True


