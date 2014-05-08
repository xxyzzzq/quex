from   quex.engine.analyzer.commands.core         import repr_acceptance_id, \
                                                         repr_pre_context_id, \
                                                         repr_positioning, \
                                                         Accepter, \
                                                         Router, \
                                                         Command, \
                                                         CommandList, \
                                                         IfPreContextSetPositionAndGoto
from   quex.engine.analyzer.door_id_address_label import DoorID
from   quex.engine.tools                          import typed, E_Values
from   quex.blackboard                            import E_PreContextIDs, \
                                                         E_IncidenceIDs, \
                                                         E_TransitionN, \
                                                         E_Cmd
from   itertools                                  import ifilter, imap

class DropOut(object):
    """The general drop-out of a state has the following two 'sub-tasks'

                /* (1) Check pre-contexts to determine acceptance */
                if     ( pre_context_4_f ) acceptance = 26;
                else if( pre_context_3_f ) acceptance = 45;
                else if( pre_context_8_f ) acceptance = 2;
                else                       acceptance = last_acceptance;

                /* (2) Route to terminal / position input pointer. */
                switch( acceptance ) {
                case 2:  input_p -= 10; goto TERMINAL_2;
                case 15: input_p  = post_context_position[4]; goto TERMINAL_15;
                case 26: input_p  = post_context_position[3]; goto TERMINAL_26;
                case 45: input_p  = last_acceptance_position; goto TERMINAL_45;
                }

       The first sub-task is described by the member '.access_accepter' which is a list
       of objects of class 'AcceptanceCheckerElement'. An empty list means that
       there is no check and the acceptance has to be restored from 'last_acceptance'.
       
       The second sub-task is described by member '.terminal_router' which is a list of 
       objects of class 'TerminalRouterElement'.

       The exact content of both lists is determined by analysis of the acceptance
       trances.

       NOTE: This type supports being a dictionary key by '__hash__' and '__eq__'.
             Required for the optional 'template compression'.
    """
    __slots__ = ("__list", "_hash")

    def __init__(self, TheAccepter=None, TheTerminalRouter=None):
        if TheAccepter is None and TheTerminalRouter is None:
            self.__list = CommandList()
        else:
            cl = self.__trivialize(TheAccepter, TheTerminalRouter)
            self.__list = CommandList.from_iterable(cl)

    def has_accepter(self):
        return self.access_accepter() is not None

    def access_accepter(self):
        """RETURN: None, if accepter has been disabled. 

        A disabled accepter means, that acceptance is derived solely from 
        'last_acceptance'.
        """
        for cmd in self.__list:
            if cmd.id == E_Cmd.Accepter: return cmd.content
        return None

    def replace_position_registers(self, PositionRegisterMap):
        self.__list.replace_position_registers(PositionRegisterMap)

    def get_command_list(self):
        return self.__list

    def cost(self):
        return self.__list.cost()

    def __hash__(self):
        return hash(self.__list)

    def __eq__(self, Other):
        if Other.__class__  != self.__class__: return False
        return self.__list == Other.__list

    def __ne__(self, Other):
        return not (self == Other)

    def __trivialize(self, TheAccepter, TheTerminalRouter):
        """If there is no stored acceptance involved, then one can directly
        conclude from the pre-contexts to the acceptance_id. Then the drop-
        out action can be described as a sequence of checks

           # [0] Check          [1] Position and Goto Terminal
           if   pre_context_32: input_p = x; goto terminal_893;
           elif pre_context_32: goto terminal_893;
           elif pre_context_32: input_p = x; goto terminal_893;
           elif pre_context_32: goto terminal_893;

        Such a configuration is considered trivial. No restore is involved.

        RETURNS: None                                          -- if not trivial
                 list((pre_context_id, TerminalRouterElement)) -- if trivial
        """
        # If the 'last_acceptance' is not determined in this state, then it
        # must be derived from previous storages. We cannot simplify here.
        if TheAccepter is None: 
            return (TheTerminalRouter,)
        elif not TheAccepter.content.has_acceptance_without_pre_context():
            # If no pre-context is met, then 'last_acceptance' needs to be 
            # considered.
            return (TheAccepter, TheTerminalRouter)

        def router_element(TerminalRouter, AcceptanceId):
            for x in TerminalRouter:
                if x.acceptance_id == AcceptanceId: return x
            assert False  # There MUST be an element for each acceptance_id!

        router = TheTerminalRouter.content
        return [
            IfPreContextSetPositionAndGoto(check.pre_context_id, 
                                           router_element(router, check.acceptance_id))
            for check in TheAccepter.content
        ]

    def __repr__(self):
        return "".join(str(cmd) for cmd in self.__list)

class DropOutGotoDoorId(object):
    @typed(DoorId=DoorID)
    def __init__(self, DoorId):
        self.door_id = DoorId

class DropOutIndifferent(DropOut):
    def __init__(self):
        DropOut.__init__(self)
        pass

    def replace_position_registers(self, PositionRegisterMap):
        pass

    def __repr__(self):
        return "    goto CheckTerminated;"

class DropOutBackwardInputPositionDetection(DropOut):
    __slots__ = ("__reachable_f")
    def __init__(self, AcceptanceF):
        """A non-acceptance drop-out can never be reached, because we walk a 
           path backward, that we walked forward before.
        """
        self.__reachable_f = AcceptanceF

    def replace_position_registers(self, PositionRegisterMap):
        pass

    @property
    def reachable_f(self):         return self.__reachable_f

    def __hash__(self):            
        return self.__reachable_f
    def __eq__(self, Other):       
        if not isinstance(Other, DropOutBackwardInputPositionDetection): return False
        return self.__reachable_f == Other.__reachable_f
    def __repr__(self):
        if not self.__reachable_f: return "<unreachable>"
        else:                      return "<backward input position detected>"

