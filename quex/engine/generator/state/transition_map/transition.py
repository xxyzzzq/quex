from quex.blackboard import setup as Setup, \
                            Lng

def do(Interval, Target, IndentF=False):
    global Setup
    global Lng

    code = Target.code()
    txt  = []
    if type(code) == list: txt.extend(code)
    else:                  txt.append(code)

    if Setup.comment_transitions_f: 
        txt.append(Lng.COMMENT(Interval.get_utf8_string()))

    return txt

