#include <stdio.h>

#include "tiny_lexer.h"
#include "messaging-framework.h"

static quex_Token* construct_with_token_bank(quex_tiny_lexer*  lexer, quex_Token* token_bank);
static void        destruct_with_token_bank(quex_tiny_lexer* lexer, quex_Token* token_bank);
static void        print_token(quex_Token*  token);
static void        copy(quex_tiny_lexer* lexer, MemoryChunk* chunk);
static bool        receive_loop_arbitrary_chunks(quex_tiny_lexer* lexer, quex_Token** prev_token_p);

int 
main(int argc, char** argv) 
{        
    quex_tiny_lexer       qlex;
    quex_Token            token_bank[2];    /* 2 for current & look ahead.   */
    quex_Token*           prev_token;
    MemoryChunk           current_chunk = { 0, 0 }; 

    prev_token = construct_with_token_bank(&qlex, &token_bank[0]);

    /* LOOP until 'BYE' token arrives, followed by 'TERMINATION'             */
    while( 1 + 1 == 2 ) {
        copy(&qlex, &current_chunk);

        if( ! receive_loop_arbitrary_chunks(&qlex, &prev_token) ) break;
    }

    destruct_with_token_bank(&qlex, &token_bank[0]);

    return 0;
}

static void
copy(quex_tiny_lexer* lexer, MemoryChunk* chunk)
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
print_token(quex_Token*  token)
{
    size_t PrintBufferSize = 1024;
    char   print_buffer[1024];

    printf("Consider: %s\n", QUEX_NAME_TOKEN(get_string)(token, 
                                                         print_buffer, 
                                                         PrintBufferSize));
}

