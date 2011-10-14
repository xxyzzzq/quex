#include<fstream>    
#include<iostream> 

#include <./Simple>

using namespace std;

int 
main(int argc, char** argv) 
{        
    // we want to have error outputs in stdout, so that the unit test could see it.
    quex::Token   token;
#   if defined(__QUEX_OPTION_UNIT_TEST_UTF8__)
    quex::Simple  qlex(argc == 1 ? "example.txt" : argv[1], "UTF-8");
    cout << "## UTF-8 encoding\n";
#   else
    quex::Simple  qlex(argc == 1 ? "example.txt" : argv[1]);
#   endif

    cout << "## An Assert-Abortion might be an intended element of the experiment.\n";
    qlex.token_p_set(&token);
    do {
        qlex.receive();
        cout << qlex.line_number() << ", " << qlex.column_number() << ": " << string(token) << endl;
    } while( token.type_id() != COL_TERMINATION );
    

    return 0;
}

