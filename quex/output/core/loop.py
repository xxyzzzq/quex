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

In parallel, matching state machines may be mounted to the loop. Two types
must be distinguished ('SM' = state machine):

(i) SM's first lexatom 'a' IN 'L'

    => There is a subset 'La' in 'L' which is associated with a terminal
    'Terminal a'.  If SM fails to match, the first lexatom is still a loop
    lexatom, and therefore, the loop CONTINUES after the first lexatom. 

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

    The position of the first input must be stored in 'ir' so that upon 
    drop-out it may be restored into 'i'. After the appriate 'Terminal a'
    is executed, the loop continues. The 'Pruned SM' is the SM without
    the transition on the first lexatom.

(ii) SM's first lexatom 'a' NOT IN 'L'

    => There is no terminal associated with the first lexatom. The loop was
    supposed to be quit, if there would not have been the SM. Therefore, if SM
    fails, the loop must exit and the position must be restored to where the
    first lexatom appeared.

          .------.                       
    --+-->: ...  :                      
          +------+                                match
          |  La  |--->[ ir = i ]--->( Pruned SM )------->[ Terminal SM ]
          +------+                       |
          : ...  :                       | drop-out
          '------'                       |
                                     [ i = ir ]--------->[ Terminal Exit ]

___________
DEFINITION: 'SML':  Set of state machines where the first lexatom belongs to
                    'L'. Upon drop-out, it LOOPS back.
            'SMX':  Set of state machines where the first lexatom does not
                    belong to 'L'. Upon drop-out, it EXITS the loop.
__________
PROCEDURE:

(1) -- Determine 'L'.
    -- Generate 'Terminal i' for all subsets 'Li' in 'L'.
       Each terminal transits to the loop start.

(2) Group state machines into: 'SMi':  SM's first lexatom in 'L'.
                               'SMni': SM's first lexatom not in 'L'.

    (Some state machines may be mentioned in both sets)

(3) -- Determine 'pure L', the set of lexatoms in 'L' which do not appear
                           as first lexatoms in parallel state machines.

    -- Determine ('Li', 'TerminalId', 'Pruned SM') for each SM in 'SMi'.
                  'Li' = subset of 'L'. 
                  'TerminalId' indicates the terminal associated with 'Li'.
                  'Pruned SM' = SM with the first lexatom pruned.

    -- Determine ('X', 'Pruned SM') for each SM in 'SMni'. 
                  'X' = set of first lexatoms of SM.
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

SmlInfo = namedtuple("SmlInfo", ("trigger_set", "incidence_id", "pruned_sm"))
SmxInfo = namedtuple("SmxInfo", ("trigger_set", "pruned_sm"))

class LoopEventHandlers:
    """Event handlers in terms of 'List of Operations' (objects of class 'Op'):

        .on_loop_entry:          upon entry into loop
        .on_loop_exit:            upon exit from loop
        .on_before_reload:  before buffer reload is performed.
        .on_after_reload:   after buffer reload is performed.
        .on_loop_reentry:           upon every iteration of loop entry.
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
              |  X2  |----------> Terminal Beyond: --input_p; goto TerminalExit;
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

        .---------( ++ip )-----+                    Loop continues
        |    .------.          |                    at AFTER position of 
        '--->|      |          |                    the first lexatom 'ir'.
             | pure |--->[ Terminals A ]<--------.  
             |  L   |--->[ Terminals B ]<--------.
             |      |--->[ Terminals C ]<--------.
             +------+                            | 
             |      |                        ( i = ir )  
             | LaF  |                            | 
             |      |                            | drop-out     
             |      |--->( ir = i )----[ StateMachine ]---.
             |      |                                      \
             +------+                                       +--->[ Terminals Y ]
             |      |                                      /
             | FnL  |--->( ir = i )----[ StateMachine ]---'
             |      |                            |
             '------'                            | drop-out
                                                 v
                                           Beyond continues 
                                           AT position of 
                                           the first lexatom 'ir'.
    """
    """
    assert EngineType is not None
    # NOT: assert (not EngineType.subject_to_reload()) or ReloadStateExtern is
    # None. This would mean, that the user has to make these kinds of decisions.
    # But, we are easily able to ignore meaningless ReloadStateExtern objects.
    event_handler = LoopEventHandlers(LexemeMaintainedF, CcFactory, OnLoopExit)

    iid_loop_exit    = dial_db.new_incidence_id()
    iid_loop_exit_rs = dial_db.new_incidence_id() # beyond with restoring input position
    iid_loop         = dial_db.new_incidence_id() # return to the beginning of the loop

    # (*) StateMachine for Loop and Parallel State Machines
    #
    sm = _get_state_machine(CcFactory, 
                            [sm for sm, t in ParallelSmTerminalPairList], 
                            iid_loop_exit, iid_loop_exit_rs, iid_loop)

    sm = Setup.buffer_codec.transform(sm)

    # (*) Analyzer from StateMachine
    #
    door_id_loop_reentry, \
    analyzer               = _get_analyzer(sm, EngineType, ReloadStateExtern, 
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

def _get_terminal_list(CcFactory, ParallelTerminalList, 
                       IidLoop, DoorIdLoopReEntry, 
                       IidLoopExit, OnLoopExit,
                       IidLoopExitRs):

    door_id_loop                   = DoorID.incidence_id(IidLoop)
    door_id_loop_exit              = DoorID.incidence_id(IidLoopExit)
    door_id_loop_exit_with_restore = DoorID.incidence_id(IidLoopExitRs)

    terminal_list = _get_loop_terminals(CcFactory, LexemeEndCheckF, 
                                        DoorIdLoopReEntry, 
                                        door_id_loop_exit)
    terminal_list.extend(
        ParallelTerminalList
    )

    on_loop = [ 
        Op.GotoDoorId(DoorIdLoopReEntry) 
    ]
    on_loop_exit_rs = [
        Op.Restore(IidLoopExitRs),
        Op.GotoDoorId(door_id_loop_exit) 
    ]
   
    terminal_list.extend([
        Terminal(on_loop,         "LOOP",                   IidLoop)
        Terminal(OnLoopExit,      "LOOP EXIT",              IidLoopExit)
        Terminal(on_loop_exit_rs, "LOOP EXIT WITH RESTORE", IidLoopExitRs)
    ])

    return terminal_list

def _get_state_machine(CcFactory, ParallelSmList, IidBeyond, IidBeyondRs, IidLoop):
    """Generate a state machine that implements the basic transitions for
    looping mount the parallel state machines. The loops are not closed, yet.
    Instead loop transitions end in terminals that return to the loop entry.

    RETURNS: StateMachine
    """
    if ParallelSmList is None: ParallelSmList = []

    pure_L,   \
    SML_list, \
    SMX_list  = _configure_this(ParallelSmList, CcFactory)

    # (*) Single transitions on 'pure loop characters'.
    # 
    # Loop State ---( loop character set )----> State Accepting on Iid
    #
    # The 'specific Iid' identifies the terminal which implements the loop
    # reaction to the occurrnce of a loop character.
    #
    sm = StateMachine.from_IncidenceIdMap(CcFactory.iterable_in_sub_set(pure_L))

    # (*) First Transitions to Parallel State Machines that 
    #     INTERSECT with the loop character set 'L'.
    #
    # Loop State ---( First Lexatom Set )---> Pruned State Machine
    #
    # Upon drop-out the position after the first lexatom is restored and 
    # the loop CONTINUES.
    for sub_set, incidence_id, pruned_sm in SML_list:
        _mount_pruned_sm(sm, sub_set, pruned_sm, IidLoop)

    # (*) First Transitions to Parallel State Machines that 
    #     DO NOT INTERSECT with the loop character set 'L'.
    #
    # Loop State ---( First Lexatom Set )---> Pruned State Machine
    #
    # Upon drop-out the position after the first lexatom is restored and 
    # the loop EXITS.
    for sub_set, pruned_sm in SMX_list:
        _mount_pruned_sm(sm, sub_set, pruned_sm, IidBeyondRs)

    # Mount the transition to 'on_beyond, only after all state machines have 
    # been mounted.
    _mount_beyond_on_init_state(sm, IidBeyond)
    return _clean_from_spurious_acceptance_beyond(beautifier.do(sm), IidBeyondRs)

def _configure_this(ParallelSmList, CcFactory):
    """Considers the list of state machines which need to be mounted to the
    loop. 'L' is the complete set of lexatoms which 'loop'. 

    RETURNS: [0] Pure L,   the subset of 'L' which are NOT first lexatoms of 
                           any state machine.
             [1] SML_list, the list of informations about state machines which
                           have a first lexatom transition inside 'L'.
             [2] SMX_list, the list of informations about state machines which
                           DO NOT have a first lexatom transition inside 'L'.

    SML_list = list of 'SmlInfo' objects.
    SMX_list = list of 'SmxInfo' objects.
    """
    L        = CcFactory.loop_character_set()
    pure_L   = L.clone()
    sml_list = []  # information about 'SML'
    smx_list = []  # information about 'SMX'
    for sm in ParallelSmList:
        original_sm_id = sm.get_id() # Clones MUST have the same state machine id!
        # Iterate of 'first transition, remaining state machine' list
        for first_trigger_set, pruned_sm in sm.cut_first_transition():
            pruned_sm.set_id(original_sm_id)

            # First lexatoms, that are NOT loop lexatoms.
            not_in_L = first_trigger_set.difference(L)
            if not not_in_L.is_empty():
                smx_list.append(SmxInfo(not_in_L, pruned_sm))               # use the clone
            
            # First lexatom, that are also loop lexatoms.
            in_L = first_trigger_set.intersection(L)
            if not in_L.is_empty():
                pure_L.subtract(in_L)
                sml_list.extend(
                    SmlInfo(sub_set, incidence_id, 
                            pruned_sm.clone(StateMachineId=original_sm_id)) # clone each.
                    for sub_set, incidence_id in CcFactory.iterable_in_sub_set(in_L)
                )

    return pure_L, sml_list, smx_list

def _mount_pruned_sm(loop_sm, FirstTransitionTriggerSet, PrunedSm, IidOnDropOut):
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

def _mount_beyond_on_init_state(sm, IidBeyond):
    """Add transitions on anything in the input that is not covered yet to the 
    state that accepts 'Beyond', i.e. loop exit.
    """
    # Due to '_mount_SMX()' there might be another state that accepts 
    # 'IidBeyond', but that one restores the input position. 
    # Here, the input position is NOT restored.
    # => new state.
    beyond_state_si = sm.create_new_state(MarkAcceptanceId=IidBeyond, 
                                          RestoreInputPositionF=False)
    init_state      = sm.get_init_state()
    universal_set   = Setup.buffer_codec.source_set
    remainder       = init_state.target_map.get_trigger_set_union_complement(universal_set)
    init_state.add_transition(remainder, beyond_state_si)

def _clean_from_spurious_acceptance_beyond(sm, IidBeyondRs):
    """It is conceivable, that the 'beyond acceptance' appears together with
    a state machines acceptance. In that case, the 'beyond acceptance ' needs
    to be deleted.
    """
    for state in sm.iterable_acceptance_states():
        if   not state.single_entry.has_acceptance_id(IidBeyondRs):       continue
        elif not state.single_entry.has_other_acceptance_id(IidBeyondRs): continue
        state.single_entry.remove_acceptance_id(IidBeyondRs)

    return sm

def _get_loop_terminals(CcFactory, LexemeEndCheckF, DoorIdLoopReEntry, DoorIdLoopExit): 
    """Characters are grouped into sets with the same counting action. This
    function generates terminals for each particular counting action. The
    function 'get_appendix()' in order to add further commands to each 
    terminal.

              .----------.        ,----------.   no
          --->| Count Op |-------< LexemeEnd? >------> Loop
              '----------'        '----+-----'
                                       | yes
                                 .-------------.
                                 |  Lexeme End |
                                 |  Count Op   |-----> OnLexemeEnd
                                 '-------------'

    Loop count actions are only implemented in loop
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
            return _lexeme_end_check(CC_Type)
        else:
            return [
                Op.GotoDoorIdIfInputPNotEqualPointer(DoorIdLoop, E_R.LexemeEnd),
                Op.ColumnCountReferencePDeltaAdd(E_R.InputP, 
                                                 CcFactory.get_column_count_per_chunk(), 
                                                 False),
                Op.GotoDoorId(DoorIdLoopExit) 
            ]

    def _lexeme_end_check(CC_Type):
        return [
            Op.GotoDoorIdIfInputPNotEqualPointer(DoorIdLoop, E_R.LexemeEnd),
            Op.GotoDoorId(DoorIdLoopExit) 
        ] 

    def _no_lexeme_end_check(CC_Type):
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
                 "LOOP TERMINAL %i" % i, x.incidence_id())
        for i, x in enumerate(CcFactory.__map)
    ] 

def _get_terminal_beyond(OnBeyond, BeyondIid):
    """Generate Terminal to be executed upon exit from the 'loop'.
    
       BeyondIid  -- 'Beyond Incidence Id', that is the incidencen id if of
                     the terminal to be generated.
    """
    code_on_beyond = CodeTerminal(Lng.COMMAND_LIST(OnBeyond))
    result = Terminal(code_on_beyond, "<BEYOND>", BeyondIid) # Put last considered character back
    return result

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
