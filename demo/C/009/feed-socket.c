/* Socket Feeder
 * --------------
 *
 * This application shall read content from a file and pass it through a socket
 * so that on the other side a lexical analyzer may listen on the socket and
 * directly examine it.
 *
 *
 *           socket feeder                          lexer-socket
 *          .----------------------.               .-------------------------.
 * .------. |    .--------.        |               |           .----------.  |
 * | file |-+--->| socket |    .--------.      .--------.      | lexical  |  |
 * '------' |    | feeder |--->| socket |----->| socket |----->| analyzer |  |
 *          |    '--------'    '--------'      '--------'      '----------'  |
 *          '----------------------'               '-------------------------'
 *
 *
 * (C) Frank-Rene Schaefer
 *                                                                           */
#include <arpa/inet.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

static void feed_file_to_socket(FILE* fh, int socket_fd, int ChunkSize, int Delay_ms);
static int  connect_to_server();

int 
main(int argc, char** argv)
/* Reads a file whose name is given on the command line add flushes it through
 * socket 0x4711 on this host: 
 *
 * USAGE:
 *
 *  (i) $1 == "string":
 *
 *     $2 = string to be sent. 
 *
 *     Send the string given by $2 over the line to the quex analyzer. Use
 *     this to send the "bye" token which terminates the session.
 *
 *  $2 == "file":
 *
 *     $2 = name of file containing the content to be sent. 
 *
 *  $3 Chunk size of chunks fed into socket.                                  
 *  $4 Milliseconds to wait in between sendings.                             
 *
 *  EXAMPLES: 
 *
 *  The 'bye' token is sent by
 *
 *     > feed-socket string bye  
 *
 *  The content of file "example-feed.txt" is sent in chunks of 7 byte every 5 
 *  milliseconds by
 *
 *     > feed-socket file example-feed.txt 7 5
 *
 * The string "hello world" is sent in chunks of 2 bytes every second by
 *
 *     > feed-socket string 'hello world' 2 1000
 *  
 *  (C) Frank-Rene Schaefer                                                  */
{
    enum mode { 
        FEED_STRING, 
        FEED_FILE, 
        FEED_BAD 
    }            mode;
    int          socket_fd = 0;
    const char*  specification_str; 
    FILE*        fh        = argc > 1 ? fopen(argv[1], "rb") : NULL;
    const int    ChunkSize = argc > 2 ? atoi(argv[2]) : 3;
    const int    Delay_ms  = argc > 3 ? atoi(argv[3]) : 1;

    if( argc < 2 ) {
        printf("command line argument 1: mode 'string' or 'file' not specified.\n");
        exit(-1);
    }
    else {
        if     ( strcmp(argv[1], "string") == 0 ) mode = FEED_STRING;
        else if( strcmp(argv[1], "file") == 0 )   mode = FEED_FILE;
        else {
            printf("command line argument 1: mode 'string' or 'file' not specified.\n");
            exit(-1);
        }
    }
    if( argc < 3 ) {
        printf("command line argument 2: missing specification of file or string.\n");
    }
    else {
        specification_str = argv[2];
    }

    socket_fd = connect_to_server();
    if( socket_fd == -1 ) return -1;

    feed_file_to_socket(fh, socket_fd, ChunkSize, Delay_ms);
    return 0;
}

static int
connect_to_server()
{
    struct sockaddr_in  addr;
    int                 socket_fd = socket(AF_INET, SOCK_STREAM, 0);

    if( socket_fd == -1 ) {
        printf("client: socket() terminates with failure.\n");
        return -1;
    }

    addr.sin_family      = AF_INET;
    addr.sin_port        = htons(0x4711);
    addr.sin_addr.s_addr = inet_addr("127.0.0.1");

    if( connect(socket_fd, (struct sockaddr *)&addr, sizeof(addr)) == -1 ) {
        printf("client: connect() terminates with failure.\n");
        return -1;
    }

    return socket_fd;
}

static void
feed_file_to_socket(FILE* fh, int socket_fd, int ChunkSize, int Delay_ms)
/* Take the content found in 'fh' and feeds it into socket 'socket_fd' in 
 * chunks of size 'ChunkSize'. When done, this function returns.             */
{
    char   buffer[256];
    size_t read_n; 

    assert(ChunkSize <= 256);

    while( 1 + 1 == 2 ) {
        /* Read some bytes from the file that contains the source for 
         * feeding.                                                          */
        read_n = fread(&buffer[0], 1, ChunkSize, fh);
        buffer[read_n] = '\0';
        printf("read: %i: [%s]\n", read_n, &buffer[0]);
        if( ! read_n ) break;

        /* Flush the bytes into the socket.                                  */
        if( write(socket_fd, &buffer[0], read_n) == -1 ) {
            printf("client: write() terminates with failure.\n");
            return;
        }
        usleep(1000L * Delay_ms);
    }
    printf("<done>\n");
}

static void
feed_string_to_socket(const char* content, size_t Size, int socket_fd, int ChunkSize, int Delay_ms)
/* Take the content found in 'fh' and feeds it into socket 'socket_fd' in 
 * chunks of size 'ChunkSize'. When done, this function returns.             */
{
    char   buffer[256];
    size_t read_n; 

    assert(ChunkSize <= 256);

    while( 1 + 1 == 2 ) {
        /* Read some bytes from the file that contains the source for 
         * feeding.                                                          */
        read_n = fread(&buffer[0], 1, ChunkSize, fh);
        buffer[read_n] = '\0';
        printf("read: %i: [%s]\n", read_n, &buffer[0]);
        if( ! read_n ) break;

        /* Flush the bytes into the socket.                                  */
        if( write(socket_fd, &buffer[0], read_n) == -1 ) {
            printf("client: write() terminates with failure.\n");
            return;
        }
        usleep(1000L * Delay_ms);
    }
    printf("<done>\n");
}
