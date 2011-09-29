#include <string.h>
#include<fstream>    
#include<iostream> 

#include "Simple"

int 
main(int argc, char** argv) 
{        
    using namespace std;
    const static size_t BUFFER_SIZE = 10000;
    uint8_t             BUFFER[BUFFER_SIZE];
    quex::Token*   token_p;
    quex::Simple   qlex(BUFFER, BUFFER_SIZE, BUFFER + 1); 

    // -- Call the low lever driver to fill the fill region
    const char* str  = "bye";
    size_t      receive_n = strlen(str);
    memcpy(BUFFER + 1, str, receive_n*sizeof(char));
    
    // -- Inform the buffer about the number of loaded characters NOT NUMBER OF BYTES!
    qlex.buffer_fill_region_finish(receive_n);

    // -- Loop until the 'termination' token_p arrives
    do {
        qlex.receive(&token_p);

        cout << token_p->get_string() << endl;

    } while( token_p->type_id() != QUEX_TKN_TERMINATION );

    return 0;
}


 	  	 
