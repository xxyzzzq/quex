#include "br_scan"
#include "iostream"

int 
main(int argc, char** argv) 
{        
    blackray::Token*  token_p = 0x0;
    quex::br_scan    qlex("example.txt");

    do {
        qlex.receive(&token_p);
        std::cout << token_p->number_ << std::endl;
    } while( token_p->type_id() != BR_TKN_TERMINATION);

    return 0;
}
