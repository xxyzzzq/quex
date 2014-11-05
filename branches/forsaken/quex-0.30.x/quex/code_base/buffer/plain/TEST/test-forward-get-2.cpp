#include <iostream>
#include <sstream>
#include <cstring>

#include <quex/code_base/buffer/plain/fixed_size_character_stream>
#include <test-core.h>

using namespace quex;
using namespace std;

int
main(int argc, char** argv)
{
    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        std::cout << "Forward Iteration: EOF at first load.\n";
        return 0;
    }
    istringstream ifs("La vie est belle.");
    fixed_size_character_stream_plain<istringstream, uint8_t>  input_strategy(&ifs);
    
    buffer<uint8_t> x(&input_strategy, 32, 5, 0);
    //_____________________________________________________________________________________________

    x.show_content();
    while( 1 + 1 == 2 ) {
        const int tmp = x.get_forward();
        //
        x.show_content();
        //
        if( tmp == ' ' ) x.mark_lexeme_start();
        else if( x.is_begin_of_file() ) { break; /* we are at the end, simply do get_forward again */ }
        else if( tmp == x.BLC ) {
            cout << "try load\n";
            // x.x_show_content();
            if( x.load_forward() == -1 ) break;
        }
    }
    std::cout << "end of file\n";
    return 0;
}
