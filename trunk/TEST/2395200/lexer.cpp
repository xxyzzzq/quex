#include <fstream>    
#include <fstream> 
#include "EasyLexer"
#include <quex/code_base/test_environment/StrangeStream>


using namespace std;

int 
main(int argc, char** argv) 
{        
    // we want to have error outputs in stdout, so that the unit test could see it.
    quex::Token                    token;
    ifstream                       istr("example.txt");
    quex::StrangeStream<ifstream>  strange_stream(&istr);
    quex::EasyLexer                qlex(&strange_stream);

    cout << "## An Assert-Abortion might be an intended element of the experiment.\n";
    qlex.token_p_set(&token);
    QUEX_TYPE_TOKEN_ID token_id = -1;
    do {
        token_id = qlex.receive();
        if( token_id != QUEX_TKN_TERMINATION ) { cout << string(token) << endl; } 
        else                                   { cout << token.type_id_name() << endl; }
    } while( token_id != QUEX_TKN_TERMINATION );

    return 0;
}

