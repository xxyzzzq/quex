#include<fstream>    
#include<fstream> 
#include <./Simple>

using namespace std;

int 
main(int argc, char** argv) 
{        
    // we want to have error outputs in stdout, so that the unit test could see it.
    quex::Token     Token;
    ifstream        istr("example.txt");
    quex::Simple    qlex(&istr);

    qlex._parent_memento = 0;
    qlex.include_pop();

    return 0;
}

