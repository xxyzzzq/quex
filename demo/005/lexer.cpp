#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include <./tiny_lexer>
#include <./tiny_lexer-token_ids>

using namespace std;

QUEX_TYPE_CHARACTER  EmptyLexeme = 0x0000;  /* Only the terminating zero */

string space(int N) 
{ string tmp; for(int i=0; i<N; ++i) tmp += "    "; return tmp; }

int 
main(int argc, char** argv) 
{        
    // (*) create token
    quex::Token       Token;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::tiny_lexer  qlex(argc == 1 ? "example.txt" : argv[1]);
    FILE*             fh = 0x0;

    // (*) print the version 
    // cout << qlex.version() << endl << endl;

    cout << ",------------------------------------------------------------------------------------\n";
    cout << "| [START]\n";

    int  number_of_tokens = 0;
    bool continue_lexing_f = true;
    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
        qlex.receive(&Token);

        // (*) print out token information
        //     -- name of the token
        cout << space(qlex.include_depth) << qlex.line_number() << ":  ";
        cout << Token.type_id_name() << "\t" << Token.text().c_str() << endl;

        switch( Token.type_id() ) {
        default: 
            break;

        case QUEX_TKN_INCLUDE: 
            qlex.receive(&Token);
            cout << space(qlex.include_depth) << Token.type_id_name() << "\t" << Token.text().c_str() << endl;
            if( Token.type_id() != QUEX_TKN_IDENTIFIER ) {
                continue_lexing_f = false;
                cout << space(qlex.include_depth) << "found 'include' without a subsequent filename. hm?\n";
                break;
            }

            cout << space(qlex.include_depth) << ">> including: " << Token.text().c_str() << endl;
            fh = fopen((const char*)(Token.text().c_str()), "r");
            if( fh == NULL ) {
                cout << space(qlex.include_depth) << "file not found\n";
                return 0;
            }
            qlex.include_push(fh);
            qlex.parent_memento()->included_file_handle = fh;
            break;

        case QUEX_TKN_TERMINATION:
            fh = qlex.parent_memento()->included_file_handle;
            if( qlex.include_pop() == false ) {
                continue_lexing_f = false;
            } else {
                cout << space(qlex.include_depth) << "<< return from include\n";
                fclose(fh);
            }
            break;
        }


        ++number_of_tokens;

        // (*) check against 'termination'
    } while( continue_lexing_f );

    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";

    return 0;
}
