#include<iostream>
#include<fstream>

#include<quex/code_base/buffer/iconv/fixed_size_character_stream>

using namespace std;

int
main(int argc, char** argv) 
{
    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        cout << "Converting Stream in N Tiny Beats\n";
        return 0;
    }

    std::FILE*   fh = fopen("test.txt", "r");
    uint8_t      raw_buffer[5];
    char*        target_charset = (char*)"UCS-4BE";
    uint8_t      buffer[512];
    quex::fixed_size_character_stream_iconv<std::FILE, uint32_t>   is(fh, raw_buffer, 5, "UTF8", target_charset);

    if( argc > 1 ) target_charset = argv[1];

    const int LoadedN = is.read_characters((uint32_t*)buffer, 128);

    cout << "character n = " << LoadedN << endl;
 
    for(int i=0; i < LoadedN*4 ; i+=4) {
        unsigned char b0 = buffer[i+0];
        unsigned char b1 = buffer[i+1];
        unsigned char b2 = buffer[i+2];
        unsigned char b3 = buffer[i+3];
        printf("%02X.%02X.%02X.%02X\n", (unsigned)b0, (unsigned)b1, (unsigned)b2, (unsigned)b3);
    }
}
