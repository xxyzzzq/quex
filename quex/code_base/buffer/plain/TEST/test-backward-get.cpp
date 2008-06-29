#include <iostream>
#include <sstream>

#include <quex/code_base/buffer/plain/fixed_size_character_stream>
#include <test-core.h>

using namespace quex;
using namespace std;

int
main(int argc, char** argv)
{
    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        std::cout << "Backwards Iteration\n";
        std::cout << "CHOICES: BLC=0, BLC=1, BLC=0xFF;\n";
        std::cout << "SAME;\n";
        return 0;
    }
    istringstream  ifs("Das Korn wird geerntet und zur Verarbeitung gemahlen.");
    fixed_size_character_stream_plain<istringstream, uint8_t>  input_strategy(&ifs);

    buffer<uint8_t>* p = 0x0;
    if( argc > 1 ) {
        if(      strcmp(argv[1], "BLC=0") == 0 )    p = new buffer<uint8_t>(&input_strategy, 25, 5, (uint8_t)0);
        else if( strcmp(argv[1], "BLC=1") == 0 )    p = new buffer<uint8_t>(&input_strategy, 25, 5, (uint8_t)1); 
        else if( strcmp(argv[1], "BLC=0xFF") == 0 ) p = new buffer<uint8_t>(&input_strategy, 25, 5, (uint8_t)0xFF); 
        else {
            cout << "argv[0] == '" << argv[1] << "' --- unrecognized choice\n";
            return (-1);
        }
    } else {
        cout << "no choice specified\n";
        return (-1);
    }

    buffer<uint8_t>& x = *p;
    for(int i=0; i<42; ++i) {
        if( x.get_forward() == x.BLC ) { x.load_forward(); --i; }
        // The lexeme start must be marked, otherwise the fallback region grows to much.
        x.mark_lexeme_start();
    }
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
