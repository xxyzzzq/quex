

def do(SM_List):
    """Result: A state machine that matches what is matched by one of the
               state machines but by no other.

       Formula:
                       union(All) - intersection(All)
    """
    tmp0 = union.do(SM_List)
    tmp1 = intersection.do(SM_List)
    return difference(tmp0, tmp1)

