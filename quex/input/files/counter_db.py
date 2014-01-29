from   quex.engine.state_machine.core               import StateMachine
from   quex.engine.state_machine.transformation     import homogeneous_chunk_n_per_character
import quex.engine.state_machine.transformation     as     transformation
import quex.engine.state_machine.index              as     index
import quex.engine.analyzer.engine_supply_factory   as     engine
from   quex.engine.analyzer.state.drop_out          import DropOutUnreachable
from   quex.engine.analyzer.terminal.core           import Terminal
from   quex.engine.analyzer.core                    import Analyzer
from   quex.engine.analyzer.state.core              import ReloadState, AnalyzerState
from   quex.engine.analyzer.state.entry_action      import TransitionAction
from   quex.engine.analyzer.door_id_address_label   import dial_db, DoorID
from   quex.engine.analyzer.state.entry_action      import TransitionID
from   quex.engine.analyzer.transition_map          import TransitionMap
from   quex.engine.analyzer.commands                import CommandList, \
                                                           GotoDoorId, \
                                                           InputPIncrement, \
                                                           InputPDereference, \
                                                           InputPDecrement, \
                                                           InputPToLexemeStartP, \
                                                           GotoDoorIdIfInputPEqualPointer, \
                                                           ColumnCountAdd, \
                                                           ColumnCountGridAdd, \
                                                           ColumnCountGridAddWithReferenceP, \
                                                           LexemeStartToReferenceP, \
                                                           LineCountAdd, \
                                                           LineCountAddWithReferenceP, \
                                                           ColumnCountReferencePSet, \
                                                           ColumnCountReferencePDeltaAdd
from   quex.engine.generator.languages.variable_db  import variable_db
from   quex.engine.generator.code.core              import CodeTerminal
from   quex.engine.interval_handling                import NumberSet
from   quex.engine.tools                            import typed, \
                                                           print_callstack
from   quex.blackboard import setup as Setup, \
                              Lng,            \
                              E_IncidenceIDs, \
                              E_StateIndices, \
                              E_CharacterCountType

from   collections import namedtuple

CountCmdInfo = namedtuple("CountCmdInfo_tuple", ("trigger_set", "command_list", "cc_type"))
# cc_type = (E_CharacterCountType)

    def get_count_command_map(self, CharacterSet = None):
        """Provide a map which associates intervals with line/column counting 
        actions as well as appropriate increments of the input pointer.

           map: 
                            interval --> CommandList

        The mapping is provided in the form of a list, where the intervals in
        the list are NOT NECESSARILY ADJACENT!
        sorted pairs of (interval, action).

        ARGUMENTS:
                  CharacterSet -- Considered set of characters.

        The intervals of the result list will constitute of the intervals 
        of the given CharacterSet. If the CharacterSet is None then the
        whole range of characters is considered.

        RETURNS:  [0] list( (interval, CommandList) )
                  [1] ColumnNPerChunk

        Where the ColumnNPerChunk is not None, if and only if the column number
        increment can be computed by "(input_p - reference_p) * C". That is
        all column related characters have the same horizontal size.

        ___________________________________________________________________________
        REFERENCE POINTER COUNTING

        Counting by means of a reference pointer may spare intermediate column
        number increments. Instead, one only needs to do

                column_n += (input_p - reference_p) * C

        as soon as a 'non-column character' occurs. Consider the figure below:

              ---- memory address --->
                                             later
                                             iterator
                                                 |
              | | | | | | |*| | | | | | | | | | | | | | | | | | | | | |
                           |
                      reference_p 
                      = iterator

        The '*' stands for a 'grid' or a 'newline' character.  If such a character
        appears, the 'reference_p' is set to the current 'iterator'.  As long as no
        such character appears, the term to be added is proportional to 'iterator -
        reference_p'.  The counter implementation profits from this.  It does not
        increment the 'column_n' as long as only 'normal' characters appear.  It
        only adds the delta multiplied with a constant.
        ___________________________________________________________________________
        """
        assert CharacterSet is None or isinstance(CharacterSet, NumberSet)
        

        column_count_per_chunk = self.get_column_number_per_chunk(CharacterSet)
        counter_dictionary     = self.get_counter_dictionary(CharacterSet, column_count_per_chunk)

        cm = TransitionMap()
        for number_set, command_list in counter_dictionary:
            assert CharacterSet is None or CharacterSet.is_superset(number_set)
            cm.extend((interval, command_list) for interval in number_set.get_intervals())

        if column_count_per_chunk is not None:
            on_before_reload = [
                ColumnCountReferencePDeltaAdd(self.iterator_name, 
                                              self.column_count_per_chunk)
            ]
            on_after_reload = [
                ColumnCountReferencePSet(self.iterator_name)
            ]


        return cm, column_count_per_chunk, on_before_reload, on_after_reload


def get_loop_setup():
    def __init__(self, CounterDb, CharacterSet, ExitDoorId=None, IteratorName=None, LexemeF=True):
        assert not CharacterSet.is_empty()
        assert isinstance(CharacterSet, NumberSet)
        assert isinstance(CounterDb, CounterDB)
        
        if IteratorName is None:
            IteratorName = Lng.INPUT_P()

        # If 'column_count_per_chunk' is not None, then reference positions may 
        # be used for counting (i.e. "column_n += (input_p - reference_p) * C").
        # This avoids 'column_n += C' at every single step.
        self.iterator_name          = IteratorName

        # count_command_map:
        #
        #               map:  CLIID -->  (NumberSet, CommandList)
        #
        # where the CommandList does the required column/line number counting 
        # for the given NumberSet. The tuple (NumberSet, CommandList) is
        # implemented as CountCmdInfo.
        self.column_count_per_chunk, \
        self.count_command_map       = CounterDb.get_count_command_map(CharacterSet) 

        on_entry         = []
        on_reentry       = []
        on_inconsiderate = []
        on_exit          = []
        on_before_reload = []
        on_after_reload  = []

        if self.column_count_per_chunk is not None:
            on_entry.append(ColumnCountReferencePSet(self.iterator_name))
            on_exit.append(ColumnCountReferencePDeltaAdd(self.iterator_name, 
                                                         self.column_count_per_chunk))
            on_before_reload.append(ColumnCountReferencePDeltaAdd(self.iterator_name, 
                                                                  self.column_count_per_chunk))
            on_after_reload.append(ColumnCountReferencePSet(self.iterator_name))
            door_id_on_lexeme_end = {
                E_CharacterCountType.CHARACTER: door_id_before_exit, # column += C*(input_p-reference_p)
                E_CharacterCountType.LINE:      door_id_exit,
                E_CharacterCountType.GRID:      door_id_exit,
            }
            variable_db.require("reference_p")

        if not Setup.variable_character_sizes_f():
            # (1) Mark begin of letter
            #     on_entry:    NOTHING TO BE DONE
            #     on_re_entry: NOTHING TO BE DONE
            # (2) Reset begin of letter
            on_inconsiderate.append(InputPDecrement()) 

            # (3) Allow the maximum of bytes to be loaded.
            #     LexemeStartP = InputP => The whole buffer is reloaded! 
            #     THIS CAN ONLY BE DONE IF THE LEXEME IS NOT IMPORTANT!
            on_before_reload.append(InputPToLexemeStartP())
        else:
            assert IteratorName == Lng.INPUT_P()
            # (1) Mark begin of letter
            on_entry.append(LexemeStartToReferenceP(self.iterator_name))
            on_reentry.append(LexemeStartToReferenceP(self.iterator_name))
            # (2) Reset begin of letter
            on_inconsiderate.append(InputPToLexemeStartP())

        on_inconsiderate.append(GotoDoorId(ExitDoorId))
        on_reentry.append(InputPDereference())
        on_exit.append(GotoDoorId(ExitDoorId))

    @typed(GlobalReloadState = (None, ReloadState),
           TargetState       = (None, AnalyzerState))
    def get_analyzer(self, EngineType, GlobalReloadState=None, CheckLexemeEndF=False):
        """
        GlobalReloadState = None --> no Reload
        TargetState = None       --> loop.

        The possibility of a dynamic character size codec forces to transform
        the single state into a state machine: 
        
                                        .----.    .---.
                                .-> ... | 11 |-->-| 1 |  line_n += 1;
                               +--> ... '----'    '---'   
                              +---> ... | 21 |-->--'|
                             +----> ... '----'      |
                    .------./           | 31 |-->---' 
                    | init |------> ... '----'                                     
                    '------'+-----> ...       
                             '----> ... 
                                     
        State '1' represents a counting action.  After the transformation is
        done, the structure can be transformed into a state machine where the
        transitions to '1' are bend into transitions to 'init'. It enters the
        'init' state at a door that inhibits the corresponding counting actions.
        
                        .-----------------------------------.
                        |                       .----.      |
                  .-(Door)------.       .-> ... | 11 |-->---| 
                  | line_n += 1 |      +--> ... '----'      |
                  '-------------'     +---> ... | 21 |-->---|
                        |            +----> ... '----'      |
                        |   .------./           | 31 |-->---' 
                        '-->| init |------> ... '----'                                     
                            '------'+-----> ...       
                                     '----> ... 
        """                                      
        assert    not EngineType.requires_buffer_limit_code_for_reload() \
               or GlobalReloadState is not None 
        assert    GlobalReloadState is None \
               or EngineType.requires_buffer_limit_code_for_reload() 
        

        sm,               \
        iid_inconsiderate = self.__get_counting_state_machine(self.count_command_map) 

        # The 'bending' of CLIID-s to the init state must wait until the entry actions
        # have been determined. Only this way, it is safe to assume that the different
        # counting actions are implemented at a seperate entry.
        analyzer      = Analyzer(sm, EngineType, GlobalReloadState=GlobalReloadState)
        door_id_loop  = self.setup_loop_anchor(analyzer)

        terminal_list = self.get_terminal_list(iid_inconsiderate, 
                                               door_id_loop,
                                               CheckLexemeEndF)

        # Setup DoorIDs in entries and transition maps
        analyzer.prepare_DoorIDs()

        # (The following is a null operation, if the analyzer.engine_type does not
        #  require reload preparation.)
        for state in analyzer.state_db.itervalues():
            state.prepare_for_reload(analyzer, self.on_before_reload, self.on_after_reload)

        # (*) All transitions are captured with 'inconsiderate'. No failure possible!
        #
        analyzer.init_state().drop_out = DropOutUnreachable()

        return analyzer, terminal_list

    def setup_loop_anchor(self, analyzer):
        """Sets up the init state of the analyzer so that it can be gotoed
        in a loop.

        RETURNS: DoorID which should be targetted by as re-entry into the loop.
        """
        anchor = analyzer.init_state()

        # -- Actions before the loop start
        anchor.entry.enter_before(anchor.index, E_StateIndices.NONE, 
                                  self.on_entry)

        # -- Actions that happen at every loop re-entry
        on_re_entry = []

        loop_transition_id = anchor.entry.enter(anchor.index, anchor.index, 
                                                TransitionAction(on_re_entry))

        # Determine DoorID-s -- those specified now, won't change later.
        anchor.entry.categorize(anchor.index)   

        return anchor.entry.get(loop_transition_id).door_id

    def cmd_check_lexeme_end(cl, CcType):
        if self.door_id_on_lexeme_end_db is None: return

        door_id = door_id_on_lexeme_end_db[CcType]
        cl.append(
            GotoDoorIdIfInputPEqualPointer(door_id, "LexemeEnd")
        )

    def get_terminal_list(self, IncidenceIdInconsiderate, 
                          DoorIdLoop, CheckLexemeEndF):
        incidence_id_exit = dial_db.new_incidence_id()
        door_id_exit      = DoorID.incidence(incidence_id_exit)
        goto_loop_anchor  = GotoDoorId(DoorIdLoop)

        def get_terminal(IncidenceId, CmdList, Name):
            terminal = Terminal(CodeTerminal([Lng.COMMAND(cmd) for cmd in CmdList]),
                                Name=Name)
            terminal.set_incidence_id(IncidenceId)
            return terminal

        def get_count_terminal(cliid, CcType):
            """SpecialF = is related character set related to characters and 
                          not to newline or grid?
            """
            cl = [
                cmd for cmd in self.count_command_map[cliid].command_list 
            ]
            self.cmd_check_lexeme_end(cl, CcType)
            cl.append(goto_loop_anchor)

            name = self.count_command_map[cliid].trigger_set.get_string(Option="hex")
            return get_terminal(cliid, cl, name)

        result = []
        if IncidenceIdInconsiderate is not None:
            result.append(
                get_terminal(IncidenceIdInconsiderate, on_inconsiderate, 
                             "<Inconsiderate>")
            )

        result.append(
            get_terminal(incidence_id_exit, self.on_exit, "<Exit>")
        )

        result.extend(
            get_count_terminal(cliid, info.cc_type)
            for cliid, info in self.count_command_map.iteritems()
        )

        return result

    def __on_entry_on_exit_prepare(self, AfterExitDoorId):
        """Actions to be performed at entry into the counting code fragment and 
        when exiting.

        RETURNS:

            [0], [1]    Commands to be executed [0] upon entry, i.e. when the 
                        counting starts, and [1] upon counting is terminated.

            None, None  If there is no need to do anthing upon entry or exit.
        """
        if Setup.variable_character_sizes_f():
            on_entry = [ ColumnCountReferencePSet(self.iterator_name) ]
        else:
            on_entry = []

        if self.column_count_per_chunk is None:
            if AfterExitDoorId is not None: on_exit = CommandList(GotoDoorId(AfterExitDoorId))
            else:                           on_exit = None
            return on_entry, on_exit
        else:
            on_entry    = CommandList(ColumnCountReferencePSet(self.iterator_name))
            on_exit_cmd = ColumnCountReferencePDeltaAdd(self.iterator_name, 
                                                        self.column_count_per_chunk)
            if AfterExitDoorId is not None: 
                on_exit = CommandList(on_exit_cmd, GotoDoorId(AfterExitDoorId))
            else:
                on_exit = CommandList(on_exit_cmd)
            return on_entry, on_exit

    def __on_before_after_reload_prepare(self, LexemeF):
        """Actions to be performed before and after reload.

        RETURNS: 
        
            [0], [1]    Commands to be executed before and after buffer reload. 
                        This basically adapts the reference pointer for column 
                        number counting. 
                     
            None, None  If column number counting cannot profit from the a fixed
                        ColumnCountPerChunk (applying "column += (p-reference_p)*c")

        The LexemeF tells whether the current lexeme is important, i.e. treated
        by some handler. If not, the how buffer may be reloaded by setting the 
        lexeme start pointer to the input pointer.
        """
        on_before_reload = []
        on_after_reload  = []
        if self.column_count_per_chunk is not None:
            on_before_reload.append(
                ColumnCountReferencePDeltaAdd(self.iterator_name, 
                                              self.column_count_per_chunk)
            )
            on_after_reload.append(
                ColumnCountReferencePSet(self.iterator_name)
            )

        if not LexemeF and not Setup.variable_character_sizes_f():
            # The lexeme start pointer defines the lower border of memory to be 
            # kept when reloading. Setting it to the input pointer allows for 
            # the whole buffer to be reloaded. THIS CAN ONLY BE DONE IF THE 
            # LEXEME IS NOT IMPORTANT!
            on_before_reload.append(
                LexemeStartToReferenceP(self.iterator_name)
            )

        return CommandList.from_iterable(on_before_reload), \
               CommandList.from_iterable(on_after_reload)

    def __get_counting_state_machine(self, CountCommandMap):
        """A CountCommandMap tells about character sets and the count action
        which they require. That is, 

                    CountCommandMap: 'cliid' --> 'count_info'

        where 'cliid' is a unique index which idenfies the required count action.
        The 'count_info' object contains the character set which is concerned
        (and the count action, but this is irrelevant here).

        Based on the 'CountCommandMap' a simple state machine is created that
        has a state reqpresenting each count action. (A plain transition map
        would not suffice in case that dynamic character sizes are involved).

        Then, this state machine is transformed according to the required 
        buffer codec (see 'Setup.buffer_codec_transformation_info').


        RETURN: [0] State machine that associates counting patterns with 
                    acceptance ids.

                [1] A mapping from the 'cliid' of the counting action to the
                    index of the state which is entered when the correspondent
                    character is detected.

        """
        # -- Generate for each character set that has the same counting action a
        #    transition in the state machine. 
        # -- Associate the target state with an 'AcceptanceID'.
        #    (AcceptanceID-s survive the transformation and NFA-to-DFA)
        # -- Store the relation between the counting action (given by the 'cliid')
        #    and the acceptance id.
        def add(sm, IncidenceId, TriggerSet):
            state_index   = sm.add_transition(sm.init_state_index, TriggerSet,
                                              AcceptanceF=True)
            sm.states[state_index].mark_self_as_origin(IncidenceId, state_index)

        sm          = StateMachine()
        covered_set = NumberSet()
        for cliid, count_info in CountCommandMap.iteritems():
            # 'cliid' = unique command list incidence id.
            add(sm, cliid, count_info.trigger_set)
            covered_set.unite_with(count_info.trigger_set)

        iid_inconsiderate = dial_db.new_incidence_id()
        if not covered_set.is_all():
            add(sm, iid_inconsiderate, covered_set.inverse()) 

        # Perform possible a character set transformation, if the buffer codec
        # is not unicode.
        dummy, sm = transformation.do_state_machine(sm)

        # Any state which is not acceptance will be 'Accept Exit'.
        # EXCEPTION: Init state -- this state cannot accept else it would be
        #            an 'accept anything' which causes trouble.
        for state_index, state in sm.states.iteritems():
            if state.is_acceptance(): continue
            state.set_acceptance()
            state.mark_self_as_origin(iid_inconsiderate, state_index)

        return sm, iid_inconsiderate

