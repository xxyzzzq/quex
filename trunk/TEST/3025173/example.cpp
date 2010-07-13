#include "br_scan"

int 
main(int argc, char** argv) 
{        
    blackray::Token*  token_p = 0x0;
    quex::br_scan    qlex("example.txt");

    do {
        qlex.receive(&token_p);
    } while( 1 + 1 == 2 );

    return 0;
}
