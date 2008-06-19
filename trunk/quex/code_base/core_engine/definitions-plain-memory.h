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
#ifndef __QUEX_CORE_OPTION_CHARACTER_TYPE_DEFINED
    typedef char   QUEX_CHARACTER_TYPE;
    typedef char   QUEX_LEXEME_CHARACTER_TYPE;
#endif

typedef char*  QUEX_CHARACTER_POSITION;

typedef QUEX_ANALYSER_RETURN_TYPE  (*QUEX_MODE_FUNCTION_P)(QUEX_LEXER_CLASS*);

struct QUEX_CORE_ANALYSER_STRUCT {
    QUEX_CHARACTER_TYPE*  lexeme_start_p;                 
    QUEX_CHARACTER_TYPE*  input_p;
    QUEX_CHARACTER_TYPE*  buffer_begin;
    QUEX_CHARACTER_TYPE   char_covered_by_terminating_zero;   // MANDATORY MEMBER!
    QUEX_MODE_FUNCTION_P  __current_mode_analyser_function_p;

#ifdef __QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
    // NOTE: The begin of line pre-condition needs to be stored 
    //       in a member variable, because it cannot be derived  
    //       quickly from the variable 'char_covered_by_terminating_zero'.
    //       The begin of line may also occur at the beginning of 
    //       a file/stream.
    // NOTE: All other trivial pre-conditions can be derived from variable
    //       'char_covered_by_terminating_zero' because it contains
    //       the last character that occured---in any case, even when there
    //       was a post-condition, it ate only the last character from the
    //       core pattern.
    int begin_of_line_f;           
#endif
};

#ifndef     QUEX_SETTING_BUFFER_LIMIT_CODE
#    define QUEX_SETTING_BUFFER_LIMIT_CODE (0)
#endif
#define QUEX_END_OF_FILE()         (1)
#define QUEX_BEGIN_OF_FILE()       (me->input_p == me->buffer_begin - 1)

#define QUEX_BUFFER_INCREMENT()           (++(me->input_p));
#define QUEX_BUFFER_DECREMENT()           (--(me->input_p)); 
#define QUEX_BUFFER_TELL_ADR(position)    position    = me->input_p;
#define QUEX_BUFFER_SEEK_ADR(position)    me->input_p = position;
#define QUEX_BUFFER_GET(character)        \
        character = *(me->input_p);       \
        QUEX_DEBUG_INFO_INPUT(character); 
#define QUEX_BUFFER_LOAD_FORWARD()   (-1 /* reload not successful, no bytes loaded */)
#define QUEX_BUFFER_LOAD_BACKWARD()  /* empty */

/* QUEX_BUFFER_SEEK_START_POSITION()
 *
 *    After pre-condition state machines analyzed backwards, the analyzer needs
 *    to go to the point where the actual analysis starts. The macro
 *    performs this positioning of the input pointer.
 */
#define QUEX_BUFFER_SEEK_START_POSITION() \
        (me->input_p) = (me->lexeme_start_p); 

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


#define QUEX_CORE_MARK_LEXEME_START() (me->lexeme_start_p = me->input_p)

/* Drop Out Procedures: 
**   
**   A buffer model can (and the quex buffer does) profit from the fact that
**   some limitting characters can be defined that tell the lexer: 're-load'.
**   These limitting characters drop through all trigger conditions. When such
**   a drop out occurs, the buffer mode can determine wether this was a limitting
**   character imposing a reload, or a normal drop out.
**   
**   Plain memory does not profit from drop out for any buffer reloading.
**   => macro is commented out.
**
**   #define  __QUEX_CORE_OPTION_TRANSITION_DROP_OUT_HANDLING
**
**   For an example see the 'quex-buffer' implementation of this header.
*/

/* NOTE: Again, whenever pre-conditions are involved the buffer needs to 
**       contain a character (== Buffer Limit Code, or Begin of File) 
**       before the character stream starts. For regular inverted
**       state machines, this delimits the token stream, for the
**       begin-of-line condition, this ensures that the pointer 
**       'me->input_p - 1' is always welldefined.
*/
#define QUEX_PREPARE_BEGIN_OF_LINE_CONDITION_FOR_NEXT_RUN() \
        me->begin_of_line_f = (*(me->input_p - 1) == '\n');
        
#define QUEX_PREPARE_LEXEME_OBJECT()                                 \
        me->char_covered_by_terminating_zero = *(me->input_p); \
        *(me->input_p)= '\0';                                  \
	    Lexeme = (QUEX_LEXEME_CHARACTER_TYPE*)(me->lexeme_start_p);                              

/* The QUEX_DO_NOT_PREPARE_LEXEME_OBJECT is the alternative to 
** QUEX_PREPARE_LEXEME_OBJECT in case that no Lexeme object is
** to be prepared, but the QUEX_UNDO_PREPARE_LEXEME_OBJECT must
** still be a valid operation at the beginning of the next analysis.
*/
#define QUEX_DO_NOT_PREPARE_LEXEME_OBJECT()   /* empty */

/* At the beginning of the file, the initialization sets the
** character that covers the terminating zero to '\0'. In this
** case, one cannot say that '\n' is a valid condition for 
** the 'begin of line' flag.    
*/
#define QUEX_UNDO_PREPARE_LEXEME_OBJECT()                                          \
        if( me->char_covered_by_terminating_zero != (QUEX_CHARACTER_TYPE)'\0' ) {  \
           *(me->input_p) = me->char_covered_by_terminating_zero;                  \
            me->char_covered_by_terminating_zero = (QUEX_CHARACTER_TYPE)'\0';      \
        }

/* IMPORTANT: 
**
**    The lexeme length must use the **current position** as a reference.
**    It can be assumed, that in case of acceptance, the SEEK to the last
**    acceptance has preceeded this command. 
**
**    IF YOU REFER THE LEXEME LENGTH TO THE LAST ACCEPTANCE POSITION, THEN
**    THE DEFAULT ACTION MAY FAIL, BECAUSE THE LAST_ACCEPTANCE_INPUT_POSITION
**    CAN BE ANYTHING.
*/
#define QUEX_PREPARE_LEXEME_LENGTH()  \
	    LexemeL = (size_t)(me->input_p - me->lexeme_start_p);       

#define __QUEX_CORE_OPTION_RETURN_ON_DETECTED_MODE_CHANGE    /* nothing happens here (yet) */                         

#if ! defined (__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS)
#   define QUEX_DEBUG_LABEL_PASS(Terminal)   /* empty */
#   define QUEX_DEBUG_INFO_INPUT(Character)  /* empty */
#   define QUEX_DEBUG_ADR_ASSIGNMENT(Variable, Value) /* empty */
#   define QUEX_DEBUG_ASSIGNMENT(Variable, Value)     /* empty */
#else
#   define __QUEX_PRINT_SOURCE_POSITION()                             \
          std::fprintf(stderr, "%s:%i: @%08X \t", __FILE__, __LINE__, \
                       (int)(me->input_p - me->buffer_begin));            

#   define QUEX_DEBUG_LABEL_PASS(Label)   \
           __QUEX_PRINT_SOURCE_POSITION()   \
           std::fprintf(stderr, Label "\n")

#   define QUEX_DEBUG_ASSIGNMENT(Variable, Value)   \
           __QUEX_PRINT_SOURCE_POSITION() \
           std::fprintf(stdout, Variable " = " Value "\n")

#   define QUEX_DEBUG_ADR_ASSIGNMENT(Variable, Value)   \
           __QUEX_PRINT_SOURCE_POSITION() \
           std::fprintf(stdout, Variable " = @%08X\n", (int)(Value - me->_buffer_begin))

#   define QUEX_DEBUG_INFO_INPUT(Character)                              \
           __QUEX_PRINT_SOURCE_POSITION()                                  \
             Character == '\n' ? std::fprintf(stderr, "input:    '\\n'\n") \
           : Character == '\t' ? std::fprintf(stderr, "input:    '\\t'\n") \
           :                     std::fprintf(stderr, "input:    (%x) '%c'\n", (char)Character, (int)Character) 
#endif
#endif // __INCLUDE_GUARD_QUEX_ANALYSER_CORE_DEFINITIONS_H__

