#include<iostream>
#include<cstdio>

#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/buffer/converter/BufferFiller_Converter.i>
#include <quex/code_base/buffer/converter/iconv/Converter_IConv.i>
#include <quex/code_base/buffer/Buffer.i>


int
main(int argc, char** argv) 
{
    using namespace std;
    using namespace quex;

    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        cout << "read_characters: User buffer size varries (UTF-8)\n";
        cout << "CHOICES: 1, 2, 3, 4, 5, 6, 7, 8, 9;\n";
        cout << "SAME;\n";
        return 0;
    }
    assert(sizeof(QUEX_TYPE_CHARACTER) == 4);

    if( argc < 2 )  {
        printf("Missing choice argument. Use --hwut-info\n");
        return 0;
    }

    std::FILE*           fh = fopen("test.txt", "r");
    const int            RawMemorySize = 6;
    char*                target_charset = (char*)"UCS-4BE";
    size_t               memory_size = 3;
    memory_size = argv[1][0] - '0';
    assert(memory_size >= 1);
    assert(memory_size <= 9);
    QUEX_TYPE_CHARACTER  memory[memory_size];

    QUEX_NAME(BufferFiller_Converter)<FILE>* filler = \
        QUEX_NAME(BufferFiller_Converter_new)(fh, QUEX_NAME(Converter_IConv_new)(), 
                                              "UTF8", 
                                              target_charset, RawMemorySize);

    size_t loaded_n = 0;
    do {
        loaded_n = filler->base.read_characters(&filler->base, 
                                                (QUEX_TYPE_CHARACTER*)memory, memory_size);

        cout << "## loaded character n = " << loaded_n << endl;
     
        for(size_t i=0; i < loaded_n ; ++i) {
            uint8_t*  raw = (uint8_t*)(memory + i);
            printf("%02X.%02X.%02X.%02X\n", (unsigned)raw[0], (unsigned)raw[1], (unsigned)raw[2], (unsigned)raw[3]);
        }
    } while( loaded_n == memory_size );
}
