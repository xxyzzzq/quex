from quex.engine.tools import typed

from quex.blackboard import E_PreContextIDs, \
                            E_IncidenceIDs, \
                            E_PostContextIDs

class SeCmd:
    def __init__(self):
        self.__acceptance_id = E_IncidenceIDs.MATCH_FAILURE

    def set_acceptance_id(self, PatternId):
        self.__acceptance_id = PatternId

    def acceptance_id(self):
        return self.__acceptance_id

    def _string_annotate(self, Str):
        if self.__acceptance_id == E_IncidenceIDs.MATCH_FAILURE: return Str
        return "%s%s" % (Str, self.__acceptance_id)

    def __eq__(self, Other):
        return self.__acceptance_id == Other.__acceptance_id

    def __ne__(self, Other):
        """This function implements '__ne__' for all derived classes. It relies
        on the possibly overwritten '__eq__' operator.
        """
        return not self.__eq__(self, Other)

class Accept(SeCmd):
    def __init__(self):
        SeCmd.__init__(self)
        self.__pre_context_id               = E_PreContextIDs.NONE
        self.__restore_position_register_f = False

    def clone(self, ReplDbPreContext=None, ReplDbAcceptance=None):
        result = Accept()
        if ReplDbAcceptance is None: result.set_acceptance_id(self.acceptance_id())
        else:                        result.set_acceptance_id(ReplDbAcceptance[self.acceptance_id()])
        if ReplDbPreContext is None: result.__pre_context_id = self.__pre_context_id
        else:                        result.__pre_context_id = ReplDbPreContext[self.__pre_context_id]
        result.__restore_position_register_f = self.__restore_position_register_f
        return result

    def set_pre_context_id(self, PatternId):
        self.__pre_context_id = PatternId

    def pre_context_id(self):
        return self.__pre_context_id

    def set_restore_position_register_f(self):
        self.__restore_position_register_f = True

    def restore_position_register_f(self):
        return self.__restore_position_register_f

    def __eq__(self, Other):
        if   not Other.__class__ == Accept:                       return False
        elif not SeCmd.__eq__(self, Other):                       return False
        elif not self.__pre_context_id == Other.__pre_context_id: return False
        return self.__restore_position_register_f == Other.__restore_position_register_f

    def __str__(self):
        acceptance_id_txt = ""
        pre_txt           = ""
        restore_txt       = ""
        if self.acceptance_id() != E_IncidenceIDs.MATCH_FAILURE:
            acceptance_id_txt = repr(self.acceptance_id()).replace("L", "")
        if self.__pre_context_id != E_PreContextIDs.NONE:            
            if self.__pre_context_id == E_PreContextIDs.BEGIN_OF_LINE:
                pre_txt = "pre=bol"
            else: 
                pre_txt = "pre=%s" % repr(self.__pre_context_id).replace("L", "")
        if self.__restore_position_register_f: 
            restore_txt = self._string_annotate("R")

        txt = [ x for x in (acceptance_id_txt, pre_txt, restore_txt) if x ]
        if txt: return "A(%s)" % reduce(lambda x, y: "%s,%s" % (x,y), txt)
        else:   return "A"

class StoreInputPosition(SeCmd):
    @typed(RegisterId=long)
    def __init__(self, RegisterId=E_PostContextIDs.NONE):
        SeCmd.__init__(self)
        self.__position_register_id = RegisterId

    def clone(self, ReplDbPreContext=None, ReplDbAcceptance=None):
        result = StoreInputPosition()
        if ReplDbAcceptance is None: result.set_acceptance_id(self.acceptance_id())
        else:                        result.set_acceptance_id(ReplDbAcceptance[self.acceptance_id()])
        result.__position_register_id = self.__position_register_id
        return result

    def __eq__(self, Other):
        if   Other.__class__ != StoreInputPosition: return False
        elif not SeCmd.__eq__(self, Other):         return False
        return self.__position_register_id == Other.__position_register_id

    def __str__(self):
        return self._string_annotate("S")

class SingleEntry(object):
    __slots__ = ('__list')

    def __init__(self, CloneF=False):
        if not CloneF: self.__list = []

    @staticmethod
    def from_iterable(Iterable):
        result = SingleEntry()
        result.set(Iterable)
        return result

    def clone(self, ReplDbPreContext=None, ReplDbAcceptance=None):
        return SingleEntry.from_iterable(x.clone(ReplDbPreContext=ReplDbPreContext, ReplDbAcceptance=ReplDbAcceptance) for x in self.__list)

    def get_list(self):
        return self.__list

    @typed(Cmd=SeCmd)
    def add(self, Cmd):
        self.__list.append(Cmd.clone())

    def find(self, CmdClass):
        for cmd in self.__list:
            if cmd.__class__ == CmdClass: return cmd
        return None

    def get_iterable(self, CmdClass):
        for cmd in self.__list:
            if cmd.__class__ == CmdClass: yield cmd
        
    def add_Cmd(self, CmdClass):
        cmd = self.find(CmdClass)
        if cmd is not None: return
        self.__list.append(CmdClass())

    def remove_Cmd(self, CmdClass):
        L = len(self.__list)
        for i in xrange(L-1, -1, -1):
            cmd = self.__list[i]
            if cmd.__class__ == CmdClass: del self.__list[i]

    def has_acceptance_id(self, AcceptanceID):
        for cmd in self:
            if cmd.__class__ == Accept and cmd.acceptance_id() == AcceptanceID:
                return True
        return False

    def has_begin_of_line_pre_context(self):
        for cmd in self:
            if cmd.__class__ == Accept and cmd.pre_context_id() == E_PreContextIDs.BEGIN_OF_LINE:
                return True
        return False

    def has(self, Cmd):
        for candidate in self.__list:
            if candidate == Cmd: return True
        return False

    def hopcroft_combinability_key(self):
        """Two states have the same hopcroft-combinability key, if and only if
        they are combinable during the initial state split in the hopcroft
        minimization. Criteria:
        
        (1) Acceptance states of a different origin constellation. The
            decision making about the winning pattern must be the same for all
            states of a state set that is possibly combined into one single
            state. 
        
            In particular, non-acceptance states can never be combined with
            acceptance states.
        
        (2) Two states of the same pattern where one stores the input position
            and the other not, cannot be combined. Otherwise, the input
            position would be stored in unexpected situations.

        The approach is the following: For each investigated behavior a a tuple
        of numbers can be derived that describes it uniquely. The tuple of all
        tuples is used during the hopcroft minimization to distinguish between
        combinable states and those that are not.
        """
        def acceptance_info():
            """Before the track analysis, the acceptance in a state is simple
            given by its precedence, i.e. its acceptance id. Thus, the sorted
            sequence of acceptance ids identifies the acceptance behavior.
            """
            return tuple(sorted(x.acceptance_id() 
                                for x in self if x.__class__ == Accept))

        # (2) Separate by Store-Input-Position Behavior
        def store_info():
            """The storing of input positions in registers is independent of its
            position in the command list (as long as it all happens before the increment
            of the input pointer, of course).

            The sorted list of position storage registers where positions are stored
            is a distinct description of the position storing behavior.
            """
            return tuple(sorted(x.acceptance_id() 
                                for x in self if x.__class__ == StoreInputPosition))

        result = (acceptance_info(), store_info())
        return result

    def merge(self, Other):
        assert isinstance(Other, SingleEntry)
        self.__list.extend(
            cmd.clone() for cmd in Other.__list if not self.has(cmd)
        )

    def merge_list(self, CmdIterableIterable):
        for origin_iterable in CmdIterableIterable:
            self.merge(origin_iterable)

    def set(self, CmdList, ArgumentIsYoursF=False):
        if ArgumentIsYoursF: 
            assert type(CmdList) == list
            self.__list = CmdList
        else:                
            self.__list = [ cmd.clone() for cmd in CmdList ]

    def clear(self):
        self.__list = []

    def delete_dominated(self):
        """Simplification to make Hopcroft Minimization more efficient. The first unconditional
        acceptance makes any lower priorized acceptances meaningless. 

        This function is to be seen in analogy with the function 'get_acceptance_detector'. 
        Except for the fact that it requires the 'end of core pattern' markers of post
        conditioned patterns. If the markers are not set, the store input position commands
        are not called properly, and when restoring the input position bad bad things happen 
        ... i.e. segmentation faults.
        """
        # NOTE: Acceptance origins sort before non-acceptance origins
        min_acceptance_id = None
        for cmd in (x for x in self.__list if x.__class__ == Accept):
            if min_acceptance_id is None or min_acceptance_id > cmd.acceptance_id():
                min_acceptance_id = cmd.acceptance_id()

        # Delete any Accept command where '.acceptance_id() > min_acceptance_id'
        L = len(self.__list) 
        for i in xrange(L-1, -1, -1):
            cmd = self.__list[i]
            if cmd.__class__ == Accept and cmd.acceptance_id() > min_acceptance_id:
                del self.__list[i]

    def get_string(self, CmdalStatesF=True):
        if   not self.__list:       return "\n"
        elif len(self.__list) == 1: return "%s\n" % self.__list[0]

        def key(X):
            if   X.__class__ == Accept:              
                return (0, X.acceptance_id(), X.pre_context_id(), X.restore_position_register_f())
            elif X.__class__ == StoreInputPosition: 
                return (1, X.acceptance_id())

        return reduce(lambda x, y: "%s, %s" % (x, y), sorted(self.__list, key=key))

    def take_out_FAILURE(self):
        L = len(self.__list)
        for i in xrange(L-1, -1, -1):
            if self.__list[i].acceptance_id() == E_IncidenceIDs.MATCH_FAILURE:
                del self.__list[i]

    def is_there_a_non_FAILURE(self):
        for origin in self.__list:
            if origin.acceptance_id() != E_IncidenceIDs.MATCH_FAILURE:
                return True
        return False

    def __iter__(self):
        for x in self.__list:
            yield x

    def __len__(self):
        return len(self.__list)

