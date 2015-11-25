/* PURPOSE: ByteLoader under the influence of segmented input.
 *
 * In contrast to 'file input', not the whole input is completely available 
 * from the beginning. Instead, the input arrives in chunks, and the 
 * ByteLoader needs to cope with the timely segmented incoming chunks.
 *
 * Practical applications of these scenario are pipes, socket connections,
 * or specifically scanning of the standard input. 
 *
 * EXPERIMENT:
 *
 * In this experiment two processes are spawned: A writer process that writes
 * chunks of data into a pipe and a reader process that reads the content. 
 * The experiment is repeated for a large set of combinations of write-chunk
 * and read-chunk sizes. At the end of each send-receive cycle, a memory 
 * comparison verifies that the whole content has been received propperly.
 *
 * CHOICES:
 *
 * -- Normal:  without a 'on_nothing()' handler.
 *
 * -- Handler: with a dedicated 'on_nothing()' handler. The handler shall
 *             signalize 'end-of-stream' as soon as more than 32 bytes have 
 *             been received. The memcmp() then only happens on the first 32
 *             bytes.                    
 *
 * (C) Frank-Rene Schaefer
 *                                                                           */
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <quex/code_base/buffer/loader/ByteLoader_POSIX>
#include <quex/code_base/buffer/loader/ByteLoader.i>
#include <quex/code_base/buffer/loader/ByteLoader_POSIX.i>
#include <quex/code_base/MemoryManager.i>

#include <hwut_unit.h>

static void   writer_process(int fd, int WriteChunkSize);
static void   reader_process(int fd, int ReadChunkSize,
                             bool (*on_nothing)(ByteLoader*, size_t, size_t));
static void   test(int WriteChunkSize, int ReadChunkSize,
                   bool (*on_nothing)(ByteLoader*, size_t, size_t));
              
static bool   self_on_nothing(ByteLoader* me, size_t TryN, size_t RequestN);

int  sum_loaded_n;
char send_data[] = "A MESSAGE OF A KILO BYTE BEGINS WITH A BIT";

int 
main(int argc, char** argv)
{
    int  w_chunk;
    int  r_chunk;
    int  experiment_n = 0;
    bool (*on_nothing)(ByteLoader* me, size_t TryN, size_t RequestN);

    hwut_info("Segmented Input;\n"
              "CHOICES: Normal, Handler;\n"
              "SAME;");

    hwut_if_choice("Normal")  { on_nothing = NULL; }
    hwut_if_choice("Handler") { on_nothing = self_on_nothing; }

    /* Varry receive and write chunks sizes. */
    for(r_chunk=1; r_chunk<17; ++r_chunk) {
        for(w_chunk=1; w_chunk<19; ++w_chunk) {
            test(w_chunk, r_chunk, on_nothing);
            experiment_n += 1;
        }
    }
    printf("<terminated: %i>\n", experiment_n);
    return 0;
}

static void 
test(int WriteChunkSize, int ReadChunkSize,
     bool (*on_nothing)(ByteLoader*, size_t, size_t))
{
    int     fd[2]; 
    pid_t   child_pid;

    pipe(fd);
    child_pid = fork();

    switch( child_pid ) {
    case -1:
        printf("Error: forking a process failed.\n");
        exit(1);
    case 0:
        close(fd[0]); /* Child closes input side of pipe.                    */
        writer_process(fd[1], WriteChunkSize);
        break;
    default:
        close(fd[1]); /* Parent closes output side of pipe.                  */
        reader_process(fd[0], ReadChunkSize, on_nothing);
        break;
    }

    return;
}

static void
writer_process(int fd, int WriteChunkSize)
{
    int  L          = sizeof(send_data);
    int  chunk_size = 0;
    int  i;

    for(i=0; i <= L; i += WriteChunkSize) {
        if( L - i < WriteChunkSize ) chunk_size = L - i;
        else                         chunk_size = WriteChunkSize;
        write(fd, &send_data[i], chunk_size);

        usleep(100);
    }
    exit(0);
}

static void
reader_process(int fd, int ReadChunkSize,
               bool (*on_nothing)(ByteLoader*, size_t, size_t))
{
    char        buffer[64];
    ByteLoader* loader = ByteLoader_POSIX_new(fd);
    int         cmp_n=0;
    int         loaded_n=0;
    bool        end_of_stream_f;

    loader->on_nothing = on_nothing;

    sum_loaded_n = 0;
    do {
        usleep(10);

        loaded_n = loader->load(loader, &buffer[sum_loaded_n], ReadChunkSize, &end_of_stream_f);

        if( ! loaded_n ) break;

        sum_loaded_n += loaded_n;
    } while( 1 + 1 == 2 );

    cmp_n = loader->on_nothing ? 32 : sizeof(send_data);
    
    if( memcmp(buffer, send_data, cmp_n) != 0) {
        buffer[sum_loaded_n] = '\0';
        printf("sent:   [%s];\n", send_data);
        printf("buffer: [%s];\n", buffer);
        exit(-1);
    }

    loader->delete_self(loader);
}

static bool 
self_on_nothing(ByteLoader* me, size_t TryN, size_t RequestN)
/* A handler on missing input. If the handler returns 'false', the ByteLoader
 * must break up the reception.                                              */
{
    if( TryN > 1000) {
        printf("Max. try number exceeded: %i\n", (int)TryN);
        exit(-1);
    }
    return sum_loaded_n < 32; 
}
