from   quex.engine.analyzer.state.core         import AnalyzerState
from   quex.engine.analyzer.state.entry_action import DoorID, \
                                                      SetPathIterator
from   quex.engine.analyzer.mega_state.core    import MegaState_Entry, \
                                                      MegaState_DropOut
from   quex.engine.analyzer.transition_map     import TransitionMap       
import quex.engine.state_machine.index         as     index

from   quex.engine.tools                       import UniformObject

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
        self.uniform_CommandList_along_path = UniformObject(EqualCmp=CommandList.is_equivalent)

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
            OnPathStateIndex = PreviousStep.state_index
        else:
            OnPathStateIndex = None

        for transition_id, action in TheEntry.action_db.iteritems():
            clone = action.clone()
            print "#tid:", transition_id, OnPathStateIndex
            if transition_id.source_state_index != OnPathStateIndex:
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

        print "#-- action_db:", [(x,y) for x,y in self.action_db.iteritems() ]
        print "#-- reascl:", self.transition_reassignment_candidate_list
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

class CharacterPathStep(namedtuple("CharacterPathStep_tuple", ("state_index", "trigger"))):
    """See also class 'CharacterPath' where the role of the CharacterPathStep
       is explained further.

       The CharacterPathStep contains information about one single step
       along the CharacterPath. It tells from what state the step starts

                        .source_state_index   .trigger     
                        .---.                                        .---.
                        | 1 |------------------ 'g' ---------------->| 3 |
                        '---'                                        '---'

       The '2' is the '.source_state_index' of the next CharacterPathStep on the
       CharacterPath. The step from state 1 to X is described by:

                current.state_index =  1   # Index of the state where the step starts
                current.trigger     = 'g'  # The triggering character
                next.state_index    =  3   # Index of the state where the step goes
   
       Note, that this setup fits well the case where the path is described by a
       list of CharacterPathStep-s. 

       Special Case: 
       
          .trigger = None

          => Terminal, no further transition. '.state_index' is the first state 
             behind the path.
    """
    def __new__(self, StateIndex, TransitionChar):
        assert isinstance(StateIndex, long)
        assert TransitionChar is None or isinstance(TransitionChar, (int, long))
        return super(CharacterPathStep, self).__new__(self, StateIndex, TransitionChar)

    def __repr__(self):
        return ".state_index = %s;\n" \
               ".trigger     = '%s';\n" \
               % (self.state_index, self.trigger)

class CharacterPath(object):
    """________________________________________________________________________

    Represents identified path in the state machine such as:


       ( 1 )--- 'a' -->( 2 )--- 'b' -->( 3 )--- 'c' -->( 4 )--- 'd' -->( 5 )

    where the remaining transitions in each state match (except for the last).
    A CharacterPath contains a '.step_list' of CharacterPathSteps, e.g.
  
    .step_list:

       .------------------. .------------------. .------------------.
       |.state_index = 1  | |.state_index = 2  | |.state_index = 3  |
       |.trigger     = 'a'| |.trigger     = 'b'| |.trigger     = 'b'| . . .
       '------------------' '------------------' '------------------'
   
    .terminal:

       The AnalyzerState which is entered from the last element of the path via
       a single character transition. It is not implemented by the CharacterPath.
       As soon as another state is appended, it becomes part of the path and the 
       newly appended becomes the terminal.

    .implemented_state_index_list:
     
      A list of state indices which the path can cover. This does not include
      the last state triggered by the terminal element of '.step_list'. As in the
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

        -- where the .step_list contains a single CharacterPathStep, i.e.
        
              [ .state_index = X, .trigger = C ]

        -- The terminal state is 'B'

    (3) A recursive search starts for more single character transitions 
        beginning from state B. Each time another single character transition
        is found, the terminal is integrated into the path and the new 
        terminal is setup.
    ___________________________________________________________________________
    """
    __slots__ = ("index", "entry", "drop_out", 
                 "__step_list",       
                 "__transition_map", "__transition_map_wildcard_char", 
                 "__entry_uniformity_along_path_f") 

    def __init__(self, StartState, TheTransitionMap, TransitionCharacter):
        if StartState is None: return # Only for Clone

        assert isinstance(StartState, AnalyzerState)
        assert isinstance(TransitionCharacter, (int, long))
        assert isinstance(TheTransitionMap, TransitionMap)

        self.entry    = PathWalkerState_Entry(StartState.entry)
        self.drop_out = MegaState_DropOut(StartState) 

        self.__step_list                    = [ CharacterPathStep(StartState.index, TransitionCharacter) ]
        self.__transition_map               = TheTransitionMap.clone()
        self.__transition_map_wildcard_char = TransitionCharacter
        self.__transition_map.set_target(TransitionCharacter, E_StateIndices.VOID)
        self.__entry_uniformity_along_path_f   = True

    def clone(self):
        result = CharacterPath(None, None, None)

        result.entry                           = deepcopy(self.entry)
        result.drop_out                        = deepcopy(self.drop_out)
        result.__step_list                     = [ x for x in self.__step_list ] # CharacterPathStep are immutable
        result.__transition_map                = self.__transition_map.clone()
        result.__transition_map_wildcard_char  = self.__transition_map_wildcard_char
        result.__entry_uniformity_along_path_f = self.__entry_uniformity_along_path_f
        return result

    def extended_clone(self, PreviousTerminal, TransitionCharacter, TransitionMapWildCardPlug):
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
        assert    isinstance(TransitionMapWildCardPlug, DoorID) \
               or Target == E_StateIndices.DROP_OUT

        result = self.clone()

        if TransitionMapWildCardPlug != -1: 
            assert self.__transition_map_wildcard_char is not None
            assert self.__transition_map.get_target(self.__transition_map_wildcard_char) == E_StateIndices.VOID
            self.__transition_map.set_target(self.__transition_map_wildcard_char, TransitionMapWildCardPlug)
            self.__transition_map_wildcard_char = None

        before_previous_state_index = self.__step_list[-1].state_index
        result.__step_list.append(CharacterPathStep(PreviousTerminal.index, TransitionCharacter))

        # Adapt the entry's action_db: include the entries of the new state
        # (The index of the state on the path determines the path iterator's offset)
        offset = len(result.__step_list) + 1
        prev_step = result.__step_list[-1]
        result.entry.action_db_update(PreviousTerminal.entry, offset, 
                                      PreviousStep=self.__step_list[-1])

        command_list = PreviousTerminal.entry.action_db.get_command_list(before_previous_state_index,
                                                                         PreviousTerminal.index, 
                                                                         TriggerId=0)
        result.entry.uniform_CommandList_along_path <<= command_list

        # Adapt information about entry and drop-out actions
        result.drop_out.add(PreviousTerminal.index, PreviousTerminal.drop_out)

        return result

    def has_wildcard(self):
        return self.__transition_map_wildcard_char is not None

    @property
    def step_list(self):
        return self.__step_list

    @property
    def transition_map(self):
        return self.__transition_map

    def entry_uniformity_with_predecessor(self, State):
        """Check whether the entry of the last state on the path executes the
           same CommandList as the entry to 'State'. 
        """
        # There can be only one transition from source to target. Otherwise,
        # the path finding algorithm would not have accepted the CharacterStep.
        source_state_index = self.__step_list[-1].state_index
        target_state_index = State.index
        
        # CommandList upon Entry to State
        # (TriggerIndex == 0, because there can only be one transition from
        #                     one state to the next on the path).
        command_list = State.entry.action_db.get_command_list(target_state_index, 
                                                              source_state_index)
        assert command_list is not None
        if not self.entry.uniform_CommandList_along_path.fit(command_list):
            return False

        return True

    def entry_uniformity_along_path_unset(self):
        self.__entry_uniformity_along_path_f = False

    @property
    def uniform_entry_command_list_along_path(self):
        """RETURNS: 
        
           ComandList -- For each step on the path the same ComandList
                         is executed.
           None       -- Each step on the path requires a different 
                         CommandLists to be executed. 
        """
        return self.entry.uniform_CommandList_along_path.content

    def finalize(self):
        # Ensure that there is no wildcard in the transition map
        if self.__transition_map_wildcard_char is None: return

        self.__transition_map.smoothen(self.__transition_map_wildcard_char)
        self.__transition_map_wildcard_char = None

    def contains_state(self, StateIndex):
        for dummy in ifilter(lambda x: x.state_index == StateIndex, self.__step_list[:-1]):
            return True
        return False

    def state_index_list_size(self):
        return len(self.__step_list) - 1

    def state_index_list(self):
        assert len(self.__step_list) > 1
        return [ x.state_index for x in self.__step_list[:-1] ]

    def state_index_set(self):
        assert len(self.__step_list) > 1
        return set(x.state_index for x in self.__step_list[:-1])

    def __len__(self):
        assert False, "Ambigous: len = length of path or number of states on path?"
        return len(self.__step_list)

    def __repr__(self):
        return self.get_string()

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
        for x in self.__step_list[:-1]:
            sequence_txt += "(%i)--'%s'-->" % (x.state_index, chr(x.trigger))
        sequence_txt += "[%i]" % norm(self.__step_list[-1].state_index)

        return "".join(["start    = %i;\n" % norm(self.__step_list[0].state_index),
                        "path     = %s;\n" % sequence_txt,
                        "skeleton = {\n%s}\n"  % skeleton_txt, 
                        "wildcard = %s;\n" % repr(self.__transition_map_wildcard_char is not None)])

