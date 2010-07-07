#include <string.h>
#include<fstream>    
#include<iostream> 

#include "Simple"

int 
main(int argc, char** argv) 
{        
    using namespace std;
    const static size_t MESSAGING_FRAMEWORK_BUFFER_SIZE = 10000;
    uint8_t MESSAGING_FRAMEWORK_BUFFER[MESSAGING_FRAMEWORK_BUFFER_SIZE];
    quex::Token*   token;
    quex::Simple   qlex(MESSAGING_FRAMEWORK_BUFFER, MESSAGING_FRAMEWORK_BUFFER_SIZE); 

    // -- Call the low lever driver to fill the fill region
    const char* str = "struct";
    size_t receive_n = strlen(str);
    memcpy(MESSAGING_FRAMEWORK_BUFFER, str, receive_n*sizeof(char));
    
    // -- Inform the buffer about the number of loaded characters NOT NUMBER OF BYTES!
    qlex.buffer_fill_region_finish(receive_n);

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


 	  	 
