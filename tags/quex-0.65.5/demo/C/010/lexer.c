#include <stdio.h>

#ifdef QUEX_EXAMPLE_WITH_CONVERTER
#   include "lexUTF8.h"
#else
#   include "lexPlain.h"
#endif
typedef QUEX_TYPE_ANALYZER CLexer;
typedef QUEX_TYPE_TOKEN    CToken;
#include "receiver.h"

/* Input chunks: at syntactic boarders.
 *                                                                           */
static CToken*     construct_with_single_token(CLexer* lexer, CToken* token, 
                                               const char* CodecName);
static void        destruct_with_single_token(CLexer* lexer, CToken* token);
static bool        loop_syntactic_chunks(CLexer* lexer, CToken** prev_token);

/* Input chunks: arbitrary.
 *                                                                           */
static CToken*     construct_with_token_bank(CLexer*  lexer, CToken* token_bank, 
                                             const char* CodecName);
static void        destruct_with_token_bank(CLexer* lexer, CToken* token_bank);
static bool        loop_arbitrary_chunks(CLexer* lexer, CToken** prev_token_p);

/* Content by 'copying' or 'filling'.
 *                                                                           */
static void        content_copy(CLexer* lexer, MemoryChunk* chunk);
static void        content_fill(CLexer* lexer, MemoryChunk* chunk);


typedef struct {
/* Configuration: 
 *
 * The analysis process is configured by a set of function 
 * pointers to specify construction, destruction, the receive loop, and the
 * way how content is filled into the engine's buffer. If a codec name is
 * given, a converter is used for filling.                                   
 *                                                                           */
    CToken*     (*construct)(CLexer* lexer, CToken* token_bank, 
                             const char* CodecName);
    void        (*destruct)(CLexer* lexer, CToken* token_bank);
    bool        (*loop)(CLexer* lexer, CToken** prev_token_p);
    void        (*provide_content)(CLexer* lexer, MemoryChunk* chunk);
    size_t      (*receiver_copy)(ELEMENT_TYPE* BufferBegin, 
                                 size_t        BufferSize);
    size_t      (*receiver_fill)(ELEMENT_TYPE** buffer);

    const char* codec_name;
} Configuration;

static bool  Configuration_from_command_line(Configuration* p, int argc, char** argv);
static void  print_token(CToken*  token);

Configuration     cfg;

#define PRINT_FUNCTION() printf("called: %s;\n", __func__);

int 
main(int argc, char** argv) 
/* Running a lexical analysis process. It works with an examplary 'receiver
 * framework'. The precise analysis process is configured by the command line.
 *
 * [1] "syntactic" --> receive loop handles chunks which are expected not to 
 *                     cut in between matching lexemes.
 *     "arbitrary" --> chunks may be cut in between lexemes.
 *
 * [2] "fill"      --> content is provided by user filling as dedicated region.
 *     "copy"      --> user provides content to be copied into its 'place'.
 *                                                                           */
{        
    CLexer        qlex;
    MemoryChunk   chunk = { 0, 0 };
    CToken        token[2];       /* For 'syntactic', the second token
    *                                  * is redundant.                       */
    CToken*       prev_token;     /* For 'syntactic', the previous token
    *                                  * is meaningless.                     */

    if( ! Configuration_from_command_line(&cfg, argc, argv) ) {
        printf("Error, not enough command line arguments.\n");
        return -1;
    }

    {
        prev_token = cfg.construct(&qlex, &token[0], cfg.codec_name);

        while( 1 + 1 == 2 ) {
            cfg.provide_content(&qlex, &chunk);

            if( ! cfg.loop(&qlex, &prev_token) ) break;
        }

        cfg.destruct(&qlex, &token[0]);
    }

    return 0;
}

static bool
Configuration_from_command_line(Configuration* p, int argc, char** argv)
/* Interpret command line to configure the analysis process. The process'
 * behavior is controlled by a set of function pointers which are set here.
 *
 * RETURNS: true, configuration ok.
 *          false, else.
 *                                                                           */
{
    if(argc < 3) {
        printf("[1] --> 'syntactic' or 'arbitrary'\n");
        printf("[2] --> 'fill' or 'copy'\n");
        return false;
    }

    if( strcmp(argv[1], "syntactic") == 0 ) {
        p->construct     = construct_with_single_token;
        p->destruct      = destruct_with_single_token;
        p->loop          = loop_syntactic_chunks;
        p->receiver_copy = receiver_copy_syntax_chunk;
        p->receiver_fill = receiver_fill_syntax_chunk;
    } else {
        p->construct     = construct_with_token_bank;
        p->destruct      = destruct_with_token_bank;
        p->loop          = loop_arbitrary_chunks;
        p->receiver_copy = receiver_copy;
        p->receiver_fill = receiver_fill;
    }
    p->provide_content = (strcmp(argv[2], "copy") == 0) ? content_copy : content_fill;

#   ifdef QUEX_EXAMPLE_WITH_CONVERTER
    p->codec_name      = "UTF8";
#   else
    p->codec_name      = (const char*)0;
#   endif

    return true;
}

static CToken*
construct_with_single_token(CLexer* lexer, CToken* token, const char* CodecName)
/* Construct the lexical analyzer with one token object to chew on. With the
 * CodecName != 0, a converter is activated. 
 *
 * RETURNS: A meaningless 0.                                                 */
{
    QUEX_NAME_TOKEN(construct)(token);
    QUEX_NAME(from_ByteLoader)(lexer, (QUEX_NAME(ByteLoader)*)0, CodecName);

    /* -- LOOP until 'bye' token arrives */
    (void)QUEX_NAME(token_p_swap)(lexer, token);

    return (CToken*)0;
}

static void
destruct_with_single_token(CLexer* lexer, CToken* token)
{
    QUEX_NAME(destruct)(lexer);
    QUEX_NAME_TOKEN(destruct)(token);
}

static CToken*
construct_with_token_bank(CLexer*  lexer, CToken* token_bank, const char* CodecName)
/* Construct the lexical analyzer to chew on two swapping tokens from a token
 * bank. CodecName != 0, a converter is activated. 
 *
 * RETURNS: A pointer to the 'previous token'.                               */
{
    CToken*           prev_token;

    /* Initialize analyzer.                                                  */
    QUEX_NAME(from_ByteLoader)(lexer, (QUEX_NAME(ByteLoader)*)0, CodecName);

    /* initialize token objects.                                             */
    QUEX_NAME_TOKEN(construct)(&token_bank[0]);
    QUEX_NAME_TOKEN(construct)(&token_bank[1]);
    token_bank[0]._id = QUEX_TKN_TERMINATION;

    /* Give the analyzer a token to prepare.                                 */
    prev_token = &(token_bank[1]);
    QUEX_NAME(token_p_swap)(lexer, &token_bank[0]);

    return prev_token;
}

static void
destruct_with_token_bank(CLexer* lexer, CToken* token_bank)
{
    QUEX_NAME(destruct)(lexer);
    QUEX_NAME_TOKEN(destruct)(&token_bank[0]);
    QUEX_NAME_TOKEN(destruct)(&token_bank[1]);
}

static void
content_copy(CLexer* lexer, MemoryChunk* chunk)
/* Fill the analyzer's buffer by copying data into it, that is the function
 *
 *                            '.fill(...)' 
 *
 * of the buffer is called directly. Data is received from an examplary 
 * 'receiver framework' which fills data into an 'rx_buffer'.     
 *
 * This process involves some extra copying of data compared to to 'filling'.*/
{
    uint8_t*   rx_buffer = 0x0;             /* A pointer to the receive buffer 
    *                                        * of the messaging framework.   */
    size_t     received_n = (size_t)-1;
    PRINT_FUNCTION();

    /* NOTE: 'chunk' is initialized to '{ 0, 0 }'.
     *       => safe to assume that 'begin_p == end_p' upon first run.       */

    /* Receive content from some messaging framework.                        */
    if( chunk->begin_p == chunk->end_p ) {                                   
        /* If the receive buffer has been read, it can be released.          */
        /* Receive and set 'begin' and 'end' of incoming chunk.              */
        received_n     = cfg.receiver_fill(&rx_buffer);               
        chunk->begin_p = rx_buffer;                                      
        chunk->end_p   = chunk->begin_p + received_n;                    
    } else {                                                                 
        /* If begin_p != end_p => first digest remainder.                    */
    }

    /* Copy buffer content into the analyzer's buffer-as much as possible.
     * 'fill()' returns a pointer to the first not-eaten byte.               */
    chunk->begin_p = lexer->buffer.fill(&lexer->buffer, 
                                        chunk->begin_p, chunk->end_p);
}

static void
content_fill(CLexer* lexer, MemoryChunk* chunk)
/* Filling the analyzer's buffer by 'filling'. That is the buffer provides the
 * user with two pointers that boarder the region where content needs to be 
 * filled. Then an examplary messaging framework fills the content directly
 * into it. Then, the buffer needs to 'finish' the filled data. This process
 * evolves around the two functions.
 *
 *   .fill_prepare(...) ---> providing 'begin_p' and 'end_p' where to fill.
 *   .fill_finish(...) ---> post processing the content.
 *
 * Filling involves less copying of data than 'copying'.                     */
{
    size_t received_n = (size_t)-1;
    PRINT_FUNCTION();

    /* Initialize the filling of the fill region                             */
    lexer->buffer.fill_prepare(&lexer->buffer, 
                               (void**)&chunk->begin_p, (const void**)&chunk->end_p);

    /* Call the low level driver to fill the fill region                     */
    received_n = cfg.receiver_copy(chunk->begin_p, chunk->end_p - chunk->begin_p); 

    /* Current token becomes previous token of next run.                     */
    lexer->buffer.fill_finish(&lexer->buffer, &chunk->begin_p[received_n]);
}

static bool
loop_syntactic_chunks(CLexer* lexer, CToken** prev_token)
/* Loop until the 'TERMINATION' token arrives. Here, considering input which 
 * is 'chunked' at syntax boarders, the 'prev_token' is not considered.
 *                                                                      
 * RETURNS: true, if analysis may continue; BYE has not been received.
 *          false, if analysis may NOT continue; BYE has been received.      */
{
    QUEX_TYPE_TOKEN_ID    token_id;
    (void)prev_token; 
    PRINT_FUNCTION();

    while( 1 + 1 == 2 ) {
        token_id = QUEX_NAME(receive)(lexer);

        /* TERMINATION => possible reload 
         * BYE         => end of game                                        */
        if( token_id == QUEX_TKN_TERMINATION ) break;
        if( token_id == QUEX_TKN_BYE )         break; 

        print_token(lexer->token);
    }
    
    return token_id != QUEX_TKN_BYE; /* 'Bye' token ends the lexing session. */
}

static bool
loop_arbitrary_chunks(CLexer* lexer, CToken** prev_token_p)
/* Loop over received tokens until 'TERMINATION' or 'BYE' occurs. The previous
 * token must be tracked to identify a 'BYE, TERMINATION' sequence. The 
 * start of the lexeme must be tracked, so that after re-filling the inter-
 * rupted match cycle may restart. 
 *
 * RETURNS: true, if analysis may continue; BYE has not been received.
 *          false, if analysis may NOT continue; BYE has been received.      */
{
    QUEX_TYPE_TOKEN_ID    token_id;
    QUEX_TYPE_CHARACTER*  prev_lexeme_start_p;
    PRINT_FUNCTION();

    /* Loop until 'TERMINATION' or 'BYE' is received.                   
     *   TERMINATION => possible reload                               
     *   BYE         => end of game                                          */
    token_id = (QUEX_TYPE_TOKEN_ID)-1;
    while( 1 + 1 == 2 ) {
        prev_lexeme_start_p = QUEX_NAME(lexeme_start_pointer_get)(lexer);

        /* Current token becomes previous token of next run.                 */
        *prev_token_p = QUEX_NAME(token_p_swap)(lexer, *prev_token_p);

        token_id = QUEX_NAME(receive)(lexer);
        if( token_id == QUEX_TKN_TERMINATION || token_id == QUEX_TKN_BYE )
            break;
        if( (*prev_token_p)->_id != QUEX_TKN_TERMINATION ) 
            print_token(*prev_token_p);
    }

    if( token_id == QUEX_TKN_BYE ) return false;

    /* Reset the 'read_p' to restart the interrupted match cycle.            */
    QUEX_NAME(input_pointer_set)(lexer, prev_lexeme_start_p);
    return true;
}

static void
print_token(CToken*  token)
{
    size_t PrintBufferSize = 1024;
    char   print_buffer[1024];

    printf("   Token: %s\n", QUEX_NAME_TOKEN(get_string)(token, print_buffer, 
                                                         PrintBufferSize));
}

