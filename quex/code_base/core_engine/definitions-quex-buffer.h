#ifndef __INCLUDE_GUARD_QUEX_ANALYSER_CORE_DEFINITIONS_QUEX_BUFFER_H__
#define __INCLUDE_GUARD_QUEX_ANALYSER_CORE_DEFINITIONS_QUEX_BUFFER_H__

#include <quex/code_base/buffer/buffer>

struct QUEX_CORE_ANALYSER_STRUCT;

#ifdef __QUEX_OPTION_UNIT_TEST_ISOLATED_CODE_GENERATION
    typedef int                                    QUEX_ANALYSER_RETURN_TYPE;
    typedef QUEX_CORE_ANALYSER_STRUCT              QUEX_LEXER_CLASS;   
    typedef quex::buffer_core</*default*/>::character_type    QUEX_CHARACTER_TYPE;
    typedef quex::buffer_core</*default*/>::character_type    QUEX_LEXEME_CHARACTER_TYPE;
#endif
typedef quex::buffer_core<QUEX_CHARACTER_TYPE>   QUEX_CORE_BUFFER_TYPE;
typedef quex::buffer_core<QUEX_CHARACTER_TYPE>::memory_position   QUEX_CHARACTER_POSITION;


// The Analyzer Function for a Mode:
typedef QUEX_ANALYSER_RETURN_TYPE  (*QUEX_MODE_FUNCTION_P)(QUEX_LEXER_CLASS*);


#define QUEX_INLINE_KEYWORD inline

struct QUEX_CORE_ANALYSER_STRUCT {
    quex::buffer_core<QUEX_CHARACTER_TYPE>*  __buffer;
    QUEX_MODE_FUNCTION_P                     __current_mode_analyser_function_p;

#ifdef  __QUEX_CORE_OPTION_RETURN_ON_MODE_CHANGE
    // A mode change must force a return from to the caller function so that the
    // function pointer of the correspondent analyser function can be reset. If
    // the following flag is set, the lexer function calls the new analyser 
    // immediately.
    bool                   __continue_analysis_after_adapting_mode_function_p_f;
#endif

    QUEX_CHARACTER_TYPE    char_covered_by_terminating_zero;   // MANDATORY MEMBER!

#ifdef __QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
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
    int                    begin_of_line_f;                    
#endif
};

#define QUEX_CORE_ANALYSER_STRUCT_init_ARGUMENT_LIST \
        QUEX_CORE_ANALYSER_STRUCT*,                  \
        QUEX_CHARACTER_TYPE*,                        \
        quex::buffer_core<QUEX_CHARACTER_TYPE>*,     \
        QUEX_MODE_FUNCTION_P 

QUEX_INLINE_KEYWORD
void
QUEX_CORE_ANALYSER_STRUCT_init(QUEX_CORE_ANALYSER_STRUCT*   me, 
                               QUEX_CHARACTER_TYPE*         InputStartPosition,
                               quex::buffer_core<QUEX_CHARACTER_TYPE>* the_buffer,
                               QUEX_MODE_FUNCTION_P                    TheInitialAnalyserFunctionP) 
{
    /* Provide a string object 'Lexeme' and an integer 'LexemeL' to support
     ** further treatment inside the action.
     **
     ** TODO: Provide mechanism for actions that rely on Lexeme and LexemeL and
     **       those that do not. If one of the two is not required the preparation can be 
     **       spared. (see function __terminal_states())
     **
     ** NOTE: The buffer object containing the stream to be analysed is temporarily
     **       corrupted by setting a terminating zero and the end of the matched lexeme.
     **       At the entry state, this is undone using QUEX_UNDO_PREPARE_LEXEME_OBJECT.
     **
     ** NOTE: QUEX_PREPARE_LEXEME_OBJECT is to be called **after** the macro
     **       QUEX_STREAM_SEEK(last.._acceptance) thus one can assume that 
     **       last_acceptance_positioni+1 points the position right after the (core-)expression
     **       to be matched---even in case of post-conditions.
     */
    me->char_covered_by_terminating_zero = '\0'; 
    me->__buffer = the_buffer;
    me->__current_mode_analyser_function_p = TheInitialAnalyserFunctionP;
    // me->__buffer->seek_streampos(InputStartPosition);     
#ifdef __QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION    
    me->begin_of_line_f = 1;
#endif
}


QUEX_INLINE_KEYWORD
void
QUEX_CORE_ANALYSER_STRUCT_mark_lexeme_start(QUEX_CORE_ANALYSER_STRUCT* me)
{
    me->__buffer->mark_lexeme_start();
}

/* After pre-condition state machines analyzed backwards, the analyzer needs
** to go to the point where the actual analysis starts. The following macro
** performs this positioning of the input pointer.
*/
#define QUEX_CORE_SEEK_ANALYSER_START_POSITION \
        me->__buffer->set_current_p(me->__buffer->get_lexeme_start_p() - 1);

/* Drop Out Procedures: 
**   
**   A buffer model can (and the quex buffer does) profit from the fact that
**   some limitting characters can be defined that tell the lexer: 're-load'.
**   These limitting characters drop through all trigger conditions. When such
**   a drop out occurs, the buffer mode can determine wether this was a limitting
**   character imposing a reload, or a normal drop out.
**
**   return 0 -->  continue with normal 'drop out handling'
**   return 1 -->  get a new input and handle the state transition again.
**
*/
#define  __QUEX_CORE_OPTION_TRANSITION_DROP_OUT_HANDLING

#define  QUEX_END_OF_FILE() \
         me->__buffer->is_end_of_file()

#define QUEX_STREAM_GET(character)                 \
        (character) = me->__buffer->get_forward(); \
        __quex_assert(me->__buffer->current_p() >= me->__buffer->get_lexeme_start_p());

#define QUEX_STREAM_GET_BACKWARDS(character)        \
        (character) = me->__buffer->get_backward(); 
// NOTE: __quex_assert(me->__buffer->current_p() < me->__buffer->get_lexeme_start_p());
//       Does not make sense here, since the macro may be used for backward input
//       position detection after a post condition has triggered (pseudo ambiguous
//       post conditions).

#define QUEX_STREAM_TELL(position)            \
        (position)  = me->__buffer->tell_adr();

#define QUEX_STREAM_SEEK(position)            \
        me->__buffer->seek_adr(position);    

    
/* NOTE: See note at the member definition of '.begin_of_line_f'
*/   
#define QUEX_PREPARE_BEGIN_OF_LINE_CONDITION_FOR_NEXT_RUN \
        me->begin_of_line_f = me->__buffer->get_current_character() == '\n';
        
/* NOTE: The following macro is posted after QUEX_STREAM_SEEK(last_acceptance_input_position)
**       Thus, the subsequent character has to be set to zero, not the current. It can
**       can never be known were the drop out actually happend that caused the current 
**       pattern to win.
** NOTE: The subsequent character is always present, because the buffer hold at the end
**       a limiting character.
*/
#define QUEX_PREPARE_LEXEME_OBJECT                                                       \
        me->char_covered_by_terminating_zero = me->__buffer->get_subsequent_character(); \
        me->__buffer->set_subsequent_character('\0');                                    \
        Lexeme = (QUEX_LEXEME_CHARACTER_TYPE*)(me->__buffer->get_lexeme_start_p());                              

/* The QUEX_DO_NOT_PREPARE_LEXEME_OBJECT is the alternative to 
** QUEX_PREPARE_LEXEME_OBJECT in case that no Lexeme object is
** to be prepared, but the QUEX_UNDO_PREPARE_LEXEME_OBJECT must
** still be a valid operation at the beginning of the next analysis.
*/
#define QUEX_DO_NOT_PREPARE_LEXEME_OBJECT            \
        me->char_covered_by_terminating_zero = (QUEX_CHARACTER_TYPE)'\0';

#define QUEX_UNDO_PREPARE_LEXEME_OBJECT                                                   \
        if( me->char_covered_by_terminating_zero != (QUEX_CHARACTER_TYPE)'\0' ) {         \
           me->__buffer->set_subsequent_character(me->char_covered_by_terminating_zero);  \
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
#define QUEX_PREPARE_LEXEME_LENGTH                                                       \
        __quex_assert(me->__buffer->current_p() >= me->__buffer->get_lexeme_start_p());     \
        LexemeL = (size_t)(me->__buffer->current_p() - me->__buffer->get_lexeme_start_p() + 1);       

#ifdef  __QUEX_CORE_OPTION_RETURN_ON_MODE_CHANGE

// We equal __previous_mode_p to __current_mode_p here, so that it does not
// have to happen at each time get_token() is called.
#   define __QUEX_CORE_OPTION_RETURN_ON_DETECTED_MODE_CHANGE                     \
           if( self.__previous_mode_p != self.__current_mode_p) {                \
               self.__previous_mode_p = self.__current_mode_p;                   \
               self.__continue_analysis_after_adapting_mode_function_p_f = true; \
               return 1;                                                         \
           }

#else

#   define __QUEX_CORE_OPTION_RETURN_ON_DETECTED_MODE_CHANGE    /* nothing happens here (yet) */                         

#endif

#endif // __INCLUDE_GUARD_QUEX_ANALYSER_CORE_DEFINITIONS_QUEX_BUFFER_H__

