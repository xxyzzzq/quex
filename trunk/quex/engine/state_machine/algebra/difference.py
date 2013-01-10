import quex.engine.state_machine.algebra.intersection as intersection
import quex.engine.state_machine.algebra.inverse      as inverse

def do(A, B): 
    A_and_B     = intersect.do(A, B)
    not_and_A_B = inverse.do(A_and_B)

    # Difference: It only remains in A what is not in A and B.
    return intersect.do(A, not_A_and_B)
