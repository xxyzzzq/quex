#include <stdio.h>

#include "tiny_lexer.h"
#include "messaging-framework.h"

static quex_Token* construct_with_token_bank(quex_tiny_lexer*  lexer, quex_Token* token_bank);
static void        destruct_with_token_bank(quex_tiny_lexer* lexer, quex_Token* token_bank);
static void        print_token(quex_Token*  token);
static void        fill(quex_tiny_lexer* lexer, MemoryChunk* chunk);
static bool        receive_loop_arbitrary_chunks(quex_tiny_lexer* lexer, quex_Token** prev_token_p);

int 
main(int argc, char** argv) 
{        
    quex_tiny_lexer  qlex;
    quex_Token       token_bank[2];         /* 2 for current & look ahead.   */
    MemoryChunk      current_chunk = { 0, 0 }; 
    quex_Token*      prev_token;

    prev_token = construct_with_token_bank(&qlex, &token_bank[0]);

    /* LOOP until 'BYE' token arrives, followed by 'TERMINATION'             */
    while( 1 + 1 == 2 ) {
        fill(&qlex, &current_chunk);

        if( ! receive_loop_arbitrary_chunks(&qlex, &prev_token) ) break;
    }

    destruct_with_token_bank(&qlex, &token_bank[0]);
    return 0;
}

static quex_Token*
construct_with_token_bank(quex_tiny_lexer*  lexer, quex_Token* token_bank)
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
destruct_with_token_bank(quex_tiny_lexer* lexer, quex_Token* token_bank)
{
    QUEX_NAME(destruct)(lexer);
    QUEX_NAME_TOKEN(destruct)(&token_bank[0]);
    QUEX_NAME_TOKEN(destruct)(&token_bank[1]);
}

static bool
receive_loop_arbitrary_chunks(quex_tiny_lexer* lexer, quex_Token** prev_token_p)
{
    quex_Token*           prev_token;       /* Used  or swapping tokens.     */
    QUEX_TYPE_TOKEN_ID    token_id;
    QUEX_TYPE_CHARACTER*  prev_lexeme_start_p;

    /* Loop until 'TERMINATION' or 'BYE' is received.                   
     *   TERMINATION => possible reload                               
     *   BYE         => end of game                                      */
    token_id = (QUEX_TYPE_TOKEN_ID)-1;
    while( 1 + 1 == 2 ) {
        prev_lexeme_start_p = QUEX_NAME(lexeme_start_pointer_get)(lexer);

        /* Current token becomes previous token of next run.             */
        prev_token = QUEX_NAME(token_p_swap)(lexer, prev_token);

        token_id = QUEX_NAME(receive)(lexer);
        if( token_id == QUEX_TKN_TERMINATION || token_id == QUEX_TKN_BYE )
            break;
        if( prev_token->_id != QUEX_TKN_TERMINATION ) 
            print_token(prev_token);
    }

    if( token_id == QUEX_TKN_BYE ) return false;

    /* Reset the 'read_p' to restart the interrupted match cycle.        */
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

