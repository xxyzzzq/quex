from quex.blackboard                         import E_StateIndices

MegaState_Target_DROP_OUT_hash = hash(E_StateIndices.DROP_OUT)

class MegaState_Target(object):
    """________________________________________________________________________
    
    Where an AnalyzerState's transition map associates a character interval
    with a target state index, a MegaState's transition map associates a
    character interval with a MegaState_Target.

    A MegaState_Target determines the target state, or target state's entry
    door, by means of a state key. It is very well possible that it is
    homogeneous and independent of the state key. In that case, it contains a
    '.target_state_index' or '.door_id'. If not, the '.scheme' member describes
    the relationship between and target state index. For example, a given
    interval X triggers to MegaState_Target T, i.e. there is an element in the
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

              MegaState_Target.init()

    initializes the .object_db. An independent copy of the .object_db can be
    obtained by

              my_copy = MegaState_Target.disconnect_object_db()

    FINALIZATION: _____________________________________________________________

    Once the whole state configuration and the states' entry doors are
    determined, the actual MegaState_Target object can be finalized. That is:
       
       -- A common target may become a scheme, if the DoorIDs differ depending
          on the 'from_state_index' (from .implemented_state_index_list()).

       -- A scheme may become a common target, if the target DoorID 
          is the same for all indices in .implemented_state_index_list().

    Finalization sets the 'scheme_id' if it is a scheme. It set's the
    '.door_id' if the target state's door is the same for all involved states.

    ___________________________________________________________________________
    NOTE: All 'DropOut' MegaState_Target are represented by the single object
          'MegaState_Target_DROP_OUT'. This saves memory.
    """
    __slots__   = ('__drop_out_f', '__scheme', '__scheme_id', '__hash', '__target_state_index', '__door_id')
    __object_db = dict()

    @staticmethod
    def init():
        """Initializes: '__object_db' which keeps track of generated MegaState_Target-s."""
        MegaState_Target.__object_db.clear()
        # The Drop-Out target must be always in there.
        MegaState_Target.__object_db[E_StateIndices.DROP_OUT] = MegaState_Target_DROP_OUT

    @staticmethod
    def disconnect_object_db():
        """Disconnects the '__object_db' so that it may be used without influencing 
           the '__object_db' of MegaState_Target.
        """
        tmp_object_db                = MegaState_Target.__object_db
        MegaState_Target.__object_db = dict()
        return tmp_object_db

    @staticmethod
    def create(Target):
        assert Target is not None 

        result = MegaState_Target.__object_db.get(Target)
        if result is None: 
            result = MegaState_Target(Target)
            MegaState_Target.__object_db[Target] = result

        return result

    def __init__(self, Target):
        global MegaState_Target_DROP_OUT_hash
        if Target is None: # Only to be used by 'self.clone()'
            return 

        self.__target_state_index = None
        self.__scheme             = None
        self.__scheme_id          = None # Only possibly set in 'finalize'
        self.__door_id            = None # Only possibly set in 'finalize'

        if   Target == E_StateIndices.DROP_OUT: 
            self.__drop_out_f = True; 
            self.__hash       = MegaState_Target_DROP_OUT_hash 
            return

        self.__drop_out_f = False
        self.__hash       = None
        if   isinstance(Target, long):   self.__target_state_index = Target 
        elif isinstance(Target, tuple):  self.__scheme             = Target
        elif isinstance(Target, DoorID): self.__door_id            = Target # only by '.finalize()'
        else:                            assert False, Target.__class__.__name__

    def get_hash(self):
        if self.__hash is None: 
            if self.__target_state_index is not None: self.__hash = hash(self.__target_state_index)
            elif self.__scheme is not None:           self.__hash = hash(self.__scheme)
            else:                                     self.__hash = hash(self.__door_id)
        return self.__hash
    @property
    def scheme(self):              return self.__scheme
    @property
    def target_state_index(self):  return self.__target_state_index
    @property
    def target_door_id(self):      return self.__door_id
    @property
    def drop_out_f(self):          return self.__drop_out_f
    @property
    def scheme_id(self):           return self.__scheme_id

    def replace_door_ids(self, MapOldDoorIdToNewDoorId):
        """RETURNS: True  if there where internal replacements of door ids.
                    False if there was no replacement to be done.
        """
        if self.__target_state_index is not None: 
            return False

        elif self.__door_id is not None:
            new_door_id = MapOldDoorIdToNewDoorId.get(self.__door_id)
            if new_door_id is None: return False
            self.__door_id = new_door_id

        elif self.__scheme is not None:
            new_scheme = None
            for i, door_id in enumerate(self.__scheme):
                new_door_id  = MapOldDoorIdToNewDoorId.get(self.__door_id)
                if new_door_id is None: continue
                if new_scheme is None: new_scheme = list(self.__scheme)
                new_scheme[i] = new_door_id

            if new_scheme is None: return False

            self.__scheme = tuple(new_scheme)

        return True

    def finalize(self, TheMegaState, StateDB, scheme_db):
        """Once the whole state configuration and the states' entry doors are
        determined, the actual MegaState_Target object can be finalized.
        That is:
           
           -- A common target may become a scheme, if the DoorIDs differ
              depending on the 'from_state_index' (which is one of the
              .implemented_state_index_list()).

           -- A scheme may become a common target, if the target DoorID 
              is the same for all indices in .implemented_state_index_list().
        """
        if self.drop_out_f:
            return

        implemented_state_index_list = TheMegaState.implemented_state_index_list()
        L = len(implemented_state_index_list)
        assert L > 1

        def determine_scheme_id(scheme_db, Scheme):
            scheme_id = scheme_db.get(Scheme)
            if scheme_id is None: 
                scheme_id = len(scheme_db)
                scheme_db[Scheme] = scheme_id
            return scheme_id

        # NOTE: Due to the possible cover-up of parts of the transition map, it
        #       is possible that not all implemented states of a MegaState trigger
        #       to '.target_state_index' or the states mentioned in '.scheme'.
        #
        #       This results in '.get_door_id(To, From)' being 'None' sometimes. 
        #       This is not an error!
        if self.scheme is not None:
            assert len(self.scheme) == L
            # The targets in a 'scheme' may be implemented by the same MegaState--
            # with the CommandList at state entry. In this case, a target state
            # scheme translates into a common transition to target DoorID.
            prototype = None
            for state_index in implemented_state_index_list:
                state_key          = TheMegaState.map_state_index_to_state_key(state_index)
                target_state_index = self.scheme[state_key]

                if target_state_index != E_StateIndices.DROP_OUT:
                    # DROP_OUT cannot be in a scheme, if there was some non-DROP-OUT there.
                    # => Only give it a chance as long as no DROP_OUT target appears.
                    target_entry = StateDB[target_state_index].entry
                    door_id      = target_entry.action_db.get_door_id(target_state_index, state_index)
                    if   prototype is None:    prototype = door_id; continue
                    elif prototype == door_id: continue

                # The scheme is indeed not uniform => Stay with the scheme
                self.__scheme_id = determine_scheme_id(scheme_db, self.__scheme)
                return # Nothing to be done
            else:
                # All has been uniform => generate transition through common DoorID
                assert prototype is not None
                return MegaState_Target.create(prototype)

        elif self.target_state_index is not None:
            # The common target state may be entered by different doors
            # depending on the 'from_state' which is currently implemented by
            # the MegaState. Then, a common 'target_state_index' translates into 
            # a target scheme. DoorID's for each element are computed later
            # depending on the '.implemented_state_index_list'.
            target_entry = StateDB[self.target_state_index].entry
            prototype    = None
            for state_index in implemented_state_index_list:
                door_id   = target_entry.action_db.get_door_id(self.target_state_index, state_index)
                if prototype is None:      prototype = door_id; continue
                elif prototype == door_id: continue

                # The door_ids are not uniform => generate a scheme
                result = MegaState_Target.create((self.target_state_index,) * L)
                result.__scheme_id = determine_scheme_id(scheme_db, result.scheme)
                return result
            else:
                # All has been uniform => Stay with 'target_state_index'
                assert prototype is not None
                return # Nothing to be done
        else:
            pass

    def __repr__(self):
        if   self.drop_out_f:                     return "MegaState_Target:DropOut"
        elif self.target_state_index is not None: return "MegaState_Target:(%s)"       % repr(self.__target_state_index).replace("L", "")
        elif self.target_door_id is not None:     return "MegaState_Target:%s"         % repr(self.__door_id).replace("L", "")
        elif self.scheme is not None:             return "MegaState_Target:scheme(%s)" % repr(self.__scheme).replace("L", "")
        else:                                     return "MegaState_Target:<ERROR>"

    def __hash__(self):
        if   self.__drop_out_f:                     return 0
        elif self.__target_state_index is not None: return self.__target_state_index.state_index
        elif self.__scheme is not None:             return hash(self.__scheme)
        else:                                       assert False

    def __eq__(self, Other):
        if   isinstance(Other, MegaState_Target) == False: 
            return False
        elif self.__drop_out_f and Other.__drop_out_f: 
            return True
        elif self.__target_state_index is not None and Other.__target_state_index is not None:
            return self.__target_state_index == Other.__target_state_index
        elif self.__scheme  is not None and Other.__scheme  is not None:
            return self.__scheme == Other.__scheme
        else:
            return False
        ## if self.__scheme_id != Other.__scheme_id: return False
        return self.__scheme == Other.__scheme

# Globally unique object to stand up for all 'drop-outs'.
MegaState_Target_DROP_OUT      = MegaState_Target(E_StateIndices.DROP_OUT)

