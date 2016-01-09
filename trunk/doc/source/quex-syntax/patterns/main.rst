Pattern Definition
==================

Patterns are specified by means of regular expressions
:cite:`Friedl2006mastering`.  Their syntax follows a scheme that has been
popularized by the tool 'lex' :cite:`Lesk1975lex`, includes elements of
*extended POSIX regular expressions* :cite:`Spencer1994regex` and POSIX bracket
expressions. This facilitates the migration from and to other lexical analyzer
generators and test environments.  Additionally, there exist some special
commands for using *Unicode Properties* to define character sets.

.. TODO: Draw relations to *Unicode Regular Expressions* (Unicode UTR #18) is has 
.. i.e. where it is compliant, and where not.

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
            {IDENTIFIER}  => QUEX_TKN_IDENTIFIER(Lexeme);
        }

The following sections describe the formal language used to specify patterns.
First, syntactic means to specify context free regular expressions are
introduced. Second, two sections elaborate on the specification of character
sets and the use of queries into the Unicode database. Third, a section
elaborates on pre- and post-contexts for regular expressions. Eventually, a
final section introduces *regular expression algebra*. 

.. toctree::
   
    re-context-free.rst
    re-character-sets.rst
    ucs-properties.rst
    re-context-dependent.rst
    re-algebra.rst
    summary.rst
   

