EXAMPLE: Manual Buffer Filling
-------------------------------
(C) Frank-Rene Schaefer

The engine's buffer can either be filled automatically or manually. Automatic
means that the analyzer calls the loading procedure as soon as the buffer's
end has been reached. In some circumstances, there is not even a file system
where the analyzer runs, so the buffer must be filled manually. The examples
in this directory demonstrate how this is done. 

The example program can be controlled by the command line arguments:

  [1] "syntactic" --> receive loop handles chunks which are expected not to 
                      cut in between matching lexemes.
      "arbitrary" --> chunks may be cut in between lexemes.
 
  [2] "fill"      --> content is provided by user filling as dedicated region.
      "copy"      --> user provides content to be copied into its 'place'.
 
The examples for without and with BufferFiller_Converter are 'compile-time'
controlled by the macro '-DQUEX_EXAMPLE_WITH_CONVERTER'. If it is present
a converter-based buffer filler is compiled, otherwise, a plain buffer filler
is compiled.

         .---- without -DQUEX_EXAMPLE_WITH_CONVERTER ----> lexer.exe
        /
   lexer.c  
        \
         '---- with -DQUEX_EXAMPLE_WITH_CONVERTER -------> lexer_utf8.exe

Files required for the converter end with '_utf8' in their filestem, others
do not.

There is another example, which falls appart: Pointing. Here the user points
to place in memory where the lexer has to analyze. The corresponding file
is 'point.c' which compiles to 'point.exe'.

Syntactic Chunks vs. Arbitrary Chunks
=====================================

When parsing a command line, for example, it can be expected that each command
line is received completely terminated with a newline character. The content of
this line is either syntactically complete or it is wrong. In such cases the
receive cycle is simple. No history between receive cycles needs to be
maintained.  However, when receiving chunks through a socket interface, for
example, no assumption can be made about the borders and lexemes may be cut in
the middle.  In this case, the beginning of the analyzer step needs to be
remembered. When new content is loaded the analysis must start from the
beginning of the lexeme.

Filling vs. Copying
===================

Content for the engine's buffer can either be 'filled' by the user, or
'copied'. The former involves less copying, better cache-locality, but is a
little more complicated (2 function calls instead of 1).

Converters
==========

The analyser's interface is homogeneous over buffer filling policies. That,
is, in bother cases 'filling' and 'copying', the user applies the exact same
API for converted input and non-converted input. The data conversion happens
completely behind the scenes.


