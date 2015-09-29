#include<iostream>
#include<fstream>

#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/buffer/converter/BufferFiller_Converter.i>
#ifdef QUEX_OPTION_CONVERTER_ICONV
#   include <quex/code_base/buffer/converter/iconv/Converter_IConv.i>
#endif
#ifdef QUEX_OPTION_CONVERTER_ICU
#   include <quex/code_base/buffer/converter/icu/Converter_ICU.i>
#endif
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

    std::FILE*           fh = fopen("___DATA_DIR___/test.txt", "r");
    size_t               RawMemorySize = 6;
    const int            MemorySize = 1; /* no re-load necessary */
    QUEX_TYPE_CHARACTER  memory[MemorySize];
    ByteLoader*          byte_loader = ByteLoader_FILE_new(fh);
    /**/
    ptrdiff_t    Delta = 0;
    ptrdiff_t    Front = 0;
    ptrdiff_t    Back  = 0;
    if( strcmp(argv[1], "Forward") == 0 ) { Delta =  1; Front = 0;  Back = 23; } 
    else                                  { Delta = -1; Front = 23; Back = 0; }

    QUEX_NAME(BufferFiller)* filler = \
        QUEX_NAME(BufferFiller_Converter_new)(byte_loader, 
                                              ___NEW___(),
                                              ___UCS_UTF8___, 
                                              ___UCS_4_BYTE_LE___, 
                                              RawMemorySize);

    size_t loaded_n = 0;
    for(ptrdiff_t i=Front; ; i += Delta) {

        filler->derived_input_character_seek(filler, i);

        assert(filler->derived_input_character_tell(filler) == i);

        loaded_n = filler->derived_input_character_read(filler, 
                                                        (QUEX_TYPE_CHARACTER*)memory, 
                                                        MemorySize);

        if( loaded_n != 0 ) {
            /* Print first read character from position 'i' */
            uint8_t*  raw = (uint8_t*)&memory[0];
            printf("%02X.%02X.%02X.%02X\n", (unsigned)raw[3], (unsigned)raw[2], (unsigned)raw[1], (unsigned)raw[0]);
        }

        if( i == Back ) break;
    }
}
