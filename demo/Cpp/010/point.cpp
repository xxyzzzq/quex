#include <fstream>
#include <iostream> 
#include <sstream> 

#include "tiny_lexer"
#include "messaging-framework.h"

int 
main(int argc, char** argv) 
{        
    using namespace std;

    quex::Token           token;           
    quex::tiny_lexer*     qlex;
    size_t                receive_n = (size_t)-1;
    int                   i = 0;

    receive_n = messaging_framework_receive_to_internal_buffer();

    __quex_assert( QUEX_SETTING_BUFFER_MIN_FALLBACK_N == 0 );
    qlex = new quex::tiny_lexer(MESSAGING_FRAMEWORK_BUFFER, 
                                MESSAGING_FRAMEWORK_BUFFER_SIZE,
                                &MESSAGING_FRAMEWORK_BUFFER[receive_n]);

    /* Iterate 3 times doing the same thing in order to illustrate
     * the repeated activation of the same chunk of memory.                  */
    for(i = 0; i < 3; ++i ) {
        (void)qlex->token_p_swap(&token);

        /* -- Loop until the 'termination' token arrives                     */
        do {
            qlex->receive();

            if( token.type_id() != QUEX_TKN_TERMINATION )
                printf("Consider: %s\n", string(token).c_str());

            if( token.type_id() == QUEX_TKN_BYE ) 
                printf("##\n");

        } while( token.type_id() != QUEX_TKN_TERMINATION );

        qlex->reset(MESSAGING_FRAMEWORK_BUFFER, 
                    MESSAGING_FRAMEWORK_BUFFER_SIZE,
                    &MESSAGING_FRAMEWORK_BUFFER[receive_n]);
    }

    delete qlex;

    return 0;
}

