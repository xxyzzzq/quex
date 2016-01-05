Pattern Definition
==================

In Quex patterns are specified by means of regular expressions.  Their syntax
follows a scheme that has been popularized by the tool 'lex'
:cite:`Lesk1975lex`, includes elements of *extended POSIX regular expressions*
:cite:`Spencer1994regex` and POSIX bracket expressions. This facilitates the
migration from and to other lexical analyzer generators and test environments.
Additionally, support for *Unicode Properties* is provided. A compliance to
*Unicode Regular Expressions* (Unicode UTR #18) is currently not targeted,
though, because this expressive power is usually not required for compiler
generation.  

The top-level section ``define`` facilitates the separation of larger regular
expressions into smaller parts. Also, defining patterns only in this section
supports clean mode descriptions--free of pattern definitions. This is
especially handy when Unicode-related regular expression impose some larger
specifications.  The following example displays pattern definition in a
``define`` section and pattern expansion inside a ``mode``.
     
.. code-block:: cpp

    define {
       /* Eating white space                          */
       WHITESPACE    [ \t\n]+
       /* An identifier can never start with a number */
       IDENTIFIER    [_a-zA-Z][_a-zA-Z0-9]*
    }

    mode MINE {
        {WHITESPACE}  { /* do nothing */ }
        {IDENTIFIER}  => TKN_IDENTIFIER(Lexeme);
    }

The description of patterns by means of a formal language is the subject of the
following subsections. The explanation is divided into the consideration of
context-free expressions and context-dependent expressions.

.. toctree::
   
    context-free.rst
    character-set-expressions.rst
    ucs-properties.rst
    context-free-pitfalls.rst
    context-dependent.rst
    context-dependent-pitfalls.rst
   

