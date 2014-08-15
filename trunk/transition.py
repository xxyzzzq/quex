
def do(txt, TriggerMapEntry, IndentF=False):
    global Lng

    if IndentF:
        txt.append(1)  # indent one scope

    code = TriggerMapEntry[1].code()
    if type(code) == list: txt.extend(code)
    else:                  txt.append(code)

    if Setup.comment_transitions_f: 
        interval = TriggerMapEntry[0] 
        txt.append(Lng.COMMENT(interval.get_utf8_string()))
    else: 
        pass # txt.append("\n")
    return 

