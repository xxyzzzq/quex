/* PURPOSE: This tests checks that the byte loader NEVER seeks before 
 *          the initial position.
 *
 * (C) Frank-Rene Schaefer                                                   */
#include <quex/code_base/buffer/loader/ByteLoader>
#include <hwut_unit.h>
#include <assert.h>

void
initial_position(ByteLoader* me)
{
    QUEX_TYPE_STREAM_POSITION ip;
    QUEX_TYPE_STREAM_POSITION target = 0;
    int                       count;

    count = 0;
    for(ip=0; ip < TEST_FILE_SIZE ; ++ip) {
        me->initial_position = ip;
        for(target=0; target < TEST_FILE_SIZE + 4; ++target) {
            me->seek(me, target);
            // printf("ip: %i; target %i; tell: %i; \n", (int)ip, (int)target, (int)me->tell(me));
            if( target < ip )                  hwut_verify(target != me->tell(me));
            else if( target < TEST_FILE_SIZE ) hwut_verify(target == me->tell(me));
            ++count;
        }
    }
    printf("<terminated: %i>\n", count);
}

