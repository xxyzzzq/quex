from   quex.engine.analyzer.state.core         import AnalyzerState
from   quex.engine.analyzer.state.entry_action import DoorID, \
                                                      SetPathIterator
from   quex.engine.analyzer.mega_state.core    import MegaState_Entry, \
                                                      MegaState_DropOut
from   quex.engine.analyzer.transition_map     import TransitionMap       
import quex.engine.state_machine.index         as     index

from   quex.blackboard import E_StateIndices

from   itertools   import ifilter
from   collections import namedtuple

from   copy import deepcopy

class PathWalkerState_Entry(MegaState_Entry):
    """________________________________________________________________________

    Entry into a PathWalkerState. As the base's base class 'Entry' it holds
    information about what CommandList is to be executed upon entry from a
    particular source state.
    
    PRELIMINARY: Documentation of class 'MegaState_Entry'.

    A PathWalkerState is a MegaState, meaning it implements multiple states at
    once. Entries into the PathWalkerState must have an action that sets the
    'state key' for the state that it is about to represent. The 'state key'
    of a PathWalkerState is the offset of the path iterator from the character
    path's base.

    During analysis, only the '.action_db' is of interest. There the 
    'SetPathIterator' command is to each TransitionAction's CommandList. The
    command lists 'equal' and 'not-equal' relationships remain the same, since
    the 'SetPathIterator' for all TransitionAction of a given state. Thus,
    the DoorID objects can act as unique identifiers of command lists.
    ___________________________________________________________________________
    """
    def __init__(self, TheEntry):
        MegaState_Entry.__init__(self)

        self.action_db_update(TheEntry, 0)
        self.previous_on_path_CommandList = None

    def action_db_update(self, TheEntry, Offset, PreviousStep=None):
        """Include 'TheState.entry.action_db' into this state. That means,
        that any mappings:
           
             transition (StateIndex, FromStateIndex) --> CommandList 

        is ABSORBED AS THEY ARE from  'TheEntry.action_db'.  Additionally, any
        command list must contain the 'SetPathIterator' command that sets the
        state key for represented state. At each (external) entry into the path
        walker state the 'state_key' must be set, so that it can mimik the
        represented state.
        """
        if PreviousStep is not None:
            OnPathDoorId     = PreviousStep.door_id
            OnPathStateIndex = PreviousStep.state_index
        else:
            OnPathDoorId     = None
            OnPathStateIndex = None

        for transition_id, action in TheEntry.action_db.iteritems():
            clone = action.clone()
            print "#tid:", transition_id, OnPathStateIndex
            if transition_id.action_id.source_state_index != OnPathStateIndex:
                # Create new 'SetPathIterator' for the state which is represented
                clone.command_list.misc.add(SetPathIterator(Offset=Offset))
            else:
                # Entry along path.
                #
                #   => The state_key does not have to be set at entry. It 
                #      results directly from the iterator position.
                #   => It makes sense to have a dedicated DoorID which is going
                #      to be set by 'action_db.categorize()'. The translation
                #      is then documented in '.transition_reassignment_db'.
                self.transition_reassignment_candidate_list.append((OnPathStateIndex, transition_id))
                # clone.door_id = None

            self.action_db[transition_id] = clone

        print "#REASCL:", self.transition_reassignment_candidate_list
        self.previous_on_path_CommandList = TheEntry.action_db.get_command_list_by_door_id(OnPathDoorId)
        return

    def adapt_SetStateKey(self, PathWalkerIndex, PathID):
        """Ensure that any 'SetPathIterator' contains the right references
        to the pathwalker and path id.
        """
        for action in self.action_db.itervalues():
            found_f = False
            for command in action.command_list:
                if not isinstance(command, SetPathIterator): continue

                assert not found_f # Double check that is  not more than one 
                #                  # such command per command_list.
                found_f = True
                command.set_path_walker_id(PathWalkerIndex)
                command.set_path_id(PathID)
                # There shall not be more then one 'SetPathIterator' command 
                # for one transition.

        return

class CharacterPathStep(namedtuple("CharacterPathStep_tuple", ("state_index", "trigger", "door_id"))):
    """See also class 'CharacterPath' where the role of the CharacterPathStep
       is explained further.

       The CharacterPathStep contains information about one single step
       along the CharacterPath. It tells from what state the step starts

                           Start    Trigger      DoorID
                           State    Character    
                            .---.                      .---.
                        ----| 1 |----- 'g' ----->[(3,4)] 3 |---
                            '---'                      '---'

       So, the step from state 1 to 3 would be described by:

                .state_index = 1       # Index of the state where the step starts
                .trigger     = 'g'     # The triggering character
                .door_id     = (3,4)   # The DoorID in the target state.
   
       Note, that this setup fits well the case where the path is described by a
       list of CharacterPathStep-s. Then, the last state is not element of the 
       list which corresponds to the fact that it is not element of the path.
    """
    def __new__(self, StateIndex, TransitionChar, TargetDoorId):
        assert isinstance(StateIndex, long)
        assert isinstance(TransitionChar, (int, long))
        assert isinstance(TargetDoorId, DoorID)      
        return super(CharacterPathStep, self).__new__(self, StateIndex, TransitionChar, TargetDoorId)

    def __repr__(self):
        return ".state_index = %s;\n" \
               ".trigger     = '%s';\n" \
               ".door_id     = %s;\n"  \
               % (self.state_index, self.trigger, self.door_id)

class CharacterPath(object):
    """________________________________________________________________________

    Represents identified path in the state machine such as:


       ( 1 )--- 'a' -->( 2 )--- 'b' -->( 3 )--- 'c' -->( 4 )--- 'd' -->( 5 )

    where the remaining transitions in each state match (except for the last).
    A CharacterPath contains a '.sequence' of CharacterPathSteps, e.g.
  
      .sequence:

       .----------------. .----------------. .----------------. .----------------. 
       |.trigger = 'a'  |-|.trigger = 'b'  |-|.trigger = 'c'  |-|.trigger = 'd'  |
       |.door_id = (2,1)| |.door_id = (3,3)| |.door_id = (4,2)| |.door_id = (5,1)|
       '----------------' '----------------' '----------------' '----------------' 

       where '.door_id = (x,y)' stands for a door in state 'x' with some index 'y'. 
   
     .terminal:

       The AnalyzerState which is entered from the last element of the path via
       a single character transition. It is not implemented by the CharacterPath.
       As soon as another state is appended, it becomes part of the path and the 
       newly appended becomes the terminal.

     .implemented_state_index_list:
     
      A list of state indices which the path can cover. This does not include
      the last state triggered by the terminal element of '.sequence'. As in the
      example, the state '5' is EXTERNAL and not part of the path itself.

     .uniform_door_id

      which is 'None' if the entries along the path are all uniform. 
      
      This does not include the entry to the terminal state. This entry is
      implemented by the terminal state itself, not by this path.

     .entry

      entry information foreach entry into the state. In particular it contains
      the '.action_db' which contains the CommandLists according to each
      DoorID which is relevant for the path. 

      The 'entry.action_db' does not contain information about entry into the
      terminal state, because it is not implemented by the path.

     .drop_out

      maps: state_index --> DropOut object
    ___________________________________________________________________________
    EXPLANATION:

    The steps of path generation are the following:

    (1) The function '__find()' finds an initial transition of a state A to a 
        state B via a single character C. Let (b,a,C) be the DoorID where state
        B is entered from A via C.

    (2) In function '__find_continuation()' a CharacterPath is created which

        -- where the .sequence contains a single CharacterPathStep, i.e.
        
              [ .trigger = C, .door_id = (b,a,C) ]

        -- The terminal state is 'B'

    (3) A recursive search starts for more single character transitions 
        beginning from state B. Each time another single character transition
        is found, the terminal is integrated into the path and the new 
        terminal is setup.
    ___________________________________________________________________________
    """
    __slots__ = ("index", "entry", "drop_out", 
                 "__sequence",       
                 "__transition_map", "__transition_map_wildcard_char") 

    def __init__(self, StartState, TheTransitionMap, TransitionCharacter, TargetDoorId):
        if StartState is None: return # Only for Clone

        assert isinstance(StartState, AnalyzerState)
        assert isinstance(TransitionCharacter, (int, long))
        assert isinstance(TheTransitionMap, TransitionMap)

        self.entry    = PathWalkerState_Entry(StartState.entry)
        self.drop_out = MegaState_DropOut(StartState) 

        self.__sequence                     = [ CharacterPathStep(StartState.index, TransitionCharacter, TargetDoorId) ]
        self.__transition_map               = TheTransitionMap.clone()
        self.__transition_map_wildcard_char = TransitionCharacter
        self.__transition_map.set_target(TransitionCharacter, E_StateIndices.VOID)

    def clone(self):
        result = CharacterPath(None, None, None, None)

        result.entry                          = deepcopy(self.entry)
        result.drop_out                       = deepcopy(self.drop_out)
        result.__sequence                     = [ x for x in self.__sequence ] # CharacterPathStep are immutable
        result.__transition_map               = self.__transition_map.clone()
        result.__transition_map_wildcard_char = self.__transition_map_wildcard_char
        return result

    def extended_clone(self, PreviousTerminal, TransitionCharacter, TargetDoorId, TransitionMapWildCardPlug):
        """Append 'State' to path:

        -- add 'State' to the sequence of states on the path.

        -- absorb the 'State's' drop-out and entry actions into the path's 
           drop-out and entry actions.
        
        If 'TransitionCharacter' is None, then the state is considered a
        terminal state. Terminal states are not themselves implemented inside a
        PathWalkerState. Thus, their entry and drop out information does not
        have to be absorbed.
        """
        assert    TransitionCharacter is not None
        assert    TransitionMapWildCardPlug is None \
               or isinstance(TransitionMapWildCardPlug, DoorID) \
               or Target == E_StateIndices.DROP_OUT

        StartStateIndex = PreviousTerminal.index
        result = self.clone()

        if TransitionMapWildCardPlug != -1: 
            assert self.__transition_map_wildcard_char is not None
            assert self.__transition_map.get_target(self.__transition_map_wildcard_char) == E_StateIndices.VOID
            self.__transition_map.set_target(self.__transition_map_wildcard_char, TransitionMapWildCardPlug)
            self.__transition_map_wildcard_char = None

        result.__sequence.append(CharacterPathStep(StartStateIndex, TransitionCharacter, TargetDoorId))

        # Adapt the entry's action_db: include the entries of the new state
        # (The index of the state on the path determines the path iterator's offset)
        offset = len(result.__sequence) + 1
        prev_step = result.__sequence[-1]
        result.entry.action_db_update(PreviousTerminal.entry, offset, 
                                      PreviousStep=self.__sequence[-1])

        # Adapt information about entry and drop-out actions
        result.drop_out.add(PreviousTerminal.index, PreviousTerminal.drop_out)

        return result

    def has_wildcard(self):
        return self.__transition_map_wildcard_char is not None

    @property
    def sequence(self):
        return self.__sequence

    @property
    def transition_map(self):
        return self.__transition_map

    @property
    def uniform_entry_command_list_along_path(self):
        """RETURNS: 
        
           ComandList -- For each step on the path the same ComandList
                         is executed.
           None       -- Each step on the path requires a different 
                         CommandLists to be executed. 
        """
        step      = self.__sequence[0]
        prototype = self.entry.action_db.get_command_list_by_door_id(step.door_id)
        for step in self.__sequence[1:-1]:
            command_list = self.entry.action_db.get_command_list_by_door_id(step.door_id)
            if not command_list.is_equivalent(prototype):
                return None
        return prototype

    def contains_state(self, StateIndex):
        for dummy in ifilter(lambda x: x.state_index == StateIndex, self.__sequence):
            return True
        return False

    def is_uniform_with_predecessor(self, State):
        """Considers the command lists for Entry and DropOut of the state. If
        the are uniform with the current setting.

        RETURNS: True  -- Uniform Entry and DropOut-s.
                 False -- One of them is not uniform.
        """
        # (*) DropOut
        #
        # It can easily check uniformity with all. This does not restrict the
        # general solution. Since as a result of having subsequent states on a
        # path uniform, all drop-outs on the path are uniform.
        if not self.drop_out.is_uniform_with(State.drop_out):
            return False

        # (*) Entry
        # 
        # Check whether the entry of the last state on the path executes the
        # same as the entry to 'State'.
        door_id = self.__sequence[-1].door_id
        
        # CommandList upon Entry to TargetState
        command_list = State.entry.action_db.get_command_list_by_door_id(door_id)
        if not self.entry.previous_on_path_CommandList.is_equivalent(command_list):
            return False

        return False

    def finalize(self):
        # Ensure that there is no wildcard in the transition map
        if self.__transition_map_wildcard_char is None: return

        self.__transition_map.smoothen(self.__transition_map_wildcard_char)
        self.__transition_map_wildcard_char = None

    def get_string(self, NormalizeDB=None):
        # assert NormalizeDB is None, "Sorry, I guessed that this was no longer used."
        def norm(X):
            assert isinstance(X, (int, long)) or X is None
            return X if NormalizeDB is None else NormalizeDB[X]

        L            = max(len(x[0].get_utf8_string()) for x in self.__transition_map)
        skeleton_txt = ""
        for interval, target_door_id in self.__transition_map:
            interval_str  = interval.get_utf8_string()
            skeleton_txt += "   %s%s -> %s\n" % (interval_str, " " * (L - len(interval_str)), target_door_id)

        sequence_txt = ""
        for x in self.__sequence[:-1]:
            sequence_txt += "(%i)--'%s'-->" % (x.state_index, chr(x.trigger))
        sequence_txt += "[%i]" % norm(self.__sequence[-1].state_index)

        return "".join(["start    = %i;\n" % norm(self.__sequence[0].state_index),
                        "path     = %s;\n" % sequence_txt,
                        "skeleton = {\n%s}\n"  % skeleton_txt, 
                        "wildcard = %s;\n" % repr(self.__transition_map_wildcard_char is not None)])

    def __repr__(self):
        return self.get_string()

    def __len__(self):
        return len(self.__sequence)

    def state_index_list_size(self):
        return len(self.__sequence)

    def state_index_list(self):
        assert len(self.__sequence) > 1
        return [ x.state_index for x in self.__sequence ]

    def state_index_set(self):
        assert len(self.__sequence) > 1
        return set(x.state_index for x in self.__sequence)

