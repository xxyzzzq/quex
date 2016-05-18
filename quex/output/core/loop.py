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
    parallel_terminal_list = []
    parallel_sm_list       = []
    for sm, terminal in ParallelSmTerminalPairList:
        parallel_terminal_list.append(terminal)
        parallel_sm_list.append(sm)

    iid_loop_exit = dial_db.new_incidence_id()

    assert EngineType is not None
    event_handler  = LoopEventHandlers(LexemeMaintainedF, CcFactory, OnLoopExit)

    # LoopMap: Associate characters with the reactions on their occurrence ____
    #
    loop_map,        \
    appendix_sm_list = _get_loop_map(TheCountMap, parallel_sm_list, 
                                     iid_loop_exit)

    # Loop represented by Analyzer-s and Terminal-s ___________________________
    #
    analyzer_list = _get_analyzer_list(LoopMap, EventHandler, appendix_sm_list)
    terminal_list = _get_terminal_list(LoopMap, EventHandler, parallel_terminal_list,
                                       iid_loop_exit)

    # Generate Code ___________________________________________________________
    #
    txt            = _get_source_code(analyzer_list, terminal_list) 
    
    return txt, DoorID.incidence(iid_loop_exit)

@typed(LoopMap=[LoopMapEntry])
def _get_analyzer_list(LoopMap, EventHandler, AppendixSmList): 
    """An appendix state machine is a parallel state machine that is pruned by
    its first transition. The first transition is absorbed into the 'LoopMap'.
    
    RETURNS: list of Analyzer-s.
    """
    # IncidenceId for terminal that initiates continuation of loop.
    iid_loop_after_appendix_drop_out = dial_db.new_incidence_id() 

    # Core Loop Analyzer 
    loop_analyzer,         \
    door_id_loop           = _get_loop_analyzer(LoopMap, EventHandler)

    # Appendix Analyzers 
    appendix_analyzer_list = _get_appendix_analyzers(LoopMap, EventHandler, 
                                                     AppendixSmList,
                                                     iid_loop_after_appendix_drop_out) 

    return [ loop_analyzer ] + appendix_analyzer_list

def _get_terminal_list(LoopMap, EventHandler, ParallelTerminalList, IidLoopExit):
    """RETURNS: list of all Terminal-s.
    """
    loop_terminal_list = _get_loop_terminal_list(LoopMap, EventHandler,
                                                 iid_loop_after_appendix_drop_out, 
                                                 door_id_loop, IidLoopExit) 

    return loop_terminal_list + ParallelTerminalList 

def _get_loop_map(TheCountMap, SmList, IidLoopExit):
    """A loop map tells about the behavior of the core loop. It tells what
    needs to happen as a consequence to an incoming character. Two options:

        -- Return to loop (normal case)
        -- Enter the tail (appendix) of a parallel state machine.

    RETURNS: List of LoopMapEntry-s. 

    A LoopMapEntry consists of:

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
    appendix_sm_list = _get_LoopMapEntry_list_parallel_state_machines(TheCountMap, 
                                                                      SmList)

    L_couple = NumberSet.from_union_of_iterable(
        lei.character_set for lei in couple_list
    )

    # 'plain_list': Transitions to 'normal terminals' 
    #               => perform count action and loop.
    L_plain    = L.difference(L_couple)
    plain_list = _get_LoopMapEntry_list_plain(TheCountMap, L_plain)

    # 'L_exit': Transition to exit
    #           => remaining characters cause exit.
    L_loop = NumberSet.from_union_of_iterable(
        x.character_set for x in chain(couple_list, plain_list)
    )
    universal_set = Setup.buffer_codec.source_set
    L_exit        = L_loop.get_complement(universal_set)
    exit_list     = [ LoopMapEntry(L_exit, None, IidLoopExit, None) ]

    result = couple_list + plain_list + exit_list

    assert not any(lei is None for lei in result)
    assert not any(lei.character_set is None for lei in result)
    assert not any(lei.incidence_id is None for lei in result)
    return result, appendix_sm_list

def _get_LoopMapEntry_list_plain(TheCountBase, L_pure):
    """RETURNS: list of LoopMapEntry-s.

    The list defines the loop behavior for characters which are not transits
    to appendix state machines. The LoopMapEntry-s are setup as below:

         [0] Character set to trigger to a terminal.
         [1] CountAction.
         [2] IncidenceId of the CountAction.
         [3] 'None' indicating: no appendix sm, no 'goto couple state'.
    """
    assert L_pure is not None
    return [
        LoopMapEntry(character_set, ca, ca.get_incidence_id(), None)
        for character_set, ca in TheCountBase.iterable_in_sub_set(L_pure)
    ]

def _get_LoopMapEntry_list_parallel_state_machines(TheCountBase, SmList):
    """Perform separation:
    
       Parallel state machine  -->  first transition  +  appendix state machine
    
    The 'first transition' is mounted on the loop state machine triggering an
    acceptance that causes a transit to the appendix state machine. 

    RETURNS: list of LoopMapEntry-s 
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

    def _determine_LoopMapEntry(sm_db, CharacterSet, CA, AppendixSmList):
        appendix_sm_id    = combined(sm_db, appendix_sm_list)
        has_transitions_f = sm_db[appendix_sm_id].get_init_state().has_transitions()
        if has_transitions_f:
            # There is an appendix after the first transition.
            # => goto the appendix state machine
            return LoopMapEntry(CharacterSet, CA, dial_db.new_incidence_id(), 
                                appendix_sm_id, True)
        else:
            # There is NO appendix after the first transition.
            # => directly goto to terminal of the matched state machine.
            appendix_sm_id = min(sm.get_id() for sm in AppendixSmList)
            return LoopMapEntry(CharacterSet, CA, dial_db.new_incidence_id(),
                                appendix_sm_id, False)

    # Combine the appendix state machine lists which are related to character
    # sets into a single combined appendix state machine.
    appendix_sm_db = {}
    loop_map       = [
        _determine_LoopMapEntry(appendix_sm_db, character_set, ca, appendix_sm_list)
        for character_set, ca, appendix_sm_list in distinct
    ]
    return loop_map, appendix_sm_db.values()

@typed(LoopMap=[LoopMapEntry])
def _get_loop_analyzer(LoopMap, EventHandler):
    """Construct a state machine that triggers only on one character. Actions
    according the the triggered character are implemented using terminals which
    are entered upon acceptance.

            .------.
       ---->| Loop |
            |      |----> accept A                 (normal loop terminals)
            |      |----> accept B
            |      |----> accept C
            :      :         :
            |      |----> accept CoupleIncidenceA  (couple terminals towards
            |      |----> accept CoupleIncidenceB   appendix state machines)
            |      |----> accept CoupleIncidenceC    
            :______:         :
            | else |----> accept iid_loop_exit
            '------'

    RETURNS: [0] Loop analyzer (prepared state machine)
             [1] DoorID of loop entry
    """
    # Loop StateMachine
    sm           = StateMachine.from_IncidenceIdMap(
                       (lei.character_set, lei.incidence_id) for lei in LoopMap
                   )

    # Code Transformation
    sm           = Setup.buffer_codec.transform(sm)

    # Loop Analyzer
    analyzer     = analyzer_generator.do(sm, 
                                         EventHandler.engine_type, 
                                         EventHandler.reload_state_extern, 
                                         OnBeforeReload = EventHandler.on_before_reload, 
                                         OnAfterReload  = EventHandler.on_after_reload)

    door_id_loop = _prepare_entry_and_reentry(analyzer, 
                                              EventHandler.on_loop_entry, 
                                              EventHandler.on_loop_reentry) 

    return analyzer, door_id_loop

@typed(LoopMap=[LoopMapEntry])
def _get_loop_terminal_list(LoopMap, EventHandler, IidLoopAfterAppendixDropOut, 
                            DoorIdLoop, IidLoopExit):
    """RETURNS: List of terminals of the loop state:

        (i)   Counting terminals: Count and return to loop entry.
        (ii)  Couple terminals:   Count and goto appendix state machine.
        (iii) Exit terminal:      Exit loop.

    The '<LOOP>' terminal serves as an address for the appendix state machines.
    If they fail, they can accept its incidence id and re-enter the loop from
    there.
    """
    door_id_loop_exit = DoorID.incidence_id(IidLoopExit)

    result = [
        EventHandler.get_loop_terminal_code(lei, DoorIdLoop, door_id_loop_exit) 
        for lei in LoopMap
    ]
    result.append(
        Terminal(EventHandler.on_loop_after_appendix_drop_out(DoorIdLoop),
                 "<LOOP>", IidLoopAfterAppendixDropOut)
    )
    result.append(
        Terminal(EventHandler.on_loop_exit, "<LOOP EXIT>", IidLoopExit)
    )

    return result

@typed(LoopMap=[LoopMapEntry])
def _get_appendix_analyzers(LoopMap, EventHandler, AppendixSmList, 
                            IidLoopAfterAppendixDropOut): 
    """Parallel state machines are mounted to the loop by cutting the first
    transition and implementing it in the loop. Upon acceptance of the first
    character the according tail (appendix) of the state machine is entered.

    RETURNS: [0] List of appendix state machines in terms of analyzers.
             [1] Appendix terminals.
    """
    # Codec Transformation
    appendix_sm_list = [
        Setup.buffer_code.transform(sm) for sm in AppendixSmList
        if sm.get_init_state().has_transitions()
    ]

    # Appendix Sm Drop Out => Restore position of last loop character.
    # (i)  Couple terminal stored input position in 'CharacterBeginP'.
    # (ii) Terminal 'LoopAfterAppendixDropOut' restores that position.
    # Accepting on the initial state of an appendix state machine ensures
    # that any drop-out ends in this restore terminal.
    for init_state in (sm.get_init_state() for sm in appendix_sm_list):
        init_state.set_acceptance()
        init_state.mark_acceptance_id(IidLoopAfterAppendixDropOut)

    # Appendix Analyzer List
    return [
        analyzer_generator.do(sm, 
                              EventHandler.engine_type, 
                              EventHandler.reload_state_extern, 
                              OnBeforeReload = EventHandler.on_before_reload, 
                              OnAfterReload  = EventHandler.on_after_reload)
        for sm in appendix_sm_list
    ]

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

def _get_source_code(analyzer_list, terminal_list):
    """RETURNS: String containing source code for the 'loop'. 

       -- The source code for the (looping) state machine.
       -- The terminals which contain counting actions.

    Also, it requests variable definitions as they are required.
    """
    txt = flatten_list_of_lists(
        generator.do_analyzer(analyzer) for analyzer in analyzer_list
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
    @typed(TheCountMap=CountInfoMap, LexemeEndCheckF=bool, MaintainLexemeF=bool)
    def __init__(self, TheCountMap, 
                 LexemeEndCheckF, MaintainLexemeF, 
                 EngineType, ReloadStateExtern, UserOnLoopExit): 

        self.__prepare_begin_and_end(TheCountMap.on_loop_entry, 
                                     TheCountMap.on_loop_exit + UserOnLoopExit)
        self.__prepare_before_and_after_reload(MaintainLexemeF, 
                                               TheCountMap.on_before_reload, 
                                               TheCountMap.on_after_reload) 

        self.column_number_per_code_unit = TheCountMap.get_column_count_per_chunk()
        self.lexeme_end_check_f          = LexemeEndCheckF

        self.reload_state_extern = ReloadStateExtern
        self.engine_type         = EngineType

    def __prepare_begin_and_end(self, OnLoopEntry, OnLoopExit):
        """With codecs of dynamic character sizes (UTF8), the pointer to the 
        first letter is stored in 'lexatom_begin_p'. To reset the input 
        pointer 'input_p = lexatom_begin_p' is applied.  
        """
        if not Setup.buffer_codec.variable_character_sizes_f():
            # 1 character == 1 code unit
            # => reset to last character: 'input_p = input_p - 1'
            putback         = [ Op.Decrement(E_R.InputP) ]
            on_loop_reentry = []
        else:
            # 1 character == variable number of code units
            # => store begin of character in 'lexeme_start_p'
            # => reset to last character: 'input_p = lexeme_start_p'
            putback         = [ Op.Assign(E_R.InputP, E_R.CharacterBeginP) ]
            on_loop_reentry = [ Op.Assign(E_R.CharacterBeginP, E_R.InputP) ]

        self.on_loop_entry = OpList.concatinate(on_loop_reentry, OnLoopEntry)
        self.on_loop_exit  = OpList.concatinate(putback, OnLoopExit)

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

        self.on_before_reload = OpList.concatinate(on_before_reload,OnBeforeReload)
        self.on_after_reload  = OpList.concatinate(on_after_reload, OnAfterReload)

    @typed(TheLoopMapEntry=LoopMapEntry)
    def get_loop_terminal_code(self, TheLoopMapEntry, DoorIdLoop, DoorIdLoopExit): 
        """RETURNS: A loop terminal. 

        A terminal: (i)    Counts,
                    (ii)   checks possibly for the lexeme end, and
                    (iii)a either re-enters the loop, or
                    (iii)b transits to an appendix state machine (couple terminal).
        """
        IncidenceId = TheLoopMapEntry.incidence_id
        AppendixSm  = TheLoopMapEntry.appendix_sm_id
        CountAction = TheLoopMapEntry.count_action

        code = CountAction.get_OpList(self.column_number_per_code_unit) 

        if AppendixSmId is not None:
            if not lei.appendix_sm_has_transitions_f:
                # If there is no appendix, directly goto to the terminal.
                code.extend([
                    Op.GotoDoorId(DoorID.incidence_id(AppendixSmId)) 
                ])
            else:
                assert not self.lexeme_end_check_f 
                # Couple Terminal: transit to appendix state machine.
                code.extend([
                    Op.Assign(E_R.CharacterBeginP, E_R.InputP),
                    Op.GotoDoorId(DoorID.state_machine_entry(AppendixSmId)) 
                ])
        elif not self.lexeme_end_check_f: 
            # Loop Terminal: directly re-enter loop.
            code.append(
                Op.GotoDoorId(DoorIdLoop) 
            )
        else:
            # Check Terminal: check against lexeme end before re-entering loop.
            code.append(
                Op.GotoDoorIdIfInputPNotEqualPointer(DoorIdLoop, E_R.LexemeEnd)
            )
            if     self.column_number_per_code_unit is not None \
               and CountAction.cc_type == E_CharacterCountType.COLUMN: 
                # With reference counting, no column counting while looping.
                # => Do it now, before leaving.
                code.append(
                    Op.ColumnCountReferencePDeltaAdd(E_R.InputP, 
                                                     self.column_number_per_code_unit, 
                                                     False)
                )
            code.append(
                Op.GotoDoorId(DoorIdLoopExit) 
            )

        return Terminal(code, "<LOOP TERMINAL %i>" % IncidenceId, IncidenceId)

    def on_loop_after_appendix_drop_out(self, DoorIdLoop):
        # 'CharacterBeginP' has been assigned in the 'Couple Terminal'.
        # (see ".get_loop_terminal_code()").
        return [
            Op.Assign(E_R.InputP, E_R.CharacterBeginP),
            Op.GotoDoorId(DoorIdLoop)
        ]

class LoopMapEntry:
    def __init__(self, CharacterSet, TheCountAction, CoupleIncidenceId, AppendixSmId, 
                 HasTransitionsF=False):
        self.character_set  = CharacterSet
        self.count_action   = TheCountAction
        self.incidence_id   = CoupleIncidenceId
        self.appendix_sm_id = AppendixSmId
        self.appendix_sm_has_transitions_f = HasTransitionsF

    def add_appendix_sm(self, SM):
        if any(sm.get_id() == SM.get_id() for sm in self.appendix_sm_list):
            return
        self.appendix_sm_list.append(SM)

    def __repr__(self):
        return "(%s, %s, %s, %s)" % \
               (self.character_set, self.count_action, self.incidence_id, self.appendix_sm)

