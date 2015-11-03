#line 1 "converter-statefulness-template.cpp"
#include <cstring>
#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#ifdef    __QUEX_OPTION_LITTLE_ENDIAN
#   undef __QUEX_OPTION_LITTLE_ENDIAN
#endif
#ifdef    __QUEX_OPTION_BIG_ENDIAN
#   undef __QUEX_OPTION_BIG_ENDIAN
#endif
#include <quex/code_base/buffer/Buffer.i>
#ifdef QUEX_OPTION_CONVERTER_ICONV
#   include <quex/code_base/buffer/filler/converter/iconv/Converter_IConv.i>
#endif
#ifdef QUEX_OPTION_CONVERTER_ICU
#   include <quex/code_base/buffer/filler/converter/icu/Converter_ICU.i>
#endif
#include <quex/code_base/buffer/filler/BufferFiller.i>
#include <quex/code_base/converter_helper/from-utf8.i>
#include <quex/code_base/converter_helper/from-utf16.i>
#include <quex/code_base/converter_helper/from-utf32.i>
#include <quex/code_base/converter_helper/from-unicode-buffer>
#include <quex/code_base/converter_helper/from-unicode-buffer.i>

#include <quex/code_base/single.i>

using namespace std;
using namespace quex;

int get_input(const char* Choice, uint8_t* buffer, size_t BufferSize);
void print_content(QUEX_TYPE_CHARACTER* Begin, QUEX_TYPE_CHARACTER* End);

int cl_has(int argc, char** argv, const char* What)
{ return argc > 1 && strcmp(argv[1], What) == 0; }

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Converter: Possible 'statefulness' has been ruled out (%i bit);\n", (int)(8*sizeof(QUEX_TYPE_CHARACTER)));
        /* Please, use the ICU converter utility to find correct ICU coding names:
         * http://demo.icu-project.org/icu-bin/convexp?s=IANA                       */
        printf("CHOICES:   UTF-8, UTF-16;\n");
        return 0;
    }
    else if( argc < 2 ) {
        printf("Not enough arguments, use --hwut-info;\n");
        return 0;
    }

    const char*            input_codec = argv[1];
    QUEX_NAME(Converter)*  converter   = ___NEW___(input_codec, 0x0);

    /* Load file content corresponding the input coding                      */
    const size_t  Size = 16384;
    uint8_t       in[Size];
    const size_t  ContentSize = get_input(input_codec, in, Size);
    if( ! ContentSize ) return -1;

    QUEX_TYPE_CHARACTER         out[Size];
    const QUEX_TYPE_CHARACTER*  out_end = &out[Size];

    /* (2.2) Convert buffer content.                                         */
    for(size_t i=ContentSize; i != 0 ; --i) {
        uint8_t*                in_iterator  = &in[0];
        uint8_t*                in_end       = &in[i];
        QUEX_TYPE_CHARACTER*    out_iterator = &out[0];

        if( converter->stomach_clear ) converter->stomach_clear(converter);

        bool   Result = converter->convert(converter, 
                                           &in_iterator,  in_end, 
                                           &out_iterator, out_end);

        printf(">> result:  %s; ", Result ? "true" : "false");
        printf("output iterator offset: %04i\n", (int)(out_iterator - out));
        printf("## input iterator offset:  %04i\n", (int)(in_iterator - in));

        /* (2.3) Print the content. Each character in hex and its utf-8 correspondance. */
        print_content(out, out_iterator);
    }

    /* (3) delete the converter (maybe, check then also for memory leaks with valgrind) */
    converter->delete_self(converter);
}

int 
get_input(const char* Choice, uint8_t* buffer, size_t BufferSize)
{
    const char* filename = 0x0;

    /* Converters may differ parsing the default UTF-16 and UTF-8 encoding.
     * Depending on the particular behavior, the BOM may have to be provided.
     * Thus, each directory provides its own example2.* files.               */
    if     ( strcmp("UTF-8",  Choice) == 0 ) {
        filename = "___DATA_DIR___/examples/small.utf8";
    }
    else if( strcmp("UTF-16", Choice) == 0 )  {
        filename = "___DATA_DIR___/examples/small.utf16";
    }
    else {
        printf("Coding %s not supported, use --hwut-info;\n", Choice);
        return 0;
    }

    FILE*    fh           = fopen(filename, "rb");
    size_t   content_size = (size_t)-1;

    if( fh == NULL ) {
        printf("Could not open file '%s'.\n", filename);
        return 0;
    } 
    fread(buffer, 16384, sizeof(char), fh);

    content_size = ftell(fh);
    if( ! content_size ) {
        printf("File '%s' is empty.\n", filename);
        return 0;
    }
    return content_size;
}

void 
print_content(QUEX_TYPE_CHARACTER* Begin, QUEX_TYPE_CHARACTER* End)
{
    uint8_t   utf8_c[10];
    uint8_t*  p = 0x0;

    printf("%i: [", (int)(End-Begin));
    for(const QUEX_TYPE_CHARACTER* iterator = Begin; iterator != End; ) {
        p = utf8_c;
        switch( sizeof(QUEX_TYPE_CHARACTER) ) {
        case 1:  quex::utf8_to_utf8_character((const uint8_t**)&iterator, &p); break;
        case 2:  quex::utf16_to_utf8_character((const uint16_t**)&iterator, &p); break;
        case 4:  quex::utf32_to_utf8_character((const uint32_t**)&iterator, &p); break;
        default: assert(false);
        }
        *p = '\0';
        printf("%s", utf8_c);
    }
    printf("]\n\n");
}
