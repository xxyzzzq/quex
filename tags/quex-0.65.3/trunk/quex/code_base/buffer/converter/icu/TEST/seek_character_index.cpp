#include<iostream>
#include<fstream>

#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/buffer/converter/BufferFiller_Converter.i>
#include <quex/code_base/buffer/converter/icu/Converter_ICU.i>
#include <quex/code_base/single.i>

using namespace std;

int
main(int argc, char** argv)
{
    using namespace std;
    using namespace quex;

    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        cout << "Stream Position Seek: Plain search\n";
        cout << "CHOICES: Forward, Backward;\n";
        return 0;
    }
    assert(sizeof(QUEX_TYPE_CHARACTER) == 4);

    if( argc < 2 )  {
        printf("Missing choice argument. Use --hwut-info\n");
        return 0;
    }

    std::FILE*           fh = fopen("test.txt", "r");
    size_t               RawMemorySize = 6;
    const int            MemorySize = 1; /* no re-load necessary */
    QUEX_TYPE_CHARACTER  memory[MemorySize];
    /**/
    ptrdiff_t    Delta = 0;
    ptrdiff_t    Front = 0;
    ptrdiff_t    Back  = 0;
    if( strcmp(argv[1], "Forward") == 0 ) { Delta =  1; Front = 0;  Back = 23; } 
    else                                  { Delta = -1; Front = 23; Back = 0; }

    QUEX_NAME(BufferFiller_Converter)<FILE>* filler = \
             QUEX_NAME(BufferFiller_Converter_new)(fh, 
                                                   QUEX_NAME(Converter_ICU_new)(), 
                                                   "UTF-8", 0x0, RawMemorySize);

    size_t loaded_n = 0;
    for(int i=Front; ; i += Delta) {

        filler->base.seek_character_index(&filler->base, i);

        assert(filler->base.tell_character_index(&filler->base) == i);

        loaded_n = filler->base.read_characters(&filler->base, 
                                               (QUEX_TYPE_CHARACTER*)memory, MemorySize);

        if( loaded_n != 0 ) {
            /* Print first read character from position 'i' */
            uint8_t*  raw = (uint8_t*)(memory);
            printf("%02X.%02X.%02X.%02X\n", (unsigned)raw[3], (unsigned)raw[2], (unsigned)raw[1], (unsigned)raw[0]);
        }

        if( i == Back ) break;
    }
}
