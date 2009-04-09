#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include <./tiny_lexer>
#include <./tiny_lexer-token_ids>

using namespace std;

QUEX_TYPE_CHARACTER  EmptyLexeme = 0x0000;  /* Only the terminating zero */

void    print(quex::tiny_lexer& qlex, quex::Token& Token, bool TextF = false);
void    print(quex::tiny_lexer& qlex, const char* Str1, const char* Str2=0x0, const char* Str3=0x0);

int 
main(int argc, char** argv) 
{        
    // (*) create token
    quex::Token       my_token;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::tiny_lexer  qlex(argc == 1 ? "example.txt" : argv[1]);

    // (*) print the version 
    // cout << qlex.version() << endl << endl;

    cout << ",------------------------------------------------------------------------------------\n";
    cout << "| [START]\n";

    int  number_of_tokens = 0;
    bool continue_lexing_f = true;
    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
        qlex.receive(&my_token);

        // (*) print out token information
        //     -- name of the token
        print(qlex, my_token, (const char*)my_token.text().c_str());

        if( my_token.type_id() == QUEX_TKN_INCLUDE ) { 
            qlex.receive(&my_token);
            print(qlex, my_token, (const char*)my_token.text().c_str());
            if( my_token.type_id() != QUEX_TKN_IDENTIFIER ) {
                continue_lexing_f = false;
                print(qlex, "found 'include' without a subsequent filename. hm?\n");
                break;
            }
            print(qlex, ">> including: ", (const char*)my_token.text().c_str());
            qlex.include_push<FILE>(my_token.text().c_str());
            break;
        }
        else if( my_token.type_id() == QUEX_TKN_TERMINATION ) {
            if( qlex.include_pop() == false ) 
                continue_lexing_f = false;
            else 
                print(qlex, "<< return from include\n");
        }

        ++number_of_tokens;

        // (*) check against 'termination'
    } while( continue_lexing_f );

    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";

    return 0;
}

string  space(int N)
{ string tmp; for(int i=0; i<N; ++i) tmp += "    "; return tmp; }

void  print(quex::tiny_lexer& qlex, quex::Token& my_token, bool TextF /* = false */)
{ 
    cout << space(qlex.include_depth) << my_token.line_number() << ": (" << my_token.column_number() << ")";
    cout << my_token.type_id_name();
    if( TextF ) cout << "\t'" << my_token.text().c_str() << "'";
    cout << endl;
}

void print(quex::tiny_lexer& qlex, const char* Str1, const char* Str2 /* = 0x0 */, const char* Str3 /* = 0x0*/)
{
    cout << space(qlex.include_depth) << Str1;
    if( Str2 != 0x0 ) cout << Str2;
    if( Str3 != 0x0 ) cout << Str3;
    cout << endl;
}
