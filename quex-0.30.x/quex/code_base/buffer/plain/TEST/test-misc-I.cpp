#include <test-core.h>
#include <iostream>

using namespace std;

int
main(int argc, char** argv)
{
    if( argc > 1 and strcmp(argv[1], "--hwut-info") == 0 ) {
	cout << "Miscenllaneous Scenarios: Content Size = 11, Fallback Size = 10\n";
	cout << "CHOICES: istream, stdio;\n";
	cout << "SAME;\n";
	return 0;
    }
    if( argc < 2 ) {
	cerr << "error: choice argument required (use --hwut-info)\n";
	return -1;
    }
    if( strcmp(argv[1], "istream") == 0 ) test_istream(11, 10);
    else                                  test_stdio(11, 10);

    return 0;
}
