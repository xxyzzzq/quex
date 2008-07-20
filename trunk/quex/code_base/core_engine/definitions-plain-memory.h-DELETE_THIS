#ifndef __INCLUDE_GUARD_QUEX_ANALYSER_CORE_DEFINITIONS_H__
#define __INCLUDE_GUARD_QUEX_ANALYSER_CORE_DEFINITIONS_H__


#ifndef __QUEX_CORE_OPTION_ANALYZER_RETURN_TYPE_DEFINED
    typedef int  QUEX_ANALYSER_RETURN_TYPE;
#   ifdef    __QUEX_OPTION_ANALYSER_RETURN_TYPE_IS_VOID
#      undef __QUEX_OPTION_ANALYSER_RETURN_TYPE_IS_VOID
#   endif
#endif

struct QUEX_CORE_ANALYSER_STRUCT;
#ifndef __QUEX_CORE_OPTION_LEXER_CLASS_DEFINED
    typedef QUEX_CORE_ANALYSER_STRUCT   QUEX_LEXER_CLASS;   
#endif

#ifndef __QUEX_CORE_OPTION_ANALYZER_RETURN_TYPE_DEFINED
    typedef int    QUEX_ANALYSER_RETURN_TYPE;
#endif


typedef QUEX_ANALYSER_RETURN_TYPE  (*QUEX_MODE_FUNCTION_P)(QUEX_LEXER_CLASS*);

#ifndef     QUEX_SETTING_BUFFER_LIMIT_CODE
#    define QUEX_SETTING_BUFFER_LIMIT_CODE (0)
#endif

#define QUEX_DEFINITION_Lexeme       (me->lexeme_start_p)
#define QUEX_DEFINITION_LexemeBegin  (me->lexeme_start_p)
#define QUEX_DEFINITION_LexemeEnd    (me->input_p)
#define QUEX_DEFINITION_LexemeL      ((size_t)(((LexemeEnd) - (LexemeBegin))))

/* QUEX_BUFFER_SEEK_START_POSITION()
 *
 *    After pre-condition state machines analyzed backwards, the analyzer needs
 *    to go to the point where the actual analysis starts. The macro
 *    performs this positioning of the input pointer.
 */
#define QUEX_INLINE_KEYWORD static

#define QUEX_CORE_ANALYSER_STRUCT_init_ARGUMENT_LIST \
        QUEX_CORE_ANALYSER_STRUCT*,                  \
        QUEX_CHARACTER_TYPE*,                     \
        QUEX_MODE_FUNCTION_P 

QUEX_INLINE_KEYWORD
void
QUEX_CORE_ANALYSER_STRUCT_init(QUEX_CORE_ANALYSER_STRUCT* me, 
                               QUEX_CHARACTER_TYPE*       InputStartPosition, 
                               QUEX_MODE_FUNCTION_P       TheInitianAnalyserFunctionP) 
{
    /* Provide a string object 'Lexeme' and an integer 'LexemeL' to support
     ** further treatment inside the action.
     **
     ** NOTE: The buffer object containing the stream to be analysed is temporarily
     **       corrupted by setting a terminating zero and the end of the matched lexeme.
     **       At the entry state, this is undone using QUEX_UNDO_PREPARE_LEXEME_OBJECT.
     **
     ** NOTE: QUEX_PREPARE_LEXEME_OBJECT is to be called **after** the macro
     **       QUEX_STREAM_SEEK(last.._acceptance) thus one can assume that 
     **       me->input_p points to the position right after the (core-)expression
     **       to be matched---even in case of post-conditions.
     */
    me->char_covered_by_terminating_zero   = '\0';              
    /* InputStartPosition == 0x0 means that no new buffer has been allocated, take to old one */
    me->buffer_begin                       = InputStartPosition == 0x0 ? me->buffer_begin : InputStartPosition;
    me->input_p                            = me->buffer_begin; 
    me->__current_mode_analyser_function_p = TheInitianAnalyserFunctionP;
#   ifdef __QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION    
    me->begin_of_line_f                    = 1;
#   endif
}


#define __QUEX_CORE_OPTION_RETURN_ON_DETECTED_MODE_CHANGE    /* nothing happens here (yet) */                         

#endif // __INCLUDE_GUARD_QUEX_ANALYSER_CORE_DEFINITIONS_H__

