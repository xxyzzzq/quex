Pattern Definition
==================

Patterns are specified by means of regular expressions
:cite:`Friedl2006mastering`.  Their syntax follows a scheme that has been
popularized by the tool 'lex' :cite:`Lesk1975lex`, includes elements of
*extended POSIX regular expressions* :cite:`Spencer1994regex` and POSIX bracket
expressions. This facilitates the migration from and to other lexical analyzer
generators and test environments.  Additionally, there exist some special
commands for using *Unicode Properties* to define character sets.

.. Compliance to *Unicode Regular Expressions* (Unicode UTR #18) is has 
.. not been a design goal, though. 

.. note::

    The top-level section ``define`` exists to name patterns. This supports the
    aggregation of complex pattern descriptions out of smaller parts.
    Moreover, it supports the separation of *pattern definitions* and *pattern
    matching behavior*, whereby the latter happens inside a mode. 

    The following example shows patterns for ``WHITESPACE`` and ``IDENTIFIER``
    defined in a ``define`` section. The ``mode`` defines clean pattern action
    pairs by solely expanding the defined patterns.
         
    .. code-block:: cpp

        define {
           /* Eating white space                          */
           WHITESPACE    [ \t\n]+
           /* An identifier can never start with a number */
           ID_BEGIN      [_a-zA-Z]
           ID_CONTINUE   [_a-zA-Z0-9]*
           IDENTIFIER    {ID_BEGIN}{ID_CONTINUE}
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
   
.. rubric:: Footnotes

