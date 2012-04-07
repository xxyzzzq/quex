#include<fstream>
#include<iostream>

#include "EasyLexer"

using namespace std;

int main(int argc, char** argv)
{
    QUEX_TYPE_TOKEN_ID   token_id = 0;
    quex::EasyLexer      qlex("example.txt");

    do {
        token_id = qlex.receive();       
        cout << string(*(qlex.token_p())) << endl;
    } while( qlex.token_p()->type_id() != QUEX_TKN_TERMINATION );

    return 0;
}
