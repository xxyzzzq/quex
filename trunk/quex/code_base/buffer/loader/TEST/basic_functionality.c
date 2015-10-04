/* PURPOSE: This tests checks on the basic member functions of a ByteLoader
 *          implementation:
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
 * 'ByteLoader'. The only macro that needs to be defined in 'TEST_FILE_SIZE'.
 * A test application needs to construct the derived class' object and call
 * 'verify_basic_functionality()' of this file. The test does not produce any
 * output and relies solely on 'hwut_verify()' macros.
 *
 * (C) Frank-Rene Schaefer                                                   */

static long pseudo_random_next(long i);
static void verify_load(ByteLoader* me, int Offset, int N);

/* Maintain the content of the file, so that it may be compared whether the 
 * content that is loaded is always the same.                                */
static uint8_t reference[TEST_FILE_SIZE];

int
verify_basic_functionality(ByteLoader* me, int LoadN)
{
    long seed = 0;

    me->seek(me, 0);
    hwut_verify(TEST_FILE_SIZE == me->load(me, reference, TEST_FILE_SIZE));

    for(i=0; i < 65536 ; ++i) {
        /* SEEK */
        me->seek(me, seed % (TEST_FILE_SIZE + 3) );

        if( position > TEST_FILE_SIZE ) continue;

        /* TELL */
        me->seek(me, seed % 100);
        hwut_verify(position == me->tell(me));

        /* LOAD */
        verify_load(me, position, LoadN);

        seed = pseudo_random_next(seed);
    }
}

static void
verify_load(ByteLoader* me, int Offset, int N)
/* Loads 'N' bytes and compares the loaded content with what is stored 
 * in the reference storage.                                             */
{
    uint8_t  buffer[4096];
    uint8_t* content = &buffer[4];
    assert(N < 4096);

    /* Set borders to detect overwrite.                                  */
    memset(&buffer[0], 0x5A, 4);
    memset(&buffer[N], 0x5A, 4);

    loaded_n = me->load(me, content, N);

    hwut_verify(loaded_n <= QUEX_MIN(TEST_FILE_SIZE, N));

    /* Make sure that the content corresponds to the reference data.     */
    hwut_verify(memcmp((void*)&reference[Offset], (void*)content, (size_t)loaded_n);

    /* Make sure nothing has been written beyond borders.                */
    hwut_verify(&buffer[0] == 0x5A);
    hwut_verify(&buffer[1] == 0x5A);
    hwut_verify(&buffer[2] == 0x5A);
    hwut_verify(&buffer[3] == 0x5A);
    hwut_verify(&buffer[N+0] == 0x5A);
    hwut_verify(&buffer[N+1] == 0x5A);
    hwut_verify(&buffer[N+2] == 0x5A);
    hwut_verify(&buffer[N+3] == 0x5A);
}

static long 
pseudo_random_next(long i)
{ return (i * 7 << 5); }
