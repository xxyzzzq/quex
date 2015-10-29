/* PURPOSE: This tests checks on the basic member functions of a Buffer 
 *          to seek, i.e. SETTING the 'read_p' to a specific character index.
 *
 * FUNCTIONS:
 *                  Buffer_tell()
 *                  Buffer_seek()
 *                  Buffer_seek_forward()
 *                  Buffer_seek_backward()
 *
 * MASSIVE seeking of a random position puts heave charge on all of the
 * mentioned functions. The histogram of seek positions and seek position 
 * differences has been checked to cover all positions of a file multiple
 * times. If can be verified using 'gnuplot' as mentioned below in the 
 * comment of 'basic_functionality()'.
 *
 * Before massive random seeking is applied a 'single step' seek forward
 * and single step backward is done until the border is reached, and then
 * one more time. 
 *
 * Correctness of the buffer's consistency is probed by all active asserts
 * plus some 'hwut_verify' macros.
 *
 * The functions of this file serve as a basis to setup Buffer seek and tell
 * tests. Examples of such setups are 'test-Plain.c' and 'test-Converter.c'.
 *
 * (C) Frank-Rene Schaefer                                                   */
#include <basic_functionality.h>
#include <hwut_unit.h>


QUEX_NAMESPACE_MAIN_OPEN

static QUEX_TYPE_CHARACTER       reference[8192];
static QUEX_TYPE_STREAM_POSITION reference_load(const char* file_stem);
static bool                      verify_content(QUEX_NAME(Buffer)* me, 
                                                QUEX_TYPE_STREAM_POSITION Position, 
                                                QUEX_TYPE_STREAM_POSITION position_limit);
static void                      print_difference(QUEX_NAME(Buffer)* me);
static bool                      seek_forward(QUEX_NAME(Buffer)*        me,
                                              QUEX_TYPE_STREAM_POSITION PositionLimit);
static bool                      seek_backward(QUEX_NAME(Buffer)*        me,
                                               QUEX_TYPE_STREAM_POSITION PositionLimit);

bool
basic_functionality(QUEX_NAME(Buffer)* me, const char* ReferenceFileName)
/* InputFile is the name of the file on which the buffer filler operates. 
 * This function searches for the correspondant file that contains raw buffer
 * content in unicode that corresponds to the InputFile's data. 
 *
 * RETURNS: true -- success
 *          false -- else.                                                   */
{
    int  i;
    QUEX_TYPE_STREAM_POSITION position = 0;
    QUEX_TYPE_STREAM_POSITION previous = 0;
    QUEX_TYPE_STREAM_POSITION position_limit;
    QUEX_TYPE_STREAM_POSITION random_value = 1234567890;
    static bool               virginity_f = true;

    if( virginity_f ) {
        virginity_f = false;
        printf("##  Investigate statistics with gnuplot:\n"
               "##  In 'basic_functionality.c'; change line '#if 0' --> '#if 1'\n"
               "##  => redirect to file, e.g. 'tmp.dat'\n"
               "##  => gnuplot\n"
               "##     > hist(x,width)=width*floor(x/width)\n"
               "##     > set boxwith 1\n"
               "##     > plot \"tmp.dat\" u (hist($2,1)):(1.0) smooth freq w boxes\n"
               "##     use: $1: histogram of position; \n"
               "##     use: $2: historgram of differences.\n");
    }

    __quex_assert( ! QUEX_NAME(Buffer_is_empty)(me));

    /* position_limit = number of characters in the file, i.e. the number of
     * raw unicode characters in the reference file.                         */
    position_limit = reference_load(ReferenceFileName);
    hwut_verify(position_limit);

    /* Before all, go in both directions in 1 character steps until limit.   */
    hwut_verify(seek_forward(me, position_limit));
    hwut_verify(seek_backward(me, position_limit));

    /* MASSIVE random positioning tests.                                     */
    for(i=0; i < 65536 ; ++i) {
        /* Choose a position from 0 to size + 3. Choose a position beyond the
         * possible maximum, so that the error handling check is included.   
         * 13  = largest prime < 2**4;
         * 251 = largest prime < 2**8; 65521 = largest prime < 2**32;        */
        random_value = hwut_random_next(random_value);
        previous     = position;
        position     = random_value % (position_limit + 3);

#       if 0
        printf("%i %i # stats\n", (int)position, (int)(position - previous));     
#       endif
        (void)previous;

        /* SEEK */
        QUEX_NAME(Buffer_seek)(me, position);

        /* TELL */
        if( position < position_limit ) {
            hwut_verify(position == QUEX_NAME(Buffer_tell)(me));
        }

        /* LOAD */
        if( ! verify_content(me, position, position_limit) ) return false;
    }

    printf("# <terminated: reference-file: %s; sub-tests: %i; checksum: %i; position_limit: %i>\n",
           ReferenceFileName, (int)i, (int)position, (int)position_limit);
    return true;
}

static bool
verify_content(QUEX_NAME(Buffer)* me, 
               QUEX_TYPE_STREAM_POSITION Position, 
               QUEX_TYPE_STREAM_POSITION PositionLimit)
/* The 'Buffer_seek()' must have positioned the 'read_p' to the character at
 * the specific position. The stretch from 'read_p' to text end must be the
 * same as in the reference buffer. Moreover, the stretch from buffer begin to
 * text and can be compared with what is stored about 'begin_character_index'.
 */ 
{
    QUEX_TYPE_CHARACTER*       BeginP = &me->_memory._front[1];
    ptrdiff_t                  ContentSize = me->input.end_p - BeginP;
    QUEX_TYPE_STREAM_POSITION  begin_character_index = QUEX_NAME(Buffer_input_character_index_begin)(me);

    if( Position < PositionLimit ) {
        if( *me->_read_p != reference[Position] ) {
            printf("ERROR: read_p: %p; begin: %p; end: %p;\n"
                   "ERROR: position: %i; position_limit: %i;\n"
                   "ERROR: *_read_p: %04X; *reference[Position]: %04X;\n",
                   me->_read_p, &me->_memory._front[1], me->_memory._back, 
                   (int)Position, (int)PositionLimit,
                   (int)*(me->_read_p), (int)reference[Position]);
            print_difference(me);
            hwut_verify(false);
        }
    }
    else if( ! ContentSize) {
        hwut_verify(Position >= PositionLimit);
        return true;
    }

    /* Make sure that the content corresponds to the reference data.     */
    if( memcmp((void*)&reference[begin_character_index], (void*)BeginP, 
               (size_t)ContentSize) != 0) {
        print_difference(me);
        return false;
    }
    return true;
}

static bool
difference(QUEX_NAME(Buffer)* me, QUEX_TYPE_STREAM_POSITION CI)
{
    const QUEX_TYPE_STREAM_POSITION ci_begin = QUEX_NAME(Buffer_input_character_index_begin)(me);

    return me->_memory._front[1 + CI - ci_begin] != reference[CI];
}

#define FOR_RANGE(C, BEGIN, END) \
        for(C=BEGIN; C<END; ++C)

static void
print_difference(QUEX_NAME(Buffer)* me)
{
    const QUEX_TYPE_STREAM_POSITION ci_begin = QUEX_NAME(Buffer_input_character_index_begin)(me);
    const QUEX_TYPE_STREAM_POSITION ci_end   = QUEX_NAME(Buffer_input_character_index_end)(me);
    QUEX_TYPE_STREAM_POSITION       ci;
    QUEX_TYPE_STREAM_POSITION       ci_diff;
    QUEX_TYPE_STREAM_POSITION       ci_print_begin;
    QUEX_TYPE_STREAM_POSITION       ci_print_end;

    /* Find the place, where the reference differ's from the buffer.         */
    ci_diff = (QUEX_TYPE_STREAM_POSITION)-1;
    FOR_RANGE(ci, ci_begin, ci_end) {
        if( difference(me, ci) ) {
            ci_diff = ci;
            break;
        }
    }

    printf("ci_begin: %i; ci_end: %i; ci_diff: %i;\n",
           (int)ci_begin, (int)ci_end, (int)ci_diff);
    if( ci_diff == (QUEX_TYPE_STREAM_POSITION)-1 ) {
        printf("memcmp reported difference but not difference was found.\n");
        hwut_verify(false);
    }

    /* Determine range to be printed.                                        */
    ci_print_begin = QUEX_MAX(ci_begin, ci_diff - 10);
    ci_print_end   = QUEX_MIN(ci_end,   ci_diff + 11);

    /* Print.                                                                */
    printf("ci:         ");
    FOR_RANGE(ci, ci_print_begin, ci_print_end) {
        printf("%4i.", (int)ci);
    }
    printf("\n");
    printf("difference: ");
    FOR_RANGE(ci, ci_print_begin, ci_print_end) {
        if( difference(me, ci) ) printf("!!!!!");
        else                     printf("     ");
    }
    printf("\n");
    printf("buffer:     ");
    FOR_RANGE(ci, ci_print_begin, ci_print_end) {
        printf("%4x.", (int)me->_memory._front[1 + ci - ci_begin]);
    }
    printf("\n");
    printf("reference:  ");
    FOR_RANGE(ci, ci_print_begin, ci_print_end) {
        printf("%4x.", (int)reference[ci]);
    }
    printf("\n");
}

const char*
find_reference(const char* file_stem)
/* Finds the correspondent unicode file to fill the reference buffer with
 * pre-converted data. A file stem 'name' is converted into a file name 
 *
 *             name-SIZE-ENDIAN.dat
 *
 * where SIZE indicates the size of a buffer element in bits (8=Byte, 16= 
 * 2Byte, etc.); ENDIAN indicates the system's endianess, 'le' for little
 * endian and 'be' for big endian. 
 */
{
    static char file_name[256];

    if( sizeof(QUEX_TYPE_CHARACTER) == 1 ) {
        snprintf(&file_name[0], 255, "%s.dat", file_stem);
    }
    else {
        snprintf(&file_name[0], 255, "%s-%i-%s.dat", file_stem, sizeof(QUEX_TYPE_CHARACTER)*8, 
                 QUEXED(system_is_little_endian)() ? "le" : "be");
    }
    return &file_name[0];
}

static QUEX_TYPE_STREAM_POSITION
reference_load(const char* FileName)
/* The content of the file is directly loaded into the 'reference' buffer 
 * so that it may be used to compare against actually loaded results.        */
{
    FILE*      fh;
    size_t     loaded_byte_n;

    fh = fopen(FileName, "rb");
   
    if( !fh ) {
        printf("Could not load '%s'.\n", FileName);
        return 0;
    }

    loaded_byte_n = fread(&reference[0], 1, sizeof(reference), fh);
    fclose(fh);
    return loaded_byte_n / sizeof(QUEX_TYPE_CHARACTER);
}

static bool 
seek_forward(QUEX_NAME(Buffer)* me, QUEX_TYPE_STREAM_POSITION PositionLimit)
/* Seek in steps of 1 backward until 0 is reached and try again.             */
{
    ptrdiff_t count_n;
    for(count_n = 0; count_n != PositionLimit-1; ++count_n ) {
        if( count_n < PositionLimit ) {
            hwut_verify(count_n == QUEX_NAME(Buffer_tell(me)));
        }
        if( ! verify_content(me, QUEX_NAME(Buffer_tell)(me), PositionLimit) ) {
            return false;
        }
        hwut_verify(QUEX_NAME(Buffer_seek_forward)(me, 1));
    }
    hwut_verify(QUEX_NAME(Buffer_tell)(me) == PositionLimit - 1);

    hwut_verify(! QUEX_NAME(Buffer_seek_forward)(me, 1));
    hwut_verify(me->input.character_index_end_of_stream != -1);

    hwut_verify(QUEX_NAME(Buffer_tell)(me) == PositionLimit - 1);
    return true;
}

static bool 
seek_backward(QUEX_NAME(Buffer)* me, QUEX_TYPE_STREAM_POSITION PositionLimit)
/* Seek in steps of 1 backward until 0 is reached and try again.             */
{
    ptrdiff_t count_n;
    for(count_n = 0; count_n != PositionLimit-1; ++count_n ) {
        if( count_n < PositionLimit ) {
            hwut_verify(PositionLimit - count_n - 1 == QUEX_NAME(Buffer_tell)(me));
        }
        if( ! verify_content(me, QUEX_NAME(Buffer_tell)(me), PositionLimit) ) {
            return false;
        }
        hwut_verify(QUEX_NAME(Buffer_seek_backward)(me, 1));
    }
    hwut_verify(QUEX_NAME(Buffer_tell)(me) == 0);

    /* Give in an extra, hopeless, try. */
    hwut_verify(! QUEX_NAME(Buffer_seek_backward)(me, 1));
    hwut_verify(QUEX_NAME(Buffer_tell)(me) == 0);
    return true;
}

QUEX_NAMESPACE_MAIN_CLOSE
