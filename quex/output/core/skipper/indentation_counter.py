from   quex.input.code.core                         import CodeTerminal
from   quex.engine.analyzer.door_id_address_label   import DoorID
from   quex.engine.operations.operation_list        import Op
from   quex.engine.analyzer.door_id_address_label   import dial_db
from   quex.engine.analyzer.terminal.core           import Terminal
from   quex.engine.loop_counter                     import LoopCountOpFactory
from   quex.engine.state_machine.character_counter  import CountInfo
import quex.output.core.loop                        as     loop
from   quex.blackboard                              import Lng, \
                                                           E_IncidenceIDs, \
                                                           E_R, \
                                                           setup as Setup

def do(Data, TheAnalyzer):
    """________________________________________________________________________
    Counting whitespace at the beginning of a line.

                   .-----<----+----------<--------------+--<----.
                   |          | count                   |       | count = 0
                   |          | whitespace              |       |
                 .---------.  |                         |       |
       --------->|         +--'                         |       |
                 |         |                            |       |
                 |         |                            |       |
                 |         |          .------------.    |       |
                 |         +----->----| suppressor |----'       |
                 |         |          | + newline  |            | 
                 | COUNTER |          '------------'            |
                 |         |          .---------.               |
                 |         +----->----| newline |---------------'
                 |         |          '---------'
                 |         |          .----------------.
                 |         |----->----| on_indentation |---------> RESTART
                 '---------'   else   '----------------'
                                           

    Generate an indentation counter. An indentation counter is entered upon 
    the detection of a newline (which is not followed by a newline suppressor).
    
    Indentation Counter:

                indentation = 0
                column      = 0
                       |
                       |<------------------------.
                .-------------.                  |
                | INDENTATION |       indentation += count
                | COUNTER     |       column      += count
                '-------------'                  |
                       |                         |
                       +-------- whitspace -->---'
                       |
                   Re-Enter 
                   Analyzer
                                            
    An indentation counter is a single state that iterates to itself as long
    as whitespace occurs. During that iteration the column counter is adapted.
    There are two types of adaption:

       -- 'normal' adaption by a fixed delta. This adaption happens upon
          normal space characters.

       -- 'grid' adaption. When a grid character occurs, the column number
          snaps to a value given by a grid size parameter.

    When a newline occurs the indentation counter exits and restarts the
    lexical analysis. If the newline is not followed by a newline suppressor
    the analyzer will immediately be back to the indentation counter state.
    ___________________________________________________________________________
    """
    counter_db            = Data["counter_db"]
    isetup                = Data["indentation_setup"]
    incidence_db          = Data["incidence_db"]
    default_ih_f          = Data["default_indentation_handler_f"]
    mode_name             = Data["mode_name"]
    sm_suppressed_newline = Data["sm_suppressed_newline"]
    sm_newline            = isetup.sm_newline.get()
    sm_comment            = isetup.sm_comment.get()

    assert sm_suppressed_newline  is None or sm_suppressed_newline.is_DFA_compliant()
    assert sm_newline is None             or sm_newline.is_DFA_compliant()
    assert sm_comment is None             or sm_comment.is_DFA_compliant()

    # -- 'on_indentation' == 'on_beyond': 
    #     A handler is called as soon as an indentation has been detected.
    on_loop_exit = [
        Op.IndentationHandlerCall(default_ih_f, mode_name),
        Op.GotoDoorId(DoorID.continue_without_on_after_match())
    ]

    # -- 'on_bad_indentation' is invoked if a character appeared that has been
    #    explicitly disallowed to be used as indentation.
    bad_indentation_iid = dial_db.new_incidence_id() 

    reload_state        = TheAnalyzer.reload_state

    sm_terminal_list    = _get_state_machine_vs_terminal_list(sm_suppressed_newline, 
                                                              isetup.sm_newline.get(),
                                                              isetup.sm_comment.get(), 
                                                              counter_db)

    # 'whitespace' --> normal counting
    # 'bad'        --> goto bad character indentation handler
    # else         --> non-whitespace detected => handle indentation
    ccfactory = LoopCountOpFactory.from_ParserDataIndentation(isetup, 
                                                              counter_db, 
                                                              Lng.INPUT_P(), 
                                                              DoorID.incidence(bad_indentation_iid))

    # (*) Generate Code
    code,          \
    door_id_beyond = loop.do(ccfactory, 
                             OnLoopExit        = on_loop_exit,
                             EngineType        = TheAnalyzer.engine_type,
                             ReloadStateExtern = reload_state,
                             LexemeMaintainedF = True,
                             ParallelSmTerminalPairList = sm_terminal_list)

    _code_terminal_on_bad_indentation_character(code, isetup, mode_name, incidence_db, 
                                                bad_indentation_iid)

    return code

def _get_state_machine_vs_terminal_list(SmSuppressedNewline, SmNewline, SmComment, CounterDb): 
    """Get a list of pairs (state machine, terminal) for the newline, suppressed
    newline and comment:

    newline --> 'eat' newline state machine, then RESTART counting the
                columns of whitespace.
    newline_suppressor + newline --> 'eat' newline suppressor + newline
                     then CONTNIUE with column count of whitespace.
    comment --> 'eat' anything until the next newline, then RESTART
                 counting columns of whitespace.
    """
    result = []
    # If nothing is to be done, nothing is appended
    _add_pair(result, SmSuppressedNewline, "<INDENTATION SUPPRESSED NEWLINE>")
    _add_pair(result, SmNewline, "<INDENTATION NEWLINE>")
    _add_pair(result, SmComment, "<INDENTATION COMMENT>")

    for sm, terminal in result:
        assert sm.get_id() == terminal.incidence_id()
    return result

def _add_pair(psml, SmOriginal, Name):
    """Add a state machine-terminal pair to 'psml'. A terminal is generated
    which transits to 'INDENTATION_HANDLER'. The state machine is cloned
    for safety.
    """
    if SmOriginal is None: return

    incidence_id = dial_db.new_incidence_id()

    # Disconnect from machines being used elsewhere.
    sm = SmOriginal.clone()
    sm.set_id(incidence_id)

    code = [ 
        Lng.GOTO(DoorID.incidence(E_IncidenceIDs.INDENTATION_HANDLER)) 
    ]

    terminal = Terminal(CodeTerminal(code), Name, incidence_id)
    # TRY:     terminal.set_requires_goto_loop_entry_f()
    # INSTEAD: GOTO 'INDENTATION_HANDLER'

    psml.append((sm, terminal))

def _code_terminal_on_bad_indentation_character(code, ISetup, ModeName, 
                                                incidence_db, BadIndentationIid):
    if ISetup.bad_character_set.get() is None:
        return
    on_bad_indentation_txt = Lng.SOURCE_REFERENCED(incidence_db[E_IncidenceIDs.INDENTATION_BAD])
    code.extend([
        "%s\n" % Lng.LABEL(DoorID.incidence(BadIndentationIid)),
        "#define BadCharacter (me->buffer._read_p[-1])\n",
        "%s\n" % on_bad_indentation_txt,
        "#undef  BadCharacter\n",
        "%s\n" % Lng.GOTO(DoorID.global_reentry())
    ])

