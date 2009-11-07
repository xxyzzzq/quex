#include<fstream>    
#include<iostream> 
#include<sstream> 

#include "tiny_lexer"
#include "messaging-framework.h"

typedef struct {
    QUEX_TYPE_CHARACTER* begin;
    QUEX_TYPE_CHARACTER* end;
} MemoryChunk;

void swap(QUEX_TYPE_TOKEN** A, QUEX_TYPE_TOKEN** B)
{ QUEX_TYPE_TOKEN* tmp = *A; *A = *B; *B = tmp; }

int 
main(int argc, char** argv) 
{        
    using namespace std;

    quex::tiny_lexer  qlex((QUEX_TYPE_CHARACTER*)0x0, 0);   // No args to constructor --> raw memory 

    quex::Token    token_bank[2];     // Two tokens required, one for look-ahead
    quex::Token*   prev_token;        // Use pointers to swap quickly.
    quex::Token*   current_token;     // 

    QUEX_TYPE_CHARACTER*  rx_buffer = 0x0;  // A pointer to the receive buffer that
    //                                      // the messaging framework provides.

    MemoryChunk           chunk;      // Pointers to the memory positions under
    //                                // consideration.

    QUEX_TYPE_CHARACTER*  prev_lexeme_start_p = 0x0; // Store the start of the 
    //                                               // lexeme for possible 
    //                                               // backup.

    // -- initialize the token pointers
    prev_token    = &(token_bank[1]);
    current_token = &(token_bank[0]);
    current_token->set(QUEX_TKN_TERMINATION);
    //
    // -- trigger reload of memory
    chunk.begin = chunk.end;

    // -- LOOP until 'bye' token arrives
    while( 1 + 1 == 2 ) {
        // -- Receive content from a messaging framework
        //    The function 'buffer_fill_region_append()' may possibly not
        //    concatinate all content, so it needs to be tested wether new
        //    content needs to be loaded.
        if( chunk.begin == chunk.end ) {
            // -- If the receive buffer has been read, it can be released.
            if( rx_buffer != 0x0 ) messaging_framework_release(rx_buffer);
            // -- Setup the pointers 
            const size_t Size  = messaging_framework_receive(&rx_buffer);
            chunk.begin = rx_buffer;
            chunk.end   = chunk.begin + Size;
        } else {
            // If chunk.begin != chunk.end, this means that there are still
            // some characters in the pipeline. Let us use them first.
        }

        // -- Copy buffer content into the analyzer's buffer
        //    (May be, not all content can be copied into the buffer, in 
        //     this case the '_append(...)' function returns a position
        //     different from 'chunk.end'. This would indicate the there
        //     are still bytes left. The next call of '_apend(...)' will
        //     deal with it.)
        chunk.begin = qlex.buffer_fill_region_append(chunk.begin, chunk.end);

        // -- Loop until the 'termination' token arrives
        while( 1 + 1 == 2 ) {
            prev_lexeme_start_p = qlex.buffer_lexeme_start_pointer_get();
            
            // Let the previous token be the current token of the previous run.
            swap(&prev_token, &current_token);

            qlex.receive(current_token);

            // TERMINATION => possible reload
            // BYE         => end of game
            if( current_token->type_id() == QUEX_TKN_TERMINATION || current_token->type_id() == QUEX_TKN_BYE )
                break;

            // If the previous token was not a TERMINATION, it can be considered
            // by the syntactical analyzer (parser).
            if( prev_token->type_id() != QUEX_TKN_TERMINATION )
                cout << "Consider: " << string(*prev_token) << endl;
        }

        // -- If the 'bye' token appeared, leave!
        if( current_token->type_id() == QUEX_TKN_BYE ) break;

        // -- Reset the input pointer, so that the last lexeme before TERMINATION
        //    enters the matching game again.
        qlex.buffer_input_pointer_set(prev_lexeme_start_p);
    }

    return 0;
}

