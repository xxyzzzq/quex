#include<fstream>    
#include<iostream> 

#include "EasyLexer"

#ifndef     ENCODING_NAME
#    define ENCODING_NAME (0x0)
#endif

static void print_token(quex::Token* token_p);

int 
main(int argc, char** argv) 
{        
    using namespace std;

    quex::Token*       token_p = 0x0;
    quex::EasyLexer    qlex(argc == 1 ? "example.txt" : argv[1], ENCODING_NAME);

    cout << ",-----------------------------------------------------------------\n";
    cout << "| [START]\n";

    int number_of_tokens = 0;
    do {
        qlex.receive(&token_p);

        print_token(token_p);

        ++number_of_tokens;

    } while( token_p->type_id() != QUEX_TKN_TERMINATION );

    cout << "| [END] number of token = " << number_of_tokens << "\n";
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
    switch( token_p->_id ) {
    case QUEX_TKN_INDENT: 
    case QUEX_TKN_DEDENT: 
    case QUEX_TKN_NODENT: 
    case QUEX_TKN_TERMINATION: 
        /* In this case, the token still carries an old lexeme; Printing it
         * would be confusing.                                               */
        cout << token_p->type_id_name() << endl;
        break;
    default:
        cout << string(*token_p) << endl;
        break;
    }
#   else
    cout << token_p->type_id_name() << endl;
#   endif
}
