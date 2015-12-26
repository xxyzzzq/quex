/* PURPOSE: Testing Buffer-Seeking with BufferFiller_Converter.
 *
 * Buffer-Seeking tries to set the 'read_p' to a specific character given by a
 * character index. For this, new content may be loaded into the buffer.  The
 * tests of these files do a 'wild tell&seek' on positions in a stream.  All
 * tests are based on the file:
 *
 *                        basic_functionality.c
 *
 * located in this directory. For each file to be treated, there is a reference
 * file which is loaded into a reference buffer. At any point in time, the
 * content of the buffer is checked against the references. 
 *
 * Of course, all asserts are active during the test. So, the slightest
 * misbehavior is detected. If a histogram of seek positions or seek position
 * differences is desired, consider 'basic_functionality.c' which tells how
 * to output and print statistics with gnuplot.
 *
 * CHOICES: Choices consist of multiple tokens as they are 
 *          ICU/IConv       -- The converter to be used 
 *          linear/stepping -- linear => compute byte stream positions for input.
 *                             stepping => step to position from some reference.
 *          cls             -- 'clueless stomach'. If specified the converter
 *                             does not have a clue about how many bytes are in
 *                             its stomach.
 *
 * The stepping is imposed by opening a file of a dynamic character length 
 * codec, namely 'UTF8'. Then, no linear relationship can be assumed between 
 * input byte position and stream position.
 *
 * (C) Frank-Rene Schaefer                                                   */
#include <hwut_unit.h>
#include <basic_functionality.h>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/filler/converter/iconv/Converter_IConv>
#include <quex/code_base/buffer/filler/converter/iconv/Converter_IConv.i>
#include <quex/code_base/buffer/loader/ByteLoader_Memory>
#include <quex/code_base/buffer/loader/ByteLoader_Memory.i>
// #include <quex/code_base/MemoryManager.i>

QUEX_NAMESPACE_MAIN_OPEN
typedef enum { TEST_ICU, TEST_ICONV } E_ConverterTestType;

static void      test(E_ConverterTestType CTT, bool LinearF, bool ClueLessStomachF, size_t BPC);
static void      test_file(E_ConverterTestType CTT, const char* Codec, bool LinearF, bool ClueLessStomachF, const char* FileName, const char* FileStem);
static ptrdiff_t clueless_stomach_byte_n(QUEX_NAME(Converter)* me);

QUEX_NAMESPACE_MAIN_CLOSE

int
main(int argc, char** argv)
{
    const size_t  BPC = sizeof(QUEX_TYPE_CHARACTER);

    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Buffer Tell&Seek: BufferFiller_Converter_IConv (BPC=%i, FALLBACK=%i);\n", 
               BPC, QUEX_SETTING_BUFFER_MIN_FALLBACK_N);
        printf("CHOICES: ICU-linear, ICU-stepping,\n"
               "         IConv-linear, IConv-stepping,\n"
               "         IConv-stepping-cls, ICU-stepping-cls;\n"
               "SAME;\n");
        return 0;
    }

    hwut_if_choice("ICU-linear")     test(TEST_ICU,   true, false, BPC);
    hwut_if_choice("ICU-stepping")   test(TEST_ICU,   false, false, BPC);
    hwut_if_choice("IConv-linear")   test(TEST_ICONV, true, false, BPC);
    hwut_if_choice("IConv-stepping") test(TEST_ICONV, false, false, BPC);

    /* Clueless stomach: The converter has no clue how many bytes are left
     * in its stomach. This is an extra challenge for the 'seeker'.          */
    hwut_if_choice("ICU-stepping-cls")   test(TEST_ICU,   false, true, BPC);
    hwut_if_choice("IConv-stepping-cls") test(TEST_ICONV, false, true, BPC);

    return 0;
}

QUEX_NAMESPACE_MAIN_OPEN

static void
test(E_ConverterTestType CTT, bool LinearF, bool ClueLessStomachF, size_t BPC)
{
    const char*   file_4 = LinearF ? "examples/languages.ucs4-be"    : "examples/languages.utf8";
    const char*   file_2 = LinearF ? "examples/small.ucs4-be"        : "examples/small.utf8";
    const char*   file_1 = LinearF ? "examples/festgemauert.ucs4-be" : "examples/festgemauert.dat";
    const char*   codec  = LinearF ? (CTT == TEST_ICONV ? "UCS-4BE" : "UTF-32-BE") : "UTF-8";

    /* Need a new converter for each test. */
    switch( BPC ) {
    case 4:  test_file(CTT, codec, LinearF, ClueLessStomachF, file_4, "examples/languages");   /* only with UCS4         */
    case 2:  test_file(CTT, codec, LinearF, ClueLessStomachF, file_2, "examples/small");       /* only with UCS4, UCS2   */
    case 1:  test_file(CTT, codec, LinearF, ClueLessStomachF, file_1, "examples/festgemauert");/* with UCS4, UCS2, ASCII */
             break;
    default: hwut_verify(false);
    }
}

static void
test_file(E_ConverterTestType CTT, const char* Codec, bool LinearF, bool ClueLessStomachF, const char* FileName, const char* FileStem)
{
    QUEX_NAME(Buffer)         buffer;
    QUEX_NAME(Converter)*     converter;
    /* With 'BufferFiller_Plain()' no conversion takes place. Thus, the file
     * containing the REFERENCE data and the INPUT file are the SAME.        */
    const char*               ref_file_name = find_reference(FileStem); 
#   if 0
    QUEX_NAME(ByteLoader)*    byte_loader   = QUEX_NAME(ByteLoader_FILE_new_from_file_name)(FileName);
#   else
    QUEX_NAME(ByteLoader)*    byte_loader   = QUEX_NAME(ByteLoader_Memory_new_from_file_name)(FileName);
#   endif
    const size_t              MemorySize    = true ? 5 : 16;
    QUEX_TYPE_CHARACTER       memory[MemorySize];
    QUEX_NAME(BufferFiller)*  filler;  

    switch( CTT ) {
    case TEST_ICU:   converter = QUEX_NAME(Converter_ICU_new)(Codec, 0); break;
    case TEST_ICONV: converter = QUEX_NAME(Converter_IConv_new)(Codec, 0); break;
    default:         __quex_assert(false); 
    }
    __quex_assert(converter);

    if( ClueLessStomachF ) {
        converter->stomach_byte_n = clueless_stomach_byte_n;
    }

    if( ! byte_loader ) {
        printf("Failed to open '%s'.", FileName);
        hwut_verify(false);
    }

    filler = QUEX_NAME(BufferFiller_Converter_new)(byte_loader, converter, 7);

    /* If file was not opened in binary mode no converter filler is created! */
    __quex_assert(filler); 

    QUEX_NAME(Buffer_construct)(&buffer, filler, &memory[0], MemorySize, 0, 
                                E_Ownership_EXTERNAL);
    if( LinearF ) { 
        __quex_assert(filler->byte_n_per_character != -1);
        __quex_assert(byte_loader->binary_mode_f);
    }
    else {
        __quex_assert(filler->byte_n_per_character == -1);
    }

    /* REFERENCE file and INPUT file are the SAME.                           */
    hwut_verify(basic_functionality(&buffer, ref_file_name));

    filler->delete_self(filler);
    byte_loader->delete_self(byte_loader);
    converter->delete_self(converter);
}

static ptrdiff_t
clueless_stomach_byte_n(QUEX_NAME(Converter)* me)
{ 
    /* A '-1' tells the caller that the converter has no clue about the number
     * of bytes in its stomach.                                              */
    return (ptrdiff_t)-1;
}
QUEX_NAMESPACE_MAIN_CLOSE
