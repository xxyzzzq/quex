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

        .on_begin:          upon entry into loop
        .on_end:            upon exit from loop
        .on_before_reload:  before buffer reload is performed.
        .on_after_reload:   after buffer reload is performed.
        .on_step:           upon every iteration of loop entry.
    """
    @typed(IncidenceIdMap=list, MaintainLexemeF=bool)
    def __init__(self, MaintainLexemeF, OnBegin=None, OnEnd=None, 
                 OnBeforeReload=None, OnAfterReload=None):
        self.__prepare_begin_and_end(OnBegin, OnEnd)
        self.__prepare_before_and_after_reload(MaintainLexemeF, OnBeforeReload, OnAfterReload)

    def __prepare_begin_and_end(self, OnBegin, OnEnd):
        """With codecs of dynamic character sizes (UTF8), the pointer to the 
        first letter is stored in 'lexatom_begin_p'. To reset the input 
        pointer 'input_p = lexatom_begin_p' is applied.  
        """
        if not Setup.buffer_codec.variable_character_sizes_f():
            # 1 character == 1 chunk
            # => reset to last character: 'input_p = input_p - 1'
            putback      = [ Op.Decrement(E_R.InputP) ]
            self.on_step = []
        else:
            # 1 character == variable number of chunks
            # => store begin of character in 'lexeme_start_p'
            # => rest to laset character: 'input_p = lexeme_start_p'
            putback      = [ Op.Assign(E_R.InputP, E_R.CharacterBeginP) ]
            self.on_step = [ Op.Assign(E_R.CharacterBeginP, E_R.InputP) ]
        self.on_begin = concatinate(self.on_step, OnBegin)
        self.on_end   = concatinate(on_putback, OnEnd)

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

@typed(ReloadF=bool, LexemeEndCheckF=bool, AfterBeyond=list)
def do(CcFactory, AfterBeyond, LexemeEndCheckF=False, EngineType=None, 
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
    """
    assert EngineType is not None
    # NOT: assert (not EngineType.subject_to_reload()) or ReloadStateExtern is
    # None. This would mean, that the user has to make these kinds of decisions.
    # But, we are easily able to ignore meaningless ReloadStateExtern objects.

    iid_beyond    = dial_db.new_incidence_id()
    iid_beyond_rs = dial_db.new_incidence_id() # beyond with restoring input position
    iid_loop      = dial_db.new_incidence_id() # return to the beginning of the loop
    event_handler = LoopEventHandlers(LexemeMaintainedF, 
                                      OnBegin        = ccfactory.on_begin, 
                                      OnEnd          = ccfactory.on_end,
                                      OnBeforeReload = ccfactory.on_before_reload,
                                      OnAfterReload  = ccfactory.on_after_reload) 

    # (*) StateMachine for Loop and Parallel State Machines
    #
    sm = _get_state_machine(CcFactory, 
                            [sm for sm, t in ParallelSmTerminalPairList], 
                            iid_beyond, iid_beyond_rs, iid_loop)

    sm = Setup.buffer_codec.transform(sm)

    # (*) Analyzer from StateMachine
    #
    door_id_loop, \
    analyzer      = _get_analyzer(sm, EngineType, ReloadStateExtern, event_handler)

    # (*) Terminals for Loop and Parallel State Machines
    #

    terminal_list = _get_terminal_list(CcFactory, event_handler, AfterBeyond, 
                                       LexemeEndCheckF, IidBeyond, DoorIdLoop)

    # (*) Generate Code _______________________________________________________
    txt = _get_source_code(analyzer, ParallelSmTerminalPairList, terminal_list, 
                           CcFactory.requires_reference_p())
    
    return txt, DoorID.incidence(iid_beyond)

def _get_terminal_list(CcFactory, ParallelSmTerminalPairList, 
                       event_handler, AfterBeyond, 
                       LexemeEndCheckF, IidBeyond, DoorIdLoop):

    after_beyond  = event_handler.on_end + AfterBeyond
    terminal_list = _get_loop_terminals(CcFactory, LexemeEndCheckF, after_beyond, 
                                        iid_beyond, door_id_loop)
    terminal_list.extend(
        terminal for sm, terminal in ParallelSmTerminalPairList
    )
    terminal_list.append(
        _get_terminal_beyond(after_beyond, IidBeyond)
    )

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

def _get_loop_terminals(CcFactory, LexemeEndCheckF, AfterBeyond, 
                        IidBeyond, DoorIdLoop):
    """Characters are grouped into sets with the same counting action. This
    function generates terminals for each particular counting action. The
    function 'get_appendix()' in order to add further commands to each 
    terminal.

    RETURNS: List of 'Terminal' objects.
    """
    def get_appendix_with_lexeme_end_check(ccfactory, CC_Type):
        """       .----------.        ,----------.   no
              --->| Count Op |-------< LexemeEnd? >------> Loop
                  '----------'        '----+-----'
                                           | yes
                                     .-------------.
                                     |  Lexeme End |
                                     |  Count Op   |-----> OnLexemeEnd
                                     '-------------'
        """  
        if ccfactory.requires_reference_p() and CC_Type == E_CharacterCountType.COLUMN: 
            return [
                Op.GotoDoorIdIfInputPNotEqualPointer(DoorIdLoop, E_R.LexemeEnd),
                Op.ColumnCountReferencePDeltaAdd(E_R.InputP, ccfactory.get_column_count_per_chunk(), False),
            ] + AfterBeyond
        else:
            return [
                Op.GotoDoorIdIfInputPNotEqualPointer(DoorIdLoop, E_R.LexemeEnd),
            ] + AfterBeyond

    def get_appendix_normal(ccfactory, CC_Type):
        return [ Op.GotoDoorId(DoorIdLoop) ]

    # Choose the function that generates appendix code to terminal code 
    # depending on lexeme end check being accomplished or not.
    if LexemeEndCheckF: get_appendix = get_appendix_with_lexeme_end_check
    else:               get_appendix = get_appendix_normal

    return [ 
        _get_terminal(x, get_appendix) for x in CcFactory.__map 
    ] 

def _get_terminal(CcFactory, X, get_appendix):
    op_list  = X.map_CharacterCountType_to_OpList(CcFactory.get_column_count_per_chunk()) 
    appendix = get_appendix(CcFactory, X.cc_type)
    terminal = Terminal(CodeTerminal(Lng.COMMAND_LIST(chain(op_list, appendix))), 
                        Name="%s" % X.cc_type)
    terminal.set_incidence_id(X.incidence_id)
    return terminal

def _get_terminal_beyond(OnBeyond, BeyondIid):
    """Generate Terminal to be executed upon exit from the 'loop'.
    
       BeyondIid  -- 'Beyond Incidence Id', that is the incidencen id if of
                     the terminal to be generated.
    """
    code_on_beyond = CodeTerminal(Lng.COMMAND_LIST(OnBeyond))
    result = Terminal(code_on_beyond, "<BEYOND>") # Put last considered character back
    result.set_incidence_id(BeyondIid)
    return result

def _get_loop_with_state_machines(LoopTargetMap, SmList):
    """Generates a state machine that loops on 'LoopTargetMap', i.e. executes
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
    L = NumberSet.from_union_of_iterable(
        number_set for number_set in LoopTargetMap
    )
    # Sort State Machines
    LnF, \
    loop_list, \
    no_loop_list = _sort_by_first_character(SmList, L)
    
    # LnF:          Loop lexatoms, that are not first lexatoms.
    # loop_list:    Tuples of (first lexatom set, sm_list) where the first 
    #               lexatom set is completely IN 'L'.
    # no_loop_list: Tuples of (first lexatom set, sm_list) where the first 
    #               lexatom set is completely OUTSIDE 'L'.
    for number_set, incidence_id in LoopTargetMap:
        pure = number_set.intersection(LnF)
        ti = sm.add(sm.init_state_index, pure)
        sm.states[ti].mark_acceptance_id(incidence_id)
        
    def mount_sub_state_machine(sm, LexatomSet, sub_sm, IidOnDropOut):
        combined_sm.get_init_state().set_read_position_store_f()  # 'ir = i'
        combined_sm.fill_gaps(IidOnDropOut)
        ti = sm.add(sm.init_state_index, LexatomSet, 
                    sub_sm.init_state_index)
        sm.absorb(combined_sm)

    for lexatom_set, original_iid, combined_sm in loop_list:
        iid_continue = get_continue_iid(original_iid)
        mount_sub_state_machine(sm, lexatom_set, combined_sm, iid_continue)
        # IidLoopContinue --> Terminal: "i = ir + 1; goto Terminal(lexatom_set);" 

    for lexatom_set, combined_sm in no_loop_list:
        mount_sub_state_machine(sm, lexatom_set, combined_sm, IidLoopExit)
        # IidLoopExit --> Terminal: "goto exit-of-loop;"
    
    return sm

def _sort_by_first_character(SmList, L):
    """RETURNS: [0] L without any first lexatom.
                [1] List of tuples (NSet, CombinedSm) where NSet IN L.
                [2] List of tuples (NSet, CombinedSm) where NSet NOT IN L.

                3x None, in case of error.
    """
    L_without_F = L.clone()
    for sm in SmList:
        trigger_set = sm.cut_first_transition()

        in_L  = trigger_set.intersection(L)
        if in_L:  
            in_list.append((in_L, sm))
            L_without_F.subtract(in_L)

        out_L = trigger_set.difference(L)
        if out_L: 
            in_list.append((out_L, sm))

    return L_without_F, _clean_this(in_list), _clean_this(out_list)

def _clean_this(FirstSmList):
    """Takes a list of tuples (NSet, state machine) where the number sets NSet
    may possibly intersect. If the number sets of two tuples intersect the
    intersection is associated with the list of their state machines.
    
    RETURNS: List of tuples (NSet, state machine list)
     
    where no two number sets in the tuples intersect. The result therefore is
    a mapping:

         Number Set ------> combined state machine buildt from a list of 
                            state machines that trigger on Number set as 
                            first lexatom.
    """
    result = []
    for i, i_entry in enumerate(FirstSmList):
        i_trigger_set, i_sm = candidate
        i_remainder         = i_trigger_set.clone()
        for k, k_entry in enumerate(FirstSmList):
            if k == i: continue
            k_trigger_set, k_sm = candidate
            common = i_trigger_set.intersection(k_trigger_set)
            if common.is_empty(): continue
            result.append((common, [i_sm, k_sm]))
            i_remainder.subtract(common)
        result.append((i_remainder, [i_sm]))

    for i in reversed(range(len(result))):
        i_trigger_set, i_sm_list = result[i]
        for i in range(i):
            k_trigger_set, k_sm_list = result[k]
            if i_trigger_set.is_equal(k_trigger_set):
                result[k].extend(i_sm_list)
                del result[i]

    return [
        (trigger_set, get_combined_state_machine(sm_list))
        for trigger_set, sm_list in result
    ]

def _get_analyzer(sm, EngineType, ReloadStateExtern, event_handler):
    analyzer     = analyzer_generator.do(sm, EngineType, ReloadStateExtern,
                                         OnBeforeReload = copy(event_handler.on_before_reload), 
                                         OnAfterReload  = copy(event_handler.on_after_reload))

    door_id_loop = _prepare_entry_and_reentry(analyzer, 
                                              event_handler.on_begin, 
                                              event_handler.on_step) 

    return analyzer, door_id_loop

def _prepare_entry_and_reentry(analyzer, OnBegin, OnStep):
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
                                                  OnBegin)

    # OnReEntry
    tid_reentry = entry.enter_OpList(init_state_index, index.get(), 
                                     OpList.from_iterable(OnStep))
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
