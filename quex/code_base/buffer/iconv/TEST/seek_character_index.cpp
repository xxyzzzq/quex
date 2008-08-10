#include<iostream>
#include<fstream>

#include<quex/code_base/buffer/iconv/BufferFiller_IConv>
#include<quex/code_base/buffer/iconv/BufferFiller_IConv.i>

using namespace std;

int
main(int argc, char** argv)
{
    using namespace std;
    using namespace quex;

    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        cout << "Seek character index position\n";
        cout << "CHOICES: Forward, Backward;\n";
        return 0;
    }
    assert(sizeof(QUEX_CHARACTER_TYPE) == 4);

    if( argc < 2 )  {
        printf("Missing choice argument. Use --hwut-info\n");
        return 0;
    }

    std::FILE*           fh = fopen("test.txt", "r");
    char*                target_charset = (char*)"UCS-4BE";
    size_t               RawMemorySize = 6;
    uint8_t              raw_memory[RawMemorySize];
    const int            MemorySize = 1; /* no re-load necessary */
    QUEX_CHARACTER_TYPE  memory[MemorySize];
    /**/
    const int    Delta = strcmp(argv[1], "Forward") == 0 ?  1 : -1;
    const int    Front = strcmp(argv[1], "Forward") == 0 ?  0 : 23;
    const int    Back  = strcmp(argv[1], "Forward") == 0 ? 23 : 0;

    QuexBuffer                   buffer;
    QuexBufferFiller_IConv<FILE> filler;

    QuexBufferFiller_IConv_init(&filler, fh, "UTF8", target_charset, (uint8_t*)raw_memory, RawMemorySize);

    size_t loaded_n = 0;
    for(int i=Front; ; i += Delta) {

        filler.base.seek_character_index(&filler.base, i);
        loaded_n = filler.base.read_characters(&filler.base, 
                                               (QUEX_CHARACTER_TYPE*)memory, MemorySize);

        /* Print first read character from position 'i' */
        uint8_t*  raw = (uint8_t*)(memory);
        printf("%02X.%02X.%02X.%02X\n", (unsigned)raw[0], (unsigned)raw[1], (unsigned)raw[2], (unsigned)raw[3]);

        if( i == Back ) break;
    }
}
