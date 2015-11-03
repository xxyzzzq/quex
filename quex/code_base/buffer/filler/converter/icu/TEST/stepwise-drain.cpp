/* PURPOSE: Checking the following functions of a Converter_IConv:
 * 
 *             .convert()          '.   
 *             .stomach_byte_n()    | => Behavior of Converter
 *             .stomach_clear()    .'
 * 
 * WHERE CONTENT IS CONVERTED IN MANY TINY STEPS.
 *
 * The following things must hold:
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
 * The test is repeated trice call '.stomach_clear()' to ensure it does nothing
 * bad.
 *
 * This is compiled for four different setting QUEX_TYPE_CHARACTER:
 *                  uint8_t, uint16_t, uint32_t, wchar_t.
 * 
 * (C) Frank-Rene Schaefer                                                   */

#include <basic_functionality.h>
#include <hwut_unit.h>

int
main(int argc, char** argv)
{
    using namespace quex;

    hwut_info("Convert drain character by drain character: " STR(QUEX_TYPE_CHARACTER) ";");

    test_with_available_codecs(test_conversion_stepwise_drain);
}

