.. _sec-character-encodings:

Character Encodings
===================

Many cultures of the world in the history of mankind developed many types of
scripts. A script in a more technical sense describes the relationship between a
*phonetic expression* or a *meaning* and its *graphical representation*[#f1]_.
The atomic element of a writing is a character and its numerical representation
is called a *code-point* or a *character code*. The formal relationship between
characters and code-points is called an *encoding*. A lexical analyzer
generator striving to be universal must therefore reflect the multitude of
encodings. Much development in computer science at the end of the 2000's
century has been made in a region of the world where the English was
predominant. For this reason, the so called ASCII Standard encoding became
widespread in the whole world, even though, it does only support English
characters. 

With the dramatic change of global interactions and communications, the need 
for character encodings from other languages becomes indispensable. On of the
major goals is to support the lexical analysis of any type of encoding. Quex
supports the usage of character encodings in two ways:

#. The internal engine can be converted to run directly based on the 
   desired encoding.

#. A converter may be plugged in which converts an incoming file stream
   into Unicode. The lexical analyzer engine still runs on Unicode
   characters.

The following section provides an overview about the lexical analysis process
of a generated engine. The subsequent section elaborates on the adaption of the
lexical analyzer engine for a particular encoding. The remaining sections deal
with the usage of libraries for the conversion of character encodings to
Unicode. Concluding on converters, a separate section explains how user
generated converters can be plugged into the process.

.. note:

   With Unicode lexical analyzers there is a certain potential that the
   generated code might be very large to an extend that the compiler is not
   able to cope with it. In this case, make sure modes that are only inherited
   are labeled with ``<inheritable: only>`` as a mode option. Further, consider
   one of the compression algorithms mentioned in section :ref:`sec-tuning`.

.. toctree::

   process.txt
   engine-encoding.txt
   converter.txt
   user-defined.txt
   converter_helper.txt
   bom.txt

.. rubric:: Footnotes

.. [#f1] Humans reflect over information in terms of phonetic expressions or 
         meanings. Therefore scripts provide the basis for the *transport of information*
         over time and space. Being able to transport information from person
         to person, or preserve information for later generations is the key
         for any development of civilization.

         The usage of automated tools for the writing and interpretation of information
         acts as an accelerator for the motor of civilization. In the vision
         of the author quex makes its contribution to civilization by providing means
         for automatic interpretation of information.
