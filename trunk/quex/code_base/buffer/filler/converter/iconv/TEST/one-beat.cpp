/* PURPOSE: Checking the following functions of a Converter_IConv:
 * 
 *             .convert()          '.   
 *             .stomach_byte_n()    | => Behavior of Converter
 *             .stomach_clear()    .'
 *
 * WHERE CONTENT IS CONVERTED IN A SINGLE BEAT.
 * 
 * These functions implement the main behavior of a Converter. The following
 * things must hold:
 * 
 *   (1) The result of the '.convert()' function must be correct.
 * 
 *       For this, the result is compared with some reference file which
 *       contains alread the correct result.
 * 
 *   (2) The '.convert()' function must adapt (i) the source pointer to
 *       indicate how many input bytes have been treated. (ii) The drain pointer
 *       must also be adapted to indidicate how many input.
 * 
 *       Since everything is converted in a single beat, the adapted source
 *       pointer must stand at the the end of the source and the drain pointer
 *       at the end of the drain.
 * 
 *       In a variation it is checked the case where the drain is not able to
 *       hold all converted characters.
 * 
 *   (3) This test converts everything in one single beat, so it must be
 *       expected that the '.stomach_byte_n()' is zero.
 *
 *   (4) The input buffer is NOT to be touched!
 *
 * The test is repeated trice. Call '.stomach_clear()' to ensure it does nothing
 * bad.
 *
 * This is compiled for four different setting QUEX_TYPE_CHARACTER:
 *                  uint8_t, uint16_t, uint32_t, wchar_t.
 * 
 * (C) Frank-Rene Schaefer                                                   */

#include <basic_functionality.h>
#include <quex/code_base/buffer/filler/converter/iconv/Converter_IConv.i>
#include <quex/code_base/buffer/filler/converter/Converter.i>
#include <hwut_unit.h>
#define STR(X) #X

int
main(int argc, char** argv)
{
    using namespace quex;

    hwut_info("Converter_IConv: Convert all in one beat (" STR(QUEX_TYPE_CHARACTER) ");"
              "CHOICES: ASCII, UTF8, UTF16, UCS4-BE;")
    if( ! argc ) abort();

    QUEX_NAME(Converter)* converter = QUEX_NAME(Converter_IConv_new)(argv[1], (const char*)0);
    
    test_conversion_in_one_beat(converter, argv[1]);

    printf("<terminated>\n");
}

