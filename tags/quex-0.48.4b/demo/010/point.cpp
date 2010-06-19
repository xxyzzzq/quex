#include<fstream>    
#include<iostream> 
#include<sstream> 

#include "tiny_lexer"
#include "messaging-framework.h"

int 
main(int argc, char** argv) 
{        
    using namespace std;

    quex::Token*       token;
    quex::tiny_lexer   qlex(MESSAGING_FRAMEWORK_BUFFER, MESSAGING_FRAMEWORK_BUFFER_SIZE); 

    // -- Call the low lever driver to fill the fill region
    size_t receive_n = messaging_framework_receive_to_internal_buffer();

    // -- Inform the buffer about the number of loaded characters NOT NUMBER OF BYTES!
    qlex.buffer_fill_region_finish(receive_n-1);

    // -- Loop until the 'termination' token arrives
    token = qlex.token_p();
    do {
        qlex.receive();

        if( token->type_id() == QUEX_TKN_BYE ) 
            cout << "## ";

        if( token->type_id() != QUEX_TKN_TERMINATION )
            cout << "Consider: " << string(*token) << endl;
        
    } while( token->type_id() != QUEX_TKN_TERMINATION );

    return 0;
}

