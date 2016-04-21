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
from   quex.engine.misc.tools                         import typed
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

class SmlInfo:
    def __init__(self, TriggerSet, CountOpList, CoupleIncidenceId, PrunedSm):
        self.trigger_set         = TriggerSet
        self.count_op_list       = CountOpList
        self.couple_incidence_id = CoupleIncidenceId
        self.pruned_sm           = PrunedSm 

@typed(ReloadF=bool, LexemeEndCheckF=bool, OnLoopExit=list)
def do(CcFactory, OnLoopExit, LexemeEndCheckF=False, EngineType=None, 
       ReloadStateExtern=None, LexemeMaintainedF=False,
       ParallelSmTerminalPairList=None):
    """Iterate over lexatoms given in the CcFactory, but also in paralell 
    implement the 'ParallelSmTerminalPairList' with its own terminals.
        
               Buffer Limit Code          --> Reload
               Matched Character Sequence --> Loop Entry
               Else                       --> Exit Loop

    NOTE: This function does NOT code the FAILURE terminal. The caller needs to 
          do this if required.

    Generate code to iterate over the input stream until

           -- A lexatom occurs not in CharacterSet, or
           -- [optional] the 'LexemeEnd' is reached.

    That is, simplified:
                             input in Set
                             .--<--.
                            |      |  LexemeEnd
                            |      +----->------> (Exit)
                          .----.   |
               --------->( Loop )--+----->------> Exit
                          '----'       input 
                                     not in Set
        
    At the end of the iteration, the 'input_p' points to (the begin of) the
    first lexatom which is not in 'L' (or the LexemeEnd).

            [i][i][i]..................[i][i][X][.... 
                                             |
                                          input_p
            
    During the 'loop' possible line/column count commands may be applied. To
    achieve the iteration, a simplified pattern matching engine is implemented:

              transition
              map
              .------.  
              |  i0  |----------> Terminal0:       OpList0   
              +------+
              |  i1  |----------> Terminal1:       OpList1   
              +------+
              |  X2  |----------> Terminal LoopExit: --input_p; goto TerminalExit;
              +------+
              |  i2  |----------> Terminal2:       OpList2
              +------+

    Generates a state machine that loops on 'LoopTargetMap', i.e. executes
    some commands as reaction to lexatoms, but also in parallel may match
    some other patterns given the state machine list 'SmList'. Definitions:

        L      = lexatoms that trigger 'looping'.
        F      = set of first lexatoms in the 'SmList'.
        pure L = lexatoms that only appear in L.
        LaF    = L and F, lexatoms that are first lexatoms and loop lexatoms.
                 If the later state machine fails the 'normal' loop terminal
                 is executed and the loop continues.
        FnL    = F but not L, first lexatoms which are no loop lexatoms.
                 If the later state machine fails the loop exits.
        ip     = input pointer to the lexatom to be treated.

    As soon as a character appears that neither fits 'L' nor 'F' the loop 
    exits. The resulting structure is shown below (reload state transition 
    omitted).
                                                 
                                                             Loop continues           
        .---------( ++ip )----+--------<-------------------. at AFTER position of 
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
    """
    assert EngineType is not None
    # NOT: assert (not EngineType.subject_to_reload()) or ReloadStateExtern is
    # None. This would mean, that the user has to make these kinds of decisions.
    # But, we are easily able to ignore meaningless ReloadStateExtern objects.
    event_handler = LoopEventHandlers(LexemeMaintainedF, CcFactory, OnLoopExit)

    iid_loop      = dial_db.new_incidence_id() # continue loop
    iid_loop_exit = dial_db.new_incidence_id()

    # (*) StateMachine for Loop and Parallel State Machines
    #
    loop_sm, \
    sml_list = _get_state_machines(CcFactory, 
                                   [sm for sm, t in ParallelSmTerminalPairList], 
                                   iid_loop_exit, iid_loop)

    # (*) Codec transformation (if required)
    #
    sm = Setup.buffer_codec.transform(sm)
    for sml in sml_list:
        sml.pruned_sm = Setup.buffer_code.transform(sml.pruned_sm)

    # (*) Analyzer from StateMachine
    #
    door_id_loop_reentry, \
    analyzer              = _get_analyzer(sm, EngineType, ReloadStateExtern, 
                                          event_handler)

    # (*) Terminals for Loop and Parallel State Machines
    #
    terminal_list = _get_terminal_list(CcFactory, 
                                       [t for sm, t in ParallelSmTerminalPairList], 
                                       iid_loop, door_id_loop_reentry,
                                       iid_loop_exit, event_handler.on_loop_exit,
                                       iid_loop_exit_with_restore) 

    # (*) Generate Code _______________________________________________________
    #
    txt = _get_source_code(analyzer, terminal_list, 
                           CcFactory.requires_reference_p())
    
    return txt, DoorID.incidence(iid_loop_exit)

def _get_state_machines(CcFactory, ParallelSmList, IidLoop):
    """Generate a state machine that implements the basic transitions for
    looping mount the parallel state machines. The loops are not closed, yet.
    Instead loop transitions end in terminals that return to the loop entry.

    (i) Loop Terminals: Lexatoms which do not appear in a parallel state machine:
        * loop action (given by CcFactory).
        * goto loop reentry

    (ii) Couple Terminals: Lexatoms which appear in parallel state machine:
        * loop action (given by CcFactory)
        * ir = i (store input position)
        * goto pruned state machine.

    For both, (i) and (ii) terminals need to be generated. This function generates
    state machines that accept and report 'incidence_id's which are related to the
    terminals.

    RETURNS: [0] Loop StateMachine
             [1] List of (first transition trigger set, 
                          couple incidence id, 
                          pruned StateMachine)

    The 'couple incidence id' relates to a terminal (type 'ii') that stores the
    input position, performs the loop action (given by CcFactory) and goes to
    the pruned state machine.
    """
    if ParallelSmList is None: ParallelSmList = []

    pure_L,  \
    sml_list = _configure_parallel_state_machines(ParallelSmList, CcFactory, 
                                                  IidLoop)
    # All parallel state machines are pruned of the first transition and 
    # they accept by default 'IidLoop'.
    #
    #        .-----------.
    #        | pruned sm |----> accept X
    #        |-----------|
    #        | drop-out  |----> accept IidLoop
    #        '-----------'
    #

    # (*) Transitions on 'PURE LOOP characters'.
    # 
    loop_sm = StateMachine.from_IncidenceIdMap(
        (ci.trigger_set, ci.incidence_id)
        for ci in CcFactory.iterable_in_sub_set(pure_L)
    )
    #            .------.
    #       ---->| Loop |
    #            |      |-------> accept A
    #            |      |-------> accept B
    #            |      |-------> accept C
    #            :      :            :

    # (*) Transitions to Parallel State Machines.
    #
    # Upon drop-out the position after the first lexatom is restored and 
    # the loop CONTINUES.
    init_si = loop_sm.init_state_index
    for first_trigger_set, couple_incidence_id, pruned_sm in sml_list:
        ti = loop_sm.add_transition(init_si, first_trigger_set, 
                                    AcceptanceF=True)
        loop_sm.states[i].mark_acceptance_id(couple_incidence_id)

    #           .------.
    #      ---->| Loop |
    #           |      |-------> accept A
    #           |      |-------> accept B
    #           |      |-------> accept C
    #           :      :            :
    #           |      |-------> accept CoupleIncidenceA
    #           |      |-------> accept CoupleIncidenceB
    #           |      |-------> accept CoupleIncidenceC
    #           :      :            :

    # (*) Loop Exit on unconcerned characters/lexatoms.
    #
    _mount_loop_exit_on_init_state(sm, IidLoopExit)

    #           .------.
    #      ---->| Loop |
    #           |      |-------> accept A
    #           |      |-------> accept B
    #           |      |-------> accept C
    #           :      :            :
    #           |      |-------> accept CoupleIncidenceA
    #           |      |-------> accept CoupleIncidenceB
    #           |      |-------> accept CoupleIncidenceC
    #           :______:            :
    #           | else |-------> accept IidLoopExit
    #           '------'
    return sm, sml_list

def _configure_parallel_state_machines(ParallelSmList, CcFactory, IidLoop):
    """Considers the list of state machines which need to be mounted to the
    loop. 'L' is the complete set of lexatoms which 'loop'. 

    RETURNS: [0] Pure L,   the subset of 'L' which are NOT first lexatoms of 
                           any state machine.
             [1] SML_list, list of SmlInfo-s.
    """
    L        = CcFactory.loop_character_set()
    sml_list = []  # information about 'SML'
    for sm in ParallelSmList:
        original_sm_id = sm.get_id() # Clones MUST have the same state machine id!
        # Iterate of 'first transition, remaining state machine' list
        for first_trigger_set, cloned_pruned_sm in sm.cut_first_transition(CloneStateMachineId=True):
            assert_covered_by_L(first_trigger_set, L)
            # [AIRL] Accept at init state: IidLoop.
            # => Upon drop-out input position is restored (position where 
            #    'IidLoop' was accepted) and loop continues. 
            pruned_sm.get_init_state().set_acceptance()
            pruned_sm.get_init_state().mark_acceptance_id(IidLoop)
            sml_list.extend(
                SmlInfo(TriggerSet        = ci.character_set, 
                        CountOpList       = ci.get_OpList(),
                        CoupleIncidenceId = dial_db.new_incidence_id(),
                        PrunedSm          = cloned_pruned_sm)
                for ci in CcFactory.iterable_in_sub_set(first_trigger_set)
            )

    pure_L = L.clone()
    for sml in sml_list:
        pure_L.subtract(sml.trigger_set)

    return pure_L, sml_list

def assert_covered_by_L(first_trigger_set, L):
    # First lexatoms, that are NOT loop lexatoms.
    assert first_trigger_set.difference(L).is_empty(), \
           "First transition of state machine that is mounted in loop\n" \
           "does contain a character which is not covered by the loop\n" \
           "character set. This should have been caught by the input\n" \
           "file parser!"

def _mount_first_transition(loop_sm, FirstTransitionTriggerSet, PrunedSm, IidOnDropOut):
    """Mounts the 'PrunedSm' to the state machine of the loop. If the pruned
    state machine fails, it needs to go to a specific terminal. This is done
    by letting the first state of the pruned state machine accept the 
    'IidOnDropOut' (if the state itself does not accept). If the state machine
    fails, it goes to that terminal which either goes back to the loop or 
    exits.
    """
    loop_sm.states.update(PrunedSm.states)
    ti = loop_sm.add_transition(loop_sm.init_state_index, 
                                FirstTransitionTriggerSet, 
                                PrunedSm.init_state_index)
    mounted_init_state = loop_sm.states[PrunedSm.init_state_index]
    if not mounted_init_state.is_acceptance():
        mounted_init_state.set_acceptance()
        mounted_init_state.mark_acceptance_id(IidOnDropOut)

def _mount_loop_exit_on_init_state(sm, IidLoopExit):
    """Add transitions on anything in the input that is not covered yet to the 
    state that accepts 'LoopExit', i.e. loop exit.
    """
    # Due to '_mount_SMX()' there might be another state that accepts 
    # 'IidLoopExit', but that one restores the input position. 
    # Here, the input position is NOT restored.
    # => new state.
    loop_exit_state_si = sm.create_new_state(MarkAcceptanceId=IidLoopExit, 
                                             RestoreInputPositionF=False)
    init_state      = sm.get_init_state()
    universal_set   = Setup.buffer_codec.source_set
    remainder       = init_state.target_map.get_trigger_set_union_complement(universal_set)
    init_state.add_transition(remainder, loop_exit_state_si)

def _get_terminal_list(CcFactory, ParallelTerminalList, 
                       IidLoop, DoorIdLoopReEntry, 
                       IidLoopExit, OnLoopExit):
    """Collect all terminals:

    -- Terminals performing counting operations according to
       the loop-lexatoms (those are the 'loop terminals').
    -- Terminals that go to: loop re-entry, 
                             loop exit, and 
                             loop-exit after resetting the input pointer.
    -- Terminals related to the parallel state machines.

    NOTE: Nothing has to be done for 'restore input position and continue 
          loop'. The input position is restored upon acceptance of 'IidLoop'
          and the counting action happend at the couple terminal.

    RETURNS: list of Terminal-s.
    """

    door_id_loop      = DoorID.incidence_id(IidLoop)
    door_id_loop_exit = DoorID.incidence_id(IidLoopExit)

    # Terminals counting 'pure loop characters'
    terminal_list = _get_loop_terminals(CcFactory, LexemeEndCheckF, 
                                        DoorIdLoopReEntry, 
                                        door_id_loop_exit)

    # Terminals transiting to parallel (pruned) state machines.
    terminal_list.extend(_get_couple_terminals(SML_List))

    # Terminals of parallel state machines.
    terminal_list.extend(_get_parallel_sm_terminals(ParallelCodeList))

    # Terminal that only re-enters the loop 
    # (after having reset the position where it accepted the input).
    on_loop = [ 
        Op.GotoDoorId(DoorIdLoopReEntry) 
    ]
    terminal_list.append(
        Terminal(on_loop, "<LOOP>", IidLoop)
    )

    # What happens if the incoming character does not fit the loop.
    # => exit.
    terminal_list.append(
        Terminal(OnLoopExit, "<LOOP EXIT>", IidLoopExit)
    )

    return terminal_list

def _get_loop_terminals(CcFactory, LexemeEndCheckF, DoorIdLoopReEntry, DoorIdLoopExit): 
    """CcFactory associates counting actions with NumberSet-s on which they
    are triggered. This function implements the counting actions in Terminal-s.
    Additionally, to the counting action the 'lexeme end check' operations may 
    have to be appended. The incidence ids of the Terminals correspond to the
    incidence ids mentioned in the CcFactory.

    RETURNS: List of 'Terminal' objects.
    """
    def _op_list(CcFactory, X, get_appendix):
        """Loop operations: (i)   Counting line and column numbers.
                            (ii)  Lexeme end check, if required.
                            (iii) Goto loop re-entry, or loop-exit.

        Operation 'i' is determined by 'map_CharacterCountType_to_OpList()' and may be
        an empty operation, if the counts are determined from lexeme length. Operations
        'ii' and 'iii' are determined get 'get_appendix()' which is configured in the
        calling function.
        """
        return   X.map_CharacterCountType_to_OpList(CcFactory.get_column_count_per_chunk()) \
               + get_appendix(X.cc_type)

    def _lexeme_end_check_with_delta_add(CC_Type):
        if CC_Type != E_CharacterCountType.COLUMN: 
            #   input_p != LexemeEnd ? --yes--> DoorIdLoopReEntry
            #   --> DoorIdLoopExit
            return _lexeme_end_check(CC_Type)
        else:
            #   input_p != LexemeEnd ? --yes--> DoorIdLoopReEntry
            #   column_n = (input_p - reference_p) * column_n_per_chunk
            #   --> DoorIdLoopExit
            return [
                Op.GotoDoorIdIfInputPNotEqualPointer(DoorIdLoop, E_R.LexemeEnd),
                Op.ColumnCountReferencePDeltaAdd(E_R.InputP, 
                                                 CcFactory.get_column_count_per_chunk(), 
                                                 False),
                Op.GotoDoorId(DoorIdLoopExit) 
            ]

    def _lexeme_end_check(CC_Type):
        #   input_p != LexemeEnd ? --yes--> DoorIdLoopReEntry
        #   --> DoorIdLoopExit
        return [
            Op.GotoDoorIdIfInputPNotEqualPointer(DoorIdLoop, E_R.LexemeEnd),
            Op.GotoDoorId(DoorIdLoopExit) 
        ] 

    def _no_lexeme_end_check(CC_Type):
        #   --> DoorIdLoopReEntry
        return [ 
            Op.GotoDoorId(DoorIdLoopReEntry) 
        ]

    # Choose the function that generates the 'appendix' operations.
    if not LexemeEndCheckF: 
        get_appendix = _no_lexeme_end_check
    elif CcFactory.requires_reference_p():
        get_appendix = _lexeme_end_check_with_delta_add
    else:
        get_appendix = _lexeme_end_check

    return [ 
        Terminal(_op_list(x, get_appendix), 
                 "<LOOP TERMINAL %i>" % i, 
                 x.incidence_id())
        for i, x in enumerate(CcFactory.__map)
    ] 

def _get_couple_terminals(SML_List):
    """A 'couple terminal' connects the loop state machine to the pruned state
    machine that follows. It does the following:

        * Apply the counting action of the character that causes the transition
          to the pruned state machine.
        * Goto the beginning of the pruned state machine.
        * (Storing the input position.)

    NOTE: Pruned state machine may accept on the init state! They are 
          continuations of 'real state machines' that did not accept on the 
          init state.

    The storing of the input position happens with the 'accept' mechanism (see
    [AIRL]). The pruned state machine accepts on the init state 'IidLoop'.
    If the pruned state machine drops-out without accepting its own terminal,
    the terminal 'IidLoop' is entered which restores the input position that
    has been stored upon acceptance in the init state of the pruned state
    machine.

    RETURNS: list of Terminal-s
    """
    def _op_list(Info):
        door_id_sm_entry = DoorID.state_machine_entry(info.pruned_sm.get_id())
        op_list = CcFactory.op_list_for_sub_set(Info.character_set)
        assert op_list is not None
        op_list.append(Op.GotoDoorId(door_id_sm_entry))
        return op_list

    return [ 
        Terminal(_op_list(info)
                 "<LOOP COUPLE TERMINAL %i>" % info.couple_incidence_id, 
                 info.couple_incidence_id)
        for info in SML_list
    ] 

def _get_analyzer(sm, EngineType, ReloadStateExtern, CcFactory):

    analyzer = analyzer_generator.do(sm, EngineType, ReloadStateExtern,
                                     OnBeforeReload = event_handler.on_before_reload, 
                                     OnAfterReload  = event_handler.on_after_reload)

    door_id_loop_reentry = _prepare_entry_and_reentry(analyzer, 
                                                      event_handler.on_loop_entry, 
                                                      event_handler.on_loop_reentry) 

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

def _get_source_code(analyzer, terminal_list, ReferencePRequiredF):
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

    if ReferencePRequiredF:   
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

