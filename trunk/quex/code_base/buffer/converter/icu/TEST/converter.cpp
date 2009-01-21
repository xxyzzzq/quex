#include <cstring>
#include <quex/code_base/buffer/converter/icu/BufferFiller_ICU.i>
#include <quex/code_base/unicode>
using namespace std;
using namespace quex;

int get_input(char* Choice, uint8_t* buffer, size_t BufferSize);
void print_content(uint32_t* Begin, uint32_t* End);

int cl_has(int argc, char** argv, const char* What)
{ return argc > 1 && strcmp(argv[1], What) == 0; }

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Converter: Plain;\n");
        /* Please, use the ICU converter utility to find correct ICU coding names:
         * http://demo.icu-project.org/icu-bin/convexp?s=IANA                       */
        printf("CHOICES:   UTF-8, UTF-16;\n");
        return 0;
    }
    else if( argc < 2 ) {
        printf("Not enough arguments, use --hwut-info;\n");
        return 0;
    }

    QuexConverter*  converter = QuexConverter_ICU_new();
    /* (1) opening the converter
     *     'UTF-32' == 'ISO-10646-UCS-4' in IANA */
    converter->open(converter, argv[1], "UTF-32");

    /* (2.1) Load file content corresponding the input coding */
    const size_t Size = 4096;
    uint8_t      in[Size];
    uint8_t*     in_iterator = in;
    uint32_t     out[Size];
    uint32_t*    out_iterator = out;

    const size_t ContentSize = get_input(argv[1], in, Size);
    if( ContentSize == 0 ) return -1;

    /* (2.2) Convert buffer content. */
    converter->convert(converter, &in_iterator, in + ContentSize, &out_iterator, out + Size);

    /* (2.3) Print the content. Each character in hex and its utf-8 correspondance. */
    print_content(out, out_iterator);

    /* (3) delete the converter (maybe, check then also for memory leaks with valgrind) */
    converter->delete_self(converter);
}

int 
get_input(char* Choice, uint8_t* buffer, size_t BufferSize)
{
    const char* filename = 0x0;
    if     ( strcmp("UTF-8",  Choice) == 0 )  filename = "example.utf8";
    else if( strcmp("UTF-16", Choice) == 0 )  filename = "example.utf16";
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
    fread(buffer, 4096, sizeof(char), fh);
    content_size = ftell(fh);
    if( content_size == 0 ) {
        printf("File '%s' is empty.\n", filename);
        return 0;
    }
    return content_size;
}

void 
print_content(uint32_t* Begin, uint32_t* End)
{
    uint8_t   utf8_c[10];
    size_t    utf8_c_length = (size_t)-1;
    assert(End > Begin);

    size_t    i = 0;
    for(uint32_t* iterator = Begin; iterator != End; ++iterator, ++i) {
        utf8_c_length         = quex::Quex_unicode_to_utf8(*iterator, utf8_c);
        utf8_c[utf8_c_length] = '\0';

        printf("$%04X: %02X.%02X.%02X.%02X ('%s')\n",
               (int)i * sizeof(QUEX_CHARACTER_TYPE),
               (int)((*iterator & 0xFF000000) >> 24),
               (int)((*iterator & 0x00FF0000) >> 16),
               (int)((*iterator & 0x0000FF00) >> 8),
               (int)((*iterator & 0x000000FF)),
               utf8_c);
    }
}
