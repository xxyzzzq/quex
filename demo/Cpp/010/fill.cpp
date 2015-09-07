#include<fstream>    
#include<iostream> 
#include<sstream> 

#include "tiny_lexer"

size_t 
messaging_framework_receive_into_buffer(QUEX_TYPE_CHARACTER*, size_t);

int 
main(int argc, char** argv) 
{        
    using namespace std;

    quex::Token           token_bank[2];
    quex::Token*          prev_token;
    quex::tiny_lexer      qlex((QUEX_TYPE_CHARACTER*)0x0, 0); /* No args to constructor --> raw memory */
    QUEX_TYPE_CHARACTER*  prev_lexeme_start_p = 0x0;
    QUEX_TYPE_CHARACTER*  begin_p = 0;
    QUEX_TYPE_CHARACTER*  end_p = 0;

    // -- initialize the token pointers
    prev_token = &(token_bank[1]);
    token_bank[0].set(QUEX_TKN_TERMINATION);
    qlex.token_p_swap(&token_bank[0]);

    while( 1 + 1 == 2 ) {
        // -- Initialize the filling of the fill region
        qlex.buffer.filler->fill_prepare(&qlex.buffer, (void**)begin_p, (const void**)end_p);

        // -- Call the low lever driver to fill the fill region
        size_t receive_n = messaging_framework_receive_into_buffer(begin_p, end_p - begin_p);

        // -- Inform the buffer about the number of loaded characters NOT NUMBER OF BYTES!
        qlex.buffer.filler->fill_finish(&qlex.buffer, &begin_p[receive_n]);

        // -- Loop until the 'termination' token arrives
        QUEX_TYPE_TOKEN_ID   token_id = 0;
        while( 1 + 1 == 2 ) {
            prev_lexeme_start_p = qlex.lexeme_start_pointer_get();
            
            // Let the previous token be the current token of the previous run.
            prev_token = qlex.token_p_swap(prev_token);

            token_id = qlex.receive();
            if( token_id == QUEX_TKN_TERMINATION || token_id == QUEX_TKN_BYE )
                break;
            if( prev_token->type_id() != QUEX_TKN_TERMINATION ) 
                cout << "Consider: " << string(*prev_token) << endl;
        }

        if( token_id == QUEX_TKN_BYE ) break;

        qlex.input_pointer_set(prev_lexeme_start_p);
    }

    return 0;
}

