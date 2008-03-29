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
	std::cout << "Forward Iteration: EOF at first load.\n";
	return 1;
    }
    istringstream ifs("La vie est belle.");
    
    buffer x(&ifs, 32, 5);
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
}
