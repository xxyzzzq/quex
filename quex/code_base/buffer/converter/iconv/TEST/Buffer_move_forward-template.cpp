#include <quex/code_base/buffer/TEST/Buffer_test_common.i>
#include <quex/code_base/buffer/converter/BufferFiller_Converter.i>
#include <quex/code_base/buffer/Buffer.i>
#if ! defined(QUEX_OPTION_MULTI)
#   define  QUEX_OPTION_MULTI_ALLOW_IMPLEMENTATION
#   include <quex/code_base/Multi.i>
#   undef   QUEX_OPTION_MULTI_ALLOW_IMPLEMENTATION
#endif
#include ___HEADER___

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

    QUEX_NAME(Buffer)  buffer;
    const int          RawMemorySize = 6;
    const size_t       StepSize      = atoi(argv[1]);
    std::FILE*         fh            = fopen("test.txt", "r");
    assert( fh != 0x0 );

    QUEX_NAME(Buffer_construct)(&buffer, fh, 0x0, 5, 0x0, "UTF8", RawMemorySize, false);
    assert((void*)((QUEX_NAME(BufferFiller_Converter)<FILE>*)buffer.filler)->converter->convert 
           == (void*)___CONVERT___);

    test_move_forward(&buffer, StepSize); 
    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}

