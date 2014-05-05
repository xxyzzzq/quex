from   quex.engine.analyzer.commands.core         import repr_acceptance_id, \
                                                         repr_pre_context_id, \
                                                         repr_positioning, \
                                                         Accepter, \
                                                         Router, \
                                                         IfPreContextSetPositionAndGoto
from   quex.engine.analyzer.door_id_address_label import DoorID
from   quex.engine.tools                          import typed, print_callstack
from   quex.blackboard                            import E_PreContextIDs, \
                                                         E_IncidenceIDs, \
                                                         E_TransitionN
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
    __slots__ = ("_accepter", "_terminal_router", "_hash")

    def __init__(self):
        self._hash            = None
        self._accepter        = -1    # -1: Virginity!; None: disabled
        self._terminal_router = Router()

    def access_accepter(self):
        """RETURN: None, if accepter has been disabled. 

        A disabled accepter means, that acceptance is derived solely from 
        'last_acceptance'.
        """
        assert self._accepter != -1 # Cannot be virgin!
        return self._accepter.content

    def accepter_disable(self):
        self._accepter = None

    def accepter_enable(self):
        """Enable the accepter. If the accepter has been disabled explicitly,
        then it cannot be enabled any more.
        """
        if   self._accepter is None: return False
        elif self._accepter == -1:   self._accepter = Accepter()
        return True

    def accepter_add(self, PreContextID, AcceptanceID):
        assert self._accepter is not None
        self._accepter.content.add(PreContextID, AcceptanceID)
        self._hash = None

    def terminal_router(self):
        return self._terminal_router.content

    def terminal_router_add(self, AcceptanceID, TransitionNSincePositioning):
        self._terminal_router.content.add(AcceptanceID, TransitionNSincePositioning)
        self._hash = None

    def terminal_router_replace(self, PositionRegisterMap):
        self._terminal_router.content.replace(PositionRegisterMap)

    def get_command_list(self):
        assert self._accepter != -1
        trivial_solution = self.trivialize()
        if trivial_solution is None:
            if self._accepter is not None:
                return [ self._accepter, self._terminal_router ]
            else:
                return [ self._terminal_router ]
        else:
            assert len(trivial_solution) != 0
            return [ 
                IfPreContextSetPositionAndGoto(x.pre_context_id, router_content_element)
                for x, router_content_element in trivial_solution
            ]

    def __hash__(self):
        if self._hash is None:
            h = 0x5A5A5A5A
            for x in self._accepter.content:
                h ^= hash(x.pre_context_id) ^ hash(x.acceptance_id)
            for x in self._terminal_router.content:
                h ^= hash(x.positioning) ^ hash(x.acceptance_id)
            self._hash = h
        return self._hash

    def __eq__(self, Other):
        if   not isinstance(Other, DropOut):                                     return False
        elif self._accepter.content        != Other._accepter.content:         return False
        elif self._terminal_router.content != Other._terminal_router.content:  return False
        else:                                                                    return True

    def __ne__(self, Other):
        return not (self == Other)

    def trivialize(self):
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
        if self._accepter is None: # Dependence on 'last_acceptance'
            return None

        result = []
        for check in self._accepter.content:
            for router_element in self._terminal_router.content:
                if router_element.acceptance_id == check.acceptance_id: break
            else:
                assert False # check.acceptance_id must be mentioned in self._terminal_router
            result.append((check, router_element))
            # NOTE: "if check.pre_context_id is None: break" is not necessary since 
            #       get_drop_out_object() makes sure that the acceptance_checker stops after i
            #       the first non-pre-context drop-out.

        return result

    def __repr__(self):
        if len(self._accepter.content) == 0 and len(self._terminal_router.content) == 0:
            return "    <unreachable code>"

        info = self.trivialize()
        if info is not None:
            if len(info) == 2 and info[0] is None:
                return "    goto PreContextCheckTerminated;"
            else:
                txt = []
                if_str = "if"
                for easy in info:
                    if easy[0].pre_context_id == E_PreContextIDs.NONE:
                        txt.append("    %s goto %s;\n" % \
                                   (repr_positioning(easy[1].positioning, easy[1].position_register),
                                    repr_acceptance_id(easy[1].acceptance_id)))
                    else:
                        txt.append("    %s %s: %s goto %s;\n" % \
                                   (if_str,
                                    repr_pre_context_id(easy[0].pre_context_id),
                                    repr_positioning(easy[1].positioning, easy[1].position_register),
                                    repr_acceptance_id(easy[1].acceptance_id)))
                        if_str = "else if"
                return "".join(txt)

        txt = ["    Checker:\n"]
        if_str = "if     "
        for element in self._accepter.content:
            if element.pre_context_id != E_PreContextIDs.NONE:
                txt.append("        %s %s\n" % (if_str, repr(element)))
            else:
                txt.append("        accept = %s\n" % repr_acceptance_id(element.acceptance_id))
                # No check after the unconditional acceptance
                break

            if_str = "else if"

        txt.append("    Router:\n")
        for element in self._terminal_router.content:
            txt.append("        %s\n" % repr(element))

        return "".join(txt)

class DropOutGotoDoorId(object):
    @typed(DoorId=DoorID)
    def __init__(self, DoorId):
        self.door_id = DoorId

class DropOutIndifferent(DropOut):
    def __init__(self):
        DropOut.__init__(self)
        pass

    def terminal_router_replace(self, PositionRegisterMap):
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

    def terminal_router_replace(self, PositionRegisterMap):
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

