#include <cstdlib>
#include <cstring>
#include <assert.h>
#include <quex/code_base/compatibility/inttypes.h>
#include <quex/code_base/asserts>
#include "messaging-framework.h"

static QUEX_TYPE_CHARACTER   messaging_framework_data[] = 
       "hello 4711 bonjour 0815 world 7777 le 31451 monde le monde 00 welt 1234567890 hallo 1212 hello bye";
static size_t                messaging_framework_data_size()
{ return sizeof(messaging_framework_data) / sizeof(QUEX_TYPE_CHARACTER); }

size_t 
messaging_framework_receive(QUEX_TYPE_CHARACTER** rx_buffer)
    /* Simulate the reception into a place that is defined by the low 
     * level driver. The low level driver reports the address of that place
     * and the size.                                                         */
{
    static QUEX_TYPE_CHARACTER*  iterator = messaging_framework_data;
    const size_t                 remainder_size =   messaging_framework_data_size() - 1
                                                  - (iterator - messaging_framework_data);
    size_t                       size = (size_t)(float(random()) / float(RAND_MAX) * 5.0) + 1;

    if( size >= remainder_size ) size = remainder_size; 

    *rx_buffer = iterator; 
    iterator += size;

    if( size != 0 ) {
        __quex_assert(iterator < messaging_framework_data + messaging_framework_data_size());
    } else {
        __quex_assert(iterator == messaging_framework_data + messaging_framework_data_size());
    }

    return size;
}

size_t 
messaging_framework_receive_syntax_chunk(QUEX_TYPE_CHARACTER** rx_buffer)
    /* Simulate the reception into a place that is defined by the low 
     * level driver. The low level driver reports the address of that place
     * and the size.                                                         */
{
    size_t         index_list[] = {0, 10, 29, 58, 72, 89, 98};
    static size_t  cursor = 0;

    *rx_buffer = messaging_framework_data + index_list[cursor]; 

    // Apply the messaging_framework_data + ... so that we compute in enties
    // of QUEX_TYPE_CHARACTER* and not '1'. Size shall be the number of characters.
    const size_t Size =   (messaging_framework_data + index_list[cursor + 1]) 
                        - (messaging_framework_data + index_list[cursor]);

    cursor += 1;

    return Size;
}
void 
messaging_framework_release(uint8_t* buffer)
    /* A messaging framework that provide the address of the received content
     * (a rx buffer) usually requires to release the rx buffer buffer at some point
     * in time.                                                                       */
{
    /* nothing has to happen here, we are just happy. */
}

size_t 
messaging_framework_receive_into_buffer(QUEX_TYPE_CHARACTER* BufferBegin, size_t BufferSize)
    /* Simulate a low lever driver that is able to fill a specified position in memory. */
{
    static QUEX_TYPE_CHARACTER*  iterator = messaging_framework_data;
    size_t                       size = (size_t)(float(random()) / float(RAND_MAX) * 5.0) + 1;

    assert(iterator < messaging_framework_data + messaging_framework_data_size());
    if( iterator + size >= messaging_framework_data + messaging_framework_data_size() - 1 ) 
        size = messaging_framework_data_size() - (iterator - messaging_framework_data) - 1; 
    if( size > BufferSize )    
        size = BufferSize;

    memcpy(BufferBegin, iterator, size);
    iterator += size;

    return size;
}

QUEX_TYPE_CHARACTER   MESSAGING_FRAMEWORK_BUFFER[MESSAGING_FRAMEWORK_BUFFER_SIZE];

size_t
messaging_framework_receive_to_internal_buffer()
    /* Simular a low level driver that iself has a hardware fixed position in memory 
     * which it fills on demand.                                                      */
{
    memcpy(MESSAGING_FRAMEWORK_BUFFER + 1, messaging_framework_data, messaging_framework_data_size());
    return messaging_framework_data_size();
}

