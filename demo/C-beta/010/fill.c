#include <stdio.h>

#include "tiny_lexer"

size_t 
messaging_framework_receive_into_buffer(QUEX_TYPE_CHARACTER*, size_t);

int 
main(int argc, char** argv) 
{        
    using namespace std;

    QUEX_TYPE_TOKEN           token_bank[2];
    QUEX_TYPE_TOKEN*          prev_token;
    tiny_lexer      qlex((QUEX_TYPE_CHARACTER*)0x0, 0); /* No args to constructor --> raw memory */
    QUEX_TYPE_CHARACTER*  prev_lexeme_start_p = 0x0;

    // -- initialize the token pointers
    prev_token = &(token_bank[1]);
    token_bank[0].set(QUEX_TKN_TERMINATION);
    qlex.token_p_switch(&token_bank[0]);

    while( 1 + 1 == 2 ) {
        // -- Initialize the filling of the fill region
        qlex.buffer_fill_region_prepare();

        // -- Call the low lever driver to fill the fill region
        size_t receive_n = messaging_framework_receive_into_buffer(qlex.buffer_fill_region_begin(), 
                                                                   qlex.buffer_fill_region_size());

        // -- Inform the buffer about the number of loaded characters NOT NUMBER OF BYTES!
        qlex.buffer_fill_region_finish(receive_n);

        // -- Loop until the 'termination' token arrives
        QUEX_TYPE_TOKEN_ID   token_id = 0;
        while( 1 + 1 == 2 ) {
            prev_lexeme_start_p = qlex.buffer_lexeme_start_pointer_get();
            
            // Let the previous token be the current token of the previous run.
            prev_token = qlex.token_p_switch(prev_token);

            token_id = qlex.receive();
            if( token_id == QUEX_TKN_TERMINATION || token_id == QUEX_TKN_BYE )
                break;
            if( prev_token->type_id() != QUEX_TKN_TERMINATION ) 
                cout << "Consider: " << string(*prev_token) << endl;
        }

        if( token_id == QUEX_TKN_BYE ) break;

        qlex.buffer_input_pointer_set(prev_lexeme_start_p);
    }

    return 0;
}

