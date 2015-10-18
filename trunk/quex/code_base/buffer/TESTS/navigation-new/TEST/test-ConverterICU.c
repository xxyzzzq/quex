#include <hwut_unit.h>
#include <basic_functionality.h>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/filler/converter/iconv/Converter_IConv>
#include <quex/code_base/buffer/filler/converter/iconv/Converter_IConv.i>
#include <quex/code_base/MemoryManager.i>

QUEX_NAMESPACE_MAIN_OPEN
static void test(bool LinearF, size_t BPC);
static void test_file(const char* FileName, const char* Codec, const char* FileStem);
QUEX_NAMESPACE_MAIN_CLOSE

int
main(int argc, char** argv)
{
    const size_t              BPC         = sizeof(QUEX_TYPE_CHARACTER);
    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Buffer Tell&Seek: BufferFiller_Converter_ICU (BPC=%i, FALLBACK=%i);\n", 
               BPC, QUEX_SETTING_BUFFER_MIN_FALLBACK_N);
        printf("CHOICES: linear, stepping;\n"
               "SAME;\n");
        return 0;
    }
    hwut_if_choice("linear")   test(true, BPC);
    hwut_if_choice("stepping") test(false, BPC);

    return 0;
}

QUEX_NAMESPACE_MAIN_OPEN
static void
test(bool LinearF, size_t BPC)
{
    const char*   file_4 = LinearF ? "examples/languages.ucs4-be"    : "examples/languages.utf8";
    const char*   file_2 = LinearF ? "examples/small.ucs4-be"        : "examples/small.utf8";
    const char*   file_1 = LinearF ? "examples/festgemauert.ucs4-be" : "examples/festgemauert.dat";
    const char*   codec  = LinearF ? "UCS-4BE"                       : "UTF-8";

    switch( BPC ) {
    case 4:  test_file(file_4, codec, "examples/languages");   /* only with UCS4         */
    case 2:  test_file(file_2, codec, "examples/small");       /* only with UCS4, UCS2   */
    case 1:  test_file(file_1, codec, "examples/festgemauert");/* with UCS4, UCS2, ASCII */
             break;
    default: hwut_verify(false);
    }
}

static void
test_file(const char* FileName, const char* Codec, const char* FileStem)
{
    QUEX_NAME(Buffer)         buffer;
    /* With 'BufferFiller_Plain()' no conversion takes place. Thus, the file
     * containing the REFERENCE data and the INPUT file are the SAME.        */
    const char*               ref_file_name = find_reference(FileStem); 
    ByteLoader*               byte_loader   = ByteLoader_FILE_new_from_file_name(FileName);
    QUEX_NAME(Converter)*     converter     = QUEX_NAME(Converter_ICU_new)();
    QUEX_NAME(BufferFiller)*  filler;  
    const size_t              MemorySize  = true ? 5 : 16;
    QUEX_TYPE_CHARACTER       memory[MemorySize];

    if( ! byte_loader ) {
        printf("Failed to open '%s'.", FileName);
        hwut_verify(false);
    }

    filler = QUEX_NAME(BufferFiller_Converter_new)(byte_loader, converter, 
                                                   Codec, 0x0, 7);

    /* If file was not opened in binary mode no converter filler is created! */
    __quex_assert(filler); 

    QUEX_NAME(Buffer_construct)(&buffer, filler, &memory[0], MemorySize, 0, E_Ownership_EXTERNAL);

    /* REFERENCE file and INPUT file are the SAME.                           */
    hwut_verify(basic_functionality(&buffer, ref_file_name));

    filler->delete_self(filler);
}
QUEX_NAMESPACE_MAIN_CLOSE
