from quex.input.setup import setup as Setup

def do(StateIdx, InitStateF, SMD):
    """Generate the code fragment that produce the 'input' character for
       the subsequent transition map. In general this consists of 

           (i)  incrementing/decrementing the input pointer.
           (ii) dereferencing the pointer to get a value.

       The initial state in forward lexing is an exception! The input pointer
       is not increased, since it already stands on the right position from
       the last analyzis step. When the init state is entered from any 'normal'
       state it enters via the 'epilog' generated in the function 
       do_init_state_input_epilog().
    """
    LanguageDB = Setup.language_db

    if SMD.forward_lexing_f() and InitStateF:
        # The init state in forward lexing does not increase the input pointer
        txt = []
    elif SMD.forward_lexing_f():
        # Forward Lexing: Increment Input Pointer
        txt = [        LanguageDB["$label-def"]("$input", StateIdx), "\n",
               "    ", LanguageDB["$input/increment"], "\n"]
    else:
        # Backward Lexing: Decrement Input Pointer
        txt = [         LanguageDB["$label-def"]("$input", StateIdx), "\n",
               "    " + LanguageDB["$input/decrement"], "\n"]

    txt.extend(["    ", LanguageDB["$input/get"], "\n"])

    return txt

def do_init_state_input_epilog(txt, SMD):
    """Define the transition entry of the init state **after** the init state itself.
       It contains 'increment input pointer', which is not required at the begin of
       a lexical analyzis--in forward lexing. When other states transit to the init
       state, they need to increase the input pointer. 
       All this is not necessary in backward lexing, since there, the init state's
       original entry contains 'decrement input pointer' anyway.
    """
    assert SMD.forward_lexing_f()
    LanguageDB     = Setup.language_db
    InitStateIndex = SMD.sm().init_state_index

    txt.extend([        LanguageDB["$label-def"]("$input", InitStateIndex),
                "    ", LanguageDB["$input/increment"],          "\n",
                "    ", LanguageDB["$goto"]("$entry", InitStateIndex), "\n"])
