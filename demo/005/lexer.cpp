#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include <./tiny_lexer>
#include <./tiny_lexer-token_ids>

using namespace std;

int 
main(int argc, char** argv) 
{        
    // (*) create token
    quex::token        Token;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::tiny_lexer*  qlex = new quex::tiny_lexer(argc == 1 ? "example.txt" : argv[1]);

    // (*) print the version 
    // cout << qlex->version() << endl << endl;

    cout << ",------------------------------------------------------------------------------------\n";
    cout << "| [START]\n";

    int  number_of_tokens = 0;
    bool continue_lexing_f = true;
    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
        qlex->get_token(&Token);

        // (*) print out token information
        //     -- name of the token
        cout << Token.type_id_name() << "\t" << Token.text() << endl;

        switch( Token.type_id() ) {
        default: 
            break;

        case TKN_INCLUDE: 
            {
                qlex->get_token(&Token);
                cout << Token.type_id_name() << "\t" << Token.text() << endl;
                if( Token.type_id() != TKN_IDENTIFIER ) {
                    cout << "found 'include' without a subsequent filename. hm?\n";
                    break;
                }
               
                cout << ">> including: " << Token.text() << endl;
                FILE* fh = fopen(Token.text().c_str(), "r");
                qlex->include_stack_push(fh);
                break;
                
            }
        case quex::token::ID_TERMINATION:
            if( qlex->include_stack_pop() == false ) continue_lexing_f = false;
            else                                     cout << "<< return from include\n";
            break;
        }


        ++number_of_tokens;

        // (*) check against 'termination'
    } while( continue_lexing_f );

    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";

    return 0;
}
