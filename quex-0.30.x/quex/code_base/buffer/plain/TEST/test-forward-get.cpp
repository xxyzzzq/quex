#include <iostream>
#include <sstream>
#include <cstring>

#include <quex/code_base/buffer/plain/fixed_size_character_stream>
#include <test-core.h>

int
main(int argc, char** argv)
{
    using namespace quex;
    using namespace std;

    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        std::cout << "Forward Iteration: Multiple Loads.\n";
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
        cout << "No choice specified. User '--hwut-info'.\n";
        return (-1);
    }
    buffer<uint8_t>& x = *p;
    //_____________________________________________________________________________________________

    x.show_content();
    while( 1 + 1 == 2 ) {
        const int tmp = x.get_forward();
        //
        x.show_content();
        //
        if( tmp == ' ' ) x.mark_lexeme_start();
        else if( x.is_end_of_file() ) { break; /* we are at the end, simply do get_forward() again */ }
        else if( tmp == x.BLC ) {
            cout << "try load\n";
            // x.x_show_content();
            if( x.load_forward() == -1 ) break;
        }
    }
    std::cout << "end of file\n";

    return 0;
}
