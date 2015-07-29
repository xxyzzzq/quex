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
    Token*       token_p;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    mystream  file("wiki.txt");
#   if defined (QUEX_OPTION_CONVERTER_ICU) || defined (QUEX_OPTION_CONVERTER_ICONV)
    quex::Simple  qlex(&file, "UTF-8");
#   else
    quex::Simple  qlex(&file);
#   endif

    // (*) print the version 
    cout << ",------------------------------------------------------------------------------------\n";
    cout << "| [START]\n";

    int token_n = 0;
    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
        qlex.receive(&token_p);

        // (*) print out token information
        //     -- name of the token
        if( token_n > 402508 - 20 ) {
            cout << token_n << "  ";
#   if defined (QUEX_OPTION_CONVERTER_ICU) || defined (QUEX_OPTION_CONVERTER_ICONV)
        cout << *token_p << endl;
#   else
        cout << (const char*)(token_p->type_id_name().c_str());
        cout << " '";
        cout << (const char*)(token_p->get_text().c_str());
        cout << "' " << endl;
#   endif
        }

        ++token_n;

        // (*) check against 'termination'
    } while( token_p->type_id() != QUEX_TKN_TERMINATION );

    cout << "| [END] number of token = " << token_n << "\n";
    cout << "`------------------------------------------------------------------------------------\n";

    return 0;
}
