Macro Tricks
============

Quex uses extensive macro techniques and it is not always obvious to the
uninitiated what the result of a macro expansion actually produces. An
obvious solution is to put some mark in the file of concern such as in

.. code-block:: cpp

       ...
       MySpecialMark
       QUEX_NAME(receive)((QUEX_TYPE_TOKEN&)token);

and to compile with the '-E' flag.  Then, in the output one need to search for
``MySpecialMark``.  Whatsoever follows is the expanded macro expression.  A
maybe more convenient way is to maintain a tiny file, let's say
``undeceive.cpp`` which consists of

.. code-block:: cpp

       #include "MyLexer"
       #include <stdio.h>
       #define __UNDECEIVE(X) "\n" #X "\n"
       #define UNDECEIVE(X)   __UNDECEIVE(X)
       int main(int argc, char** argv) 
       { 
           printf(UNDECEIVE(... expression ...)); 
       }

where ``... expression ...`` needs to be replaced with the required macro
expression.
