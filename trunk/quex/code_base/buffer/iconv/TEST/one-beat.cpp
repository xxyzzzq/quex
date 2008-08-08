#include<iostream>
#include<fstream>

#include<quex/code_base/buffer/iconv/BufferFiller_IConv>
#include<quex/code_base/buffer/iconv/BufferFiller_IConv.i>

using namespace std;

int
main(int argc, char** argv) 
{
    using namespace quex;

    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        cout << "Converting Stream in One Beat\n";
        return 0;
    }

    std::FILE*   fh = fopen("test.txt", "r");
    uint8_t      raw_buffer[128];
    char*        target_charset = (char*)"UCS-4BE";
    uint8_t      buffer[512];
    QuexBufferFiller_IConv<std::FILE>   filler;


    if( argc > 1 ) target_charset = argv[1];

    const int LoadedN = __QuexBufferFiller_IConv_read_characters(&filler.base, buffer, 128);
 
    for(int i=0; i < LoadedN ; i+=4) {
        unsigned char b0 = buffer[i+0];
        unsigned char b1 = buffer[i+1];
        unsigned char b2 = buffer[i+2];
        unsigned char b3 = buffer[i+3];
        printf("%02X.%02X.%02X.%02X\n", (unsigned)b0, (unsigned)b1, (unsigned)b2, (unsigned)b3);
    }
}
