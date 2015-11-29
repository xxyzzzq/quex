/* PURPOSE: This tests checks on the basic member functions of a QUEX_NAME(ByteLoader
   )*          implementation:
 *
 *                  .tell()
 *                  .seek(position)
 *                  .load()
 *                  .delete_self()
 *
 * The tests on the first three functions are implemented by function calls.
 * The propper functioning of 'delete_self' must be double checked by the 
 * consideration of valgrind's output.
 *
 * The code of this file is general, because it relies on the base class 
 * 'QUEX_NAME(ByteLoader)'. The only macro that needs to be defined in 'TEST_FILE_SIZE'.
 * A test application needs to construct the derived class' object and call
 * 'verify_basic_functionality()' of this file. The test does not produce any
 * output and relies solely on 'hwut_verify()' macros.
 *
 * (C) Frank-Rene Schaefer                                                   */
#include <basic_functionality.h>
#include <hwut_unit.h>

static bool  verify_load(QUEX_NAME(ByteLoader)* me, int Offset, int N, 
                         QUEX_TYPE_STREAM_POSITION position_limit);
static bool  test(QUEX_NAME(ByteLoader)* me, int LoadN);
static void  print_difference(const uint8_t* content, int Offset, int N, 
                              QUEX_TYPE_STREAM_POSITION position_limit);

/* Maintain the content of the file, so that it may be compared whether the 
 * content that is loaded is always the same.                                */
static uint8_t reference[TEST_FILE_SIZE];

void
verify_basic_functionality(QUEX_NAME(ByteLoader)* me)
{
    if( ! test(me, 0) ) return;
    if( ! test(me, 1) ) return;
    if( ! test(me, 2) ) return;
    if( ! test(me, TEST_FILE_SIZE-2) ) return;
    if( ! test(me, TEST_FILE_SIZE-1) ) return;
    if( ! test(me, TEST_FILE_SIZE) ) return;
}

static bool
test(QUEX_NAME(ByteLoader)* me, int LoadN)
{
    int  i;
    QUEX_TYPE_STREAM_POSITION position = 0;
    QUEX_TYPE_STREAM_POSITION position_limit;
    QUEX_TYPE_STREAM_POSITION previous;
    bool                      end_of_stream_f;

    me->seek(me, 0);
    hwut_verify(TEST_FILE_SIZE == me->load(me, reference, TEST_FILE_SIZE, &end_of_stream_f));
    position_limit = TEST_FILE_SIZE;

    for(i=0; i < 65536 ; ++i) {
        /* Choose a position from 0 to size + 3. Choose a position beyond the
         * possible maximum, so that the error handling check is included.   */
        previous = position;
        position = ((position + i) * 997) % (position_limit + 3);

        /* printf("%i %i\n", (int)position, (int)(position - previous));     */
        /* Investigate with gnuplot:
         * > hist(x,width)=width*floor(x/width)
         * > gnuplot> plot "tmp.dat" u (hist($2,1)):(1.0) smooth freq w boxes
         *   $1: histogram of position; 
         *   $2: historgram of differences.                                  */
        (void)previous;

        /* SEEK */
        me->seek(me, position);

        if( position > position_limit ) continue;

        /* TELL */
        hwut_verify(position == me->tell(me));

        /* LOAD */
        if( ! verify_load(me, position, LoadN, position_limit) ) return false;
    }
    printf("# <terminated: load_n: %i; sub-tests: %i; checksum: %i;>\n",
           (int)LoadN, (int)i, (int)position);
    return true;
}

static bool
verify_load(QUEX_NAME(ByteLoader)* me, int Offset, int N, QUEX_TYPE_STREAM_POSITION position_limit)
/* Loads 'N' bytes and compares the loaded content with what is stored 
 * in the reference storage.                                                 */
{                                                                            
    uint8_t     buffer[4096];                                  
    uint8_t*    content = &buffer[4];                          
    ptrdiff_t   loaded_n;                                      
    bool        end_of_stream_f;

    hwut_verify(N < 4096);                                                   
                                                                             
    /* Set borders to detect overwrite.                                      */
    memset(&content[-4], 0x5A, 4);
    memset(&content[N], 0x5A, 4);

    hwut_verify(content[-4] == 0x5A);
    hwut_verify(content[-3] == 0x5A);
    hwut_verify(content[-2] == 0x5A);
    hwut_verify(content[-1] == 0x5A);
    hwut_verify(content[N+0] == 0x5A);
    hwut_verify(content[N+1] == 0x5A);
    hwut_verify(content[N+2] == 0x5A);
    hwut_verify(content[N+3] == 0x5A);

    loaded_n = me->load(me, content, N, &end_of_stream_f);
    /* (i)  The 'end_of_stream_f' does not have to be set. 
     * (ii) But it MUST NOT be set if there is no end of stream!             */
    if( Offset + N < position_limit ) {
        hwut_verify(! end_of_stream_f);
    }

    hwut_verify(loaded_n <= QUEX_MIN(position_limit, N));
    if( me->binary_mode_f ) {
        hwut_verify(Offset + loaded_n == me->tell(me));
    }

    /* Make sure that the content corresponds to the reference data.         */
    if( memcmp((void*)&reference[Offset], (void*)content, (size_t)loaded_n) != 0) {
        print_difference(content, Offset, loaded_n, position_limit);
        return false;
    }

    /* Make sure nothing has been written beyond borders.                    */
    hwut_verify(content[-4] == 0x5A);
    hwut_verify(content[-3] == 0x5A);
    hwut_verify(content[-2] == 0x5A);
    hwut_verify(content[-1] == 0x5A);
    hwut_verify(content[N+0] == 0x5A);
    hwut_verify(content[N+1] == 0x5A);
    hwut_verify(content[N+2] == 0x5A);
    hwut_verify(content[N+3] == 0x5A);
    return true;
}

static void
print_difference(const uint8_t* content, int Offset, int loaded_n, QUEX_TYPE_STREAM_POSITION position_limit)
{
    int i=0;
    printf("offset: %-3i; loaded_n: %-2i; ", Offset, loaded_n);
    for(i=0; i <loaded_n; ++i) printf("%02X.", content[i]);
    printf("\n");
    printf("                           ");
    for(i=0; i <loaded_n; ++i) printf("%02X.", reference[Offset+i]);
    printf("\n");
    printf("complete reference:\n");
    for(i=0; i <= position_limit; ++i) {
        printf("%02X.", reference[i]);
        if( i % 10 == 9 ) printf("\n");
    }
    printf("\n");
}
