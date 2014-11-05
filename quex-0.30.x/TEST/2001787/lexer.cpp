#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "Simple"

using namespace std;

int 
main(int argc, char** argv) 
{        
    // (*) create token
    quex::token        Token;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::Simple * qlex = new quex::Simple(argc == 1 ? "example.dat" : argv[1], "UTF-8");

    // (*) print the version 
    // cout << qlex->version() << endl << endl;

    cout << ",------------------------------------------------------------------------------------\n";
    cout << "| [START]\n";

    int number_of_tokens = 0;
    // (*) loop until the 'termination' token arrives
    do {
	// (*) get next token from the token stream
	qlex->get_token(&Token);

	// (*) print out token information
	//     -- name of the token
	cout << string(Token) << endl;

	++number_of_tokens;

	// (*) check against 'termination'
    } while( Token.type_id() != quex::TKN_TERMINATION );

    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";

    return 0;
}
