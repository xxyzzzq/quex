#include <iostream>
#include <sstream>

#include <test-core.h>

using namespace quex;
using namespace std;

int
main(int argc, char** argv)
{
    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        std::cout << "Backwards Iteration\n";
        std::cout << "CHOICES: Normal, EOFC=1_BOFC=2_BLC=0, EOFC=1_BOFC=0_BLC=2, EOFC=0_BOFC=1_BLC=2\n";
        return 0;
    }
    istringstream ifs("Das Korn wird geerntet und zur Verarbeitung gemahlen.");
    ifs.seekg(35);


    buffer* p = 0x0;
    if( argc > 1 ) {
        if(      strcmp(argv[1], "Normal") == 0 )              p = new buffer(&ifs, 30, 2);
        else if( strcmp(argv[1], "EOFC=1_BOFC=2_BLC=0") == 0 ) p = new buffer(&ifs, 30, 0); 
        else if( strcmp(argv[1], "EOFC=1_BOFC=0_BLC=2") == 0 ) p = new buffer(&ifs, 30, 2);
        else if( strcmp(argv[1], "EOFC=0_BOFC=1_BLC=2") == 0 ) p = new buffer(&ifs, 30, 2);
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
    //
    x.seek_offset(5);

    cout << "--------------------------------------------\n";

    while( 1 + 1 == 2 ) {
        x.show_content();
        //
        const int tmp = x.get_backward();
        //
        if( tmp == ' ' ) x.mark_lexeme_start();
        // See file README.txt in directory ./quex/buffer      
        else if( x.is_begin_of_file() ) { break; /* we are at the end, simply do get_backward() again */ }
        else if( tmp == x.BLC ) {
            std::cout << "try load\n";
            if( x.load_backward() == -1 ) break;
        }
    }
    std::cout << "begin of file\n";
    return 0;
}
