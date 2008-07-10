#ifndef __INCLUDE_GUARD_QUEX_ANALYSER_CORE_DEFINITIONS_QUEX_BUFFER_H__
#define __INCLUDE_GUARD_QUEX_ANALYSER_CORE_DEFINITIONS_QUEX_BUFFER_H__

#include <quex/code_base/buffer/Buffer>

template <class T> class QuexAnalyserCore;
#define QUEX_INLINE_KEYWORD  inline   // in 'C' we will say 'static'

#define TEMPLATE_IN template<class CharacterCarrierType> inline

#ifdef __QUEX_OPTION_UNIT_TEST_ISOLATED_CODE_GENERATION
    typedef int                                      QUEX_ANALYSER_RETURN_TYPE;
#   ifdef    __QUEX_OPTION_ANALYSER_RETURN_TYPE_IS_VOID
#      undef __QUEX_OPTION_ANALYSER_RETURN_TYPE_IS_VOID
#   endif
    typedef quex::Buffer<uint8_t>::character_type    QUEX_CHARACTER_TYPE;
#endif
typedef quex::Buffer<QUEX_CHARACTER_TYPE>                    QUEX_CORE_BUFFER_TYPE;
typedef quex::Buffer<QUEX_CHARACTER_TYPE>::memory_position   QUEX_CHARACTER_POSITION;


// The Analyzer Function for a Mode:
typedef QUEX_ANALYSER_RETURN_TYPE  (*QUEX_MODE_FUNCTION_P)(QuexAnalyserCore<QUEX_CHARACTER_TYPE>*);

template<class CharacterCarrierType>
struct QuexAnalyserCore {
    quex::Buffer<CharacterCarrierType>  buffer;
    QUEX_MODE_FUNCTION_P                _current_mode_analyser_function_p;

#   ifdef  __QUEX_CORE_OPTION_RETURN_ON_MODE_CHANGE
    // A mode change must force a return from to the caller function so that the
    // function pointer of the correspondent analyser function can be reset. If
    // the following flag is set, the lexer function calls the new analyser 
    // immediately.
    bool                   __continue_analysis_after_adapting_mode_function_p_f;
#   endif

#   ifdef __QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
    // NOTE: The begin of line pre-condition needs to be stored 
    //       in a member variable, because it cannot be derived  
    //       quickly from the variable 'char_covered_by_terminating_zero == \n'.
    //       The begin of line may also occur at the beginning of 
    //       a file/stream.
    // NOTE: All other trivial pre-conditions can be derived from variable
    //       'char_covered_by_terminating_zero' because it contains
    //       the last character that occured---in any case, even when there
    //       was a post-condition, it ate only the last character from the
    //       core pattern.
    bool                   _begin_of_line_f;                    
#   endif
    QUEX_CHARACTER_TYPE    _char_covered_by_terminating_zero;   // MANDATORY MEMBER!
};

#if ! defined (__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS)
#   define QUEX_DEBUG_LABEL_PASS(LABEL)               /* empty */
#   define QUEX_DEBUG_INFO_INPUT(Character)           /* empty */
#   define QUEX_DEBUG_ADR_ASSIGNMENT(Variable, Value) /* empty */
#   define QUEX_DEBUG_ASSIGNMENT(Variable, Value)     /* empty */
#else
#   define __QUEX_PRINT_SOURCE_POSITION()                                                 \
    std::fprintf(stdout, "%s:%i: @%08X \t", __FILE__, __LINE__,                           \
                 (int)(me->buffer->tell_adr() - (me->buffer->content_front())));            

#   define QUEX_DEBUG_LABEL_PASS(Label)   \
           __QUEX_PRINT_SOURCE_POSITION() \
           std::fprintf(stdout, Label "\n")

#   define QUEX_DEBUG_ADR_ASSIGNMENT(Variable, Value)   \
           __QUEX_PRINT_SOURCE_POSITION() \
           std::fprintf(stdout, Variable " = @%08X\n", (int)(Value - me->buffer->content_front()))

#   define QUEX_DEBUG_ASSIGNMENT(Variable, Value)   \
           __QUEX_PRINT_SOURCE_POSITION() \
           std::fprintf(stdout, Variable " = " Value "\n")

#   define QUEX_DEBUG_INFO_INPUT(Character)                                \
           __QUEX_PRINT_SOURCE_POSITION()                                  \
             Character == '\n' ? std::fprintf(stdout, "INPUT:    '\\n'\n") \
           : Character == '\t' ? std::fprintf(stdout, "INPUT:    '\\t'\n") \
           :                     std::fprintf(stdout, "INPUT:    (%x) '%c'\n", (char)Character, (int)Character) 
#endif


#define QuexAnalyserCore_init_ARGUMENT_LIST      \
        QuexAnalyserCore<CharacterCarrierType>*, \
        QUEX_CHARACTER_TYPE*,                    \
        QUEX_CORE_BUFFER_TYPE*,                  \
        QUEX_MODE_FUNCTION_P 

TEMPLATE_IN void
QuexAnalyserCore_init(QuexAnalyserCore<CharacterCarrierType>*            me, 
                      QUEX_CHARACTER_TYPE*         buffer_memory,
                      size_t                       BufferSize_in_Characters,
                      QUEX_MODE_FUNCTION_P         TheInitialAnalyserFunctionP) 
{
     /* NOTE: The buffer object containing the stream to be analysed is temporarily
     **       corrupted by setting a terminating zero and the end of the matched lexeme.
     **       At the entry state, this is undone using QUEX_UNDO_PREPARE_LEXEME_OBJECT.
     **
     ** NOTE: 'QuexAnalyserCore_prepare_terminating_zero_for_Lexeme()' is to be called 
      *       **after** the 'Buffer_seek_adr(last.._acceptance)' thus one can assume that 
     **       last_acceptance_positioni+1 points the position right after the (core-)expression
     **       to be matched---even in case of post-conditions.
     */
    me->char_covered_by_terminating_zero = '\0'; 
    // the_buffer == 0x0 means that no new buffer has been allocated, take the old one
    if( buffer_memory != 0x0 ) {
        me->buffer.set_memory(buffer_memory, BufferSize_in_Characters, /* ExternalOwnerF */ false);
    }
    me->__current_mode_analyser_function_p = TheInitialAnalyserFunctionP;
    // me->buffer->seek_streampos(InputStartPosition);     
#   ifdef __QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION    
    me->_begin_of_line_f = true;
#   endif
}


#define QUEX_DEFINITION_Lexeme       (me->buffer->get_lexeme_start_p())
#define QUEX_DEFINITION_LexemeBegin  (me->buffer->get_lexeme_start_p())
#define QUEX_DEFINITION_LexemeEnd    (me->buffer->current_p())
#define QUEX_DEFINITION_LexemeL      ((size_t)(((LexemeEnd) - (LexemeBegin))))

/* QUEX_BUFFER_SEEK_START_POSITION()
 *
 *    After pre-condition state machines analyzed backwards, the analyzer needs
 *    to go to the point where the actual analysis starts. The macro
 *    performs this positioning of the input pointer.
 */
TEMPLATE_IN void
Buffer_seek_start_position(quex::Buffer<CharacterCarrierType>* buffer)
{
    buffer->set_current_p(buffer->get_lexeme_start_p());
}

    
/* NOTE: See note at the member definition of '.begin_of_line_f'
*/   
TEMPLATE_IN void
QuexAnalyserCore_prepare_begin_of_line_f(QuexAnalyserCore<CharacterCarrierType>* me)
{
    me->_begin_of_line_f = (me->buffer->get_previous_character() == '\n');
}

/* NOTE: The following macro is posted after QUEX_STREAM_SEEK(last_acceptance_input_position)
**       Thus, the subsequent character has to be set to zero, not the current. It can
**       can never be known were the drop out actually happend that caused the current 
**       pattern to win.
** NOTE: The subsequent character is always present, because the buffer hold at the end
**       a limiting character.
*/
TEMPLATE_IN void
QuexAnalyserCore_prepare_terminating_zero_for_Lexeme(QuexAnalyserCore<CharacterCarrierType>* me)
{
    me->char_covered_by_terminating_zero = me->buffer->get_current_character(); 
    me->buffer->set_current_character('\0');                                    
}

TEMPLATE_IN void
QuexAnalyserCore_undo_terminating_zero_for_Lexeme(QuexAnalyserCore<CharacterCarrierType>* me)
{
    if( me->char_covered_by_terminating_zero != (QUEX_CHARACTER_TYPE)'\0' ) {      
        me->buffer->set_current_character(me->char_covered_by_terminating_zero);  
            me->char_covered_by_terminating_zero = (QUEX_CHARACTER_TYPE)'\0';           
    }
}

#ifdef  __QUEX_CORE_OPTION_RETURN_ON_MODE_CHANGE

// We equal __previous_mode_p to __current_mode_p here, so that it does not
// have to happen at each time get_token() is called.
#   ifdef  __QUEX_OPTION_ANALYSER_RETURN_TYPE_IS_VOID
#      define __QUEX_CORE_OPTION_RETURN_ON_DETECTED_MODE_CHANGE                     \
              if( self.__previous_mode_p != self.__current_mode_p) {                \
                  self.__previous_mode_p = self.__current_mode_p;                   \
                  self.__continue_analysis_after_adapting_mode_function_p_f = true; \
                  return /*1*/;                                                         \
              }
#   else
#      define __QUEX_CORE_OPTION_RETURN_ON_DETECTED_MODE_CHANGE  /* nothing happens here (yet) */                         
#   endif

#else

#   define __QUEX_CORE_OPTION_RETURN_ON_DETECTED_MODE_CHANGE    /* nothing happens here (yet) */                         

#endif

#undef TEMPLATE_IN 
#endif // __INCLUDE_GUARD_QUEX_ANALYSER_CORE_DEFINITIONS_QUEX_BUFFER_H__

