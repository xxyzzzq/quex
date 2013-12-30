from   quex.engine.state_machine.core               import StateMachine
from   quex.engine.state_machine.transformation     import homogeneous_chunk_n_per_character
import quex.engine.state_machine.transformation     as     transformation
import quex.engine.state_machine.index              as     index
import quex.engine.analyzer.engine_supply_factory   as     engine
from   quex.engine.analyzer.state.drop_out          import DropOutGotoDoorId
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
                                                           InputPToLexemeStartP, \
                                                           GotoDoorIdIfInputPLexemeEnd, \
                                                           ColumnCountAdd, \
                                                           ColumnCountGridAddWithReferenceP, \
                                                           LineCountAddWithReferenceP, \
                                                           ColumnCountReferencePSet, \
                                                           ColumnCountReferencePDeltaAdd
from   quex.engine.generator.languages.variable_db  import variable_db
from   quex.engine.generator.code.core              import CodeTerminal
from   quex.engine.interval_handling                import NumberSet
from   quex.blackboard import setup as Setup, \
                              Lng,            \
                              E_IncidenceIDs, \
                              E_StateIndices

from   collections import namedtuple

CountCmdInfo = namedtuple("CountCmdInfo_tuple", ("trigger_set", "command_list"))

class CounterDB:
    # 'CounterDB' maps from counts to the character set that is involved.
    __slots__ = ("special", "grid", "newline")

    def __init__(self, LCC_Setup):
        """Generate a counter db from a line column counter setup."""
        assert LCC_Setup is not None
        def adapt(db):
            return dict((count, parameter.get()) for count, parameter in db.iteritems())
        self.special = adapt(LCC_Setup.space_db)
        self.grid    = adapt(LCC_Setup.grid_db)
        self.newline = adapt(LCC_Setup.newline_db)

    def get_column_number_per_chunk(self, CharacterSet):
        """Considers the counter database which tells what character causes
        what increment in line and column numbers. However, only those characters
        are considered which appear in the CharacterSet. 

        'CharacterSet' is None: All characters considered.

        If the special character handling column number increment always
        add the same value the return value is not None. Else, it is.

        RETURNS: None -- If there is no distinct column increment 
                 >= 0 -- The increment of column number for every character
                         from CharacterSet.
        """
        result     = None
        number_set = None
        for delta, character_set in self.special.iteritems():
            if CharacterSet is None or character_set.has_intersection(CharacterSet):
                if result is None: result = delta; number_set = character_set
                else:              return None

        if Setup.variable_character_sizes_f():
            result = homogeneous_chunk_n_per_character(number_set, 
                                                       Setup.buffer_codec_transformation_info)
        return result

    def get_map(self, X, Y, Z):
        assert False, "call get_count_command_map"

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

        return cm, column_count_per_chunk

class CounterCoderData:
    def __init__(self, CounterDb, CharacterSet, AfterExitDoorId=None, IteratorName=None, LexemeF=True):
        assert not CharacterSet.is_empty()
        assert isinstance(CharacterSet, NumberSet)
        assert isinstance(CounterDb, CounterDB)
        

        if IteratorName is None:
            IteratorName = Lng.INPUT_P()

        # If 'column_count_per_chunk' is not None, then reference positions may 
        # be used for counting (i.e. "column_n += (input_p - reference_p) * C").
        # This avoids 'column_n += C' at every single step.
        self.column_count_per_chunk = CounterDb.get_column_number_per_chunk(CharacterSet)
        self.iterator_name          = IteratorName

        # count_command_map:
        #
        #               map:  CLI -->  (NumberSet, CommandList)
        #
        # where the CommandList does the required column/line number counting 
        # for the given NumberSet. The tuple (NumberSet, CommandList) is
        # implemented as CountCmdInfo.
        self.count_command_map = self.__count_command_map_prepare(CounterDb, 
                                                                  CharacterSet) 

        self.on_entry, \
        self.on_exit  = self.__on_entry_on_exit_prepare(AfterExitDoorId)

        self.on_before_reload, \
        self.on_after_reload   = self.__on_before_after_reload_prepare(LexemeF)

    def get_analyzer(self, EngineType, GlobalReloadState=None, TargetState=None, CheckLexemeEndF=False):
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
               or (GlobalReloadState is not None and isinstance(GlobalReloadState, ReloadState))
        assert    GlobalReloadState is None \
               or EngineType.requires_buffer_limit_code_for_reload() 
        assert TargetState is None       or isinstance(TargetState, AnalyzerState)
        

        sm  = self.get_counting_state_machine(self.count_command_map) 
        transformation.do_state_machine(sm)

        # The 'bending' of CLI-s to the init state must wait until the entry actions
        # have been determined. Only this way, it is safe to assume that the different
        # counting actions are implemented at a seperate entry.
        analyzer = Analyzer(sm, EngineType, GlobalReloadState=GlobalReloadState)
        start    = analyzer.init_state()
        if TargetState is not None: finish = TargetState
        else:                       finish = start

        start.entry.enter_before(start.index, E_StateIndices.NONE, self.on_entry)
        start.entry.categorize(start.index)   # Determine DoorID-s -- those specified now, won't change later.

        exit_incidence_id = index.get_state_machine_id() 
        exit_door_id      = DoorID.incidence(exit_incidence_id)
        exit_terminal     = Terminal(exit_incidence_id, 
                                     CodeTerminal([ Lng.COMMAND(cmd) for cmd in self.on_exit]))

        if CheckLexemeEndF:
            check_lexeme_end = CommandList(GotoDoorIdIfInputPLexemeEnd(exit_door_id))

        trigger_id_db = {}
        # Inject the counting commands into the states that represent it
        for cli, info in self.count_command_map.iteritems():
            # States entering state 'cli' where command_list is to be performed:
            for state_index in analyzer.from_db[cli]:
                command_list = info.command_list
                command_list = command_list.concatinate(CommandList(InputPIncrement()))
                if CheckLexemeEndF: command_list = check_lexeme_end.concatinate(command_list)
                else:               command_list = info.command_list
                # Each time the same 'to-from' transition is entered a new 
                # trigger id is assigned, to make the transition unique.
                transition_id = finish.entry.enter(finish.index, state_index, TransitionAction(command_list))
                trigger_id_db[(cli, state_index)] = transition_id
            analyzer.remove_state(cli)

        def door_id_provider(analyzer, ToStateIndex, FromStateIndex):
            """Provides a DoorID for specicial transitions mentioned in the 'trigger_id_db'.
            If there is an entry in 'trigger_id_db' for ('ToStateIndex', 'FromStateIndex')
            then a corresponding DoorID is extracted from the transition_id's 
            'state_index'. If not, then 'None' is returned. This means, that 
            normal 'DoorID' mapping is to be applied (see 'relate_to_DoorIDs').
            """
            transition_id = trigger_id_db.get((ToStateIndex, FromStateIndex))
            if transition_id is None: return None

            return analyzer.state_db[transition_id.target_state_index].entry.get(transition_id).door_id

        # Setup DoorIDs in entries and transition maps
        analyzer.prepare_DoorIDs(door_id_provider)

        # (The following is a null operation, if the analyzer.engine_type does not
        #  require reload preparation.)
        for state in analyzer.state_db.itervalues():
            state.prepare_for_reload(analyzer, self.on_before_reload, self.on_after_reload)

        # (*) Transition Map __________________________________________________
        #
        for state in analyzer.state_db.itervalues():
            state.transition_map.fill_gaps(exit_door_id)
            state.drop_out = DropOutGotoDoorId(exit_door_id)

        return analyzer, exit_terminal

    def __on_entry_on_exit_prepare(self, AfterExitDoorId):
        """Actions to be performed at entry into the counting code fragment and 
        when exiting.

        RETURNS:

            [0], [1]    Commands to be executed [0] upon entry, i.e. when the 
                        counting starts, and [1] upon counting is terminated.

            None, None  If there is no need to do anthing upon entry or exit.
        """
        on_entry = CommandList(InputPToLexemeStartP())

        if self.column_count_per_chunk is None:
            if OnExitDoorId is not None: on_exit = CommandList(GotoDoorId(AfterExitDoorId))
            else:                        on_exit = None
            return on_entry, on_exit
        else:
            on_entry    = on_entry.concatinate(CommandList(ColumnCountReferencePSet(self.iterator_name)))
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
        if self.column_count_per_chunk is None:
            return None, None
        else:
            on_before_reload = ColumnCountReferencePDeltaAdd(self.iterator_name, 
                                                             self.column_count_per_chunk)
            on_after_reload  = ColumnCountReferencePSet(self.iterator_name)

        on_before_reload = CommandList(on_before_reload)
        on_after_reload  = CommandList(on_after_reload)

        if not LexemeF:
            # The lexeme start pointer defines the lower border of memory to be 
            # kept when reloading. Setting it to the input pointer allows for 
            # the whole buffer to be reloaded. THIS CAN ONLY BE DONE IF THE 
            # LEXEME IS NOT IMPORTANT!
            on_before_reload = on_before_reload.concatinate(LexemeStartToReferenceP(self.iterator_name))

        return on_before_reload, on_after_reload

    def __count_command_map_prepare(self, CounterDb, CharacterSet):
        """Returns a list of NumberSet objects where for each X of the list it holds:

             (i)  X is subset of CharacterSet
                   
             (ii) It is related to a different counter action than Y,
                  for each other object Y in the list.

           RETURNS: 

                        map:  CLI -->  (NumberSet, CommandList)

           NOTE: A 'CLI' is UNIQUE also as a state index. That is, it can be 
                 used a a 'pseudo state' which represents the CommandList
                 without extra effort.

           where each entry means: "If an input character lies in NumberSet
           then the counting action given by CommandList has to be executed.
           The CommandList is distinctly associated with a CLI, a command
           list index.
        """
        def pruned_iteritems(Db, CharacterSet):
            for value, character_set in Db.iteritems():
                if CharacterSet is None: pruned = character_set
                else:                    pruned = character_set.intersection(CharacterSet)
                if pruned.is_empty():    continue
                yield value, pruned

        def on_special(Delta):
            if self.column_count_per_chunk is None:  return ColumnCountAdd(Delta)
            else:                                    return None

        def on_grid(GridStepN):
            if self.column_count_per_chunk is None:  return ColumnCountGridAdd(GridStepN)
            else:                                    return ColumnCountGridAddWithReferenceP(GridStepN, 
                                                                                             self.iterator_name,
                                                                                             self.column_count_per_chunk)

        def on_newline(Delta):
            if self.column_count_per_chunk is None: return LineCountAdd(Delta)
            else:                                   return LineCountAddWithReferenceP(Delta, 
                                                                                      self.iterator_name, 
                                                                                      self.column_count_per_chunk)

        result = {}
        for delta, character_set in pruned_iteritems(CounterDb.special, CharacterSet):
            cmd = on_special(delta)
            if cmd is None: cl = CommandList()
            else:           cl = CommandList(cmd)
            result[index.get()] = CountCmdInfo(character_set, cl)

        result.update(
            (index.get(), CountCmdInfo(character_set, CommandList(on_grid(grid_step_n))))
            for grid_step_n, character_set in pruned_iteritems(CounterDb.grid, CharacterSet)
        )
        result.update(
            (index.get(), CountCmdInfo(character_set, CommandList(on_newline(delta))))
            for delta, character_set in pruned_iteritems(CounterDb.newline, CharacterSet)
        )

        return result

    def get_counting_state_machine(self, CountCommandMap):
        sm = StateMachine()
        for cli, count_info in CountCommandMap.iteritems():
            assert isinstance(count_info, CountCmdInfo)
            sm.add_transition(sm.init_state_index, count_info.trigger_set, cli)
        return sm

