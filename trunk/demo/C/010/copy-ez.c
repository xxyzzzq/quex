#include <stdio.h>

#include "tiny_lexer.h"
#include "messaging-framework.h"

/* Input chunks: at syntactic boarders.                                      */
static quex_Token* construct_with_token_bank(quex_tiny_lexer*  lexer, quex_Token* token_bank, const char* CodecName);
static void        destruct_with_token_bank(quex_tiny_lexer* lexer, quex_Token* token_bank);
static bool        receive_loop_arbitrary_chunks(quex_tiny_lexer* lexer, quex_Token** prev_token_p);
/* Input chunks: arbitrary.                                                  */
static quex_Token* construct_with_single_token(quex_tiny_lexer* lexer, quex_Token* token, const char* CodecName);
static void        destruct_with_single_token(quex_tiny_lexer* lexer, quex_Token* token);
static bool        receive_loop_syntactic_chunks(quex_tiny_lexer* lexer, quex_Token** prev_token);
/* Content provision by 'copying' or 'filling'.                              */
static void        content_copy(quex_tiny_lexer* lexer, MemoryChunk* chunk);
static void        content_fill(quex_tiny_lexer* lexer, MemoryChunk* chunk);

static void        print_token(quex_Token*  token);

/* Configuration: The analysis process is configured by a set of function 
 * pointers to specify construction, destruction, the receive loop, and the
 * way how content is filled into the engine's buffer. If a codec name is
 * given, a converter is used for filling.                                   */
typedef struct {
    quex_Token* (*construct)(quex_tiny_lexer*  lexer, quex_Token* token_bank, const char* CodecName);
    void        (*destruct)(quex_tiny_lexer* lexer, quex_Token* token_bank);
    bool        (*receive_loop)(quex_tiny_lexer* lexer, quex_Token** prev_token_p);
    void        (*provide_content)(quex_tiny_lexer* lexer, MemoryChunk* chunk);
    const char* codec_name;
} Configuration;

static bool  Configuration_from_command_line(Configuration* p, int argc, char** argv);

int 
main(int argc, char** argv) 
/* Running a lexical analysis process. It works with an examplary 'messaging
 * framework'. The precise analysis process is configured by the command line.
 *
 * [1] "syntactic" --> receive loop handles chunks which are expected not to 
 *                     cut in between matching lexemes.
 *     "arbitrary" --> chunks may be cut in between lexemes.
 *
 * [2] "fill"      --> content is provided by user filling as dedicated region.
 *     "copy"      --> user provides content to be copied into its 'place'.
 *
 * [3] "converter" --> the input is fed into a converter before it reaches 
 *                     the engine's buffer.
 *     "direct"    --> the input directly reaches the engines buffer.        */
{        
    quex_tiny_lexer   qlex;
    MemoryChunk       chunk = { 0, 0 };
    quex_Token        token[2];       /* For 'syntactic', the second token
    *                                  * is redundant.                       */
    quex_Token*       prev_token;     /* For 'syntactic', the previous token
    *                                  * is meaningless.                     */
    Configuration     cfg;

    if( ! Configuration_from_command_line(&cfg, argc, argv) ) {
        printf("Error, not enough command line arguments.\n");
        return -1;
    }

    {
        prev_token = cfg.construct(&qlex, &token[0], cfg.codec_name);

        while( 1 + 1 == 2 ) {
            cfg.provide_content(&qlex, &chunk);

            if( ! cfg.receive_loop(&qlex, &prev_token) ) break;
        }

        cfg.destruct(&qlex, &token[0]);
    }

    return 0;
}

static bool
Configuration_from_command_line(Configuration* p, int argc, char** argv)
/* Interpret command line to configure the analysis process 
 *                                                                           */
{
    if(argc < 4) return false;

    if( strcmp(argv[1], "syntactic") == 0 ) {
        p->construct    = construct_with_single_token;
        p->destruct     = destruct_with_single_token;
        p->receive_loop = receive_loop_syntactic_chunks;
    } else {
        p->construct    = construct_with_token_bank;
        p->destruct     = destruct_with_token_bank;
        p->receive_loop = receive_loop_arbitrary_chunks;
    }
    p->provide_content = (strcmp(argv[2], "copy") == 0) ? content_copy : content_fill;
    p->codec_name      = (strcmp(argv[3], "converter") == 0) ? "UTF8" : (const char*)0;

    return true;
}

static quex_Token*
construct_with_single_token(quex_tiny_lexer* lexer, quex_Token* token, const char* CodecName)
{
    quex_Token_construct(token);
    quex_tiny_lexer_from_ByteLoader(lexer, (ByteLoader*)0, CodecName);

    /* -- LOOP until 'bye' token arrives */
    (void)QUEX_NAME(token_p_swap)(lexer, token);

    return (quex_Token*)0;
}

static void
destruct_with_single_token(quex_tiny_lexer* lexer, quex_Token* token)
{
    QUEX_NAME(destruct)(lexer);
    QUEX_NAME_TOKEN(destruct)(token);
}

static quex_Token*
construct_with_token_bank(quex_tiny_lexer*  lexer, quex_Token* token_bank, const char* CodecName)
{
    quex_Token*           prev_token;

    /* Initialize analyzer.                                                  */
    quex_tiny_lexer_from_ByteLoader(lexer, (ByteLoader*)0, CodecName);

    /* initialize token objects.                                             */
    quex_Token_construct(&token_bank[0]);
    quex_Token_construct(&token_bank[1]);
    token_bank[0]._id = QUEX_TKN_TERMINATION;

    /* Give the analyzer a token to prepare.                                 */
    prev_token = &(token_bank[1]);
    QUEX_NAME(token_p_swap)(lexer, &token_bank[0]);

    return prev_token;
}

static void
destruct_with_token_bank(quex_tiny_lexer* lexer, quex_Token* token_bank)
{
    QUEX_NAME(destruct)(lexer);
    QUEX_NAME_TOKEN(destruct)(&token_bank[0]);
    QUEX_NAME_TOKEN(destruct)(&token_bank[1]);
}

static void
content_copy(quex_tiny_lexer* lexer, MemoryChunk* chunk)
{
    QUEX_TYPE_CHARACTER*  rx_buffer = 0x0;  /* A pointer to the receive buffer 
    *                                        * of the messaging framework.   */
    size_t                received_n = (size_t)-1;

    /* NOTE: 'chunk' is initialized to '{ 0, 0 }'.
     *       => safe to assume that 'begin_p == end_p' upon first run.       */

    /* Receive content from some messaging framework.                        */
    if( chunk->begin_p == chunk->end_p ) {                                   
        /* If the receive buffer has been read, it can be released.          */
        if( ! rx_buffer ) messaging_framework_release(rx_buffer);            
        /* Receive and set 'begin' and 'end' of incoming chunk.              */
        received_n  = messaging_framework_receive(&rx_buffer);               
        chunk->begin_p     = rx_buffer;                                      
        chunk->end_p       = chunk->begin_p + received_n;                    
    } else {                                                                 
        /* If begin_p != end_p => first digest remainder.                    */
    }

    /* Copy buffer content into the analyzer's buffer-as much as possible.
     * 'fill()' returns a pointer to the first not-eaten byte.               */
    chunk->begin_p = lexer->buffer.fill(&lexer->buffer, 
                                        chunk->begin_p, chunk->end_p);
}

static void
content_fill(quex_tiny_lexer* lexer, MemoryChunk* chunk)
{
    size_t received_n = (size_t)-1;

    /* Initialize the filling of the fill region                             */
    lexer->buffer.fill_prepare(&lexer->buffer, 
                               (void**)&chunk->begin_p, (const void**)&chunk->end_p);

    /* Call the low level driver to fill the fill region                     */
    received_n = messaging_framework_receive_into_buffer(chunk->begin_p, 
                                                         chunk->end_p - chunk->begin_p); 

    /* Current token becomes previous token of next run.                     */
    lexer->buffer.fill_finish(&lexer->buffer, &chunk->begin_p[received_n]);
}

static bool
receive_loop_syntactic_chunks(quex_tiny_lexer* lexer, quex_Token** prev_token)
/* Loop until the 'TERMINATION' token arrives. Here, considering input which 
 * is 'chunked' at syntax boarders, the 'prev_token' is not considered.
 *                                                                      
 * RETURNS: true, if analysis may continue; BYE has not been received.
 *          false, if analysis may NOT continue; BYE has been received.      */
{
    QUEX_TYPE_TOKEN_ID    token_id;
    (void)prev_token; 

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
receive_loop_arbitrary_chunks(quex_tiny_lexer* lexer, quex_Token** prev_token_p)
/* Loop over received tokens until 'TERMINATION' or 'BYE' occurs. The previous
 * token must be tracked to identify a 'BYE, TERMINATION' sequence. The 
 * start of the lexeme must be tracked, so that after re-filling the inter-
 * rupted match cycle may restart. 
 *
 * RETURNS: true, if analysis may continue; BYE has not been received.
 *          false, if analysis may NOT continue; BYE has been received.      */
{
    quex_Token*           prev_token;       /* Used  or swapping tokens.     */
    QUEX_TYPE_TOKEN_ID    token_id;
    QUEX_TYPE_CHARACTER*  prev_lexeme_start_p;

    /* Loop until 'TERMINATION' or 'BYE' is received.                   
     *   TERMINATION => possible reload                               
     *   BYE         => end of game                                          */
    token_id = (QUEX_TYPE_TOKEN_ID)-1;
    while( 1 + 1 == 2 ) {
        prev_lexeme_start_p = QUEX_NAME(lexeme_start_pointer_get)(lexer);

        /* Current token becomes previous token of next run.                 */
        prev_token = QUEX_NAME(token_p_swap)(lexer, prev_token);

        token_id = QUEX_NAME(receive)(lexer);
        if( token_id == QUEX_TKN_TERMINATION || token_id == QUEX_TKN_BYE )
            break;
        if( prev_token->_id != QUEX_TKN_TERMINATION ) 
            print_token(prev_token);
    }

    if( token_id == QUEX_TKN_BYE ) return false;

    /* Reset the 'read_p' to restart the interrupted match cycle.            */
    QUEX_NAME(input_pointer_set)(lexer, prev_lexeme_start_p);
    return true;
}

static void
print_token(quex_Token*  token)
{
    size_t PrintBufferSize = 1024;
    char   print_buffer[1024];

    printf("Consider: %s\n", QUEX_NAME_TOKEN(get_string)(token, 
                                                         print_buffer, 
                                                         PrintBufferSize));
}

