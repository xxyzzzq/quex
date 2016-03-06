Pattern-Action Pairs
====================

As described earlier, a lexical analyser has to task to analyse the incoming
character stream, identify atomic chunks (lexemes) of information and stamp
them with a token type. Examples in common programming languages are numbers
consisting of a list of digits, identifiers consisting of a list of letters,
keywords such as ``if``, ``else`` and so on.  This is the simplest form
of analysis. However, a lexical analyser might also perform other
actions as soon as the input matches a pattern. In general a lexical
analyser can be described by a set of patterns related to the actions
to be performed when a pattern matches, i.e.

.. table:: 

    ===============  ====================================================
    Pattern           Action
    ===============  ====================================================
    list of digits    Return 'Number' token together with the digits.
    list of letters   Return 'Identifier' token together with letters.
    'for', 'while'    Return keyword token.
    etc.
    ===============  ====================================================

Practical applications require a formal language for patterns. Quex
requires patterns to be described in regular expressions in the traditional
lex/flex style. The pattern action pairs in the above list can be defined
for quex in the following manner

.. code-block:: cpp

    mode MINE { 
        [0-9]+        { return TKN_NUMBER(Lexeme); }
        while         { return TKN_KEYWORD_WHILE; }
        for           { return TKN_KEYWORD_FOR; }
        [a-zA-Z_]+    { return TKN_IDENTIFIER(Lexeme); }
    }

Note, that pattern-action pairs can only occur inside modes. They can only be
specified inside a ``mode {`` .. ``}`` definition.

