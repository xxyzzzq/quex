#include <quex/code_base/buffer/TEST/Buffer_test_common.i>
#include <quex/code_base/buffer/converter/BufferFiller_Converter.i>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/single.i>
#ifdef QUEX_OPTION_BUFFER_FILLER_CONVERTER_ICONV
#   include <quex/code_base/buffer/converter/iconv/Converter_IConv.i>
#endif
#ifdef QUEX_OPTION_BUFFER_FILLER_CONVERTER_ICU
#   include <quex/code_base/buffer/converter/icu/Converter_ICU.i>
#endif

#line 7 "Buffer_tell_and_seek-template.cpp"

using namespace std;
using namespace quex;

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Tell and Seek: Bytes Per Character (BPC)=%i;\n", sizeof(QUEX_TYPE_CHARACTER));
        return 0;
    }

    QUEX_NAME(Buffer)  buffer;
    const int          RawMemorySize = 6;
    std::FILE*         fh            = fopen("___DATA_DIR___/test.txt", "r");
    size_t             SeekIndices[] = { 10, 4, 22, 8, 18, 11, 6, 
                                         2, 3, 15, 22, 17, 22, 21,
                                         0, 20, 13, 1, 16, 12, 14, 
                                         9, 7, 5, 19, 999 };
    ByteLoader*        byte_loader = ByteLoader_FILE_new(fh);
    assert( fh != 0x0 );

    QUEX_NAME(BufferFiller)* filler = QUEX_NAME(BufferFiller_Converter_new)(
                                                        byte_loader, ___NEW___(),
                                                        "UTF8", 0, RawMemorySize);
    QUEX_NAME(Buffer_construct)(&buffer, filler, 5);
    assert((void*)((QUEX_NAME(BufferFiller_Converter)*)buffer.filler)->converter->convert 
           == (void*)___CONVERT___);

    test_seek_and_tell(&buffer, SeekIndices);
    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}
