"""
Encoding Transformations:

A state machine is originally defined in terms of pure numbers. When dealing
with text, those numbers correspond to ASCII or Unicode Code Points. Input,
however, may appear in different formats, i.e. encodings. There are two ways to
cope with that: (i) converting input at run-time and (ii) converting a state
machine to treat the encoded content directly. The classes of this module
support the second solution, i.e. the transformation of a state machine that
runs on a specific encoding. All classes are derived from 'EncodingTrafo' 
which implements the interfaces to be obeyed by all.

  * EncodingTrafoUnicode:    lexatom --> same lexatom

    Mapping holds as long as the lexatom is in the range defined by the
    buffer's lexatom size and the encoding (e.g. ASCII <= 0x7F).

  * EncodingTrafoByTable:    lexatom --> other lexatom

    A given lexatom has a distinct resulting lexatom as described in a 
    table. Some lexatoms, may be exempted and cannot be transformed.

  * EncodingTrafoByFunction: lexatom sequence = function(lexatom)

    A lexatom in the original state machine is converted into a lexatom 
    sequence of the result. This type of transformations is required to
    construct state machines running of UTF8, for example.

(C) Frank-Rene Schaefer
"""
from   quex.engine.misc.interval_handling                         import NumberSet


def do(setup, BufferCodecName, BufferCodecFileName=""):
    from   quex.engine.state_machine.transformation.base              import EncodingTrafoUnicode
    from   quex.engine.state_machine.transformation.table             import EncodingTrafoByTable
    from   quex.engine.state_machine.transformation.utf8_state_split  import EncodingTrafoUTF8
    from   quex.engine.state_machine.transformation.utf16_state_split import EncodingTrafoUTF16

    if   BufferCodecName == "utf8":
        return EncodingTrafoUTF8()

    elif BufferCodecName == "utf16":
        return EncodingTrafoUTF16()

    elif BufferCodecFileName:
        os.path.splitext(os.path.basename(BufferCodecFileName))
        try: 
           os.path.splitext(os.path.basename(BufferCodecFileName))
        except:
            error.log("cannot interpret string following '--codec-file'")
        return EncodingTrafoByTable(FileName=BufferCodecFileName)

    elif BufferCodecName == "unicode":
        # (Still, 'icu' or 'iconv' may provide converted content, but ...) 
        # If the internal buffer is 'unicode', then the pattern's state 
        # machines are not converted. The requirement for the pattern's
        # range is the same as for the 'buffer element chunks'.
        return EncodingTrafoUnicode(
                            NumberSet.from_range(0, setup.get_character_value_limit()), 
                            NumberSet.from_range(0, setup.get_character_value_limit()))

    elif BufferCodecName == "unit-test":
        return EncodingTrafoUnicode(
                            NumberSet.from_range(-sys.maxint, sys.maxint),
                            NumberSet.from_range(-sys.maxint, sys.maxint))

    else:
        return EncodingTrafoByTable(BufferCodecName)
