#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "Simple"

using namespace std;

#ifndef   TEST_EPILOG
#  define TEST_EPILOG /* empty */
#endif

int main(int argc, char** argv) 
{
    // (*) create token
    quex::Token*   token_p;
    // (*) create the lexical analyser
#   if defined (QUEX_OPTION_CONVERTER_ICU) || defined (QUEX_OPTION_CONVERTER_ICONV)
    quex::Simple*  qlex = new quex::Simple(argv[1], "UTF-8");
#   else
    quex::Simple*  qlex = new quex::Simple(argv[1]);
#   endif

    // (*) loop until the 'termination' token arrives
    while (true) {
        // (*) get next token from the token stream
        qlex->receive(&token_p);

        // (*) check against 'termination'
        if (token_p->type_id() == QUEX_TKN_TERMINATION)
            break;
        // (*) print out token information
#   if defined (QUEX_OPTION_CONVERTER_ICU) || defined (QUEX_OPTION_CONVERTER_ICONV)
        cout << *token_p << endl;
#   else
        cout << (const char*)(token_p->type_id_name().c_str());
        cout << " '";
        cout << (const char*)(token_p->get_text().c_str());
        cout << "' " << endl;
#   endif
    }

    TEST_EPILOG

    delete qlex;
}
