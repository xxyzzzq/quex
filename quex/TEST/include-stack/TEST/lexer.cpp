#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "ISLexer"
#include "ISLexer-token_ids"

using namespace std;

QUEX_TYPE_CHARACTER  EmptyLexeme = 0x0000;  /* Only the terminating zero */

void    print(quex::ISLexer& qlex, quex::Token& Token, bool TextF = false);
void    print(quex::ISLexer& qlex, const char* Str1, const char* Str2=0x0);

int 
main(int argc, char** argv) 
{        
    quex::Token       Token;

    if( argc < 2 ) {
        printf("Need at least one argument.\n");
        return -1;
    }
    else if( strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Include Stack: Misc Scenarios;\n");
        printf("CHOICES: empty, 1, 2, 3, 4, 5, 20;");
        return 0;
    }

    string         Directory("example/");
    string         Filename(argv[1]);
    quex::ISLexer  qlex(string(Directory + Filename + ".txt").c_str());

    cout << "[START]\n";

    bool continue_lexing_f = true;

    do {
        qlex.receive(&Token);

        print(qlex, Token, true);

        switch( Token.type_id() ) {
        default: break;

        case QUEX_TKN_INCLUDE: {
                qlex.receive(&Token);
                print(qlex, Token, false);
                if( Token.type_id() != QUEX_TKN_IDENTIFIER ) {
                    continue_lexing_f = false;
                    print(qlex, "found 'include' without a subsequent filename. hm?: ", 
                          (const char*)(Token.type_id_name().c_str()));
                    break;
                }
               
                string     Filename((const char*)Token.text().c_str());
                Filename = Directory + Filename;
                print(qlex, ">> including: ", (const char*)(Filename.c_str()));
                FILE* fh = fopen((const char*)(Filename.c_str()), "r");
                if( fh == NULL ) {
                    print(qlex, "file not found\n");
                    return 0;
                }
                qlex.include_push(fh);
                break;
            }

        case QUEX_TKN_TERMINATION:
            if( qlex.include_pop() == false ) {
                continue_lexing_f = false;
            } else {
                print(qlex, "<< return from include\n");
            }
            break;
        }

    } while( continue_lexing_f );

    cout << "[END]\n";

    return 0;
}

string  space(int N)
{ string tmp; for(int i=0; i<N; ++i) tmp += "    "; return tmp; }

void  print(quex::ISLexer& qlex, quex::Token& Token, bool TextF /* = false */)
{ 
    cout << space(qlex.include_depth) << Token.line_number() << ": (" << Token.column_number() << ")";
    cout << Token.type_id_name();
    if( TextF ) cout << "\t" << Token.text().c_str();
    cout << endl;
}

void print(quex::ISLexer& qlex, const char* Str1, const char* Str2 /* = 0x0 */)
{
    cout << space(qlex.include_depth) << Str1;
    if( Str2 != 0x0 ) cout << Str2;
    cout << endl;
}
