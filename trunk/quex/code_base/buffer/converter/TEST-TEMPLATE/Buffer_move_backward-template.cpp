#include <quex/code_base/buffer/TEST/Buffer_test_common.i>
#include <quex/code_base/buffer/converter/BufferFiller_Converter.i>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/single.i>
#ifdef QUEX_OPTION_CONVERTER_ICONV
#   include <quex/code_base/buffer/converter/iconv/Converter_IConv.i>
#endif
#ifdef QUEX_OPTION_CONVERTER_ICU
#   include <quex/code_base/buffer/converter/icu/Converter_ICU.i>
#endif
#include <quex/code_base/buffer/BufferFiller.i>

#line 7 "Buffer_move_backward-template.cpp"

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
    std::FILE*         fh            = fopen("___DATA_DIR___/test.txt", "r");
    assert( fh != 0x0 );
    ByteLoader*              byte_loader = ByteLoader_FILE_new(fh);
    QUEX_NAME(BufferFiller)* filler = QUEX_NAME(BufferFiller_Converter_new)(
                                                  byte_loader, ___NEW___(),
                                                  "UTF8", 0, RawMemorySize);
    QUEX_NAME(Buffer_construct)(&buffer, filler, 5);
    assert((void*)((QUEX_NAME(BufferFiller_Converter)*)buffer.filler)->converter->convert 
           == (void*)___CONVERT___);

    /* Read until the end of file is reached and set the _input_p to EOF */
    while( 1 + 1 == 2 ) {
        buffer._input_p        = QUEX_NAME(Buffer_text_end)(&buffer);
        buffer._lexeme_start_p = buffer._input_p;
        if( buffer._input_p == buffer._memory._end_of_file_p ) break;
        QUEX_NAME(BufferFiller_load_forward)(&buffer);
    }
    test_move_backward(&buffer, StepSize); 
    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}

