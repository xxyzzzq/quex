#include <cstring>
#include <quex/code_base/buffer/converter/iconv/BufferFiller_IConv.i>
#include <quex/code_base/unicode>
using namespace std;
using namespace quex;

int get_input(char* Choice, uint8_t* buffer, size_t BufferSize);
void print_content(QUEX_CHARACTER_TYPE* Begin, QUEX_CHARACTER_TYPE* End);

int cl_has(int argc, char** argv, const char* What)
{ return argc > 1 && strcmp(argv[1], What) == 0; }

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Converter: Possible 'statefulness' has been ruled out (%i bit);\n", (int)(8*sizeof(QUEX_CHARACTER_TYPE)));
        /* Please, use the ICU converter utility to find correct ICU coding names:
         * http://demo.icu-project.org/icu-bin/convexp?s=IANA                       */
        printf("CHOICES:   UTF-8, UTF-16;\n");
        return 0;
    }
    else if( argc < 2 ) {
        printf("Not enough arguments, use --hwut-info;\n");
        return 0;
    }

    QuexConverter*  converter = QuexConverter_IConv_new();
    /* (1) opening the converter with default internal character format */
    converter->open(converter, argv[1], 0x0);

    /* (2.1) Load file content corresponding the input coding */
    const size_t Size = 16384;
    uint8_t      in[Size];

    const size_t ContentSize = get_input(argv[1], in, Size);
    if( ContentSize == 0 ) return -1;

    /* (2.2) Convert buffer content. */
    for(size_t i=ContentSize; i != 0 ; --i){

        uint8_t*                in_iterator = in;
        QUEX_CHARACTER_TYPE     out[Size];
        QUEX_CHARACTER_TYPE*    out_iterator = out;
        if( converter->on_conversion_discontinuity != 0x0 ) 
            converter->on_conversion_discontinuity(converter);
        bool      Result = converter->convert(converter, &in_iterator, in + i, &out_iterator, out + Size);
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
get_input(char* Choice, uint8_t* buffer, size_t BufferSize)
{
    const char* filename = 0x0;
    if     ( strcmp("UTF-8",  Choice) == 0 )  filename = "example2.utf8";
    else if( strcmp("UTF-16", Choice) == 0 )  filename = "example2.utf16";
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
    if( content_size == 0 ) {
        printf("File '%s' is empty.\n", filename);
        return 0;
    }
    return content_size;
}

void 
print_content(QUEX_CHARACTER_TYPE* Begin, QUEX_CHARACTER_TYPE* End)
{
    uint8_t   utf8_c[10];
    size_t    utf8_c_length = (size_t)-1;

    size_t    i = 0;
    printf("%i: [", (int)(End-Begin));
    for(QUEX_CHARACTER_TYPE* iterator = Begin; iterator != End; ++iterator, ++i) {
        utf8_c_length         = quex::Quex_unicode_to_utf8(*iterator, utf8_c);
        utf8_c[utf8_c_length] = '\0';
        printf("%s", utf8_c);
    }
    printf("]\n\n");
}
