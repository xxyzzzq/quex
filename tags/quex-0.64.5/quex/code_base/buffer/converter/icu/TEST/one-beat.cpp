#include<iostream>
#include<fstream>

#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/buffer/converter/BufferFiller_Converter.i>
#include <quex/code_base/buffer/converter/icu/Converter_ICU.i>
#include <quex/code_base/buffer/Buffer.i>

using namespace std;

int
main(int argc, char** argv)
{
    using namespace std;
    using namespace quex;

    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        cout << "read_characters: Raw buffer size varries (UTF-8)\n";
        cout << "CHOICES: 6, 7, 8, 9;\n";
        cout << "SAME;\n";
        return 0;
    }
    assert(sizeof(QUEX_TYPE_CHARACTER) == 4);

    if( argc < 2 )  {
        printf("Missing choice argument. Use --hwut-info\n");
        return 0;
    }

    std::FILE*   fh = fopen("test.txt", "r");
    size_t       raw_memory_size = 3;
    raw_memory_size = argv[1][0] - '0';
    assert(raw_memory_size >= 1);
    assert(raw_memory_size <= 9);
    const int            MemorySize = 512; /* no re-load necessary */
    QUEX_TYPE_CHARACTER  memory[MemorySize];

    QUEX_NAME(BufferFiller_Converter)<FILE>* filler = \
        QUEX_NAME(BufferFiller_Converter_new)(fh, 
                                              QUEX_NAME(Converter_ICU_new)(), 
                                              "UTF-8", 
                                              0x0, raw_memory_size);

    size_t loaded_n = 0;
    loaded_n = filler->base.read_characters(&filler->base, 
                                           (QUEX_TYPE_CHARACTER*)memory, MemorySize);

    cout << "## loaded character n = " << loaded_n << endl;

    for(size_t i=0; i < loaded_n ; ++i) {
        uint8_t*  raw = (uint8_t*)(memory + i);
        printf("%02X.%02X.%02X.%02X\n", (unsigned)raw[3], (unsigned)raw[2], (unsigned)raw[1], (unsigned)raw[0]);
    }

}
