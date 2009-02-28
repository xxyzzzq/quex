#include <quex/code_base/buffer/TEST/Buffer_test_common.i>
#include <quex/code_base/buffer/converter/icu/BufferFiller_ICU.i>

using namespace std;
using namespace quex;

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Tell and Seek: Bytes Per Character (BPC)=%i;\n", sizeof(QUEX_TYPE_CHARACTER));
        return 0;
    }

    QuexBuffer      buffer;
    const int       RawMemorySize = 6;


    std::FILE*     fh = fopen("test.txt", "r");
    size_t         SeekIndices[] = { 10, 4, 22, 8, 18, 11, 6, 2, 3, 15, 22, 17, 22, 21, 0, 20, 13, 1, 16, 12, 14, 9, 7, 5, 19, 999 };
    assert( fh != 0x0 );

    QuexBufferFiller_Converter<FILE>* filler = \
         QuexBufferFiller_Converter_new(fh, QuexConverter_ICU_new(), "UTF8", 0x0, RawMemorySize);
    buffer.filler = (quex::__QuexBufferFiller_tag*)filler;
    QuexBufferMemory_init(&(buffer._memory), MemoryManager_BufferMemory_allocate(5), 5);      
    QuexBuffer_init(&buffer, /* OnlyResetF */false);

    test_seek_and_tell(&buffer, SeekIndices);
    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}
