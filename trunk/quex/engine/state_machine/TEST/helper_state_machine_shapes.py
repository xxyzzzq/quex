from quex.engine.state_machine.core import StateMachine

def line(sm, *StateIndexSequence):
    prev_si = long(StateIndexSequence[0])
    for info in StateIndexSequence[1:]:
        if type(info) != tuple:
            si = long(info)
            sm.add_transition(prev_si, 66, si)
        elif info[0] is None:
            si = long(info[1])
            sm.add_epsilon_transition(prev_si, si)
        else:
            trigger, si = info
            si = long(si)
            sm.add_transition(prev_si, trigger, si)
        prev_si = si
    return sm, len(StateIndexSequence)

def get_linear(sm):
    """Build a linear state machine, so that the predecessor states
    are simply all states with lower indices.
    """
    pic = """
                  (0)--->(1)---> .... (StateN-1)
    """
    line(sm, 0, 1, 2, 3, 4, 5, 6)
    return sm, 7, pic

def get_butterfly(sm):
    pic = """           
                          .-<--(4)--<---.
                         /              |
               (0)---->(1)---->(2)---->(3)---->(6)---->(7)
                         \              |
                          '-<--(5)--<---'
    """
    line(sm, 0, 1, 2, 3, 6, 7)
    line(sm, 3, 4, 1)
    line(sm, 3, 5, 1)
    return sm, 8, pic

def get_fork(sm):
    pic = """           
                          .->--(2)-->---.
                         /              |
               (0)---->(1)---->(3)---->(5)---->(6)
                         \              |
                          '->--(4)-->---'
    """
    sm.add_transition(0L, 66, 1L)
    sm.add_transition(1L, 66, 2L)
    sm.add_transition(1L, 66, 3L)
    sm.add_transition(1L, 66, 4L)
    sm.add_transition(2L, 66, 5L)
    sm.add_transition(3L, 66, 5L)
    sm.add_transition(4L, 66, 5L)
    sm.add_transition(5L, 66, 6L)
    return sm, 7, pic

def get_fork2(sm):
    pic = """           
                          .->--(1)-->---.
                         /              |
                       (0)---->(2)---->(4)---->(5)
                         \                      |
                          '->--(3)-->-----------'
    """
    line(sm, 0, 2, 4, 5)
    line(sm, 0, 3, 5)
    line(sm, 0, 1, 4)
    return sm, 6, pic

def get_fork3(sm):
    pic = """           
                          .->--(2)-->--(5)
                         /              
               (0)---->(1)---->(3)---->(6)
                         \              
                          '->--(4)-->--(7)
    """
    line(sm, 0, 1, 2, 5)
    line(sm, 1, 3, 6)
    line(sm, 1, 4, 7)
    return sm, 8, pic

def get_fork4(sm):
    pic = """           
                  .->--(1)-->--(2)-->--.
                 /                      \  
               (0)---->(3)---->(4)-->---(7)
                 \                      /
                  '->--(5)-->--(6)-->--'
    """
    line(sm, 0, 1, 2, 7)
    line(sm, 0, 3, 4, 7)
    line(sm, 0, 5, 6, 7)
    return sm, 8, pic

def get_long_loop(sm):
    """Build a linear state machine, so that the predecessor states
    are simply all states with lower indices.
    """
    pic = """
                 .--------->(5)---->-----.
                 |                       |
                (0)---->(1)---->(2)---->(6)
                 |               |
                 '--<---(4)-----(3)
    """
    line(sm, 0, 1, 2, 6)
    line(sm, 2, 3, 4, 0)
    line(sm, 0, 5, 6)
    return sm, 7, pic

def get_nested_loop(sm):
    pic = """           
                .--<-------(5)---<------.
                |                       |
               (0)---->(1)---->(2)---->(3)---->(4)
                        |       |   
                        '---<---'
    """
    line(sm, 0, 1, 2, 3, 4)
    line(sm, 3, 5, 0)
    line(sm, 2, 1)
    return sm, 6, pic

def get_mini_loop(sm):
    pic = """           
               (0)---->(1)---->(2)---->(3)
                        |       |   
                        '---<---'
    """
    line(sm, 0, 1, 2, 3)
    line(sm, 2, 1)
    return sm, 4, pic

def get_mini_bubble(sm):
    pic = """
                (0)---->(1)---.
                         |    |
                         '-<--'
    """
    line(sm, 0, 1, 1)
    return sm, 2, pic

def get_bubble(sm):
    pic = """
                .------>(1)
               /       /   \ 
             (0)       |   |
               \       \   /
                '------>(2)
    """
    line(sm, 0, 1, 2, 1)
    line(sm, 0, 2)
    return sm, 3, pic

def get_bubble2(sm):
    pic = """
                .------>(1)------>(3)
               /       /   \     /   \ 
             (0)       |   |     |   |
               \       \   /     \   /
                '------>(2)------>(4)
    """
    line(sm, 0, 1, 3, 4, 3)
    line(sm, 0, 2, 1, 2)
    line(sm, 2, 4)
    return sm, 5, pic

def get_bubble2b(sm):
    pic = """
                .------>(1)------>(3)
               /       /         /   \ 
             (0)      \/        \/   /\ 
               \       \         \   /
                '------>(2)------>(4)
    """
    line(sm, 0, 1, 3, 4, 3)
    line(sm, 1, 2)
    line(sm, 0, 2, 4)
    return sm, 5, pic

def get_bubble3(sm):
    pic = """
                .------>(1)------>(3)
               /       /   \     /   \ 
             (0)       |   |     |   |
               \       \   /     \   /
                '------>(2)       (4)
    """
    line(sm, 0, 1, 3, 4, 3)
    line(sm, 0, 2, 1, 2)
    return sm, 5, pic

def get_bubble4(sm):
    pic = """
                .------>(1)------>(3)
               /       /   \     /   \ 
             (0)       |   |     |   |
               \       \   /     \   /
                '------>(2)<------(4)      (4 has only entry from 3)
    """
    line(sm, 0, 1, 3, 4, 3)
    line(sm, 0, 2, 1, 2)
    line(sm, 4, 2)
    return sm, 5, pic

def get_tree(sm):
    pic = """
                                .---->(3)
                          .->--(2)
                         /      '---->(4)
               (0)---->(1)
                         \      .---->(6)        
                          '->--(5)
                                '---->(7)
    """
    line(sm, 0, 1, 2, 3)
    line(sm, 2, 4)
    line(sm, 1, 5, 6)
    line(sm, 5, 7)
    return sm, 8, pic


def get_sm_shape_names():
    return "linear, butterfly, long_loop, nested_loop, mini_loop, fork, fork2, fork3, fork4, tree, mini_bubble, bubble, bubble2, bubble2b, bubble3, bubble4;"

def get_sm_shape_by_name(Name):
    sm = StateMachine(InitStateIndex=0L)
    if   Name == "linear":      sm, state_n, pic = get_linear(sm)
    elif Name == "butterfly":   sm, state_n, pic = get_butterfly(sm)
    elif Name == "long_loop":   sm, state_n, pic = get_long_loop(sm)
    elif Name == "nested_loop": sm, state_n, pic = get_nested_loop(sm)
    elif Name == "mini_loop":   sm, state_n, pic = get_mini_loop(sm)
    elif Name == "fork":        sm, state_n, pic = get_fork(sm)
    elif Name == "fork2":       sm, state_n, pic = get_fork2(sm)
    elif Name == "fork3":       sm, state_n, pic = get_fork3(sm)
    elif Name == "fork4":       sm, state_n, pic = get_fork4(sm)
    elif Name == "mini_bubble": sm, state_n, pic = get_mini_bubble(sm)
    elif Name == "bubble":      sm, state_n, pic = get_bubble(sm)
    elif Name == "bubble2":     sm, state_n, pic = get_bubble2(sm)
    elif Name == "bubble2b":    sm, state_n, pic = get_bubble2b(sm)
    elif Name == "bubble3":     sm, state_n, pic = get_bubble3(sm)
    elif Name == "bubble4":     sm, state_n, pic = get_bubble4(sm)
    else:                       sm, state_n, pic = get_tree(sm)
    return sm, state_n, pic
