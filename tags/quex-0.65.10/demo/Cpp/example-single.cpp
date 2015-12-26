#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "EasyLexer"

#ifndef QUEX_OPTION_TOKEN_POLICY_SINGLE
#   error "This example has been designed for token passing policy 'single'."
#endif

#ifndef     ENCODING_NAME
#    define ENCODING_NAME (0x0)
#endif

static void print_token(quex::Token* token_p);

int 
main(int argc, char** argv) 
{        
    using namespace std;

    quex::EasyLexer    qlex(argc == 1 ? "example.txt" : argv[1], ENCODING_NAME);
    quex::Token*       token_p  = qlex.token_p();
    QUEX_TYPE_TOKEN_ID token_id = QUEX_TKN_UNINITIALIZED;
    int                number_of_tokens = 0;

    cout << ",-----------------------------------------------------------------\n";
    cout << "| [START]\n";

    do {
        token_id = qlex.receive();

        print_token(token_p);

        ++number_of_tokens;

    } while( token_id != QUEX_TKN_TERMINATION );

    cout << "| [END] number of tokens = " << number_of_tokens << "\n";
    cout << "`-----------------------------------------------------------------\n";

    return 0;
}

static void
print_token(quex::Token* token_p)
{
    using namespace std;

#   ifdef PRINT_LINE_COLUMN_NUMBER
    cout << "(" << token_p->line_number() << ", " << token_p->column_number() << ")  \t";
#   endif
#   ifdef PRINT_TOKEN
    cout << string(*token_p) << endl;
#   else
    cout << token_p->type_id_name() << endl;
#   endif
}
