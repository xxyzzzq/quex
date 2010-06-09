#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "Simple"

using namespace std;

int main(int argc, char** argv) 
{
    // (*) create token
    quex::Token*   token;
    // (*) create the lexical analyser
#   if defined (QUEX_OPTION_ENABLE_ICU) || defined (QUEX_OPTION_ENABLE_ICONV)
    quex::Simple*  qlex = new quex::Simple(argv[1], "UTF-8");
#   else
    quex::Simple*  qlex = new quex::Simple(argv[1]);
#   endif

    // (*) loop until the 'termination' token arrives
    while (true) {
        // (*) get next token from the token stream
        token = qlex->receive();

        // (*) check against 'termination'
        if (token->type_id() == QUEX_TKN_TERMINATION)
            break;
        // (*) print out token information
#   if defined (QUEX_OPTION_ENABLE_ICU) || defined (QUEX_OPTION_ENABLE_ICONV)
        cout << *token << endl;
#   else
        cout << (const char*)(token->type_id_name().c_str());
        cout << " '";
        cout << (const char*)(token->get_text().c_str());
        cout << "' " << endl;
#   endif
    }
}
