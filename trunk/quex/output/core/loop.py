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
import quex.engine.analyzer.core                          as     analyzer_generator
from   quex.engine.state_machine.engine_state_machine_set import get_combined_state_machine
from   quex.engine.operations.operation_list              import Op, \
                                                                 OpList
import quex.engine.state_machine.index                    as     index
import quex.engine.state_machine.algorithm.beautifier     as     beautifier
from   quex.engine.analyzer.door_id_address_label         import DoorID
from   quex.engine.misc.interval_handling                 import NumberSet
from   quex.engine.misc.tools                             import typed, \
                                                                 flatten_list_of_lists
from   quex.engine.analyzer.terminal.core                 import Terminal
from   quex.engine.state_machine.core                     import StateMachine  
from   quex.engine.analyzer.door_id_address_label         import dial_db
from   quex.output.core.variable_db                       import variable_db
import quex.output.core.base                              as     generator

from   quex.blackboard import E_StateIndices, \
                              E_R, \
                              E_CharacterCountType, \
                              setup as Setup, \
                              Lng

from   collections import namedtuple
from   itertools   import chain

class LoopElementInfo:
    def __init__(self, CharacterSet, TheCountAction, CoupleIncidenceId, AppendixSmId):
        self.character_set  = CharacterSet
        self.count_action   = TheCountAction
        self.incidence_id   = CoupleIncidenceId
        self.appendix_sm_id = AppendixSmId

    def add_appendix_sm(self, SM):
        if any(sm.get_id() == SM.get_id() for sm in self.appendix_sm_list):
            return
        self.appendix_sm_list.append(SM)

    def __repr__(self):
        return "(%s, %s, %s, %s)" % \
               (self.character_set, self.count_action, self.incidence_id, self.appendix_sm)

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
    iid_loop      = dial_db.new_incidence_id() # continue loop
    iid_loop_exit = dial_db.new_incidence_id()

    event_handler = LoopEventHandlers(LexemeMaintainedF, CcFactory, OnLoopExit)

    loop_map = _get_loop_map(TheCountMap, SmList, iid_loop_exit)

    loop_analyzer,      \
    loop_terminal_list  = _get_loop_core(loop_map, iid_loop, iid_loop_exit, 
                                         ColumnNPerChunk, LexemeEndCheckF, EngineType, 
                                         ReloadStateExtern, EventHandler)

    appendix_analyzer_list, \
    appendix_terminal_list  = _get_appendix_sm_list(loop_map, iid_loop)

    # (*) Generate Code ________________________________________________________
    #
    txt = _get_source_code([loop_analyzer]    + appendix_analyzer_list,
                           loop_terminal_list + appendix_terminal_list, 
                           CcFactory.requires_reference_p())
    
    return txt, DoorID.incidence(iid_loop_exit)

def _get_loop_map(TheCountMap, SmList, IidLoopExit):
    """A loop map tells about the behavior of the core loop. It tells what
    needs to happen as a consequence to an incoming character. Two options:

        -- Return to loop (normal case)
        -- Enter the tail (appendix) of a parallel state machine.

    RETURNS: List of LoopElementInfo-s. 

    A LoopElementInfo consists of:

       .character_set: Character set that triggers.
       .count_action:  Count action related to the character set.
                       == None, if the character set causes 'loop exit'.
       .incidence_id:  Incidence Id of terminal that is triggered by character set.
                       -- incidence id of count action terminal, or
                       -- incidence id of couple terminal.
       .appendix_sm:   Appendix state machine
                       -- combined appendix state machines, or
                       -- None, indicating that there is none.
    """
    L = TheCountMap.loop_character_set()

    # 'couple_list': Transitions to 'couple terminals' 
    #                => connect to appendix state machines
    couple_list,     \
    appendix_sm_list = _get_LoopElementInfo_list_parallel_state_machines(TheCountMap, 
                                                                         SmList)

    L_couple = NumberSet.from_union_of_iterable(
        lei.character_set for lei in couple_list
    )

    # 'plain_list': Transitions to 'normal terminals' 
    #               => perform count action and loop.
    L_plain    = L.difference(L_couple)
    plain_list = _get_LoopElementInfo_list_plain(TheCountMap, L_plain)

    # 'L_exit': Transition to exit
    #           => remaining characters cause exit.
    L_loop = NumberSet.from_union_of_iterable(
        x.character_set for x in chain(couple_list, plain_list)
    )
    universal_set = Setup.buffer_codec.source_set
    L_exit        = L_loop.get_complement(universal_set)
    exit_list     = [
        LoopElementInfo(L_exit, None, IidLoopExit, None)
    ]

    result = couple_list + plain_list + exit_list

    assert not any(lei is None for lei in result)
    assert not any(lei.character_set is None for lei in result)
    assert not any(lei.incidence_id is None for lei in result)
    return result, appendix_sm_list

def _get_LoopElementInfo_list_plain(TheCountBase, L_pure):
    """RETURNS: list of LoopElementInfo-s.

    The list defines the loop behavior for characters which are not transits
    to appendix state machines. The LoopElementInfo-s are setup as below:

         [0] Character set to trigger to a terminal.
         [1] CountAction.
         [2] IncidenceId of the CountAction.
         [3] 'None' indicating: no appendix sm, no 'goto couple state'.
    """
    assert L_pure is not None
    return [
        LoopElementInfo(character_set, ca, ca.get_incidence_id(), None)
        for character_set, ca in TheCountBase.iterable_in_sub_set(L_pure)
    ]

def _get_LoopElementInfo_list_parallel_state_machines(TheCountBase, SmList):
    """Perform separation:
    
       Parallel state machine  -->  first transition  +  appendix state machine
    
    The 'first transition' is mounted on the loop state machine triggering an
    acceptance that causes a transit to the appendix state machine. 

    RETURNS: list of LoopElementInfo-s 
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

    def unique(SmList):
        """RETURNS: list of state machines, where no state machine appears
                    more than once.
        """
        result   = []
        done_set = set()
        for sm in SmList:
            if sm.get_id() in done_set: continue
            done_set.add(sm.get_id())
            result.append(sm)
        return result

    def combined(appendix_sm_db, SmList):
        sm_ulist = unique(SmList)
        id_key   = tuple(sorted(list(set(sm.get_id() for sm in sm_ulist))))
        entry = appendix_sm_db.get(id_key)
        if entry is None:
            entry = get_combined_state_machine(sm_ulist,
                                               AlllowInitStateAcceptF=True)
            appendix_sm_db[id_key] = entry
        return entry.get_id()

    # The tuples reported by 'iterable()' may contain overlapping character
    # sets. That is, their may be multiple parallel state machines that trigger
    # on the same characters in a first transition. 
    #
    distinct = [] # list of [0] Character Set
    #                       [1] Count Action related to [0]
    #                       [2] List of appendix state machines related [0]
    # All character sets [0] in the distinct list are NON-OVERLAPPING.
    for character_set, ca, appendix_sm in iterable(SmList):
        remainder = character_set
        for prev_character_set, prev_ca, prev_appendix_sm_list in distinct:
            intersection = character_set.intersection(prev_character_set)
            if intersection.is_empty(): 
                continue
            elif intersection.is_equal(prev_character_set):
                prev_appendix_sm_list.append(appendix_sm)
            else:
                prev_character_set.subtract(intersection)
                distinct.append(
                    (intersection, ca, prev_appendix_sm_list + [appendix_sm])
                )
            remainder.subtract(intersection)
            if remainder.is_empty(): break

        if not remainder.is_empty():
            distinct.append(
                (remainder, ca, [appendix_sm])
            )

    # Combine the appendix state machine lists which are related to character
    # sets into a single combined appendix state machine.
    appendix_sm_db = {}
    loop_map       = [
        LoopElementInfo(character_set, ca, dial_db.new_incidence_id(), 
                        combined(appendix_sm_db, appendix_sm_list))
        for character_set, ca, appendix_sm_list in distinct
    ]
    return loop_map, appendix_sm_db.values()

def _get_loop_core(LoopMap, IidLoop, IidLoopExit, 
                   ColumnNPerChunk, LexemeEndCheckF, EngineType, 
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
    analyzer,      \
    door_id_loop   = _get_loop_analyzer(LoopMap, IidLoop)

    terminal_list, \
    iid_loop       = _get_loop_terminals(LoopMap, IidLoop, door_id_loop, IidLoopExit, 
                                         ColumnNPerChunk, LexemeEndCheckF)

    return loop_analyzer, loop_terminal_list, door_id_loop, iid_loop

def _get_loop_analyzer(LoopMap, EngineType, EventHandler, ReloadStateExtern):
    # Loop StateMachine
    sm = StateMachine.from_IncidenceIdMap(
        (lei.character_set, lei.incidence_id) for lei in LoopMap
    )

    # Code Transformation
    sm = Setup.buffer_codec.transform(sm)

    # Loop Analyzer
    analyzer = analyzer_generator.do(sm, EngineType, ReloadStateExtern,
                                     OnBeforeReload = EventHandler.on_before_reload, 
                                     OnAfterReload  = EventHandler.on_after_reload)

    door_id_loop = _prepare_entry_and_reentry(analyzer, 
                                              EventHandler.on_loop_entry, 
                                              EventHandler.on_loop_reentry) 

    return analyzer, door_id_loop

def _get_loop_terminals(LoopMap, IidLoop, DoorIdLoop, IidLoopExit, ColumnNPerChunk, 
                        LexemeEndCheckF, OnLoopExit):
    door_id_loop_exit = DoorID.incidence_id(IidLoopExit)

    loop_terminal_list = [
        _get_loop_terminal(lei, DoorIdLoop, door_id_loop_exit, 
                           ColumnNPerChunk, LexemeEndCheckF)
        for lei in LoopMap
    ]
    loop_terminal_list.append(
        Terminal([Op.GotoDoorId(DoorIdLoop)], "<LOOP>", IidLoop)
    )
    loop_terminal_list.append(
        Terminal(OnLoopExit, "<LOOP EXIT>", IidLoopExit)
    )

    return loop_terminal_list, IidLoop

def _get_appendix_sm_list(LoopMap, IidLoop):
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
    AppendixSm  = TheLoopElementInfo.appendix_sm_id
    CountAction = TheLoopElementInfo.count_action

    code = CountAction.get_OpList(ColumnNPerChunk) 

    if AppendixSmId is not None:
        assert not LexemeEndCheckF 
        # Couple Terminal: transit to appendix state machine.
        code.append(
             Op.GotoDoorId(DoorID.state_machine_entry(AppendixSmId)) 
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
        if     ColumnNPerChunk is not None \
           and CountAction.cc_type == E_CharacterCountType.COLUMN: 
            # With reference counting, no column counting while looping.
            # => Do it now, before leaving.
            code.append(
                Op.ColumnCountReferencePDeltaAdd(E_R.InputP, ColumnNPerChunk, False)
            )
        code.append(
            Op.GotoDoorId(DoorIdLoopExit) 
        )

    return Terminal(code, "<LOOP TERMINAL %i>" % IncidenceId, IncidenceId)

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

