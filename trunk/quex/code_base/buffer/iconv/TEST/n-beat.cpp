#include<iostream>
#include<fstream>

#include<quex/code_base/memory/iconv/BufferFiller_IConv>
#include<quex/code_base/memory/iconv/BufferFiller_IConv.i>

using namespace std;

int
main(int argc, char** argv) 
{
    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        cout << "Converting Stream in N Tiny Beats\n";
        return 0;
    }

    std::FILE*   fh = fopen("test.txt", "r");
    uint8_t      raw_memory[5];
    char*        target_charset = (char*)"UCS-4BE";
    uint8_t      memory[512];

    QuexBuffer               buffer;
    QuexBufferFiller_IConv   filler;

    BufferFiller_Plain_init(&filler, fh, "UTF8", raw_memory, 5);
    QuexBuffer_init(&buffer, memory, 12, (QuexBufferFiller*)&filler);
    quex::fixed_size_character_stream_iconv<std::FILE, uint32_t>   is(fh, raw_memory, 5, "UTF8", target_charset);

    if( argc > 1 ) target_charset = argv[1];

    const int LoadedN = is.read_characters((uint32_t*)memory, 128);

    cout << "character n = " << LoadedN << endl;
 
    for(int i=0; i < LoadedN*4 ; i+=4) {
        unsigned char b0 = memory[i+0];
        unsigned char b1 = memory[i+1];
        unsigned char b2 = memory[i+2];
        unsigned char b3 = memory[i+3];
        printf("%02X.%02X.%02X.%02X\n", (unsigned)b0, (unsigned)b1, (unsigned)b2, (unsigned)b3);
    }
}
