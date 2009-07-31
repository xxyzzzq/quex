#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "Simple"

using namespace std;

int main(int argc, char** argv) 
{
    // (*) create token
    quex::Token    Token;
    // (*) create the lexical analyser
#   if defined (QUEX_OPTION_ENABLE_ICU) || defined (QUEX_OPTION_ENABLE_ICONV)
    quex::Simple*  qlex = new quex::Simple(argv[1], "UTF-8");
#   else
    quex::Simple*  qlex = new quex::Simple(argv[1]);
#   endif

    // (*) loop until the 'termination' token arrives
    while (true) {
        // (*) get next token from the token stream
        qlex->receive(&Token);

        // (*) check against 'termination'
        if (Token.type_id() == QUEX_TKN_TERMINATION)
            break;
        // (*) print out token information
#   if defined (QUEX_OPTION_ENABLE_ICU) || defined (QUEX_OPTION_ENABLE_ICONV)
        cout << Token << endl;
#   else
        cout << (const char*)(Token.type_id_name().c_str()) << " '" << (const char*)(Token.text().c_str()) << "' " << endl;
#   endif
    }
}
