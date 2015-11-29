#include <quex/code_base/buffer/TESTS/Buffer_test_common.i>
#include <quex/code_base/buffer/filler/BufferFiller_Converter.i>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/single.i>
#ifdef QUEX_OPTION_CONVERTER_ICONV
#   include <quex/code_base/buffer/filler/converter/iconv/Converter_IConv.i>
#endif
#ifdef QUEX_OPTION_CONVERTER_ICU
#   include <quex/code_base/buffer/filler/converter/icu/Converter_ICU.i>
#endif
#include <quex/code_base/buffer/filler/BufferFiller.i>

#line 7 "Buffer_seek_backward-template.cpp"

using namespace std;
using namespace quex;

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Move by Offset: Backward (BPC=%i);\n", sizeof(QUEX_TYPE_CHARACTER));
        printf("CHOICES:  1, 2, 3, 4, 5;\n");
        return 0;
    }

    QUEX_NAME(Buffer)  buffer;
    const int          RawMemorySize = 6;
    const size_t       StepSize      = atoi(argv[1]);
    std::FILE*         fh            = fopen("___DATA_DIR___/test.txt", "rb");
    assert( fh != 0x0 );
    QUEX_NAME(ByteLoader)*              byte_loader = QUEX_NAME(ByteLoader_FILE_new)(fh, true);
    QUEX_NAME(BufferFiller)* filler = QUEX_NAME(BufferFiller_Converter_new)(
                                                byte_loader, ___NEW___("UTF-8", 0),
                                                RawMemorySize);
    const size_t         MemorySize = 5;
    QUEX_TYPE_CHARACTER  memory[MemorySize];

    QUEX_NAME(Buffer_construct)(&buffer, filler, &memory[0], MemorySize, 0, E_Ownership_EXTERNAL);

    assert((void*)((QUEX_NAME(BufferFiller_Converter)*)buffer.filler)->converter->convert 
           == (void*)___CONVERT___);

    /* Read until the end of file is reached and set the _read_p to EOF */
    while( 1 + 1 == 2 ) {
        buffer._read_p         = me->input.end_p;
        buffer._lexeme_start_p = buffer._read_p;
        if( buffer._read_p == buffer.input.end_p ) break;
        QUEX_NAME(Buffer_load_forward)(&buffer);
    }
    test_seek_backward(&buffer, StepSize); 
    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}

