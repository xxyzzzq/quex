Summary
=======

This section introduced basic concepts related to lexical analysis and Quex as
a generator of lexical analyzers. The state machine approach for pattern
matching has been presented and two basic terms were defined: the lexeme and
the lexatom. For fast access lexatoms are stored in a buffer. A two-step buffer
process has been presented targetting a maximum of flexibility. The two steps
are byte loading and buffer filling. Restricting the output of analysis to
tokens supported the idea of lexical analysis as tokenization. A final section
elaborated on modes of a lexical analyzer as specification of its behavior.
