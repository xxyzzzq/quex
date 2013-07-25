from quex.engine.analyzer.state.entry_action import DoorID, DoorID_Scheme
from quex.blackboard                         import E_StateIndices

MegaState_Target_DROP_OUT_hash = hash(E_StateIndices.DROP_OUT)

class MegaState_Transition(object):
    """________________________________________________________________________
    
    Where an AnalyzerState's transition map associates a character interval
    with a target state index, a MegaState's transition map associates a
    character interval with a MegaState_Transition.

    A MegaState_Transition determines the target state, or target state's entry
    door, by means of a state key. It is very well possible that it is
    homogeneous and independent of the state key. In that case, it contains a
    '.target_state_index' or '.door_id'. If not, the '.scheme' member describes
    the relationship between and target state index. For example, a given
    interval X triggers to MegaState_Transition T, i.e. there is an element in the
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

              MegaState_Transition.init()

    initializes the .object_db. An independent copy of the .object_db can be
    obtained by

              my_copy = MegaState_Transition.disconnect_object_db()

    FINALIZATION: _____________________________________________________________

    Once the whole state configuration and the states' entry doors are
    determined, the actual MegaState_Transition object can be finalized. That is:
       
       -- A common target may become a scheme, if the DoorIDs differ depending
          on the 'from_state_index' (from .implemented_state_index_list()).

       -- A scheme may become a common target, if the target DoorID 
          is the same for all indices in .implemented_state_index_list().

    Finalization sets the 'scheme_id' if it is a scheme. It set's the
    '.door_id' if the target state's door is the same for all involved states.

    ___________________________________________________________________________
    NOTE: All 'DropOut' MegaState_Transition are represented by the single object
          'MegaState_Target_DROP_OUT'. This saves memory.
    """
    __slots__   = ('__drop_out_f', '__scheme', '__scheme_id', '__hash', '__door_id')
    __object_db = dict()

    @staticmethod
    def init():
        """Initializes: '__object_db' which keeps track of generated MegaState_Transition-s."""
        MegaState_Transition.__object_db.clear()
        # The Drop-Out target must be always in there.
        MegaState_Transition.__object_db[E_StateIndices.DROP_OUT] = MegaState_Target_DROP_OUT

    @staticmethod
    def disconnect_object_db():
        """Disconnects the '__object_db' so that it may be used without influencing 
           the '__object_db' of MegaState_Transition.
        """
        tmp_object_db                = MegaState_Transition.__object_db
        MegaState_Transition.__object_db = dict()
        return tmp_object_db

    @staticmethod
    def create(Target):
        assert Target is not None 
        assert    Target == E_StateIndices.DROP_OUT \
               or isinstance(Target, DoorID)        \
               or isinstance(Target, DoorID_Scheme)
       
        result = MegaState_Transition.__object_db.get(Target)
        if result is None: 
            result = MegaState_Transition(Target)
            MegaState_Transition.__object_db[Target] = result

        return result

    def replace_self(self, MapOldToNewDoorIDs):
        """Replaces DoorIDs based on 'MapOldToNewDoorIDs', if necessary. 

        RETURNS: None,            if no replacement was necessary.
                 A clone of self, with replaced DoorID-s if a replacement
                                  was necessary.
        """
        if self.__drop_out_f: 
            return None

        elif self.__door_id is not None:
            new_door_id = MapOldToNewDoorIDs.get(self.__door_id)
            if new_door_id is None: return None
            else:                   return MegaState_Transition(new_door_id)

        elif self.__scheme is not None:
            new_scheme = None
            for i, door_id in enumerate(self.__scheme):
                new_door_id  = MapOldToNewDoorIDs.get(door_id)
                if   new_door_id is None: 
                    continue
                elif new_scheme is None: 
                    new_scheme = list(self.__scheme)
                new_scheme[i] = new_door_id

            if new_scheme is None: return None
            else:                  return MegaState_Transition(DoorID_Scheme(new_scheme))

        else:
            assert False

    def __init__(self, Target):
        global MegaState_Target_DROP_OUT_hash
        if Target is None: # Only to be used by 'self.clone()'
            return 

        self.__scheme     = None
        self.__scheme_id  = None # Only possibly set in 'assign_scheme_ids'
        self.__door_id    = None 
        self.__drop_out_f = False
        self.__hash       = None

        if   Target == E_StateIndices.DROP_OUT: 
            self.__drop_out_f = True; 
            self.__hash       = MegaState_Target_DROP_OUT_hash 
        elif isinstance(Target, DoorID_Scheme):  
            for x in Target:
                assert x == E_StateIndices.DROP_OUT or isinstance(x, DoorID), x
            self.__scheme     = Target
        elif isinstance(Target, DoorID): 
            self.__door_id    = Target # only by '.finalize()'
        else:
            assert False, Target.__class__.__name__

    def get_hash(self):
        assert False, "Supposed to use __hash__"
        if self.__hash is None: 
            if self.__target_state_index is not None: self.__hash = hash(self.__target_state_index)
            elif self.__scheme is not None:           self.__hash = hash(self.__scheme)
            else:                                     self.__hash = hash(self.__door_id)
        return self.__hash
    @property
    def scheme(self):       return self.__scheme
    @property
    def door_id(self):      
        assert self.__door_id is None or isinstance(self.__door_id, DoorID)
        return self.__door_id
    @property
    def drop_out_f(self):   return self.__drop_out_f

    @property
    def scheme_id(self):    return self.__scheme_id

    @staticmethod
    def assign_scheme_ids(transition_map):
        def determine_scheme_id(scheme_db, Scheme):
            scheme_id = scheme_db.get(Scheme)
            if scheme_id is None: 
                scheme_id = len(scheme_db)
                scheme_db[Scheme] = scheme_id
            return scheme_id

        scheme_db = {}
        for interval, target in transition_map:
            assert isinstance(target, MegaState_Transition)
            if target.__scheme is None: continue
            target.__scheme_id = determine_scheme_id(scheme_db, target.__scheme)

    @staticmethod
    def rejoin_uniform_schemes(transition_map):
        """If all DoorIDs in a scheme are the same, the target becomes
        a 'DoorID' target instead a scheme target. That is, the target
        is no longer dependent on the state to be implemented.
        """
        def rejoin(scheme):
            prototype  = None
            for door_id in target.__scheme:
                if   door_id == prototype: continue
                elif prototype is None:    prototype = door_id  # first door_id --> protype
                else:                      return None          # scheme not uniform
            # All door_ids uniform:
            return MegaState_Transition.create(prototype)

        for i, info in enumerate(transition_map):
            interval, target = info
            if target.__scheme is None: continue
            new_target = rejoin(target.__scheme)
            if new_target is None: continue
            transition_map[i] = (interval, new_target)

        return

    def __repr__(self):
        if   self.drop_out_f:          return "MegaState_Transition:DropOut"
        elif self.door_id is not None: return "MegaState_Transition:%s"         % repr(self.__door_id).replace("L", "")
        elif self.scheme is not None:  return "MegaState_Transition:scheme(%s)" % repr(self.__scheme).replace("L", "")
        else:                          return "MegaState_Transition:<ERROR>"

    def __hash__(self):
        if self.__hash is None:
            if   self.__drop_out_f:          self.__hash = 0
            elif self.__door_id is not None: self.__hash = self.__door_id.state_index
            elif self.__scheme is not None:  self.__hash = hash(self.__scheme)
            else:                            assert False
        return self.__hash

    def __eq__(self, Other):
        if   isinstance(Other, MegaState_Transition) == False: 
            return False
        elif self.__drop_out_f and Other.__drop_out_f: 
            return True
        elif self.__door_id is not None and Other.__door_id is not None:
            return self.__door_id == Other.__door_id
        elif self.__scheme  is not None and Other.__scheme  is not None:
            return self.__scheme == Other.__scheme
        else:
            return False

# Globally unique object to stand up for all 'drop-outs'.
MegaState_Target_DROP_OUT      = MegaState_Transition(E_StateIndices.DROP_OUT)

