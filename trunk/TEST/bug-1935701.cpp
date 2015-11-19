#define QUEX_TYPE_CHARACTER uint32_t
#include<iostream>
#include<fstream>
#include<cstring>

#include<quex/code_base/test_environment/TestAnalyzer-configuration>
#include<quex/code_base/buffer/filler/BufferFiller>
#include<quex/code_base/buffer/filler/BufferFiller_Plain>
#include<quex/code_base/buffer/filler/BufferFiller_Plain.i>
#include<quex/code_base/single.i>

using namespace std;
using namespace quex;

int
main(int argc, char** argv) 
{
    if( argc <= 1 ) {
        cout << "command line argument required. try '--hwut-info'.\n";
        return 0;
    }
    else if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        cout << "sphericalcow: 1935701 - 0.24.7 buffer handling size mismatch\n";
        cout << "CHOICES: FILE, fstream";
        return 0;
    }

    const size_t         BufferSize = 512;
    QUEX_TYPE_CHARACTER  buffer[BufferSize];
    size_t               loaded_character_n = 0;  

    if( strcmp(argv[1], "FILE") == 0 ) { 
        FILE* fh = 0x0;

        fh = fopen("misc/bug-1935701-text.dat", "rb");
        if( fh == 0x0 ) {
            cout << "error file 'misc/bug-1935701-text.dat' not found.\n";
            return 0;
        }

        ByteLoader*                byte_loader = ByteLoader_FILE_new(fh, true);
        QUEX_NAME(BufferFiller)*   is = QUEX_NAME(BufferFiller_Plain_new)(byte_loader);

        loaded_character_n = is->derived_load_characters(is, buffer, BufferSize);
        fclose(fh);
        cout << "4 byte mode: loaded characters = " << loaded_character_n << "\n";

    } else {
        fstream fh;

        fh.open("misc/bug-1935701-text.dat");
        if( fh.bad() ) {
            cout << "error file 'misc/bug-1935701-text.dat' not found.\n";
            return 0;
        }
        
        ByteLoader*              byte_loader = ByteLoader_stream_new(&fh);
        QUEX_NAME(BufferFiller)* is          = QUEX_NAME(BufferFiller_Plain_new)(byte_loader);
        loaded_character_n = is->derived_load_characters(is, buffer, BufferSize);
        
        fh.close();
        cout << "4 byte mode: loaded characters = " << loaded_character_n << "\n";
    }

 
}
