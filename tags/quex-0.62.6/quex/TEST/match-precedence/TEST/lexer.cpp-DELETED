#include<fstream>    
#include<iostream> 

#include "Simple"

using namespace std;

int 
main(int argc, char** argv) 
{        
    quex::Token*  token;
    quex::Simple  qlex(argv[1]);

    cout << "[START]\n";

    do {
        token = qlex.receive();
        cout << string(*token) << endl;
    } while( token->type_id() != T_TERMINATION );

    cout << "\n[END]\n";

    return 0;
}
