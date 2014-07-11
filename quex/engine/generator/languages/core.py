# PURPOSE: Providing a database for code generation in different programming languages.
#          A central object 'db' contains for each keyword, such as '$if' '$else' a correspondent
#          keyword or sequence that corresponds to it in the given language. Some code
#          elements are slighly more complicated. Therefore the db returns for some keywords
#          a function that generates the correspondent code fragment.
# 
# NOTE: The language of reference is C++. At the current state the python code generation 
#       is only suited for unit test of state transitions, no state machine code generation.
#       Basics for other languages are in place (VisualBasic, Perl, ...) but no action has been
#       taken to seriously implement them.
#
# AUTHOR: Frank-Rene Schaefer
# ABSOLUTELY NO WARRANTY
#########################################################################################################
import quex.engine.generator.languages.cpp               as     cpp
from   quex.engine.generator.code.base                   import SourceRef, \
                                                                CodeFragment
from   quex.engine.analyzer.state.core                   import Processor
from   quex.engine.analyzer.commands.core                import E_R, \
                                                                RouterContentElement
from   quex.engine.analyzer.mega_state.template.state    import TemplateState
from   quex.engine.analyzer.mega_state.path_walker.state import PathWalkerState
from   quex.engine.analyzer.door_id_address_label        import DoorID, \
                                                                dial_db, \
                                                                get_plain_strings, \
                                                                IfDoorIdReferencedCode
from   quex.engine.misc.string_handling                  import blue_print, \
                                                                pretty_code
from   quex.engine.misc.file_in                          import open_file_or_die, \
                                                                write_safely_and_close
from   quex.engine.tools import typed, \
                                none_isinstance
from   quex.blackboard   import setup as Setup, \
                                E_StateIndices,  \
                                E_IncidenceIDs, \
                                E_InputActions,  \
                                E_TransitionN,   \
                                E_PreContextIDs, \
                                E_Cmd
from   copy      import copy
from   itertools import islice
from   math      import log
import re

#________________________________________________________________________________
# C++
#    
CppBase = {
    "$indentation_add":          cpp.__indentation_add,
    "$indentation_check_space":  cpp.__indentation_check_whitespace,
    #
    "$frame":                   cpp.__frame_of_all,
    "$code_base":               "/quex/code_base/",
    "$token-default-file":      "/token/CppDefault.qx",
    "$token_template_file":     "/token/TXT-Cpp",
    "$token_template_i_file":   "/token/TXT-Cpp.i",
    "$analyzer_template_file":  "/analyzer/TXT-Cpp",
    "$file_extension":          ".cpp",
}

class Lng_Cpp(dict):
    #------------------------------------------------------------------------------
    # Define Regular Expressions
    #------------------------------------------------------------------------------
    Match_input                 = re.compile("\\binput\\b", re.UNICODE)
    Match_iterator              = re.compile("\\iterator\\b", re.UNICODE)
    Match_Lexeme                = re.compile("\\bLexeme\\b", re.UNICODE)
    Match_LexemeBegin           = re.compile("\\bLexemeBegin\\b", re.UNICODE)
    Match_goto                  = re.compile("\\bgoto\\b", re.UNICODE)
    Match_QUEX_GOTO_RELOAD      = re.compile("\\bQUEX_GOTO_RELOAD_", re.UNICODE)
    Match_string                = re.compile("\\bstring\\b", re.UNICODE) 
    Match_vector                = re.compile("\\bvector\\b", re.UNICODE) 
    Match_map                   = re.compile("\\bmap\\b", re.UNICODE)


    def __init__(self, DB):      
        self.update(DB)
        self.__analyzer                                   = None
        self.__code_generation_switch_cases_add_statement = None
        self.__code_generation_reload_label               = None
        self.__code_generation_on_reload_fail_adr         = None
        self.__state_machine_identifier                   = None

    def register_analyzer(self, TheAnalyzer):
        self.__analyzer = TheAnalyzer

    def unregister_analyzer(self):
        # Unregistering an analyzer ensures that no one else works with the 
        # analyzer on something unrelated.
        self.__analyzer = None

    def code_generation_switch_cases_add_statement(self, Value):
        assert Value is None or self.__code_generation_switch_cases_add_statement is None
        self.__code_generation_switch_cases_add_statement = Value

    def code_generation_reload_label_set(self, Value):
        assert Value is None or self.__code_generation_reload_label is None
        self.__code_generation_reload_label = Value

    def code_generation_on_reload_fail_adr_set(self, Value):
        assert Value is None or self.__code_generation_on_reload_fail_adr is None
        self.__code_generation_on_reload_fail_adr = Value

    def set_state_machine_identifier(self, SM_Id):
        self.__state_machine_identifier = SM_Id

    @property
    def analyzer(self):
        return self.__analyzer

    def _get_log2_if_power_of_2(self, X):
        assert type(X) != tuple
        if not isinstance(X, (int, long)):
            return None

        log2 = log(X, 2)
        if not log2.is_integer(): return None
        return int(log2)
            
    def __getattr__(self, Attr): 
        # Thanks to Rami Al-Rfou' who mentioned that this is the only thing to 
        # be adapted to be compliant with current version of PyPy.
        try:             return self[Attr] 
        except KeyError: raise AttributeError

    PURE_RETURN             = "__QUEX_PURE_RETURN;"
    UNREACHABLE             = "__quex_assert_no_passage();"
    ELSE                    = "} else {\n"

    PATH_ITERATOR_INCREMENT  = "++(path_iterator);"
    BUFFER_LIMIT_CODE        = "QUEX_SETTING_BUFFER_LIMIT_CODE"
    STATE_LABEL_VOID         = "QUEX_GOTO_LABEL_VOID"
    COMMENT_DELIMITERS       = [["/*", "*/", ""], ["//", "\n", ""], ["\"", "\"", "\\\""]]
    def LEXEME_START_SET(self, PositionStorage=None):
        if PositionStorage is None: return "me->buffer._lexeme_start_p = me->buffer._input_p;"
        else:                       return "me->buffer._lexeme_start_p = %s;" % PositionStorage
    def LEXEME_START_P(self):                      return "me->buffer._lexeme_start_p"
    def LEXEME_LENGTH(self):                       return "((size_t)(me->buffer._input_p - me->buffer._lexeme_start_p))"

    def LEXEME_MACRO_SETUP(self):
        return blue_print(cpp.lexeme_macro_setup, [
            ["$$LEXEME_LENGTH$$",  self.LEXEME_LENGTH()],
            ["$$INPUT_P$$",        self.INPUT_P()],
        ])

    def LEXEME_MACRO_CLEAN_UP(self):
        return cpp.lexeme_macro_clean_up

    def CHARACTER_BEGIN_P(self):                   return "character_begin_p"
    def INPUT_P(self):                             return "me->buffer._input_p"
    def INPUT_P_INCREMENT(self):                   return "++(me->buffer._input_p);"
    def INPUT_P_DECREMENT(self):                   return "--(me->buffer._input_p);"
    def INPUT_P_ADD(self, Offset):                 return "QUEX_NAME(Buffer_input_p_add_offset)(&me->buffer, %i);" % Offset
    def INPUT_P_TO_LEXEME_START(self):             return "me->buffer._input_p = me->buffer._lexeme_start_p;"
    def INPUT_P_TO_TEXT_END(self):                 return "me->buffer._input_p = (me->buffer._end_of_file_p != (void*)0) ? me->buffer._end_of_file_p : me->buffer._memory._back;"
    def INPUT_P_DEREFERENCE(self, Offset=0): 
        if Offset == 0:  return "*(me->buffer._input_p)"
        elif Offset > 0: return "*(me->buffer._input_p + %i)" % Offset
        else:            return "*(me->buffer._input_p - %i)" % - Offset
    def LEXEME_TERMINATING_ZERO_SET(self, RequiredF):
        if not RequiredF: return ""
        return "QUEX_LEXEME_TERMINATING_ZERO_SET(&me->buffer);\n"
    def INDENTATION_HANDLER_CALL(self, DefaultF, ModeName):
        if DefaultF: prefix = ""
        else:        prefix = "%s_" % ModeName
        return "    QUEX_NAME(%son_indentation)(me, me->counter._column_number_at_end, LexemeNull);\n" % prefix
    def STORE_LAST_CHARACTER(self, BeginOfLineSupportF):
        if not BeginOfLineSupportF: return ""
        # TODO: The character before lexeme start does not have to be written
        # into a special register. Simply, make sure that '_lexeme_start_p - 1'
        # is always in the buffer. This may include that on the first buffer
        # load '\n' needs to be at the beginning of the buffer before the
        # content is loaded. Not so easy; must be carefully approached.
        return "    %s\n" % self.ASSIGN("me->buffer._character_before_lexeme_start", 
                                        self.INPUT_P_DEREFERENCE(-1))

    def DEFINE(self, NAME, VALUE):
        return "#define %s %s\n" % (NAME, VALUE)

    def UNDEFINE(self, NAME):
        return "\n#undef %s\n" % NAME

    @typed(Txt=(CodeFragment))
    def SOURCE_REFERENCED(self, Cf, PrettyF=False):
        if not PrettyF: text = Cf.get_text()
        else:           text = "".join(pretty_code(Cf.get_code()))

        return "%s%s%s" % (
            self._SOURCE_REFERENCE_BEGIN(Cf.sr),
            text,
            self._SOURCE_REFERENCE_END(Cf.sr)
        )

    def _SOURCE_REFERENCE_BEGIN(self, SourceReference):
        """Return a code fragment that returns a source reference pragma. If 
        the source reference is void, no pragma is required. 
        """
        if not SourceReference.is_void(): 
            norm_file_name = Setup.get_file_reference(SourceReference.file_name) 
            line_n = SourceReference.line_n
            if   line_n <= 0:     line_n = 1
            elif line_n >= 2**31: line_n = 2**31 - 1
            return '\n#   line %i "%s"\n' % (line_n, norm_file_name) 
        else:
            return ""

    def _SOURCE_REFERENCE_END(self, SourceReference=None):
        """Return a code fragment that returns a source reference pragma which
        tells about the file where the code has been pasted. If the SourceReference
        is provided, it may be checked wether the 'return pragma' is necessary.
        If not, an empty string is returned.
        """
        if SourceReference is None or not SourceReference.is_void(): 
            return '\n<<<<LINE_PRAGMA_WITH_CURRENT_LINE_N_AND_FILE_NAME>>>>\n'
        else:
            return ""

    def NAMESPACE_OPEN(self, NameList):
        return "".join(("    " * i + "namespace %s {\n" % name) for i, name in enumerate(NameList))
    def NAMESPACE_CLOSE(self, NameList):
        return "".join("} /* Closing Namespace '%s' */\n" % name for name in NameList)
    def NAMESPACE_REFERENCE(self, NameList):
        return reduce(lambda x, y: x + "::" + y, [""] + NameList) + "::"
    def COMMENT(self, Comment):
        """Eliminated Comment Terminating character sequence from 'Comment'
           and comment it into a single line comment.
           For compatibility with C89, we use Slash-Star comments only, no '//'.
        """
        comment = Comment.replace("/*", "SLASH_STAR").replace("*/", "STAR_SLASH")
        return "/* %s */\n" % comment

    def ML_COMMENT(self, Comment, IndentN=4):
        indent_str = " " * IndentN
        comment = Comment.replace("/*", "SLASH_STAR").replace("*/", "STAR_SLASH").replace("\n", "\n%s * " % indent_str)
        return "%s/* %s\n%s */\n" % (indent_str, comment, indent_str)

    def COMMENT_STATE_MACHINE(self, txt, SM):
        txt.append(self.ML_COMMENT(
                        "BEGIN: STATE MACHINE\n"        + \
                        SM.get_string(NormalizeF=False) + \
                        "END: STATE MACHINE")) 

    def DEFAULT_COUNTER_FUNCTION_NAME(self, ModeName):
        return "QUEX_NAME(%s_counter)" % ModeName

    def DEFAULT_COUNTER_CALL(self):
        return "__QUEX_COUNT_VOID(&self, LexemeBegin, LexemeEnd);\n"

    def DEFAULT_COUNTER_PROLOG(self, FunctionName):
        return "#ifdef      __QUEX_COUNT_VOID\n"                             \
               "#   undef   __QUEX_COUNT_VOID\n"                             \
               "#endif\n"                                                    \
               "#ifdef      __QUEX_OPTION_COUNTER\n"                         \
               "#    define __QUEX_COUNT_VOID(ME, BEGIN, END) \\\n"          \
               "            do {                              \\\n"          \
               "                %s((ME), (BEGIN), (END));     \\\n"          \
               "                __quex_debug_counter();       \\\n"          \
               "            } while(0)\n"                                    \
               "#else\n"                                                     \
               "#    define __QUEX_COUNT_VOID(ME, BEGIN, END) /* empty */\n" \
               "#endif\n"                                                    \
               % FunctionName

    @typed(TypeStr=(str,unicode), MaxTypeNameL=(int,long), VariableName=(str,unicode))
    def CLASS_MEMBER_DEFINITION(self, TypeStr, MaxTypeNameL, VariableName):
        return "    %s%s %s;" % (TypeStr, " " * (MaxTypeNameL - len(TypeStr)), VariableName)

    def REGISTER_NAME(self, Register):
        return {
            E_R.InputP:          "(me->buffer._input_p)",
            E_R.Column:          "(me->counter._column_number_at_end)",
            E_R.Line:            "(me->counter._line_number_at_end)",
            E_R.LexemeStartP:    "(me->buffer._lexeme_start_p)",
            E_R.CharacterBeginP: "character_begin_p",
            E_R.ReferenceP:      "reference_p",
            E_R.LexemeEnd:       "LexemeEnd",
        }[Register]

    def COMMAND_LIST(self, CmdList):
        return [self.COMMAND(cmd) for cmd in CmdList]

    def COMMAND(self, Cmd):
        if Cmd.id == E_Cmd.Accepter:
            else_str = ""
            txt      = []
            for element in Cmd.content:
                if element.pre_context_id == E_PreContextIDs.BEGIN_OF_LINE:
                    txt.append("    %sif( me->buffer._character_before_lexeme_start == '\\n' )" % else_str)
                elif element.pre_context_id != E_PreContextIDs.NONE:
                    txt.append("    %sif( pre_context_%i_fulfilled_f ) " % (else_str, element.pre_context_id))
                else:
                    txt.append("    %s" % else_str)
                txt.append("{ last_acceptance = %s; __quex_debug(\"last_acceptance = %s\\n\"); }\n" \
                           % (self.ACCEPTANCE(element.acceptance_id), self.ACCEPTANCE(element.acceptance_id)))
                else_str = "else "
            return "".join(txt)

        elif Cmd.id == E_Cmd.Router:
            case_list = [
                (self.ACCEPTANCE(element.acceptance_id), 
                 self.position_and_goto(self.__analyzer.engine_type, element))
                for element in Cmd.content
            ]
            txt = self.SELECTION("last_acceptance", case_list)
            result = "".join(self.GET_PLAIN_STRINGS(txt))
            return result

        elif Cmd.id == E_Cmd.RouterOnStateKey:
            case_list = [
                (state_key, self.GOTO(door_id)) for state_key, door_id in Cmd.content
            ]
            if Cmd.content.register == E_R.PathIterator:
                key_txt = "path_iterator - path_walker_%i_path_base" % Cmd.content.mega_state_index 
            elif Cmd.content.register == E_R.TemplateStateKey:
                key_txt = "state_key"
            else:
                assert False

            txt = self.SELECTION(key_txt, case_list)
            result = "".join(self.GET_PLAIN_STRINGS(txt))
            return result

        elif Cmd.id == E_Cmd.IfPreContextSetPositionAndGoto:
            pre_context_id = Cmd.content.pre_context_id
            block = self.position_and_goto(self.__analyzer.engine_type, 
                                           Cmd.content.router_element)
            txt = []
            self.IF_PRE_CONTEXT(txt, True, pre_context_id, block)
            return "".join(txt)

        elif Cmd.id == E_Cmd.QuexDebug:
            return '__quex_debug("%s");\n' % Cmd.content.string

        elif Cmd.id == E_Cmd.QuexAssertNoPassage:
            return self.UNREACHABLE

        elif Cmd.id == E_Cmd.GotoDoorId:
            return self.GOTO(Cmd.content.door_id)

        elif Cmd.id == E_Cmd.GotoDoorIdIfInputPNotEqualPointer:
            return "if( %s != %s ) %s\n" % (self.INPUT_P(), 
                                            self.REGISTER_NAME(Cmd.content.pointer), 
                                            self.GOTO(Cmd.content.door_id))

        elif Cmd.id == E_Cmd.IndentationHandlerCall:
            # If mode_specific is None => General default indentation handler.
            # else:                    => specific indentation handler.
            return self.INDENTATION_HANDLER_CALL(Cmd.content.default_f, Cmd.content.mode_name)

        elif Cmd.id == E_Cmd.Assign:
            return "    %s = %s;\n" % (self.REGISTER_NAME(Cmd.content[0]), self.REGISTER_NAME(Cmd.content[1]))

        elif Cmd.id == E_Cmd.AssignConstant:
            register = Cmd.content.register
            value    = Cmd.content.value 

            if  register == E_R.Column:
                assignment = "%s = (size_t)%s;\n" % (self.REGISTER_NAME(register), value)
                return "    __QUEX_IF_COUNT_COLUMNS(%s);\n" % assignment
            elif register == E_R.Line:
                assignment = "%s = (size_t)%s;\n" % (self.REGISTER_NAME(register), value)
                return "    __QUEX_IF_COUNT_LINES(%s);\n" % assignment
            else:
                assignment = "%s = %s;\n" % (self.REGISTER_NAME(register), value)
                return "    %s;\n" % assignment

        elif Cmd.id == E_Cmd.ColumnCountAdd:
            return "__QUEX_IF_COUNT_COLUMNS_ADD((size_t)%s);\n" % self.VALUE_STRING(Cmd.content.value) 

        elif Cmd.id == E_Cmd.ColumnCountGridAdd:
            return "".join(self.GRID_STEP("self.counter._column_number_at_end", "size_t",
                           Cmd.content.grid_size, IfMacro="__QUEX_IF_COUNT_COLUMNS"))

        elif Cmd.id == E_Cmd.ColumnCountReferencePSet:
            pointer_name = self.REGISTER_NAME(Cmd.content.pointer)
            offset       = Cmd.content.offset
            return self.REFERENCE_P_RESET(pointer_name, offset)

        elif Cmd.id == E_Cmd.ColumnCountReferencePDeltaAdd:
            return self.REFERENCE_P_COLUMN_ADD(self.REGISTER_NAME(Cmd.content.pointer), 
                                               Cmd.content.column_n_per_chunk, 
                                               Cmd.content.subtract_one_f) 

        elif Cmd.id == E_Cmd.LineCountAdd:
            txt = []
            if Cmd.content.value != 0:
                txt.append("__QUEX_IF_COUNT_LINES_ADD((size_t)%s);\n" % self.VALUE_STRING(Cmd.content.value))
            return "".join(txt)

        elif Cmd.id == E_Cmd.StoreInputPosition:
            # Assume that checking for the pre-context is just overhead that 
            # does not accelerate anything.
            if Cmd.content.offset == 0:
                return "    position[%i] = me->buffer._input_p; __quex_debug(\"position[%i] = input_p;\\n\");\n" \
                       % (Cmd.content.position_register, Cmd.content.position_register)
            else:
                return "    position[%i] = me->buffer._input_p - %i; __quex_debug(\"position[%i] = input_p - %i;\\n\");\n" \
                       % (Cmd.content.position_register, Cmd.content.offset, Cmd.content.position_register, Cmd.content.offset)

        elif Cmd.id == E_Cmd.PreContextOK:
            return   "    pre_context_%i_fulfilled_f = 1;\n"                         \
                   % Cmd.content.pre_context_id                                      \
                   + "    __quex_debug(\"pre_context_%i_fulfilled_f = true\\n\");\n" \
                   % Cmd.content.pre_context_id

        elif Cmd.id == E_Cmd.TemplateStateKeySet:
            return   "    state_key = %i;\n"                      \
                   % Cmd.content.state_key                        \
                   + "    __quex_debug(\"state_key = %i\\n\");\n" \
                   % Cmd.content.state_key

        elif Cmd.id == E_Cmd.PathIteratorSet:
            offset_str = ""
            if Cmd.content.offset != 0: offset_str = " + %i" % Cmd.content.offset
            txt =   "    path_iterator  = path_walker_%i_path_%i%s;\n"                   \
                  % (Cmd.content.path_walker_id, Cmd.content.path_id, offset_str)        \
                  + "    __quex_debug(\"path_iterator = (Pathwalker: %i, Path: %i, Offset: %i)\\n\");\n" \
                  % (Cmd.content.path_walker_id, Cmd.content.path_id, Cmd.content.offset)
            return txt

        elif Cmd.id == E_Cmd.PrepareAfterReload:
            on_success_door_id = Cmd.content.on_success_door_id 
            on_failure_door_id = Cmd.content.on_failure_door_id 

            on_success_adr = dial_db.get_address_by_door_id(on_success_door_id, RoutedF=True)
            on_failure_adr = dial_db.get_address_by_door_id(on_failure_door_id, RoutedF=True)

            return   "    target_state_index = QUEX_LABEL(%i); target_state_else_index = QUEX_LABEL(%i);\n"  \
                   % (on_success_adr, on_failure_adr)                                                        

        elif Cmd.id == E_Cmd.LexemeResetTerminatingZero:
            return "    QUEX_LEXEME_TERMINATING_ZERO_UNDO(&me->buffer);\n"

        elif Cmd.id == E_Cmd.InputPDereference:
            return "    %s\n" % self.ASSIGN("input", self.INPUT_P_DEREFERENCE())

        elif Cmd.id == E_Cmd.InputPIncrement:
            return "    %s\n" % self.INPUT_P_INCREMENT()

        elif Cmd.id == E_Cmd.InputPDecrement:
            return "    %s\n" % self.INPUT_P_DECREMENT()

        else:
            assert False, "Unknown command '%s'" % Cmd.id

    def TERMINAL_CODE(self, TerminalStateList, TheAnalyzer): 
        text = [
            cpp._terminal_state_prolog
        ]
        for terminal in sorted(TerminalStateList, key=lambda x: x.incidence_id()):
            door_id = DoorID.incidence(terminal.incidence_id())
            t_txt = ["%s __quex_debug(\"* TERMINAL %s\\n\");\n" % \
                     (self.LABEL(door_id), terminal.name())]
            code  = terminal.code(TheAnalyzer)
            assert none_isinstance(code, list)
            t_txt.extend(code)
            t_txt.append("\n")

            text.append(IfDoorIdReferencedCode(door_id, t_txt))
        return text

    def ANALYZER_FUNCTION(self, ModeName, Setup, VariableDefs, 
                          FunctionBody, ModeNameList):
        return cpp._analyzer_function(ModeName, Setup, VariableDefs, 
                                      FunctionBody, ModeNameList)

    def REENTRY_PREPARATION(self, PreConditionIDList, OnAfterMatchCode):
        return cpp.reentry_preparation(self, PreConditionIDList, OnAfterMatchCode)

    def HEADER_DEFINITIONS(self):
        return blue_print(cpp_header_definition_str, [
            ("$$CONTINUE_WITH_ON_AFTER_MATCH$$", dial_db.get_label_by_door_id(DoorID.continue_with_on_after_match())),
            ("$$RETURN_WITH_ON_AFTER_MATCH$$",   dial_db.get_label_by_door_id(DoorID.return_with_on_after_match())),
        ])

    @typed(DoorId=DoorID)
    def LABEL(self, DoorId):
        return "%s:" % dial_db.get_label_by_door_id(DoorId)

    @typed(DoorId=DoorID)
    def GOTO(self, DoorId):
        if DoorId.last_acceptance_f():
             return "QUEX_GOTO_TERMINAL(last_acceptance);"
        return "goto %s;" % dial_db.get_label_by_door_id(DoorId, GotoedF=True)

    def GOTO_BY_VARIABLE(self, VariableName):
        return "QUEX_GOTO_STATE(%s);" % VariableName 

    def GRID_STEP(self, VariableName, TypeName, GridWidth, StepN=1, IfMacro=None):
        """A grid step is an addition which depends on the current value 
        of a variable. It sets the value to the next valid value on a grid
        with a given width. The general solution is 

                  x  = (x - x % GridWidth) # go back to last grid.
                  x += GridWidth           # go to next grid step.

        For 'GridWidth' as a power of '2' there is a slightly more
        efficient solution.
        """
        assert GridWidth > 0

        grid_with_str = self.VALUE_STRING(GridWidth)
        log2          = self._get_log2_if_power_of_2(GridWidth)
        if log2 is not None:
            # For k = a potentials of 2, the expression 'x - x % k' can be written as: x & ~mask(log2) !
            # Thus: x = x - x % k + k = x & mask + k
            mask = (1 << int(log2)) - 1
            if mask != 0: cut_str = "%s &= ~ ((%s)0x%X)" % (VariableName, TypeName, mask)
            else:         cut_str = ""
        else:
            cut_str = "%s -= (%s %% (%s))" % (VariableName, VariableName, grid_with_str)

        add_str = "%s += %s + 1" % (VariableName, self.MULTIPLY_WITH(grid_with_str, StepN))

        result = []
        if IfMacro is None: 
            result.append("%s -= 1;\n" % VariableName)
            if cut_str: result.append("%s;" % cut_str)
            result.append("%s;\n" % add_str)
        else:               
            result.append("%s(%s -= 1);\n" % (IfMacro, VariableName))
            if cut_str: result.append("%s(%s);\n" % (IfMacro, cut_str))
            result.append("%s(%s);\n" % (IfMacro, add_str))

        return result

    def MULTIPLY_WITH(self, FactorStr, NameOrValue):
        if isinstance(NameOrValue, (str, unicode)):
            return "%s * %s" % (FactorStr, self.VALUE_STRING(NameOrValue))

        x = NameOrValue

        if x == 0:
            return "0"
        elif x == 1:
            return FactorStr
        elif x < 1:
            x    = int(round(1.0 / x))
            log2 = self._get_log2_if_power_of_2(x)
            if log2 is not None:
                return "%s >> %i" % (FactorStr, int(log2))
            else:
                return "%s / %s" % (FactorStr, self.VALUE_STRING(x))
        else:
            log2 = self._get_log2_if_power_of_2(x)
            if log2 is not None:
                return "%s << %i" % (FactorStr, int(log2))
            else:
                return "%s * %s" % (FactorStr, self.VALUE_STRING(x))

    def VALUE_STRING(self, NameOrValue):
        if isinstance(NameOrValue, (str, unicode)):
            return "self.%s" % NameOrValue
        elif hasattr(NameOrValue, "is_integer") and NameOrValue.is_integer():
            return "%i" % NameOrValue
        else:
            return "%s" % NameOrValue

    def REFERENCE_P_COLUMN_ADD(self, IteratorName, ColumnCountPerChunk, SubtractOneF):
        """Add reference pointer count to current column. There are two cases:
           (1) The character at the end is part of the 'constant column count region'.
               --> We do not need to go one back. 
           (2) The character at the end is NOT part of the 'constant column count region'.
               --> We need to go one back (SubtractOneF=True).

           The second case happens, for example, when a 'grid' (tabulator) character is
           hit. Then, one needs to get before the tabulator before one jumps to the 
           next position.
        """
        minus_one = { True: " - 1", False: "" }[SubtractOneF]
        delta_str = "(%s - reference_p%s)" % (IteratorName, minus_one)
        return "__QUEX_IF_COUNT_COLUMNS_ADD((size_t)(%s));\n" \
               % self.MULTIPLY_WITH(delta_str, ColumnCountPerChunk)

    def REFERENCE_P_RESET(self, IteratorName, Offset=0):
        if   Offset > 0:
            return "__QUEX_IF_COUNT_COLUMNS(reference_p = %s + %i);\n" % (IteratorName, Offset) 
        elif Offset < 0:
            return "__QUEX_IF_COUNT_COLUMNS(reference_p = %s - %i);\n" % (IteratorName, - Offset) 
        else:
            return "__QUEX_IF_COUNT_COLUMNS(reference_p = %s);\n" % IteratorName 

    
    def MODE_GOTO(self, Mode):
        return "QUEX_NAME(enter_mode)(&self, &%s);" % Mode

    def MODE_GOSUB(self, Mode):
        return "QUEX_NAME(push_mode)(&self, &%s);" % Mode

    def MODE_GOUP(self):
        return "QUEX_NAME(pop_mode)(&self);"

    def ACCEPTANCE(self, AcceptanceID):
        if AcceptanceID == E_IncidenceIDs.MATCH_FAILURE: return "((QUEX_TYPE_ACCEPTANCE_ID)-1)"
        else:                                            return "%i" % AcceptanceID

    def UNREACHABLE_BEGIN(self):
        return "if( 0 ) {"

    def UNREACHABLE_END(self):
        return "}"

    def IF_MULTI_OR(self, LOR_List):
        L = len(LOR_List)
        decision = []
        for i, info in enumerate(LOR_List): 
            lvalue, operator, rvalue = info
            if i == 0: 
                decision.append("if(   (%s %s %s)" % (lvalue, operator, rvalue))
            else:
                decision.append("\n   || (%s %s %s)" % (lvalue, operator, rvalue))
            if i != L - 1:
                decision.append("\n")
        decision.append(" ) {\n")

    def IF(self, LValue, Operator, RValue, FirstF=True, SimpleF=False):
        if isinstance(RValue, (str,unicode)): decision = "%s %s %s"   % (LValue, Operator, RValue)
        else:                                 decision = "%s %s 0x%X" % (LValue, Operator, RValue)
        if not SimpleF:
            if FirstF: return "if( %s ) {\n"          % decision
            else:      return "\n} else if( %s ) {\n" % decision
        else:
            if FirstF: return "if( %s ) "      % decision
            else:      return "else if( %s ) " % decision


    def IF_GOTO(self, LValue, Condition, RValue, DoorId, FirstF=True):
        return "%s %s\n" % (self.IF(LValue, Condition, RValue, FirstF, True), self.GOTO(DoorId))
                

    def IF_INPUT(self, Condition, Value, FirstF=True):
        return self.IF("input", Condition, Value, FirstF)

    def IF_PRE_CONTEXT(self, txt, FirstF, PreContextID, Consequence):

        if PreContextID == E_PreContextIDs.NONE:
            if FirstF: opening = [];           closing = []
            else:      opening = ["else {\n"]; closing = ["    }\n"]
        else:
            condition = self.PRE_CONTEXT_CONDITION(PreContextID) 
            if FirstF: opening = ["if( %s ) {\n" % condition]
            else:      opening = ["else if( %s ) {\n" % condition]
            closing = ["}\n"]

        txt.extend(opening)
        txt.append("    ")
        if isinstance(Consequence, (str, unicode)): txt.append(Consequence)
        else:                                       txt.extend(Consequence)
        txt.extend(closing)
        return

    def IF_END_OF_FILE(self):
        return "if( QUEX_NAME(Buffer_is_end_of_file)(&me->buffer) ) {\n"

    def IF_INPUT_P_EQUAL_LEXEME_START_P(self, FirstF=True):
        return self.IF(self.INPUT_P(), "==", self.LEXEME_START_P(), FirstF)

    def END_IF(self, LastF=True):
        return { True: "\n}", False: "" }[LastF]

    def PRE_CONTEXT_CONDITION(self, PreContextID):
        if PreContextID == E_PreContextIDs.BEGIN_OF_LINE: 
            return "me->buffer._character_before_lexeme_start == '\\n'"
        elif PreContextID == E_PreContextIDs.NONE:
            return "true"
        elif isinstance(PreContextID, (int, long)):
            return "pre_context_%i_fulfilled_f" % PreContextID
        else:
            assert False

    def PRE_CONTEXT_RESET(self, PreConditionIDList):
        if PreConditionIDList is None: return ""
        return "".join([
            "    %s\n" % self.ASSIGN("pre_context_%s_fulfilled_f" % pre_context_id, 0)
            for pre_context_id in PreConditionIDList
        ])

    def ASSIGN(self, X, Y):
        return "%s = %s;" % (X, Y)

    def ACCESS_INPUT(self, txt=None, InputAction=E_InputActions.DEREF, Indent=0):
        code = {
            E_InputActions.DEREF:                ["%s\n" % self.ASSIGN("input", self.INPUT_P_DEREFERENCE())],

            E_InputActions.INCREMENT:            ["%s\n" % self.INPUT_P_INCREMENT()],
            
            E_InputActions.INCREMENT_THEN_DEREF: [        "%s\n" % self.INPUT_P_INCREMENT(),
                                                  Indent, "%s\n" % self.ASSIGN("input", self.INPUT_P_DEREFERENCE())], 
            
            E_InputActions.DECREMENT:            ["%s\n" % self.INPUT_P_DECREMENT()], 
            
            E_InputActions.DECREMENT_THEN_DEREF: [        "%s\n" % self.INPUT_P_DECREMENT(),
                                                  Indent, "%s\n" % self.ASSIGN("input", self.INPUT_P_DEREFERENCE())], 
        }[InputAction]

        if txt is None: return "".join(code)

        txt.extend(code)

    def STATE_DEBUG_INFO(self, txt, TheState, TheAnalyzer):
        if isinstance(TheState, TemplateState):
            txt.append("__quex_debug_template_state(%i, state_key);\n" \
                       % TheState.index)
        elif isinstance(TheState, PathWalkerState):
            txt.append("__quex_debug_path_walker_state(%i, path_walker_%s_path_base, path_iterator);\n" \
                       % (TheState.index, TheState.index))
        else:
            assert isinstance(TheState, Processor)
            if TheAnalyzer.is_init_state_forward(TheState.index): 
                txt.append("__quex_debug(\"Init State\\n\");\n")
                txt.append("__quex_debug_state(%i);\n" % TheState.index)
            elif TheState.index == E_StateIndices.DROP_OUT:
                txt.append("__quex_debug(\"Drop-Out Catcher\\n\");\n")
            else:
                txt.append("__quex_debug_state(%i);\n" % TheState.index)
        return 

    def POSITION_REGISTER(self, Index):
        return "position[%i]" % Index

    @typed(X=RouterContentElement)
    def POSITIONING(self, X):
        Positioning = X.positioning
        Register    = X.position_register
        if   Positioning == E_TransitionN.VOID: 
            return   "__quex_assert(position[%i] != (void*)0);\n" % Register \
                   + "me->buffer._input_p = position[%i];\n" % Register
        # "_input_p = lexeme_start_p + 1" is done by TERMINAL_FAILURE. 
        elif Positioning == E_TransitionN.LEXEME_START_PLUS_ONE: 
            return "%s = %s + 1; " % (self.INPUT_P(), self.LEXEME_START_P())
        elif Positioning > 0:     
            return "me->buffer._input_p -= %i; " % Positioning
        elif Positioning == 0:    
            return ""
        else:
            assert False 

    def SELECTION(self, Selector, CaseList, CaseFormat="hex"):

        def __case(txt, item, Content=""):
            def format(N):
                return {"hex": "case 0x%X: ", 
                        "dec": "case %i: "}[CaseFormat] % N

            if isinstance(item, list):        
                for elm in item[:-1]:
                    txt.append(1) # 1 indentation
                    txt.append("%s\n" % format(elm))
                txt.append(1) # 1 indentation
                txt.append(format(item[-1]))

            elif isinstance(item, (int, long)): 
                txt.append(1) # 1 indentation
                txt.append(format(item))

            else: 
                txt.append(1) # 1 indentation
                txt.append("case %s: "  % item)

            if type(Content) == list: txt.extend(Content)
            elif len(Content) != 0:   txt.append(Content)

            if      self.__code_generation_switch_cases_add_statement is not None \
                and self.Match_goto.search(txt[-1]) is None                       \
                and self.Match_QUEX_GOTO_RELOAD.search(txt[-1]) is None:
                txt.append(1)
                txt.append(self.__code_generation_switch_cases_add_statement)
            txt.append("\n")

        txt = [ 0, "switch( %s ) {\n" % Selector ]

        item, consequence = CaseList[0]
        for item_ahead, consequence_ahead in CaseList[1:]:
            if consequence_ahead == consequence: __case(txt, item)
            else:                                __case(txt, item, consequence)
            item        = item_ahead
            consequence = consequence_ahead

        __case(txt, item, consequence)

        txt.append("\n")
        txt.append(0)       # 0 indentation
        txt.append("}")
        return txt

    def REPLACE_INDENT(self, txt_list, Start=0):
        for i, x in enumerate(islice(txt_list, Start, None), Start):
            if isinstance(x, int): txt_list[i] = "    " * x
        return txt_list

    def INDENT(self, txt_list, Add=1, Start=0):
        for i, x in enumerate(islice(txt_list, Start, None), Start):
            if isinstance(x, int): txt_list[i] += Add

    def GET_PLAIN_STRINGS(self, txt_list):
        self.REPLACE_INDENT(txt_list)
        return get_plain_strings(txt_list)

    def VARIABLE_DEFINITIONS(self, VariableDB):
        # ROBUSTNESS: Require 'target_state_index' and 'target_state_else_index'
        #             ALWAYS. Later, they are referenced in dead code to avoid
        #             warnings of unused variables.
        # BOTH: -- Used in QUEX_GOTO_STATE in case of no computed goto-s.
        #       -- During reload.
        VariableDB.require("target_state_index")
        VariableDB.require("target_state_else_index")

        assert type(VariableDB) != dict
        return cpp._local_variable_definitions(VariableDB.get()) 

    def RELOAD_SPECIAL(self, BeforeReloadAction, AfterReloadAction):
        assert self.__code_generation_reload_label is not None
        assert type(BeforeReloadAction) == list
        assert type(AfterReloadAction) == list

        result = [ 
           cpp_reload_forward_str[0],
           "%s:\n" % self.__code_generation_reload_label,
           cpp_reload_forward_str[1],
        ]
        result.extend(BeforeReloadAction)
        result.append(cpp_reload_forward_str[2])
        result.extend(AfterReloadAction)
        result.append(cpp_reload_forward_str[3])
        dial_db.mark_door_id_as_gotoed(DoorID.global_state_router())

        return result

    def RELOAD_PROCEDURE(self, ForwardF):
        assert self.__code_generation_reload_label is None

        if ForwardF:
            return [
                cpp_reload_forward_str[0],
                cpp_reload_forward_str[1],
                cpp_reload_forward_str[2],
            ]
        else:
            return cpp_reload_backward_str[0]

    def straighten_open_line_pragmas(self, FileName):
        norm_filename   = Setup.get_file_reference(FileName)
        line_pragma_txt = self._SOURCE_REFERENCE_END().strip()

        new_content = []
        line_n      = 1 # NOT: 0!
        fh          = open_file_or_die(FileName)
        while 1 + 1 == 2:
            line = fh.readline()
            line_n += 1
            if not line: 
                break
            elif line.strip() != line_pragma_txt:
                new_content.append(line)
            else:
                line_n += 1
                new_content.append(self._SOURCE_REFERENCE_BEGIN(SourceRef(norm_filename, line_n)))
        fh.close()
        write_safely_and_close(FileName, "".join(new_content))

    @typed(X=RouterContentElement)
    def position_and_goto(self, EngineType, X):
        # If the pattern requires backward input position detection, then
        # jump to the entry of the detector. (This is a very seldom case)
        if EngineType.is_FORWARD():
            bipd_entry_door_id = EngineType.bipd_entry_door_id_db.get(X.acceptance_id)
            if bipd_entry_door_id is not None:                        
                return self.GOTO(bipd_entry_door_id) 

        # Position the input pointer and jump to terminal.
        positioning_str   = self.POSITIONING(X)
        if len(positioning_str) != 0: positioning_str += "\n"
        goto_terminal_str = self.GOTO(DoorID.incidence(X.acceptance_id))
        return [
            positioning_str, "\n" if len(positioning_str) != 0 else "",
            goto_terminal_str
        ]

cpp_reload_forward_str = [
"""    __quex_debug3("RELOAD_FORWARD: success->%i; failure->%i", (int)target_state_index, (int)target_state_else_index);
    __quex_assert(*(me->buffer._input_p) == QUEX_SETTING_BUFFER_LIMIT_CODE);
    if( me->buffer._memory._end_of_file_p == 0x0 ) {
""",
"""
        __quex_debug_reload_before();          /* Report source position. */
        QUEX_NAME(buffer_reload_forward)(&me->buffer, (QUEX_TYPE_CHARACTER_POSITION*)position, PositionRegisterN);
""",
"""
        __quex_debug_reload_after();
        QUEX_GOTO_STATE(target_state_index);   /* may use 'computed goto' */
    }
    __quex_debug("reload impossible\\n");
    QUEX_GOTO_STATE(target_state_else_index);  /* may use 'computed goto' */
"""]

cpp_reload_backward_str = [
"""    __quex_debug3("RELOAD_BACKWARD: success->%i; failure->%i", (int)target_state_index, (int)target_state_else_index);
    __quex_assert(input == QUEX_SETTING_BUFFER_LIMIT_CODE);
    if( QUEX_NAME(Buffer_is_begin_of_file)(&me->buffer) == false ) {
        __quex_debug_reload_before();          /* Report source position. */
        QUEX_NAME(buffer_reload_backward)(&me->buffer);
        __quex_debug_reload_after();
        QUEX_GOTO_STATE(target_state_index);   /* may use 'computed goto' */
    }
    __quex_debug("reload impossible\\n");
    QUEX_GOTO_STATE(target_state_else_index);  /* may use 'computed goto' */
"""]

cpp_header_definition_str = """
#include <quex/code_base/analyzer/member/basic>
#include <quex/code_base/buffer/Buffer>
#ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE
#   include <quex/code_base/token/TokenQueue>
#endif

#ifdef    CONTINUE
#   undef CONTINUE
#endif
#define   CONTINUE do { goto $$CONTINUE_WITH_ON_AFTER_MATCH$$; } while(0)

#ifdef    RETURN
#   undef RETURN
#endif
#define   RETURN   do { goto $$RETURN_WITH_ON_AFTER_MATCH$$; } while(0)
"""

db = {}

db["C++"] = Lng_Cpp(CppBase)

#________________________________________________________________________________
# C
#    
class Lng_C(Lng_Cpp):
    def __init__(self, DB):      
        Lng_Cpp.__init__(self, DB)
    def NAMESPACE_REFERENCE(self, NameList):
        return "".join("%s_" % name for name in NameList)

db["C"] = Lng_C(CppBase)
db["C"].update([
    ("$token-default-file", "/token/CDefault.qx"),
    ("$token_template_file",    "/token/TXT-C"),
    ("$token_template_i_file",  "/token/TXT-C.i"),
    ("$analyzer_template_file", "/analyzer/TXT-C"),
    ("$file_extension",         ".c")
])

#________________________________________________________________________________
# Perl
#    
db["Perl"] = {
}

#________________________________________________________________________________
# Python
#    
db["Python"] = {
}

#________________________________________________________________________________
# Visual Basic 6
#    
db["VisualBasic6"] = {
    }

db["DOT"] = copy(db["C++"])
db["C"].update([
    ("$token-default-file", "/token/CDefault.qx"),
    ("$token_template_file",    "/token/TXT-C"),
    ("$token_template_i_file",  "/token/TXT-C.i"),
    ("$analyzer_template_file", "/analyzer/TXT-C"),
    ("$file_extension",         ".c"),
    ("$comment-delimiters", [["/*", "*/", ""], ["//", "\n", ""], ["\"", "\"", "\\\""]]),
])

