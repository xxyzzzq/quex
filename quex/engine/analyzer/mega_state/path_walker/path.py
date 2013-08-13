from   quex.engine.analyzer.state.core         import AnalyzerState
from   quex.engine.analyzer.state.drop_out     import DropOut
from   quex.engine.analyzer.state.entry_action import DoorID, \
                                                      PathIteratorSet, \
                                                      CommandList
from   quex.engine.analyzer.mega_state.core    import MegaState_Entry, \
                                                      MegaState_DropOut
from   quex.engine.analyzer.transition_map     import TransitionMap       
import quex.engine.state_machine.index         as     index

from   quex.engine.tools                       import UniformObject

from   quex.blackboard import E_StateIndices

from   itertools   import ifilter
from   collections import namedtuple

from   copy import deepcopy

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

    .implemented_state_index_set:
     
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
    __slots__ = ("__step_list",       
                 "__transition_map", 
                 "__transition_map_wildcard_char", 
                 "uniform_entry_CommandList", 
                 "uniform_DropOut") 

    def __init__(self, StartState, TheTransitionMap, TransitionCharacter):
        if StartState is None: return # Only for Clone

        assert isinstance(StartState,          AnalyzerState)
        assert isinstance(TransitionCharacter, (int, long))
        assert isinstance(TheTransitionMap,    TransitionMap)

        self.uniform_entry_CommandList = UniformObject(EqualCmp=CommandList.is_equivalent)
        self.uniform_DropOut           = UniformObject(EqualCmp=DropOut.is_equal)

        self.__step_list                    = [ CharacterPathStep(StartState.index, TransitionCharacter) ]

        self.__transition_map_wildcard_char = TransitionCharacter
        self.__transition_map               = TheTransitionMap.clone()
        self.__transition_map.set_target(self.__transition_map_wildcard_char, 
                                         E_StateIndices.VOID)

    def clone(self):
        assert    self.__transition_map_wildcard_char is None \
               or isinstance(self.__transition_map_wildcard_char, (int, long))
        assert isinstance(self.__transition_map,    TransitionMap)

        result = CharacterPath(None, None, None)

        result.uniform_entry_CommandList       = self.uniform_entry_CommandList.clone()
        result.uniform_DropOut                 = self.uniform_DropOut.clone()
        result.__step_list                     = [ x for x in self.__step_list ] # CharacterPathStep are immutable
        result.__transition_map                = self.__transition_map.clone()
        result.__transition_map_wildcard_char  = self.__transition_map_wildcard_char
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
               or TransitionMapWildCardPlug == E_StateIndices.DROP_OUT \
               or TransitionMapWildCardPlug == -1, \
                  "TransitionMapWildCardPlug: '%s'" % TransitionMapWildCardPlug

        result = self.clone()

        # CommandList upon Entry to State
        # (TriggerIndex == 0, because there can only be one transition from
        #                     one state to the next on the path).
        prev_step    = self.__step_list[-1]
        command_list = PreviousTerminal.entry.action_db.get_command_list(PreviousTerminal.index, 
                                                                         prev_step.state_index,
                                                                         TriggerId=0)
        assert command_list is not None

        result.uniform_entry_CommandList <<= command_list
        result.uniform_DropOut           <<= PreviousTerminal.drop_out

        result.__step_list.append(CharacterPathStep(PreviousTerminal.index, TransitionCharacter))

        if TransitionMapWildCardPlug != -1: 
            assert self.__transition_map_wildcard_char is not None
            assert self.__transition_map.get_target(self.__transition_map_wildcard_char) == E_StateIndices.VOID
            self.__transition_map.set_target(self.__transition_map_wildcard_char, TransitionMapWildCardPlug)
            self.__transition_map_wildcard_char = None

        return result

    def uniformity_with_predecessor(self, State):
        """Check whether the entry of the last state on the path executes the
           same CommandList as the entry to 'State'. 
        """
        # CommandList upon Entry to State
        # (TriggerIndex == 0, because there can only be one transition from
        #                     one state to the next on the path).
        prev_step    = self.__step_list[-1]
        command_list = State.entry.action_db.get_command_list(State.index, prev_step.state_index, 
                                                              TriggerId=0)
        assert command_list is not None

        if   not self.uniform_entry_CommandList.fit(command_list): return False
        elif not self.uniform_DropOut.fit(State.drop_out):         return False

        return True

    def has_wildcard(self):
        return self.__transition_map_wildcard_char is not None

    @property
    def step_list(self):
        return self.__step_list

    @property
    def transition_map(self):
        return self.__transition_map

    def finalize(self, TerminalStateIndex):
        self.__step_list.append(CharacterPathStep(TerminalStateIndex, None))
        # Ensure that there is no wildcard in the transition map
        if self.__transition_map_wildcard_char is None: return

        self.__transition_map.smoothen(self.__transition_map_wildcard_char)
        self.__transition_map_wildcard_char = None

    def contains_state(self, StateIndex):
        """Is 'StateIndex' on the path(?). This includes the terminal."""
        for dummy in (x for x in self.__step_list if x.state_index == StateIndex):
            return True
        return False

    def state_index_set_size(self):
        return len(self.__step_list) - 1

    def state_index_set(self):
        assert len(self.__step_list) > 1
        return set(x.state_index for x in self.__step_list[:-1])

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

