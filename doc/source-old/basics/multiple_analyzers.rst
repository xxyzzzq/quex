Multiple Lexical Analyzers
==========================

In case that multiple lexical analyzers are generated and linked into a single
application, some specific action needs to be taken. First of all, one needs to
compile all quex related files with the command line option::

                    -DQUEX_OPTION_MULTI

Second, one single file need to include the implementation file, that is somewhere in one
single file there must be a line like

.. code-block::  cpp
          
     #include <quex/code_base/multi.i>
            
The compilation with the given options prevents multi-
implementations of the exact same functions. The inclusion of the implementation
header in one single file ensures that the functions are present.

Modern linkers follow a struct link sequence. That means that the object file
or library which comes first determines the set of required functions and
variables. Then, only the elements of the second file are considered which are
required to fulfill the requirements of what proceeded. These elements may
require others which may come from the third file, and so on. Whenever linker
issues of undefined reference occur, the position of the file which includes
'multi.i' may be considered with caution.
