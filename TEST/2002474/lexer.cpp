#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "Simple"

using namespace std;
using namespace quex;

class mystream : public ifstream {
public:
    mystream(const char* Filename) : ifstream(Filename) { }

    void seekg(int Value) { cout << "##" << Value << endl; ifstream::seekg(Value); }
    void read(ifstream::char_type* buffer, size_t Value) { cout << "##" << Value << endl; ifstream::read(buffer, Value); }
};

int 
main(int argc, char** argv) 
{        
    // (*) create token
    Token        token;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    mystream  file("wiki.txt");
    file.seekg(65536 * 15); // atoi(argv[1]));
    Simple  qlex(&file, "UTF-8");

    // (*) print the version 
    cout << ",------------------------------------------------------------------------------------\n";
    cout << "| [START]\n";

    int number_of_tokens = 0;
    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
        qlex.receive(&token);
        // qlex.get_token(&token);

        // (*) print out token information
        //     -- name of the token
        cout << string(token) << endl;

        ++number_of_tokens;

        // (*) check against 'termination'
    } while( token.type_id() != TKN_TERMINATION );

    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";

    return 0;
}
