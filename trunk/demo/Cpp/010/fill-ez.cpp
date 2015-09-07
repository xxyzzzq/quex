#include<fstream>    
#include<iostream> 
#include<sstream> 

#include "tiny_lexer"
#include "messaging-framework.h"

size_t 
messaging_framework_receive_into_buffer(QUEX_TYPE_CHARACTER*, size_t);

int 
main(int argc, char** argv) 
{        
    using namespace std;

    quex::Token          token;
    quex::tiny_lexer     qlex((QUEX_TYPE_CHARACTER*)0x0, 0); /* No args to constructor --> raw memory */
    QUEX_TYPE_CHARACTER* begin_p = 0;
    QUEX_TYPE_CHARACTER* end_p = 0;

    (void)qlex.token_p_swap(&token);
    while( 1 + 1 == 2 ) {
        // -- Initialize the filling of the fill region
        qlex.buffer.filler->fill_prepare(&qlex.buffer, (void**)begin_p, (const void**)end_p);

        // -- Call the low lever driver to fill the fill region
        size_t receive_n = messaging_framework_receive_into_buffer_syntax_chunk(begin_p, end_p - begin_p);

        // -- Inform the buffer about the number of loaded characters NOT NUMBER OF BYTES!
        qlex.buffer.filler->fill_finish(&qlex.buffer, &begin_p[receive_n]);

        // -- Loop until the 'termination' token arrives
        while( 1 + 1 == 2 ) {
            const QUEX_TYPE_TOKEN_ID TokenID = qlex.receive();

            if( TokenID == QUEX_TKN_TERMINATION ) break;
            if( TokenID == QUEX_TKN_BYE )         return 0;

            cout << "Consider: " << string(token) << endl;
        }
    }

    return 0;
}

