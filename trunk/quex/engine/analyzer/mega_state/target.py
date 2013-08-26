from quex.engine.analyzer.state.entry_action import TransitionID, DoorID, DoorID_Scheme
from quex.engine.tools                       import UniformObject
from quex.blackboard                         import E_StateIndices

from collections import namedtuple

TargetByStateKey_DROP_OUT_hash = hash(E_StateIndices.DROP_OUT)

TargetByStateKey_Element = namedtuple("TargetByStateKey_Element_tuple", ("transition_id", "door_id"))

class TargetByStateKey_db(dict):
    def __init__(self):
        dict.clear(self)

    def init(self):
        """Initializes: '__object_db' which keeps track of generated TargetByStateKey-s."""
        dict.clear(self)


class TargetByStateKey(object):
    """________________________________________________________________________
    
    Where an AnalyzerState's transition map associates a character interval
    with a target state index, a MegaState's transition map associates a
    character interval with a TargetByStateKey.

    A TargetByStateKey determines the target state, or target state's entry
    door, by means of a state key. It is very well possible that it is
    homogeneous and independent of the state key. In that case, it contains a
    '.target_state_index' or '.door_id'. If not, the '.scheme' member describes
    the relationship between and target state index. For example, a given
    interval X triggers to TargetByStateKey T, i.e. there is an element in the
    transition map:

             ...
             [ X, T ]
             ...

    then 'T.scheme[state key]' tells the 'target state index' for a given state key.
    The door through which it enters is determined by the transition id:

        TransitionID(FromStateIndex = MS.map_state_key_to_state_index(state key), 
                     ToStateIndex   = T.scheme[state key])

    where MS is the MegaState that contains the transition map. The
    TransitionID can be translated into a DoorID by the target state's entry
    database 'action_db[TransitionId].door_id'.
    
    TRACKING SCHEMES: _________________________________________________________

    There might be multiple intervals following the same target scheme. This class
    keeps track of the schemes by means of the '.object_db'. Before handling 
    a transition map the function

              TargetByStateKey.object_db.init()

    initializes the .object_db. An independent copy of the .object_db can be
    obtained by

              my_copy = TargetByStateKey.object_db.disconnect()

    FINALIZATION: _____________________________________________________________

    Once the whole state configuration and the states' entry doors are
    determined, the actual TargetByStateKey object can be finalized. That is:
       
       -- A common target may become a scheme, if the DoorIDs differ depending
          on the 'from_state_index' (from .implemented_state_index_set).

       -- A scheme may become a common target, if the target DoorID 
          is the same for all indices in .implemented_state_index_set.

    Finalization sets the 'scheme_id' if it is a scheme. It set's the
    '.door_id' if the target state's door is the same for all involved states.

    ___________________________________________________________________________
    NOTE: All 'DropOut' TargetByStateKey are represented by the single object
          'TargetByStateKey_DROP_OUT'. This saves memory.
    """
    __slots__ = ("__scheme", "__uniform_door_id", "__scheme_id")
    object_db = TargetByStateKey_db()

    @staticmethod
    def from_transition(TransitionId, DoorId):
        result = TargetByStateKey()
        result.__scheme          = (TargetByStateKey_Element(TransitionId, DoorId),)
        result.__uniform_door_id = DoorId
        return result

    @staticmethod
    def from_2_TargetByStateKeys(A, B):
        result = TargetByStateKey()
        result.__scheme = A.__scheme + B.__scheme
        if A.__uniform_door_id == B.__uniform_door_id: 
            result.__uniform_door_id = A.__uniform_door_id
        else:
            result.__uniform_door_id = None
        return result

    @staticmethod
    def from_scheme(SchemeAsList):
        result = TargetByStateKey()
        result.__scheme = tuple(SchemeAsList)
        result.__uniform_door_id = UniformObject.from_iterable(SchemeAsList).content
        assert result.__uniform_door_id is None or isinstance(result.__uniform_door_id, DoorID)
        return result

    @staticmethod
    def special(X):
        return TargetByStateKey.from_transition(TransitionID(X,X,0), DoorID(X,0))

    def clone_adapted_self(self, MapTransitionIdToNewDoorId):
        """Replaces DoorIDs based on 'MapOldToNewDoorIDs', if necessary. 

        RETURNS: None,            if no replacement was necessary.
                 A clone of self, with replaced DoorID-s if a replacement
                                  was necessary.
        """
        new_scheme = None
        for i, x in enumerate(self.__scheme):
            new_door_id = MapTransitionIdToNewDoorId.get(x.transition_id)
            if new_door_id is None: 
                continue
            elif new_scheme is None: 
                new_scheme = list(self.__scheme)
            new_scheme[i] = TargetByStateKey_Element(x.transition_id, new_door_id)

        if new_scheme is None: return self
        else:                  return TargetByStateKey.from_scheme(new_scheme)

    @property
    def uniform_door_id(self):
        return self.__uniform_door_id

    @property
    def drop_out_f(self):
        if self.__uniform_door_id is None: return False
        return self.__uniform_door_id.state_index == E_StateIndices.DROP_OUT

    @property
    def scheme_id(self):    return self.__scheme_id

    def iterable_door_id_scheme(self):
        for x in self.__scheme:
            yield x.door_id

    @staticmethod
    def assign_scheme_ids(transition_map):
        class SchemeDB(dict):
            def get_id(self, Scheme):
                specific_key = tuple(x.door_id for x in Scheme)
                scheme_id    = dict.get(self, specific_key)
                if scheme_id is not None: return scheme_id
                new_scheme_id = len(self)
                dict.__setitem__(self, specific_key, new_scheme_id)
                return new_scheme_id

        scheme_db = SchemeDB()
        for interval, target in transition_map:
            assert isinstance(target, TargetByStateKey)
            if target.uniform_door_id is not None: continue
            target.__scheme_id = scheme_db.get_id(target.__scheme)

    @staticmethod
    def rejoin_uniform_schemes(transition_map):
        """If all DoorIDs in a scheme are the same, the target becomes
        a 'DoorID' target instead a scheme target. That is, the target
        is no longer dependent on the state to be implemented.
        """
        assert False
        def rejoin(scheme):
            prototype  = None
            for door_id in target.__door_id_scheme:
                if   door_id == prototype: continue
                elif prototype is None:    prototype = door_id  # first door_id --> protype
                else:                      return None          # scheme not uniform
            # All door_ids uniform:
            return TargetByStateKey.create(prototype)

        for i, info in enumerate(transition_map):
            interval, target = info
            if target.__door_id_scheme is None: continue
            new_target = rejoin(target.__door_id_scheme)
            if new_target is None: continue
            transition_map[i] = (interval, new_target)

        return

    def __repr__(self):
        if   self.drop_out_f:        
            return "TargetByStateKey:DropOut"
        elif self.uniform_door_id is not None: 
            return "TargetByStateKey:%s"         % repr(self.__uniform_door_id).replace("L", "")
        else:
            return "TargetByStateKey:scheme(%s)" % repr(list(self.iterable_door_id_scheme())).replace("L", "")

    def __hash__(self):
        if self.__hash is None:
            if   self.__drop_out_f:          self.__hash = 0
            elif self.__door_id is not None: self.__hash = self.__door_id.state_index
            elif self.__door_id_scheme is not None:  self.__hash = hash(self.__door_id_scheme)
            else:                            assert False
        return self.__hash

    def __eq__(self, Other):
        if   isinstance(Other, TargetByStateKey) == False: 
            return False
        elif self.__uniform_door_id != Other.__uniform_door_id:
            return False
        elif self.__uniform_door_id is not None:
            return True
        else:
            return self.__scheme == Other.__scheme

# Globally unique object to stand up for all 'drop-outs'.
TargetByStateKey_DROP_OUT = TargetByStateKey.special(E_StateIndices.DROP_OUT)
TargetByStateKey_RELOAD   = TargetByStateKey.special(E_StateIndices.RELOAD_PROCEDURE)

