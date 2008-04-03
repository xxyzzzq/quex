#include <iostream>
#include <sstream>
#include <cstring>

#include <test-core.h>

using namespace quex;
using namespace std;

int
main(int argc, char** argv)
{
    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        std::cout << "Forward Iteration: Multiple Loads.\n";
        std::cout << "CHOICES: Normal, EOFC=1_BOFC=2_BLC=0, EOFC=1_BOFC=0_BLC=2, EOFC=0_BOFC=1_BLC=2\n";
        return 0;
    }
    istringstream ifs("Das Korn wird geerntet und zur Verarbeitung gemahlen.");
    
    buffer* p = 0x0;
    if( argc > 1 ) {
        if(      strcmp(argv[1], "Normal") == 0 )              p = new buffer(&ifs, 25, 5);
        else if( strcmp(argv[1], "EOFC=1_BOFC=2_BLC=0") == 0 ) p = new buffer(&ifs, 25, 5, 1, 2, 0); 
        else if( strcmp(argv[1], "EOFC=1_BOFC=0_BLC=2") == 0 ) p = new buffer(&ifs, 25, 5, 1, 0, 2);
        else if( strcmp(argv[1], "EOFC=0_BOFC=1_BLC=2") == 0 ) p = new buffer(&ifs, 25, 5, 0, 1, 2);
        else {
            cout << "argv[0] == '" << argv[1] << "' --- unrecognized choice\n";
            exit(-1);
        }
    } else {
        cout << "no choice specified\n";
        exit(-1);
    }
    buffer& x = *p;
    //_____________________________________________________________________________________________

    x.show_content();
    while( 1 + 1 == 2 ) {
        const int tmp = x.get_forward();
        //
        x.show_content();
        //
        if( tmp == ' ' ) x.mark_lexeme_start();
        else if( tmp == x.BOFC ) { ; /* we are at the end, simply do get_forward again */ }
        else if(  tmp == x.BLC || tmp == x.EOFC || tmp == x.BOFC ) {
            cout << "try load\n";
            // x.x_show_content();
            if( x.load_forward() == -1 ) break;
        }
    }
    std::cout << "end of file\n";

    return 0;
}
