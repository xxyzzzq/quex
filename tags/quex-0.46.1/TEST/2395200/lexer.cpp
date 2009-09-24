#include<fstream>    
#include<fstream> 
#include <./Simple>
#include<quex/code_base/test_environment/StrangeStream>


using namespace std;

int 
main(int argc, char** argv) 
{        
    // we want to have error outputs in stdout, so that the unit test could see it.
    quex::Token                    token;
    ifstream                       istr("example.txt");
    quex::StrangeStream<ifstream>  strange_stream(&istr);
    quex::Simple                   qlex(&strange_stream);

    cout << "## An Assert-Abortion might be an intended element of the experiment.\n";
    do {
        qlex.receive(&token);
        if( token.type_id() != QUEX_TKN_TERMINATION ) { cout << string(token) << endl; } 
        else                                          { cout << token.type_id_name() << endl; }
    } while( token.type_id() != QUEX_TKN_TERMINATION );

    return 0;
}

