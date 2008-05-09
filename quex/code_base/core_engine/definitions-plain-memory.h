#ifndef __INCLUDE_GUARD_QUEX_ANALYSER_CORE_DEFINITIONS_H__
#define __INCLUDE_GUARD_QUEX_ANALYSER_CORE_DEFINITIONS_H__


#ifndef __QUEX_CORE_OPTION_ANALYZER_RETURN_TYPE_DEFINED
    typedef int  QUEX_ANALYSER_RETURN_TYPE;
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
    QUEX_CHARACTER_TYPE*  initial_position_p;                 
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

#define QUEX_STREAM_GET(character)            character = *(me->input_p); ++(me->input_p); 
#define QUEX_STREAM_GET_BACKWARDS(character)  --(me->input_p); character = (*(me->input_p)); 
#define QUEX_STREAM_TELL(position)            position = me->input_p;
#define QUEX_STREAM_SEEK(position)            me->input_p = position;
#define QUEX_INLINE_KEYWORD                   static


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
    me->input_p                            = InputStartPosition; 
    me->buffer_begin                       = InputStartPosition;
    me->__current_mode_analyser_function_p = TheInitianAnalyserFunctionP;
#ifdef __QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION    
    me->begin_of_line_f                    = 1;
#endif
}

#define QUEX_END_OF_FILE() \
         0
#define QUEX_BEGIN_OF_FILE() \
        (me->input_p == me->buffer_begin)


QUEX_INLINE_KEYWORD
void
QUEX_CORE_ANALYSER_STRUCT_mark_lexeme_start(QUEX_CORE_ANALYSER_STRUCT* me)
{
    me->initial_position_p = me->input_p;
}

/* After pre-condition state machines analyzed backwards, the analyzer needs
** to go to the point where the actual analysis starts. The following macro
** performs this positioning of the input pointer.
*/
#define QUEX_CORE_SEEK_ANALYSER_START_POSITION \
       me->input_p = me->initial_position_p; 

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
#define QUEX_PREPARE_BEGIN_OF_LINE_CONDITION_FOR_NEXT_RUN \
        me->begin_of_line_f = (*(me->input_p - 1) == '\n');
        
#define QUEX_PREPARE_LEXEME_OBJECT                           \
        me->char_covered_by_terminating_zero = *me->input_p; \
        *me->input_p = '\0';                                 \
	Lexeme = (QUEX_LEXEME_CHARACTER_TYPE*)(me->initial_position_p);                              

/* The QUEX_DO_NOT_PREPARE_LEXEME_OBJECT is the alternative to 
** QUEX_PREPARE_LEXEME_OBJECT in case that no Lexeme object is
** to be prepared, but the QUEX_UNDO_PREPARE_LEXEME_OBJECT must
** still be a valid operation at the beginning of the next analysis.
*/
#define QUEX_DO_NOT_PREPARE_LEXEME_OBJECT            \
        me->char_covered_by_terminating_zero = (QUEX_CHARACTER_TYPE)'\0';

/* At the beginning of the file, the initialization sets the
** character that covers the terminating zero to '\0'. In this
** case, one cannot say that '\n' is a valid condition for 
** the 'begin of line' flag.    
*/
#define QUEX_UNDO_PREPARE_LEXEME_OBJECT                                            \
        if( me->char_covered_by_terminating_zero != (QUEX_CHARACTER_TYPE)'\0' ) {  \
           *(me->input_p) = me->char_covered_by_terminating_zero;                  \
        }

/* IMPORTANT: 
**
**    The lexeme length must user the **current position** as a reference.
**    It can be assumed, that in case of acceptance, the SEEK to the last
**    acceptance has preceeded this command. 
**
**    IF YOU REFER THE LEXEME LENGTH TO THE LAST ACCEPTANCE POSITION, THEN
**    THE DEFAULT ACTION MAY FAIL, BECAUSE THE LAST_ACCEPTANCE_INPUT_POSITION
**    CAN BE ANYTHING.
*/
#define QUEX_PREPARE_LEXEME_LENGTH                                 \
	LexemeL = (size_t)(me->input_p - me->initial_position_p);       


#define __QUEX_CORE_OPTION_RETURN_ON_DETECTED_MODE_CHANGE    /* nothing happens here (yet) */                         

#endif // __INCLUDE_GUARD_QUEX_ANALYSER_CORE_DEFINITIONS_H__

