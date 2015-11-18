EXAMPLE: Lexing in Non-File Environments
----------------------------------------
(C) Frank-Rene Schaefer

In this directory examples of lexical analysis are demonstrated that show
lexical analysis under circumstance where there is no file, namely. The
examples show:

  (1) "lexer-stdin.c": lexical analysis from the standard input. The example
      can be tried by pipe-ing "example-feed.txt" into the application, i.e.

          ./lexer-stdin < example-feed.txt

  (2) "lexer-stdin-utf8.c": lexical analysis from the standard input but passed
      through a converter that converts from UTF8 to the internal buffer 
      running on UCS. To test the example pipe:

          ./lexer-stdin-utf8 < example-feed-utf8.txt

  (3) "lexer-socket.c": lexical analysis through a socket connection. To try
      this example, run the application and in parallel the "socket-feeder.sh".

          ./lexer-socket &
          ./socket-feeder.sh

All tests are designed to run on Unix-like operating system. However, an 
adaptation to other OS-es should not be too difficult.
