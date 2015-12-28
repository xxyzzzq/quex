Modes
======

A lexical analyzer mode refers to a behavior of the analyzer engine.  More
precisely, it defines a set of pattern-action pairs and incidence handlers that are
exclusively active when the analyzer is in a particular mode. The reason for that
might be syntactical. Imagine a nested mini-language in a 'mother' language that
has interferences of its patterns with the pattern of the 'mother' language. For example,
the mother language may contain floating pointer numbers defined as::

   [0-9]+"."[0-9]*   => FLOAT_NUMBER(Lexeme);

In the mini-language there might only be integers and the 'dot' is considered
a period of a sentence, such as in::

   [0-9]+   => NUMBER(Lexeme);
   "."      => TKN_PERIOD;

If both patterns were describe in a single mode, then interferences would occur.
If a number occurred at the end of a sentence, such as 1776 in::

                "... mentioned in 1776. In that year, ..."

then it would be eaten by the floating point number pattern (i.e. interpreted as
``1776.0``), since the engine follows the longest match. The period at the end 
of the sentence would not be detected. This is an example were multiple modes
are required from a syntax point of view. Another reason for having more
than one mode is computational performance. The C-pre-processor statements in 
the ``#``-regions (e.g. ``#ifdef``, ``#define``, ``#include``, etc.) rely on
a reduced syntax. Since, not the whole C-language features need to be present
in those regions it might make sense to have them parsed in something like
a ``C_PREPROCESSOR`` mode. 

The following sections elaborate on the characteristics of modes, incidence
handlers in modes, mode inheritance, the features and options to define modes. 

.. toctree:: 

   characteristics.txt
   characteristics-pitfalls.txt
   inheritance.txt
