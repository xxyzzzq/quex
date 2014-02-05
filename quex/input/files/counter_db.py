from   quex.engine.state_machine.core               import StateMachine
from   quex.engine.state_machine.transformation     import homogeneous_chunk_n_per_character
import quex.engine.state_machine.transformation     as     transformation
import quex.engine.state_machine.index              as     index
import quex.engine.analyzer.engine_supply_factory   as     engine
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

