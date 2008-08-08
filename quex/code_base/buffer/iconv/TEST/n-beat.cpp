#include<iostream>
#include<cstdio>

#include<quex/code_base/buffer/iconv/BufferFiller_IConv>
#include<quex/code_base/buffer/iconv/BufferFiller_IConv.i>


int
main(int argc, char** argv) 
{
    using namespace std;
    using namespace quex;

    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        cout << "read_characters: UTF8 (with tiny buffers)\n";
        return 0;
    }
    assert(sizeof(QUEX_CHARACTER_TYPE) == 4);

    std::FILE*           fh = fopen("test.txt", "r");
    uint8_t              raw_memory[3];
    const int            RawMemorySize = 3;
    char*                target_charset = (char*)"UCS-4BE";
    QUEX_CHARACTER_TYPE  memory[64];

    QuexBuffer                   buffer;
    QuexBufferFiller_IConv<FILE> filler;

    QuexBufferFiller_IConv_init(&filler, fh, "UTF8", target_charset, (uint8_t*)raw_memory, (size_t)3);
    QuexBuffer_init(&buffer, memory, 12, (QuexBufferFiller*)&filler);

    if( argc > 1 ) target_charset = argv[1];

    const size_t LoadedN = __QuexBufferFiller_IConv_read_characters(&filler.base, 
                                                                    (QUEX_CHARACTER_TYPE*)memory, 
                                                                    (size_t)sizeof(memory));

    cout << "character n = " << LoadedN << endl;
 
    for(int i=0; i < LoadedN*4 ; i+=4) {
        unsigned char b0 = memory[i+0];
        unsigned char b1 = memory[i+1];
        unsigned char b2 = memory[i+2];
        unsigned char b3 = memory[i+3];
        printf("%02X.%02X.%02X.%02X\n", (unsigned)b0, (unsigned)b1, (unsigned)b2, (unsigned)b3);
    }
}
