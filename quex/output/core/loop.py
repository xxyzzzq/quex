"""LOOP STATE MACHINES

A 'loop state machine' has a core state machine that loops on incoming
lexatoms 'i' as long as they fall into the set 'L' which it treats. The
first lexatom that does not fit 'L' causes an exit from the loop, as
shown below. 
                                    
                    .--<-( next i )--. i in L
                 .----.              |
      --------->( Loop )-------------+----------------> Exit
                 '----'                i not in L


The set 'L' may be divided into subsets 'L0', 'L1', etc. that require
loop-actions. Those actions are implemented by means of terminal states.  With
'NL' as the complementary set to 'L', the more general loop is shown below.

             .---------------( next i )-------------.
             |    .------.                          |
         ----+--->|  L0  |------->[ Terminal 0 ]----+
                  +------+                          |
                  |  L1  |------->[ Terminal 1 ]----+
                  +------+                          |
                  |  L2  |------->[ Terminal 2 ]----'
                  +------+
                  |  NL  |------->[ Terminal Exit ]-----------> Exit
                  '------'

_________________________________
MOUNTING PARALLEL STATE MACHINES:

In parallel, matching state machines may be mounted to the loop. The following
assumption is made:

             .-----------------------------------------------.
             | SM's first transition lexatoms are all IN 'L' |
             '-----------------------------------------------'

=> There is a subset 'La' in 'L' which is associated with a terminal 'Terminal
a'.  If SM fails to match, the first lexatom is still a loop lexatom, and
therefore, the loop CONTINUES after the first lexatom. 

      .---<-----------( next i )<-----------------------------.
      |                                                       |
      |                              [ i = ir ]--------->[ Terminal a ]
      |   .------.                       |     
    --+-->: ...  :                       | drop-out 
          +------+                       |          
          |  La  |--->[ ir = i ]--->( Pruned SM )------->[ Terminal SM ]
          +------+                                match
          : ...  :
          '------'

The position of the first input must be stored in 'ir' so that upon drop-out it
may be restored into 'i'. After the appriate 'Terminal a' is executed, the loop
continues. The 'Pruned SM' is the SM without the transition on the first
lexatom.

___________
DEFINITION: 'SML':  Set of state machines where the first lexatom belongs to
                    'L'. Upon drop-out, it LOOPS back.
__________
PROCEDURE:

(1) -- Determine 'L'.
    -- Generate 'Terminal i' for all subsets 'Li' in 'L'.
       Each terminal transits to the loop start.

(2) Group state machines into: 'SMi':  SM's first lexatom in 'L'.

    (Some state machines may be mentioned in both sets)

(3) -- Determine 'pure L', the set of lexatoms in 'L' which do not appear
                           as first lexatoms in parallel state machines.

    -- Determine ('Li', 'TerminalId', 'Pruned SM') for each SM in 'SMi'.
                  'Li' = subset of 'L'. 
                  'TerminalId' indicates the terminal associated with 'Li'.
                  'Pruned SM' = SM with the first lexatom pruned.

(4) Generate the terminals concerned for looping:

    -- Terminals for each 'La' in 'L': Append transition to loop begin.

    -- Terminals for 'SMi'-drop-outs

(4) Setup:

    -- Transitions for each 'La' in 'L' and 'Terminal a' mount a transition:

          .------------------------( next i )----------.
          |   .------.                                 |
          '-->| Loop |-----( La )---->[ Terminal a ]---'
              '------'

    -- Setup 'store input reference' upon entry in all parallel state machines.
"""
import quex.engine.analyzer.core                      as     analyzer_generator
from   quex.engine.operations.operation_list          import Op, \
                                                             OpList
import quex.engine.state_machine.index                as     index
import quex.engine.state_machine.algorithm.beautifier as     beautifier
from   quex.engine.analyzer.door_id_address_label     import DoorID
from   quex.engine.misc.tools                         import typed, \
                                                             flatten_list_of_lists
from   quex.engine.analyzer.terminal.core             import Terminal
from   quex.engine.state_machine.core                 import StateMachine  
from   quex.engine.analyzer.door_id_address_label     import dial_db
from   quex.output.core.variable_db                   import variable_db
import quex.output.core.base                          as     generator

from   quex.blackboard import E_StateIndices, \
                              E_R, \
                              E_CharacterCountType, \
                              setup as Setup, \
                              Lng

from   collections import namedtuple

class LoopElementInfo:
    def __init__(self, CharacterSet, TheCountAction, CoupleIncidenceId, AppendixSmList):
        self.character_set    = CharacterSet
        self.count_action     = CountAction
        self.incidence_id     = CoupleIncidenceId
        self.appendix_sm_list = AppendixSmList 

    def add_appendix_sm(self, SM):
        if any(sm.get_id() == SM.get_id() for sm in self.appendix_sm_list):
            return
        self.appendix_sm_list.append(SM)

@typed(ReloadF=bool, LexemeEndCheckF=bool, OnLoopExit=list)
def do(CcFactory, OnLoopExit, LexemeEndCheckF=False, EngineType=None, 
       ReloadStateExtern=None, LexemeMaintainedF=False,
       ParallelSmTerminalPairList=None):
    """Generates a structure that 'loops' quickly over incoming characters.

                                                             Loop continues           
        .---------( ++i )-----+--------<-------------------. at AFTER position of 
        |    .------.         |                            | the first lexatom 'ir'.
        '--->|      |         |                            |  
             | pure |-->[ Terminals A ]                    |  
             |  L   |-->[ Terminals B ]                    |
             |      |-->[ Terminals C ]                    |
             +------+                                      | 
             |      |                                  ( i = ir )  
             | LaF  |-->[ Terminals A ]-->-.               | drop-out     
             |      |-->[ Terminals B ]-->. \              | 
             |      |-->[ Terminals C ]-->( ir = i )--[ StateMachine ]-->[ Terminals X ]
             |      |                                               \
             +------+                                                '-->[ Terminals Y ]
             | Else |----> Exit
             '------'
    
    The terminals may contain a 'lexeme end check', that ensures that the
    borders of a lexeme are not exceeded.  The loop therefore ends:

        (i)   when a character appears, that is not a loop character.
        (ii)  one of the appendix state machine exits.
        (iii) [Optional] if the lexeme end is reached.
        
    At the end of the iteration, the input pointer points to (the begin of) the
    first lexatom behind what is treated.

            [i][i][i]..................[i][i][X][.... 
                                             |
                                          input_p
            
    During the 'loop' possible line/column count commands may be applied. 
    """
    assert EngineType is not None
    event_handler = LoopEventHandlers(LexemeMaintainedF, CcFactory, OnLoopExit)

    loop_map = _get_loop_map(L, SmList)

    loop_analyzer,      \
    loop_terminal_list, \
    iid_loop,           \
    iid_loop_exit       = _get_loop(loop_map, ColumnNPerChunk, 
                                    LexemeEndCheckF, EngineType, 
                                    ReloadStateExtern, EventHandler)

    appendix_analyzer_list, \
    appendix_terminal_list  = _get_appendices(loop_map, iid_loop)

    # (*) Generate Code ________________________________________________________
    #
    txt = _get_source_code([loop_analyzer]    + appendix_analyzer_list,
                           loop_terminal_list + appendix_terminal_list, 
                           CcFactory.requires_reference_p())
    
    return txt, DoorID.incidence(iid_loop_exit)

def _get_loop_map(L, SmList):
    """A loop map tells about the behavior of the core loop. It tells what
    needs to happen as a consequence to an incoming character. Two options:

        -- Return to loop (normal case)
        -- Enter the tail (appendix) of a parallel state machine.

    RETURNS: List of LoopElementInfo-s. 

    A LoopElementInfo consists of:

       .character_set: Character set that triggers to terminal.
       .count_action:  Count action related to the character set.
       .incidence_id:  Incidence Id of terminal that is triggered by character set.
       .appendix_sm:   Combined list of appendix state machines
                       --> single state machine.

    """
    result = _get_LoopElementInfo_list_parallel_state_machines(TheCountBase, 
                                                               SmList)

    pure_L = L.clone()
    for lei in result:
        pure_L.subtract(lei.character_set)

    result.extend(
        _get_LoopElementInfo_list_plain(TheCountBase, pure_L)
    )

    return result

def _get_LoopElementInfo_list_plain(TheCountBase, pure_L):
    """RETURNS: list of LoopElementInfo-s.

    The list defines the loop behavior for characters which are not transits
    to appendix state machines. The LoopElementInfo-s are setup as below:

         [0] Character set to trigger to a terminal.
         [1] CountAction.
         [2] IncidenceId of the CountAction.
         [3] 'None' indicating: no appendix sm, no 'goto couple state'.
    """
    return [
        LoopElementInfo(character_set, ca, ca.get_incidence_id(), None)
        for character_set, ca in TheCountBase.iterable_in_sub_set(pure_L)
    ]

def _get_LoopElementInfo_list_parallel_state_machines(TheCountBase, SmList):
    """Perform separation:
    
       Parallel state machine  -->  first transition  +  appendix state machine
    
    The 'first transition' is mounted on the loop state machine triggering an
    acceptance that causes a transit to the appendix state machine. 

    RETURNS: list of LoopElementInfo elements for the first transition.
    """
    def iterable(SmList):
        """YIELDS: [0] Character Set
                   [1] CountAction related to that character set.
                   [2] Appendix state machine related to that character set.

        The iterable reports character sets for which their is a distinct count
        action and appendix state machine.
        """
        for sm in SmList:
            for trigger_set, appendix_sm in sm.cut_first_transition(CloneStateMachineId=True):
                for character_set, ca in TheCountBase.iterable_in_sub_set(trigger_set):
                    yield character_set, ca, appendix_sm

    # The tuples reported by 'iterable()' may contain overlapping character
    # sets. That is, their may be multiple parallel state machines that trigger
    # on the same characters in a first transition. The related appendix state
    # machines are combined to a single state machine.
    #
    # 'pre_result' = list of non-overlapping character sets associated with a
    # list of related appendix state machines.
    pre_result = []
    for character_set, ca, appendix_sm in iterable(SmList):
        remainder = character_set
        for previous in pre_result:
            intersection = character_set.intersection(previous.character_set)
            if intersection.is_empty(): 
                continue
            elif intersection.is_equal(previous.character_set):
                previous.add_appendix_sm(appendix_sm)
            else:
                previous.character_set.subtract(intersection)
                pre_result.append(
                    (intersection, ca, previous.appendix_sm_list + [appendix_sm])
                )
            remainder.subtract(intersection)
            if remainder.is_empty(): break

        if not remainder.is_empty():
            pre_result.append(
                (remainder, ca, [appendix_sm])
            )

    # Combine the appendix state machine lists which are related to character
    # sets into a single combined appendix state machine.
    return [
        LoopElementInfo(lei.character_set, ca, dial_db.new_incidence_id(), 
                        _get_combined_state_machine(appendix_sm_list))
        for character_set, ca, appendix_sm_list in pre_result
    ]

def _get_loop(LoopMap, ColumnNPerChunk, LexemeEndCheckF, EngineType, 
              ReloadStateExtern, EventHandler):
    """Construct a state machine that triggers only on one character. Actions
    according the the triggered character are implemented using terminals which
    are entered upon acceptance.

            .------.
       ---->| Loop |
            |      |----> accept A                 (normal loop terminals)
            |      |----> accept B
            |      |----> accept C
            :      :         :
            |      |----> accept CoupleIncidenceA  (terminals towards
            |      |----> accept CoupleIncidenceB   appendix state machines)
            |      |----> accept CoupleIncidenceC    
            :______:         :
            | else |----> accept iid_loop_exit
            '------'

    RETURNS: [0] Loop analyzer (prepared state machine)
             [1] List of terminals directly related to loop
             [2] Incidence id of terminal that goes back to loop rentry.
             [3] Incidence id of terminal that exits loop rentry.
    """
    iid_loop      = dial_db.new_incidence_id() # continue loop
    iid_loop_exit = dial_db.new_incidence_id()

    # Loop StateMachine
    loop_sm = StateMachine.from_IncidenceIdMap(
        (lei.character_set, lei.incidence_id)
        for lei in loop_map
    )
    universal_set = Setup.buffer_codec.source_set
    remainder     = init_state.target_map.get_trigger_set_union_complement(universal_set)
    init_state    = loop_sm.get_init_state()
    init_state.add_transition(remainder, AcceptanceF=True)
    init_state.mark_acceptance_id(iid_loop_exit)

    # Code Transformation
    loop_sm = Setup.buffer_codec.transform(loop_sm)

    # Loop Analyzer
    loop_analyzer, \
    door_id_loop   = _get_loop_analyzer(loop_sm, EngineType, ReloadStateExtern, 
                                        EventHandler)

    # Terminals
    door_id_loop_exit = DoorID.incidence_id(iid_loop_exit)

    loop_terminal_list = [
        _get_loop_terminal(lei, door_id_loop, door_id_loop_exit, 
                           ColumnNPerChunk, LexemeEndCheckF)
        for lei in loop_map
    ]
    loop_terminal_list.append(
        Terminal([Op.GotoDoorId(door_id_loop)], "<LOOP>", iid_loop)
    )
    loop_terminal_list.append(
        Terminal(OnLoopExit, "<LOOP EXIT>", iid_loop_exit)
    )

    return loop_analyzer, loop_terminal_list, iid_loop, iid_loop_exit

def _get_appendices(LoopMap, IidLoop):
    """Parallel state machines are mounted to the loop by cutting the first
    transition and implementing it in the loop. Upon acceptance of the first
    character the according tail (appendix) of the state machine is entered.

    RETURNS: [0] List of appendix state machines in terms of analyzers.
             [1] Appendix terminals.
    """
    # Codec Transformation
    appendix_sm_list = [
        Setup.buffer_code.transform(lei.appendix_sm) for lei in LoopMap
    ]

    # When an appendix state machine drops out, the position of the last loop
    # character must be restored and the loop continues. This behavior is
    # implemented using the usual 'acceptance mechanism': The init state of
    # accepts 'incidence loop re-entry'. If at a later state the state machine
    # drops out, the position of the last acceptance is restored and the 
    # terminal 'loop re-entry' is entered. The loop continues after the last
    # loop character.
    for init_state in (sm.get_init_state() for sm in appendix_sm_list):
        init_state.set_acceptance()
        init_state.mark_acceptance_id(IidLoop)

    # Appendix Analyzer List
    appendix_analyzer_list = [
        analyzer_generator.do(sm, EngineType, ReloadStateExtern,
                              OnBeforeReload = EventHandler.on_before_reload, 
                              OnAfterReload  = EventHandler.on_after_reload)
        for sm in appendix_sm_list
    ]

    # Terminals
    appendix_terminal_list = [
        terminal for sm, terminal in SmTerminalList
    ]

    return appendix_analyzer_list, appendix_terminal_list

def _get_loop_terminal(TheLoopElementInfo, DoorIdLoop, DoorIdLoopExit, 
                       ColumnNPerChunk, LexemeEndCheckF):
    IncidenceId = TheLoopElementInfo.incidence_id
    AppendixSm  = TheLoopElementInfo.appendix_sm

    code = TheLoopElementInfo.count_action.get_OpList(ColumnNPerChunk) 

    if AppendixSm is not None:
        assert not LexemeEndCheckF 
        # Couple Terminal: transit to appendix state machine.
        code.append(
             Op.GotoDoorId(DoorID.state_machine_entry(AppendixSm.get_id())) 
        )
    elif not LexemeEndCheckF: 
        # Loop Terminal: directly re-enter loop.
        code.append(
            Op.GotoDoorId(DoorIdLoop) 
        )
    else:
        # Check Terminal: check against lexeme end before re-entering loop.
        code.append(
            Op.GotoDoorIdIfInputPNotEqualPointer(DoorIdLoop, E_R.LexemeEnd)
        )
        if ColumnNPerChunk is not None and CC_Type == E_CharacterCountType.COLUMN: 
            # With reference counting, no column counting while looping.
            # => Do it now, before leaving.
            code.append(
                Op.ColumnCountReferencePDeltaAdd(E_R.InputP, ColumnNPerChunk, False)
            )
        code.append(
            Op.GotoDoorId(DoorIdLoopExit) 
        )

    return Terminal(code, "<LOOP TERMINAL %i>" % IncidenceId, IncidenceId)

def _get_loop_analyzer(sm, EngineType, ReloadStateExtern, EventHandler):

    analyzer = analyzer_generator.do(sm, EngineType, ReloadStateExtern,
                                     OnBeforeReload = EventHandler.on_before_reload, 
                                     OnAfterReload  = EventHandler.on_after_reload)

    door_id_loop_reentry = _prepare_entry_and_reentry(analyzer, 
                                                      EventHandler.on_loop_entry, 
                                                      EventHandler.on_loop_reentry) 

    return analyzer, door_id_loop_reentry

def _prepare_entry_and_reentry(analyzer, OnLoopEntry, OnLoopReEntry):
    """Prepare the entry and re-entry doors into the initial state
    of the loop-implementing initial state.

                   .----------.
                   | on_entry |
                   '----------'
                        |         .------------.
                        |<--------| on_reentry |<-----.
                        |         '------------'      |
                .----------------.                    |
                |                +-----> Terminal ----+----> Exit
                |      ...       |
                |                +-----> Terminal - - 
                '----------------'

    RETURNS: DoorID of the re-entry door which is used to iterate in the loop.
    """
    # Entry into state machine
    entry            = analyzer.init_state().entry
    init_state_index = analyzer.init_state_index
        
    # OnEntry
    ta_on_entry              = entry.get_action(init_state_index, 
                                                E_StateIndices.BEFORE_ENTRY)
    ta_on_entry.command_list = OpList.concatinate(ta_on_entry.command_list, 
                                                  OnLoopEntry)

    # OnReEntry
    tid_reentry = entry.enter_OpList(init_state_index, index.get(), 
                                     OpList.from_iterable(OnLoopReEntry))
    entry.categorize(init_state_index)

    return entry.get(tid_reentry).door_id

def _get_source_code(analyzer, terminal_list, ColumnNPerChunk):
    """RETURNS: String containing source code for the 'loop'. 

       -- The source code for the (looping) state machine.
       -- The terminals which contain counting actions.

    Also, it requests variable definitions as they are required.
    """
    txt = []
    txt.extend(
        generator.do_analyzer(analyzer)
    )
    txt.extend(
        generator.do_terminals(terminal_list, analyzer)
    )
    if analyzer.engine_type.subject_to_reload():
        txt.extend(
            generator.do_reload_procedure(analyzer)
        )

    if ColumnNPerChunk is not None:   
        variable_db.require("reference_p", 
                            Condition="QUEX_OPTION_COLUMN_NUMBER_COUNTING")
    if Setup.buffer_codec.variable_character_sizes_f(): 
        variable_db.require("lexatom_begin_p")
    return txt

class LoopEventHandlers:
    """Event handlers in terms of 'List of Operations' (objects of class 'Op'):

        .on_loop_entry:     upon entry into loop
        .on_loop_exit:      upon exit from loop
        .on_before_reload:  before buffer reload is performed.
        .on_after_reload:   after buffer reload is performed.
        .on_loop_reentry:   upon every iteration of loop entry.
    """
    @typed(IncidenceIdMap=list, MaintainLexemeF=bool)
    def __init__(self, MaintainLexemeF, CcFactory, UserOnLoopExit): 
        self.__prepare_begin_and_end(CcFactory.on_loop_entry, 
                                     CcFactory.on_loop_exit + UserOnLoopExit)
        self.__prepare_before_and_after_reload(MaintainLexemeF, 
                                               CcFactory.on_before_reload, 
                                               CcFactory.on_after_reload) 

    def __prepare_begin_and_end(self, OnLoopEntry, OnLoopExit):
        """With codecs of dynamic character sizes (UTF8), the pointer to the 
        first letter is stored in 'lexatom_begin_p'. To reset the input 
        pointer 'input_p = lexatom_begin_p' is applied.  
        """
        if not Setup.buffer_codec.variable_character_sizes_f():
            # 1 character == 1 chunk
            # => reset to last character: 'input_p = input_p - 1'
            putback      = [ Op.Decrement(E_R.InputP) ]
            self.on_loop_reentry = []
        else:
            # 1 character == variable number of chunks
            # => store begin of character in 'lexeme_start_p'
            # => rest to laset character: 'input_p = lexeme_start_p'
            putback      = [ Op.Assign(E_R.InputP, E_R.CharacterBeginP) ]
            self.on_loop_reentry = [ Op.Assign(E_R.CharacterBeginP, E_R.InputP) ]
        self.on_loop_entry = concatinate(self.on_loop_reentry, OnLoopEntry)
        self.on_loop_exit  = concatinate(on_putback, OnLoopExit)

    def __prepare_before_and_after_reload(self, MaintainLexemeF, OnBeforeReload, OnAfterReload):
        """The 'lexeme_start_p' restricts the amount of data which is loaded 
        into the buffer upon reload--if the lexeme needs to be maintained. If 
        the lexeme does not need to be maintained, then the whole buffer can 
        be refilled.
        
        For this, the 'lexeme_start_p' is set to the input pointer. 
        
        EXCEPTION: Variable character sizes. There, the 'lexeme_start_p' is used
        to mark the begin of the current letter. However, letters are short, so 
        the drawback is tiny.

        RETURNS: [0] on_before_reload
                 [1] on_after_reload
        """
        if Setup.buffer_codec.variable_character_sizes_f():
            if MaintainLexemeF:
                on_before_reload = [ Op.Assign(E_R.LexemeStartP, E_R.CharacterBeginP) ]
                on_after_reload  = [ Op.Assign(E_R.CharacterBeginP, E_R.LexemeStartP) ]
            else:
                assert False
                # Here, the character begin p needs to be adapted to what has been reloaded.
                on_before_reload = [ ] # Begin of lexeme is enough.
                on_after_reload  = [ ]
        else:
            on_before_reload = [ Op.Assign(E_R.LexemeStartP, E_R.InputP) ] 
            on_after_reload  = [ ] # Op.Assign(E_R.InputP, E_R.LexemeStartP) ]

        self.on_before_reload = concatinate(on_before_reload,OnBeforeReload)
        self.on_after_reload  = concatinate(on_after_reload, OnAfterReload)

