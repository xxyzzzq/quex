#include<fstream>    
#include<iostream> 

#include <./Simple>

using namespace std;

int 
main(int argc, char** argv) 
{        
    // we want to have error outputs in stdout, so that the unit test could see it.
    quex::Token*  token_p;
    quex::Simple  qlex(argc == 1 ? "example.txt" : argv[1]);

    cout << "## An Assert-Abortion might be an intended element of the experiment.\n";
#   ifdef QUEX_OPTION_TOKEN_POLICY_SINGLE
    token_p = qlex.token_p();
#   endif
    do {
#       ifdef QUEX_OPTION_TOKEN_POLICY_SINGLE
        qlex.receive();
#       else
        token_p = qlex.receive();
#       endif
        if( token_p->type_id() == QUEX_TKN_TERMINATION ) {
            token_p->text = (QUEX_TYPE_CHARACTER*)"";
        }
#       ifdef PRINT_LINE_COLUMN
        cout << "(" << qlex.line_number() << ", " << qlex.column_number() << ")  \t";
#       endif
        cout << string(*token_p) << endl;
    } while( token_p->type_id() != QUEX_TKN_TERMINATION );

    return 0;
}

