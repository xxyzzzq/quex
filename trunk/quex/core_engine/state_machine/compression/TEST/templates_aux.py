import quex.core_engine.state_machine.compression.templates as templates 

def get_combination(TriggerMap, StateList):
    result = templates.Combination(map(long, StateList), [])
    for info in TriggerMap: result.append(info[0].begin, info[0].end, info[1])
    return result

def print_tm(TM):
    cursor = 0
    txt = [" "] * 40
    for info in TM[1:]:
        x = max(0, min(40, info[0].begin))
        txt[x] = "|"

    txt[0]  = "|"
    txt[39] = "|"
    print "".join(txt),

    txt = ""
    for info in TM:
        if type(info[1]) != list: txt += "%i, " % info[1]
        else:                     txt += "%s, " % repr(info[1])
    txt = txt[:-2] + ";"
    print "   " + txt

def print_metric(M):
    print "BorderN     = %i" % M[0]
    print "TargetCombN = %s" % repr(M[1])[1:-1].replace("[", "(").replace("]", ")")

