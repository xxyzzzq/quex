Modes
=====

In practical languages, there might be ranges in the character stream
that do not need to whole set of pattern-action pairs to be active 
all the time. It might actually be 'disturbing'. Imagine that a 
compiler would try to analyze 'C' format strings. In this case the 
detection of numbers, identifiers, etc. has no place in the process.
The concept of lexical analyzer modes allows to group pattern-action
pairs, thus enabling and disabling whole sets of pattern-action pairs.
This is critical for 'mini'-languages that are embedded into a main
language.

The lexical analyzer is exactly in one mode at a specific time.
The mode determines what pattern-action pairs are armed to trigger
on incoming characters. Additionally, they can provide their
own incidence handlers for different incidences.

The following code segment shows two modes. The first one shows a normal
'PROGRAM' mode. The second one is a small mode to detect basic string
formatting patterns. The ``self_enter_mode()`` is used to trigger the
transition from one mode to the other.

.. code-block:: cpp

    mode PROGRAM {
        <<EOF>>       { return TKN_TERMINATION; }

        [0-9]+        { return TKN_NUMBER(Lexeme); }
        [a-zA-Z_]+    { return TKN_IDENTIFIER(Lexeme); }
        while         { return TKN_KEYWORD_WHILE; }
        for           { return TKN_KEYWORD_FOR; }
        "\""          { self_enter_mode(MINI); }
        .             { }
    }

    mode MINI {
        <<EOF>>    { return TKN_TERMINATION; }

        "%s"       { return TKN_FORMAT_CHARP; }
        "%i"       { return TKN_FORMAT_INT; }
        "%f"       { return TKN_FORMAT_FLOAT; }
        "\""       { self << PROGRAM; }
        .          { }
    }

A potential disadvantage of modes is *confusion*--when used with traditional
lexical analyzer generators. In flex, for example, the end-user does not see
more than a token stream. He has no insight into the current lexical analyzer
mode. He cannot sense or control the mode transitions that are currently being
made. The mode transitions are hidden somewhere in the pattern match actions.
GNU Flex's *start conditions* are similar to modes, but the only way two modes,
A and B, can be related in flex is via 'inclusion', i.e. by letting a
pattern be active in A and B. There is no convenient mechanism to say:
'let B override all patterns of A'.  This is where the mode inheritance
relationships of Quex provide clear and convenient advantages to be
explained in the chapters to come.


