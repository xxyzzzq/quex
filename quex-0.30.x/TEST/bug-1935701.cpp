#include<iostream>
#include<fstream>

#include<quex/code_base/buffer/plain/fixed_size_character_stream>

using namespace std;

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

    uint8_t              buffer[512];
    size_t               loaded_character_n = 0;  

    if( strcmp(argv[1], "FILE") == 0 ) { 
        FILE* fh = 0x0;

        fh = fopen("misc/bug-1935701-text.dat", "r");
        if( fh == 0x0 ) {
            cout << "error file 'misc/bug-1935701-text.dat' not found.\n";
            return 0;
        }
        quex::fixed_size_character_stream_plain<std::FILE, uint8_t>     is1(fh);
        loaded_character_n = is1.read_characters(buffer, 512);
        fclose(fh);
        cout << "1 byte mode: loaded characters = " << loaded_character_n << "\n";
        
        fh = fopen("misc/bug-1935701-text.dat", "r");
        quex::fixed_size_character_stream_plain<std::FILE, uint16_t>    is2(fh);
        loaded_character_n = is2.read_characters((uint16_t*)buffer, 256);
        fclose(fh);
        cout << "2 byte mode: loaded characters = " << loaded_character_n << "\n";
        
        fh = fopen("misc/bug-1935701-text.dat", "r");
        quex::fixed_size_character_stream_plain<std::FILE, uint32_t>    is3(fh);
        loaded_character_n = is3.read_characters((uint32_t*)buffer, 128);
        fclose(fh);
        cout << "4 byte mode: loaded characters = " << loaded_character_n << "\n";
    } else {
        fstream fh;

        fh.open("misc/bug-1935701-text.dat");
        if( fh == 0x0 ) {
            cout << "error file 'misc/bug-1935701-text.dat' not found.\n";
            return 0;
        }
        quex::fixed_size_character_stream_plain<std::istream, uint8_t>     is1(&fh);
        loaded_character_n = is1.read_characters(buffer, 512);
        fh.close();
        cout << "1 byte mode: loaded characters = " << loaded_character_n << "\n";
        
        fh.open("misc/bug-1935701-text.dat");
        quex::fixed_size_character_stream_plain<std::istream, uint16_t>    is2(&fh);
        loaded_character_n = is2.read_characters((uint16_t*)buffer, 256);
        fh.close();
        cout << "2 byte mode: loaded characters = " << loaded_character_n << "\n";
        
        fh.open("misc/bug-1935701-text.dat");
        quex::fixed_size_character_stream_plain<std::istream, uint32_t>    is3(&fh);
        loaded_character_n = is3.read_characters((uint32_t*)buffer, 128);
        fh.close();
        cout << "4 byte mode: loaded characters = " << loaded_character_n << "\n";
    }

 
}
