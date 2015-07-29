#include<fstream>    
#include<iostream> 
extern "C" {
#include<assert.h> 
}

#ifndef    PRINT_TOKEN_FIRST_NUMBER 
#   define PRINT_TOKEN_FIRST_NUMBER 0
#endif

// (*) include lexical analyser header
#include "Simple"

using namespace std;

#ifndef   TEST_EPILOG
#   define TEST_EPILOG \
    printf("| [END] number of token = %li\n", token_n); \
    printf("`------------------------------------------------------------------------------------\n");
#endif

int main(int argc, char** argv) 
{
    assert(argc > 1);

    // (*) create token
    quex::Token*   token_p;
    long           token_n = 0;
#   ifdef QUEX_OPTION_TOKEN_POLICY_SINGLE
    QUEX_TYPE_TOKEN_ID token_id = (QUEX_TYPE_TOKEN_ID)0x0;
#   endif
    // (*) create the lexical analyser
#   if defined (QUEX_OPTION_CONVERTER_ICU) || defined (QUEX_OPTION_CONVERTER_ICONV)
    quex::Simple*  qlex = new quex::Simple(argv[1], "UTF-8");
#   else
    quex::Simple*  qlex = new quex::Simple(argv[1]);
#   endif

    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
#       ifdef QUEX_OPTION_TOKEN_POLICY_SINGLE
        token_id = qlex->receive();
#       else
        qlex->receive(&token_p);
#       endif

        // (*) print out token information
        cerr.flush();
        if( token_n >= PRINT_TOKEN_FIRST_NUMBER ) {
#           if defined (QUEX_OPTION_CONVERTER_ICU) || defined (QUEX_OPTION_CONVERTER_ICONV)
            cout << *token_p << endl;
#           else
            cout << (const char*)(token_p->type_id_name().c_str());
            cout << " '";
            cout << (const char*)(token_p->get_text().c_str());
            cout << "' " << endl;
#           endif
            cout.flush();
        }
        ++token_n;

        // (*) check against 'termination'
#   ifdef QUEX_OPTION_TOKEN_POLICY_SINGLE
    } while( token_id != QUEX_TKN_TERMINATION );
#   else
    } while( token_p->_id != QUEX_TKN_TERMINATION );
#   endif

    TEST_EPILOG

    delete qlex;
}
