#include <quex/code_base/buffer/TEST/Buffer_test_common.i>
#include <quex/code_base/buffer/converter/iconv/BufferFiller_IConv.i>

using namespace std;
using namespace quex;

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Tell and Seek: Bytes Per Character (BPC)=%i;\n", sizeof(QUEX_CHARACTER_TYPE));
        return 0;
    }

    QuexBuffer      buffer;
    const int       RawMemorySize = 6;
    char*           target_charset = (char*)"UCS-4LE";

    /*
    const uint16_t  test = 0x4711;
    if( ((uint8_t*)test)[0] == 47 && ((uint8_t*)test)[1] == 1 ) {
         target_charset = (char*)"UCS-4BE";
    }
    */

    QuexBufferFiller_Converter<FILE> filler;
    std::FILE*     fh = fopen("test.txt", "r");
    size_t         SeekIndices[] = { 10, 4, 22, 8, 18, 11, 6, 2, 3, 15, 22, 17, 22, 21, 0, 20, 13, 1, 16, 12, 14, 9, 7, 5, 19, 999 };
    assert( fh != 0x0 );

    QuexBufferFiller_Converter_IConv_construct(&filler, fh, "UTF8", target_charset, RawMemorySize);
    buffer.filler = (quex::__QuexBufferFiller_tag*)&filler;
    QuexBufferMemory_init(&(buffer._memory), MemoryManager_get_BufferMemory(5), 5);      
    QuexBuffer_init(&buffer, /* OnlyResetF */false);

    test_seek_and_tell(&buffer, SeekIndices);
    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}
