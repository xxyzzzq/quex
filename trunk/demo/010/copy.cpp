#include<fstream>    
#include<iostream> 
#include<sstream> 

#include "tiny_lexer"
#include "messaging-framework.h"

typedef struct {
    QUEX_TYPE_CHARACTER* begin;
    QUEX_TYPE_CHARACTER* end;
    size_t               size;
} MemoryChunk;

void swap(QUEX_TYPE_TOKEN** A, QUEX_TYPE_TOKEN** B)
{ QUEX_TYPE_TOKEN* tmp = *A; *A = *B; *B = tmp; }

int 
main(int argc, char** argv) 
{        
    using namespace std;

    quex::Token    token_bank[2];
    quex::Token*   prev_token;
    quex::Token*   current_token;

    quex::tiny_lexer      qlex;   /* No args to constructor --> raw memory */
    QUEX_TYPE_CHARACTER*  msg = 0x0;
    MemoryChunk           chunk;
    QUEX_TYPE_CHARACTER*  prev_lexeme_start_p = 0x0;

    prev_token    = &(token_bank[1]);
    current_token = &(token_bank[0]);
    current_token->set(QUEX_TKN_TERMINATION);
    chunk.begin = chunk.end;
    while( 1 + 1 == 2 ) {
        // -- Receive content from a messaging framework
        //    The function 'buffer_fill_region_append()' may possibly not
        //    concatinate all content, so it needs to be tested wether new
        //    content needs to be loaded.
        if( chunk.begin == chunk.end ) {
            if( msg != 0x0 ) messaging_framework_release(msg);
            chunk.size  = messaging_framework_receive(&msg);
            chunk.begin = msg;
            chunk.end   = chunk.begin + chunk.size;
        } else {
            // If chunk.begin != chunk.end, this means that there are still
            // some characters in the pipeline. Let us use them first.
        }

        // -- Copy buffer content into the analyzer's buffer
        chunk.begin = qlex.buffer_fill_region_append(chunk.begin, chunk.end);

        // -- Loop until the 'termination' token arrives
        while( 1 + 1 == 2 ) {
            prev_lexeme_start_p = qlex.buffer_lexeme_start_pointer_get();
            
            swap(&prev_token, &current_token);

            qlex.receive(current_token);

            if( current_token->type_id() == QUEX_TKN_TERMINATION || current_token->type_id() == QUEX_TKN_BYE )
                break;

            if( prev_token->type_id() != QUEX_TKN_TERMINATION )
                cout << "Consider: " << string(*prev_token) << endl;
        }

        // -- If the 'end of all' token appeared, leave!
        if( current_token->type_id() == QUEX_TKN_BYE ) break;

        qlex.buffer_input_pointer_set(prev_lexeme_start_p);
    }

    return 0;
}

