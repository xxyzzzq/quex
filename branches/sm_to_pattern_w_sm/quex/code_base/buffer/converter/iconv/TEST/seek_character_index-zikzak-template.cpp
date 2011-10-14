#include<iostream>
#include<fstream>

#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/buffer/converter/BufferFiller_Converter.i>
#include ___HEADER___


void 
seek_and_print(quex::QUEX_NAME(BufferFiller_Converter)<FILE>& , size_t, QUEX_TYPE_CHARACTER* );

int
main(int argc, char** argv)
{
    using namespace std;
    using namespace quex;
    assert(sizeof(QUEX_TYPE_CHARACTER) == 2);

    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        cout << "Stream Position Seek: Total Zik-Zak\n";
        cout << "CHOICES: Fixed, Dynamic;\n";
        return 0;
    }
    if( argc < 2 )  {
        printf("Missing choice argument. Use --hwut-info\n");
        return 0;
    }

    std::FILE*           fh = 0x0;            
    char*                target_charset = (char*)"UCS-2LE"; 
    char*                source_charset = (char*)""; 
    size_t               RawMemorySize = 6;
    const int            ReferenceSize = 24; 
    QUEX_TYPE_CHARACTER  reference[ReferenceSize];

    if( strcmp(argv[1], "Dynamic") == 0 ) {
        fh             = fopen("test.txt", "r");
        source_charset = (char*)"UTF8"; 
    } else {
        fh             = fopen("test-ucs4be.txt", "r");
        source_charset = (char*)___CODING_4_BYTE___; 
    }
    if( fh == 0x0 ) {
        printf("Input file not found.\n");
        exit(-1);
    }

    QUEX_NAME(BufferFiller_Converter)<FILE>* filler = \
         QUEX_NAME(BufferFiller_Converter_new)(fh, 
                                               ___NEW___(), 
                                               source_charset, target_charset, 
                                               RawMemorySize);
    /* Fill the reference buffer */
    size_t loaded_n = filler->base.read_characters(&filler->base, reference, ReferenceSize);

    /* Print the reference buffer 
     * NOTE: The buffer filler does not know anything about buffer limit codes etc. It simply
     *       fills the given amount of memory with data.                                               */
    for(size_t i=0; i < loaded_n ; ++i) {
        uint8_t*  raw = (uint8_t*)(reference + i);
        printf("[%02d] %02X.%02X   ", i, (unsigned)raw[0], (unsigned)raw[1]);
        if( (i+1) % 8 == 0 ) printf("\n");
    }
    printf("\n-------------------------------------------------------------------------------\n");

    /* Zik-Zak means: From any possible start position, we go to any possible end position. With 23
     * characters this means 529 different experiments. The strategy to do that goes as follows:
     *
     * Whenever we jump from A to B, we also jump back from B to A. This way we spare the 'navigation 
     * to position B' (which would have to be done if B was set separately. Now let A iterate over all
     * positions and B from position 0 to A (consider the possibilities displayed on a matrix which
     * is symetric with respect to the diagonal.                                                       */
    for(size_t a = 0; a < 23 ; ++a) {
        for(size_t b = a; b < 23 ; ++b) {
            seek_and_print(*filler, a, reference);
            printf(" --> ");
            seek_and_print(*filler, b, reference);
            printf(" --> ");
            seek_and_print(*filler, a, reference);
            printf("\n");
        }
    }
}

void seek_and_print(quex::QUEX_NAME(BufferFiller_Converter)<FILE>& filler, size_t Position, QUEX_TYPE_CHARACTER* reference)
{
    using namespace std;

    const int            MemorySize = 1; 
    QUEX_TYPE_CHARACTER  memory[MemorySize];

    filler.base.seek_character_index(&filler.base, Position);
    __quex_assert(filler.raw_buffer.iterators_character_index == Position);
    size_t loaded_n = filler.base.read_characters(&filler.base, memory, MemorySize);

    if( loaded_n != 0 ) {
        /* Print first read character from position 'i' */
        uint8_t*  raw = (uint8_t*)(memory);
        printf("[%02d] %02X.%02X ", (int)Position, (unsigned)raw[0], (unsigned)raw[1]);
        if( reference[Position] != memory[0] ) { printf("**ERROR**\n"); exit(-1); }
    } else {
        printf("[%02d] not reached.\n", (int)Position);
        exit(-1);
    }
}
