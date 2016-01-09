#include<fstream>    
#include<iostream> 

#include <./Simple>

using namespace std;

int 
main(int argc, char** argv) 
{        
    // we want to have error outputs in stdout, so that the unit test could see it.
    quex::Token*  token_p;
#   ifdef STRANGE_STREAM
    ifstream                       istr("example.txt");
    quex::StrangeStream<ifstream>  strange_stream(&istr);
    quex::Simple                   qlex(&strange_stream);
#   elif defined(CONVERTER_ENCODING)
    quex::Simple  qlex(argc == 1 ? "example.txt" : argv[1], CONVERTER_ENCODING);
#   else
    quex::Simple  qlex(argc == 1 ? "example.txt" : argv[1]);
#   endif

    cout << "## An Assert-Abortion might be an intended element of the experiment.\n";
#   ifdef QUEX_OPTION_TOKEN_POLICY_SINGLE
    token_p = qlex.token_p();
#   endif
    do {
#       ifdef QUEX_OPTION_TOKEN_POLICY_SINGLE
        qlex.receive();
#       else
        qlex.receive(&token_p);
#       endif
        if( token_p->type_id() == QUEX_TKN_TERMINATION ) {
            token_p->text = (QUEX_TYPE_LEXATOM*)"";
        }
#       ifdef PRINT_LINE_COLUMN
        cout << "(" << qlex.line_number() << ", " << qlex.column_number() << ")  \t";
#       endif
        if( token_p->type_id() != QUEX_TKN_TERMINATION )
            cout << string(*token_p) << endl;
        else
            cout << "<TERMINATION>\n";
        cout.flush();
    } while( token_p->type_id() != QUEX_TKN_TERMINATION );

    return 0;
}

