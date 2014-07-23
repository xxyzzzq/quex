#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "Simple"

using namespace std;
using namespace quex;

class mystream : public ifstream {
public:
    mystream(const char* Filename) : ifstream(Filename) { }

    void seekg(int Value) 
    { cout << "##" << Value << endl; ifstream::seekg(Value); }
    void read(ifstream::char_type* buffer, size_t Value) 
    { cout << "##" << Value << endl; ifstream::read(buffer, Value); }
};

int 
main(int argc, char** argv) 
{        
    // (*) create token
    Token*       token;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    mystream  file("wiki.txt");
    file.seekg(65536 * 15); // atoi(argv[1]));
#   if defined (QUEX_OPTION_CONVERTER_ICU) || defined (QUEX_OPTION_CONVERTER_ICONV)
    quex::Simple  qlex(&file, "UTF-8");
#   else
    quex::Simple  qlex(&file);
#   endif

    // (*) print the version 
    cout << ",------------------------------------------------------------------------------------\n";
    cout << "| [START]\n";

    int number_of_tokens = 0;
    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
        qlex.receive(&token);

        // (*) print out token information
        //     -- name of the token
        if( number_of_tokens > 212356 - 40 ) {
#           if defined (QUEX_OPTION_CONVERTER_ICU) || defined (QUEX_OPTION_CONVERTER_ICONV)
            cout << *token << endl;
#           else
            cout << (const char*)(token->type_id_name().c_str()) << " '" << (const char*)(token->get_text().c_str()) << "' " << endl;
#           endif
        }

        ++number_of_tokens;

        // (*) check against 'termination'
    } while( token->type_id() != TKN_TERMINATION );

    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";

    return 0;
}
