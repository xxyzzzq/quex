#include <quex/code_base/buffer/TEST/Buffer_test_common.i>
#include <quex/code_base/buffer/converter/BufferFiller_Converter.i>
#include <quex/code_base/buffer/converter/iconv/Converter_IConv.i>

using namespace std;
using namespace quex;

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Move by Offset: Forward (BPC=%i);\n", sizeof(QUEX_TYPE_CHARACTER));
        printf("CHOICES:  1, 2, 3, 4, 5;\n");
        return 0;
    }

    QuexBuffer      buffer;
    const int       RawMemorySize = 6;
    const size_t    StepSize      = atoi(argv[1]);
    char*           target_charset = (char*)"UCS-4LE";

    /*
    const uint16_t  test = 0x4711;
    if( ((uint8_t*)test)[0] == 47 && ((uint8_t*)test)[1] == 1 ) {
         target_charset = (char*)"UCS-4BE";
    }
    */

    std::FILE*                   fh = fopen("test.txt", "r");
    assert( fh != 0x0 );

    QuexBuffer_construct(&buffer, fh, 0x0, 5, "UTF8", RawMemorySize);

    test_move_forward(&buffer, StepSize); 
    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}

