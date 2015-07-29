#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/BufferFiller.i>
#include <quex/code_base/buffer/plain/BufferFiller_Plain.i>

#include "test-helper.h"

int
main(int argc, char** argv)
{
    using namespace quex;
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Load Forward: With Error in Stream (Character=%i Byte(s))\n", 
               sizeof(QUEX_TYPE_CHARACTER));
        return 0;
    }
    FILE*       fh = prepare_input_error();
    QUEX_NAME(Buffer)  buffer;

    const size_t       MemorySize  = 8;
    ByteLoader*        byte_loader = ByteLoader_FILE_new(fh);

    QUEX_NAME(Buffer_construct)(&buffer, 
                                QUEX_NAME(BufferFiller_new)(byte_loader, QUEX_TYPE_BUFFER_FILLER_PLAIN, 0, 0), 
                                0x0, MemorySize, 0, false);

    
    do {
        printf("------------------------------------------------------------\n");
        QUEX_NAME(Buffer_show_byte_content)(&buffer, 5);
        printf("     ");
        QUEX_NAME(Buffer_show_content_intern)(&buffer);
        printf("\n");
        if( buffer._memory._end_of_file_p != 0x0 ) break;
        buffer._input_p        = buffer._memory._back;
        buffer._lexeme_start_p = buffer._memory._back;
        /**/
        QUEX_NAME(BufferFiller_load_forward)(&buffer);
        printf("\n");
    } while( 1 + 1 == 2 );

    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}

