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
    quex::Simple*  qlex = new quex::Simple(argv[1], "UTF-8");

    // (*) loop until the 'termination' token arrives
    while (true) {
	// (*) get next token from the token stream
	qlex->get_token(&Token);

	// (*) check against 'termination'
	if (Token.type_id() == QUEX_TKN_TERMINATION)
	  break;
	// (*) print out token information
	cout << Token << endl;
    }
}
