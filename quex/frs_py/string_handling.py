def trim(Str):
    """Deletes whitepspace borders of a string.
       
       Transforms: input  = "  hallo, du da   "
       into        output = "hallo, du da"
    """

    if Str == "": return ""
    L = len(Str)
    for i in range(L):
        if Str[i] not in [" ", "\t", "\n"]:
            break
    else:
        # reached end of string --> empty string
        return ""

    for k in range(1, L-i):
        if Str[-k] not in [" ", "\t", "\n"]:
            break

    # note, if k = 1 then we would return Str[i:0]
    if L-i != 1:
        if k == 1:   return Str[i:]
        else:        return Str[i:-k + 1]
    else:            return Str[i:]


def blue_print(BluePrintStr, Replacements):
    """Takes a string acting as blue print and replaces all
       replacements of the form r in Replacements:

           r[0] = original pattern
           r[1] = replacements
    """
    # (*) sort the replacements so that long strings
    #     are replaced first
    Replacements.sort(lambda a, b: cmp(len(b[0]), len(a[0])))

    txt = BluePrintStr
    for orig, replacement in Replacements:
        if type(replacement) == type(""):
            txt = txt.replace(orig, replacement)
        else:
            txt = txt.replace(orig, repr(replacement))
            
    return txt


def tex_safe(Str):

    for letter in "_%&^#$":
        Str.replace(letter, "\\" + letter)

    return Str
