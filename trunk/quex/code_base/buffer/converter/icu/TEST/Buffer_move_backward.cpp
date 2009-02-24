#include <quex/code_base/buffer/TEST/Buffer_test_common.i>
#include <quex/code_base/buffer/converter/icu/BufferFiller_ICU.i>

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

    QuexBuffer      buffer;
    const int       RawMemorySize = 6;
    const size_t    StepSize      = atoi(argv[1]);

    /*
    const uint16_t  test = 0x4711;
    if( ((uint8_t*)test)[0] == 47 && ((uint8_t*)test)[1] == 1 ) {
         target_charset = (char*)"UCS-4BE";
    }
    */

    std::FILE*                       fh = fopen("test.txt", "r");
    assert( fh != 0x0 );

    QuexBufferFiller_Converter<FILE>* filler = \
        QuexBufferFiller_Converter_ICU_new(fh, "UTF8", 0x0, RawMemorySize);
    buffer.filler = (quex::__QuexBufferFiller_tag*)filler;
    QuexBufferMemory_init(&(buffer._memory), MemoryManager_BufferMemory_allocate(5), 5);      
    QuexBuffer_init(&buffer, /* OnlyResetF */false);

    /* Read until the end of file is reached and set the _input_p to EOF */
    while( 1 + 1 == 2 ) {
        buffer._input_p        = QuexBuffer_text_end(&buffer);
        buffer._lexeme_start_p = buffer._input_p;
        if( buffer._input_p == buffer._memory._end_of_file_p ) break;
        QuexBufferFiller_load_forward(&buffer);
    }
    test_move_backward(&buffer, StepSize); 
    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}

