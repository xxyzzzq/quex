#include<fstream>    
#include<iostream> 
#include<sstream> 

#include "tiny_lexer"
#include "messaging-framework.h"

int 
main(int argc, char** argv) 
{        
    using namespace std;

    quex::Token        token;           
    quex::tiny_lexer   qlex(MESSAGING_FRAMEWORK_BUFFER, 
                            MESSAGING_FRAMEWORK_BUFFER_SIZE,
                            MESSAGING_FRAMEWORK_BUFFER + 1); 

    // Iterate 3 times doing the same thing in order to illustrate
    // the repeated activation of the same chunk of memory.
    for(int i = 0; i < 3; ++i ) {
        // -- Call the low lever driver to fill the fill region
        size_t receive_n = messaging_framework_receive_to_internal_buffer();

        // -- Inform the buffer about the number of loaded characters NOT NUMBER OF BYTES!
        qlex.buffer_fill_region_finish(receive_n-1);
        // -- Each time the buffer is filled, the input pointer must be reset
        //    (Here, it is just to display the principle, ...)
        qlex.buffer_input_pointer_set(MESSAGING_FRAMEWORK_BUFFER + 1);

        // QUEX_NAME(Buffer_show_byte_content)(&qlex.buffer, 5);

        // -- Loop until the 'termination' token arrives
        (void)qlex.token_p_switch(&token);
        do {
            qlex.receive();

            if( token.type_id() != QUEX_TKN_TERMINATION )
                cout << "Consider: " << string(token) << endl;

            if( token.type_id() == QUEX_TKN_BYE ) 
                cout << "##\n";

        } while( token.type_id() != QUEX_TKN_TERMINATION );
    }

    return 0;
}

