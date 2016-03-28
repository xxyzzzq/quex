from   quex.engine.misc.tools                import typed
from   quex.engine.analyzer.terminal.factory import TerminalFactory
import quex.engine.misc.error                as     error
from   quex.input.code.base                  import CodeFragment, \
                                                    SourceRef_DEFAULT
from   quex.input.code.core                  import CodeTerminal
from   quex.blackboard import standard_incidence_db, \
                              standard_incidence_db_get_name, \
                              standard_incidence_db_is_mandatory, \
                              standard_incidence_db_get_terminal_type, \
                              standard_incidence_db_is_immutable, \
                              E_IncidenceIDs, \
                              E_TerminalType


class IncidenceDB(dict):
    """Database of CodeFragments related to 'incidences'.
    ---------------------------------------------------------------------------

                      incidence_id --> [ CodeFragment ]

    If the 'mode_option_info_db[option_name]' mentions that there can be 
    no multiple definitions or if the options can be overwritten than the 
    list of OptionSetting-s must be of length '1' or the list does not exist.

    ---------------------------------------------------------------------------
    """
    # When webbed into a state machine, certain incidences may not be changed, 
    # because their address is used all over the place.

    @staticmethod
    def from_BaseModeSequence(BaseModeSequence):
        """Collects the content of the 'incidence_db' member of this mode and
        its base modes. Incidence handlers can only defined ONCE in a mode
        hierarchy.

        RETURNS:      map:    incidence_id --> [ CodeFragment ]
        """
        def find_in_mode_hierarchy(BaseModeSequence, incidence_name):
            """Find incidence handler in the mode hierarchy. An incidence handler
            can only be defined once. If none is found 'None' is returned.
            """
            found      = None
            found_mode = None
            for mode_descr in BaseModeSequence:
                code_fragment = mode_descr.incidence_db.get(incidence_name)
                if code_fragment is None:         
                    continue
                elif found is not None:
                    error.log("Second definition of incidence handler '%s' in mode '%s'." \
                              % (incidence_name, mode_descr.name), code_fragment.sr, DontExitF=True)
                    error.log("First, defined in mode '%s'." % found_mode, found.sr)
                else:
                    found = code_fragment
                    found_mode = mode_descr.name
            return found

        def ensure_implementation_of_mandatory(IncidenceId, Code, ModeName):
            """If IncidenceId relates to a mandatory incidence handler, and
            'Code' is not defined by the user, refer to the default 
            implementation.
            """
            if   Code is not None:                                    return Code
            elif not standard_incidence_db_is_mandatory(IncidenceId): return Code

            return IncidenceDB.__default_code_fragment(incidence_id, ModeName)

        assert len(BaseModeSequence) > 0
        mode_name = BaseModeSequence[-1].name
        result    = IncidenceDB()

        # Collect all possible incidence handlers.
        for incidence_name, info in standard_incidence_db.iteritems():

            # (1) Find handler definition in base mode sequence
            code = find_in_mode_hierarchy(BaseModeSequence, incidence_name)

            # (2) Add default handler for undefined mandatory handlers
            incidence_id, comment = info
            code = ensure_implementation_of_mandatory(incidence_id, code, mode_name)

            # (3) Add incidence handler to result database
            if code is None: continue

            result[incidence_id] = code

        return result

    def __setitem__(self, Key, Value):
        dict.__setitem__(self, Key, Value)

    @staticmethod
    def __default_code_fragment(IncidenceId, ModeName):

        if IncidenceId == E_IncidenceIDs.END_OF_STREAM:
            txt = 'self_send(__QUEX_SETTING_TOKEN_ID_TERMINATION);\n'
                # NOT: "Lng.PURE_RETURN" because the terminal end of stream 
                #      exits anyway immediately--after 'on_after_match'.
            return CodeFragment(txt, SourceRef_DEFAULT)

        handler_name = standard_incidence_db_get_name(IncidenceId)
        note_txt     = 'The \'%s\' handler has not been specified.' % handler_name

        msg = {
            E_IncidenceIDs.MATCH_FAILURE:
                'Match failure, no pattern matched!', 
            E_IncidenceIDs.SKIP_RANGE_OPEN:
                'End of file occurred before closing skip range delimiter!',
            E_IncidenceIDs.INDENTATION_BAD:
                'Bad indentation character detected!',
            E_IncidenceIDs.BAD_LEXATOM:
                'Bad lexatom (character encoding error) detected!',
            E_IncidenceIDs.LOAD_FAILURE:
                'General failure while loading buffer.',
            E_IncidenceIDs.OVERFLOW:
                'Lexeme exceeds buffer size.',
        }[IncidenceId]
            
        txt =   'QUEX_ERROR_EXIT("\\nMode \'%s\': %s\\n"\n' % (ModeName, msg) \
              + '                "%s\\n");' % note_txt

        return CodeFragment(txt, SourceRef_DEFAULT)

    @typed(factory=TerminalFactory)
    def extract_terminal_db(self, factory, ReloadRequiredF):
        """SpecialTerminals: END_OF_STREAM
                             FAILURE
                             BAD_LEXATOM
                             ...
        """
        result = {}
        for incidence_id, code_fragment in self.iteritems():
            terminal_type = standard_incidence_db_get_terminal_type(incidence_id)
            if terminal_type is None:
                continue
            elif   incidence_id == E_IncidenceIDs.END_OF_STREAM \
               and not ReloadRequiredF:
                continue
            code_terminal = CodeTerminal.from_CodeFragment(code_fragment)
            assert terminal_type not in result
            terminal = factory.do(terminal_type, code_terminal)
            terminal.set_incidence_id(incidence_id)
            result[incidence_id] = terminal

        return result

    def get_CodeTerminal(self, IncidenceId):
        if IncidenceId not in self: return CodeTerminal([""])

        return CodeTerminal.from_CodeFragment(self[IncidenceId], 
                                              LexemeRelevanceF=True)

    def get_text(self, IncidenceId):
        code_fragment = self.get(IncidenceId)
        if code_fragment is None: return ""
        else:                     return "".join(code_fragment.get_code())

    def default_indentation_handler_f(self):
        return not (   self.has_key(E_IncidenceIDs.INDENTATION_ERROR) \
                    or self.has_key(E_IncidenceIDs.INDENTATION_INDENT)   \
                    or self.has_key(E_IncidenceIDs.INDENTATION_DEDENT)   \
                    or self.has_key(E_IncidenceIDs.INDENTATION_N_DEDENT) \
                    or self.has_key(E_IncidenceIDs.INDENTATION_NODENT))

