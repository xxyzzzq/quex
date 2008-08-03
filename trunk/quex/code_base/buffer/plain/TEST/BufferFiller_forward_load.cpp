#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/BufferFiller.i>

#include <iostream>

int cl_has(int argc, char** argv, const char* What)
{ return argc > 1 && strcmp(argv[1], What) == 0; }

FILE*
prepare_input()
{
    /* NOTE: This function depends on the compiler setting QUEX_CHARACTER_TYPE */

    const char   test_string[] = "Fest gemauert in der Erden";
    const char*  End = test_string + strlen(test_string);
    FILE*        fh  = tmpfile();
    /**/
    QUEX_CHARACTER_TYPE character       = (QUEX_CHARACTER_TYPE)0;
    uint8_t*            character_begin = 0x0;

    /* Let's cast using 'real' types, thus ensure that byte-allignment
     * in writing and reading is the same. */
    for(char* p = (char*)test_string; p != (char*)End; ++p) {
        /* Copy the letter into the character according to its alignment */
        character       = (QUEX_CHARACTER_TYPE)*p;
        /* Now, write down the bytes of the character in whatever aligment it was. */
        character_begin = (uint8_t*)&character;
        fwrite(character_begin, sizeof(QUEX_CHARACTER_TYPE), 1, fh);
    }
    fseek(fh, 0, SEEK_SET); /* start reading from the beginning */

    return fh;
}

int
main(int argc, char** argv)
{
    using namespace quex;
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Basics: Load Forward, 1 Character = %i Byte(s)\n", sizeof(QUEX_CHARACTER_TYPE));
        return 0;
    }
    FILE*                         fh = prepare_input();
    QuexBuffer                    buffer;
    QuexBufferFiller_Plain<FILE>  filler;
    QUEX_CHARACTER_TYPE           memory[8];

    BufferFiller_Plain_init(&filler, fh);
    QuexBuffer_init(&buffer, memory, 8, (QuexBufferFiller*)&filler);

    
    do {
        printf("------------------------------------------------------------\n");
        QuexBuffer_show_byte_content(&buffer, 5);
        printf("     ");
        QuexBuffer_show_content(&buffer);
        printf("\n");
        if( buffer._end_of_file_p != 0x0 ) break;
        buffer._input_p        = buffer._memory._back;
        buffer._lexeme_start_p = buffer._memory._back;
        /**/
        QuexBufferFiller_load_forward(&buffer);
        printf("\n");
    } while( 1 + 1 == 2 );

    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}

