#include <stdio.h>

#include "tiny_lexer.h"
#include "messaging-framework.h"

static quex_Token* init(quex_tiny_lexer*  lexer, quex_Token* token_bank);
static void        print_token(quex_Token*  token);
static void        fill(quex_tiny_lexer* lexer, MemoryChunk* chunk);

int 
main(int argc, char** argv) 
{        
    quex_tiny_lexer       qlex;

    quex_Token            token_bank[2];    /* 2 for current & look ahead.   */
    quex_Token*           prev_token;       /* Used  or swapping tokens.     */

    MemoryChunk           current_chunk = { 0, 0 }; 

    QUEX_TYPE_CHARACTER*  prev_lexeme_start_p = 0x0; /* backup start of the
    *                                                 * lexeme.              */    
    QUEX_TYPE_TOKEN_ID    token_id   = (QUEX_TYPE_TOKEN_ID)-1;

    /* Call constructors for analyzer and token bank.                        */
    prev_token = init(&qlex, &token_bank[0]);

    /* LOOP until 'BYE' token arrives, followed by 'TERMINATION'             */
    while( 1 + 1 == 2 ) {
        fill(&qlex, &current_chunk);

        /* Loop until 'TERMINATION' or 'BYE' is received.                   
         *   TERMINATION => possible reload                               
         *   BYE         => end of game                                      */
        token_id = (QUEX_TYPE_TOKEN_ID)-1;
        while( 1 + 1 == 2 ) {
            prev_lexeme_start_p = QUEX_NAME(lexeme_start_pointer_get)(&qlex);
            
            /* Current token becomes previous token of next run.             */
            prev_token = QUEX_NAME(token_p_swap)(&qlex, prev_token);

            token_id = QUEX_NAME(receive)(&qlex);
            if( token_id == QUEX_TKN_TERMINATION || token_id == QUEX_TKN_BYE )
                break;
            if( prev_token->_id != QUEX_TKN_TERMINATION ) 
                print_token(prev_token);
        }

        if( token_id == QUEX_TKN_BYE ) break; /* End of sequence of chunks.  */

        /* Reset the 'read_p' to restart the interrupted match cycle.        */
        QUEX_NAME(input_pointer_set)(&qlex, prev_lexeme_start_p);
    }

    QUEX_NAME(destruct)(&qlex);
    QUEX_NAME_TOKEN(destruct)(&token_bank[0]);
    QUEX_NAME_TOKEN(destruct)(&token_bank[1]);
    return 0;
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

static quex_Token*
init(quex_tiny_lexer*  lexer, quex_Token* token_bank)
{
    quex_Token* prev_token;

    /* Initialize analyzer.                                                  */
    quex_tiny_lexer_from_ByteLoader(lexer, (ByteLoader*)0, 0);

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
fill(quex_tiny_lexer* lexer, MemoryChunk* chunk)
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
