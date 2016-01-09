Basic Algebra
=============

Every regular expression can be associated with the set of lexemes which it
matches.  Quex's algebra on regular expressions is defined in terms of
set-theoretic operations on sets of lexemes.  The set operations of union and
intersection in the space of lexemes do not generate new lexemes, but select or
collect only the lexemes of the set on which they operate.  In the same way the
union and intersection operations on regular expressions shall result in
regulare expressions which do not match new lexemes, but only match selections
or collections of lexemes of the regular expressions on which they operate.

The basic operations of union, intersection, and complementation the are
defined in term of their counterpart on the space of lexemes.  A regular
expression is considered as a representer of the set of lexemes which it
matches.  For example, let the regular expressions P and Q be defined as
below::

       P    [0-9]{2}
       Q    [a-b]{2}

That is, P matches the lexemes::

    "00", "01", "02", ... "99"

and Q matches lexemes following the pattern::

    "aa", "ab", "ac", ... "zz"

Then, for example, the *union* of P and Q must produce a finites state
automaton, i.e. regular expression, which matches the union of both, i.e.::

    "00", "01", "02", ... "99", "aa", "ab", "ac", ... "zz"

The fundamental operations are available in quex via the commands:

.. describe:: \\Union{X0 X1 ... Xn}

   Produces a finite state automaton that matches the union of the 
   what is matched by the regular expressions ``X0``, ``X1``, ... ``Xn``.

.. describe:: \\Intersection{X0 X1 ... Xn}

   Produces a finite state automaton that matches the union of the 
   what is matched by the regular expressions ``X0``, ``X1``, ... ``Xn``.

.. describe:: \\Not{X}

   Produces a finite state automaton that matches the complementary set
   of lexemes of what is matched by the regular expressions ``X``.

There are two special patterns: the '\\None' and the '\\Any+' pattern. The first
does not match anything at all. The second matches absolutely anything that is
at least one character long. Both are useless in pattern definitions, but they
play important roles in the algebraic structure. The algebraic operations are
devided into two categories:

.. describe:: Unary Operations (short 'U').

.. describe:: Binary Operations (short 'B').

Unary operations take only one argument. Binary operations take at least two.
Another categorization is

.. describe:: Set Operations (short 'S').

.. describe:: Transformations (short 'T').

Set operations do not change or modify lexemes in the related lexeme sets.
They can be considered in terms of additions or deletions of complete lexemes.
A Transformations produce regular expressions that match new lexemes.  As
indicated in the descriptions the letters 'U', 'B', 'S' and 'L' shall indicate
the operator categories.  Following are the regular expression operators.

.. describe:: \\R{ P } -- Reverse (UT)

   Matches the reverse of what P matches.  For any lexeme Lp = { x0, x1, ...
   xn } which matches P, there is a reverse lexeme Lrp = { xn, ...  x1, x0 }
   which matches \\R{ P }. Examples:

.. describe:: \\Not{ P } -- Complement (UT)

   Matches anything that P does not match.  Any lexeme Lnp = { x0, x1, ...  xn }
   which is not matched by P is matched by \\Not{ P }.

.. describe:: \\Sequence{ P Q } -- Sequentialize (BT)

   Matches the concatination of P and Q. For any to lexemes Lp = { x0, x1, ... xn }
   matched by P and Lq = { y1, y2, ... ym } matched by Q, any lexeme 
   matched by \\Sequence{ P Q } consists of a lexeme from Lp followed by
   a lexeme from Lq.

   This operator is an explicit implementation of ``PQ`` which does
   exactly the same.

.. describe:: \\CutBegin{ P Q } -- Cut Beginning (BL)

   Prune P in front, so that ``\CutBegin{ P Q }`` starts right after what Q 
   would match. 

   Example::

              \CutBegin{"otto_mueller" "otto"} --> "_mueller"

.. note:: 

     ``\CutBegin`` cuts only *one appearance* of a lexeme from Q *at the
     beginning* of P; but it does not mean that the result cannot match a
     lexeme starting with a lexeme from Q. Let P match Lp = {xx, xy} while Q
     matches Lq = {x}, then ``\CutBegin{P Q}`` only cuts the first appearance
     of 'x' and the resulting set of lexemes is {x, y}. It contains 'x'
     which is a lexeme matched by Q.

.. note::

     When dealing with repeated expressions the rules of ``\CutBegin``
     may surprise at the first glance. Consider for example::

           \CutBegin{[0-9]+ 0}
    
     which only cuts out the first occurence of 0.  There is an infinite number
     of lexemes in ``[0-9]+`` having '0' as second character--which becomes now
     the first. Thus the above expression is equivalent to ``[0-9]+`` itself.  To
     delete ``0`` totally from ``[0-9]+`` it is necessary to write::

           \CutBegin{[0-9]+ 0+}



.. describe:: \\CutEnd{ P Q } -- Cut End (BL)

   Prune P at back, so that \\CutEnd{ P Q } ends right before Q would match. 
   Example::

              \CutEnd{"otto_mueller" "mueller"} --> "otto_"

.. describe:: \\Union{ P Q } -- Union (BS)

   Matches all lexemes which are matched by P and all lexemes which are
   matched by Q.

.. describe:: \\Intersection{ P Q } -- Intersection (BS)

   Matches only those lexemes which are matched by both P and Q.

.. describe:: \\NotBegin{ P Q } -- Complement Begin (BS)

   Matches those lexemes of P which do not start with lexemes that
   match Q.

.. describe:: \\NotEnd{ P Q } -- Complement End (BS)

   Matches those lexemes of P which do not end with lexemes that
   match Q.

.. describe:: \\NotIn{ P Q } -- Complement End (BS)

   Matches those lexemes of P which do not contain lexemes that
   match Q.


