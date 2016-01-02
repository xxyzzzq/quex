Output
======

The natural output of lexical analysis are so-called tokens. A token carries
the information about the content category that it carries and possibly the
lexeme or interpretation of the lexeme that matched when the token was
produced.  In traditional tools, such as 'flex' :cite:`todo` the user is free
in his way to react on pattern matches [#f1]_.  However, restricting this
freedom brings clarity with respect to the function of lexical analysis. 
If output of lexical analysis is a stream of tokens, then a lexical analyzer is
a translator of a stream of raw, uninterpreted information into a stream of
minimal interpreted information. In this sense, lexical analysis is a synonym
for *tokenization*. 

Token
   A token contains a *unique token identifier* which identifies the category 
   of meaning that it carries. Optionally, it may carry further information 
   about the matched lexeme. 

For example, a token may carry the meaning 'plus operator' with no further
information, it may carry the meaning 'function' together with the name of the
function to which it relates, or it may carry the meaning 'number' with some
numeric value related to it. Indeed, there are two approaches to 
handle *lexeme interpretation*:

 #. Only store a token id along with the token and possibly the raw lexeme 
    that matched the pattern. The lexeme is interpreted later by a
    'lexeme interpreter' unit.

 #. Interpret the lexeme, for example, as a number and store this 
    data along with the token.

Functionally, both are equivalent. Many times, the lexeme interpretation is
trivial and it does not harm to web it into the analyzer. In this sense, the
second approach is more practical. The first one, though, supports a clearer
design because it separates *tokenization* from *lexeme interpretation*. Also, 
with this approach lexeme copying might be spared and only the location of 
the lexeme in the buffer might be referred [#f2]_. 

Quex is aware of the token class and it supports customized token classes.
It provides a special mini language to describe token classes. Based on these
descriptions real types are defined in the target language to be used by
the generated analyzer. 

Another purpose of the token is to carry information about line and column
numbers. The location where a token occurred is important, for example, for
error reports when an interpreter must give a hint to where the error occurred.

Intuitively, a sequence of characters matches a pattern. The sequence
constitutes a lexeme and its information is stored in a token. The token is
then be reported to the user. In such scenarios, there is no need to queue
tokens. However, it is conceivable that a single incident in the input triggers
more than one token. This is the case, for example, when scopes are determined
by indentation.  Then, a single newline may close many higher indented scopes.
Thus in that case, tokens need to be queued. Quex supports both token passing
policies: single token and token queue.


.. rubric: Footnotes

.. [#f1] The same way in Quex, actions related to patterns can be freely
         specified. However, the ease of the token sending syntax pushes
         towards the concept of a lexical analyzer as a token sender.

.. [#f2] In this case, though, a callback must be implemented which 
         reacts on the buffer's content change. On this event the
         callback must saveguard all related strings.
