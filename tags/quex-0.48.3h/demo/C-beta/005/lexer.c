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
    QUEX_TYPE_TOKEN     my_token;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    QUEX_TYPE_ANALYZER  qlex;
    
    QUEX_NAME_TOKEN(construct)(&my_token);
    QUEX_NAME(construct_file_name)(&qlex, "example.txt", 0x0, false);

    printf(",------------------------------------------------------------------------------------\n");
    printf("| [START]\n");

    int  number_of_tokens = 0;
    bool continue_lexing_f = true;
    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
        qlex.receive(&my_token);

        // (*) print out token information
        //     -- name of the token
        print(qlex, my_token, (const char*)my_token.get_text().c_str());

        if( my_token.type_id() == QUEX_TKN_INCLUDE ) { 
            qlex.receive(&my_token);
            print(qlex, my_token, (const char*)my_token.get_text().c_str());
            if( my_token.type_id() != QUEX_TKN_IDENTIFIER ) {
                continue_lexing_f = false;
                print(qlex, "found 'include' without a subsequent filename. hm?\n");
                break;
            }
            print(qlex, ">> including: ", (const char*)my_token.get_text().c_str());
            QUEX_TYPE_CHARACTER* tmp = (QUEX_TYPE_CHARACTER*)my_token.get_text().c_str();
            qlex.include_push<FILE>(tmp);
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

    printf("| [END] number of token = %i\n", (int)number_of_tokens);
    printf("`------------------------------------------------------------------------------------\n");

    return 0;
}

void  
space(int N)
{ for(int i=0; i<N; ++i) printf("    "); }

void  
print(QUEX_TYPE_ANALYZER* qlex, quex::Token& my_token, bool TextF /* = false */)
{ 
    space(qlex->include_depth);
    printf("%i: (%i)", (int)my_token.line_number(), (int)my_token.column_number());
    printf(my_token.type_id_name());
    if( TextF ) printf("\t'%s'", my_token._text "'");
    printf("\n");
}

void 
print(QUEX_TYPE_ANALYZER* qlex, const char* Str1, 
      const char* Str2 /* = 0x0 */, const char* Str3 /* = 0x0*/)
{
    space(qlex->include_depth);
    printf(Str1);
    if( Str2 != 0x0 ) printf(Str2);
    if( Str3 != 0x0 ) printf(Str3);
    printf("\n");
}
