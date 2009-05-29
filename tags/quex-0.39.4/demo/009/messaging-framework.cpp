#include <cstdlib>
#include <cstring>
#include <assert.h>
#include <quex/code_base/compatibility/inttypes.h>

static QUEX_TYPE_CHARACTER   data[] = "hello 4711 bonjour 0815 world 7777 le 31451 monde le monde 00 welt 1234567890 hallo 1212 hello bye";
#define DataL  (sizeof(data) / sizeof(char))

size_t 
messaging_framework_receive(QUEX_TYPE_CHARACTER** buffer)
{
    static QUEX_TYPE_CHARACTER*  iterator = data;
    size_t                       size = (size_t)(float(random()) / float(RAND_MAX) * 5.0) + 1;

    assert(iterator < data + DataL);
    if( iterator + size >= data + DataL - 1 ) size = DataL - (iterator - data) - 1; 

    *buffer = iterator; 
    iterator += size;

    return size;
}

size_t 
messaging_framework_receive_into_buffer(QUEX_TYPE_CHARACTER* BufferBegin, size_t BufferSize)
{
    static QUEX_TYPE_CHARACTER*  iterator = data;
    size_t                       size = (size_t)(float(random()) / float(RAND_MAX) * 5.0) + 1;

    assert(iterator < data + DataL);
    if( iterator + size >= data + DataL - 1 ) size = DataL - (iterator - data) - 1; 
    if( size > BufferSize )                   size = BufferSize;

    memcpy(BufferBegin, iterator, size);
    iterator += size;

    return size;
}

void
messaging_framework_receive_to_internal_buffer()
{
}

void 
messaging_framework_release(uint8_t* buffer)
{
    /* nothing has to happen here, we are just happy. */
}
