Modes
=====

An analyzer does everything it does in a mode which defines its behavior.  This
is similar to a human and his moods [#f1]_, but differs in that an analyzer is
is only in one single mode at a time. An analyzer's behavior is primarily
determined by the patterns for which it is lurking. All patterns of a mode are
melted into one single state machine. The fewer patterns an analyzer is trying
to detect, the smaller its state machine and the more effective it can operate.
Thus, it may be more efficient to separate patterns into different modes
according the circumstances under which patterns may trigger. Also, it may be
that the language changes. For example, in a programming language, when
suddenly a phrase is to be parsed, then numbers may no longer be considered as
numbers but just as strings. So, there is a rationale for having modes.

Modes can be entered in two ways. First, there is the simple 'GOTO mode'
instruction.  Changing modes this way, the previous mode is forgotten as soon
as the target mode is entered.  Second, there is a 'GOSUB mode' instruction.
In that case, modes are stored on a stack--similar to *function calls*. The
counter part to 'GOSUB mode' is 'GOUP mode'. By means of that the mode is
entered from which the current mode has been entered--similar to a *return*
statement in a function. The 'GOSUB/GOUP' functionality allows for a mode to be
entered from more than one mode, and return without knowing the mode from where
it entered. For example, a 'mark up mode' and a 'math mode' may both use the
'string mode' mode to detect strings. As soon as a quote arrives each one
enters the 'string mode' via 'GOSUB'. The string mode returns upon the closing
quote to the one from where is was activated via 'GOUP'--without knowing
whether it was the 'mark-up' or the 'math mode'.

The behavior of an analyzer, however, is determined by more than just the
set of lurking patterns and their related actions. The following enumeration
lists all types of behavior under the syntactic means that is used to 
specify them:

.. describe:: Pattern-Action Pairs

  #. Patterns which are lurking to cause actions and send tokens.

.. describe:: Event Handlers

  #. On-Incidence definitions for 'on_failure', 'on_end_of_stream', 
     etc.

.. describe:: Tags in <...> brackets

  #. Skippers, i.e. machines that run in parallel without causing any
     token to be produced.

  #. Counting behavior, i.e. what character counts how many columns or 
     lines, or causes jumps on a column number grid.

  #. Indentation based scope parameters, defining what is a newline 
     what is white space, what is bad at the beginning of a line (the
     tab character or space?) :cite:`todo`.

  #. Transition control, specifying from where a mode can be entered
     and to what mode it may transit.

  #. Inheritance control, specifying if the mode can be inherited or
     not.

.. describe:: List of base modes  

  #. Base modes from which behavior is inherited.

In terms of software design patterns :cite:`Gamma1994design` modes are
implemented applying the *strategy pattern*. All behavior of a mode is
controlled by a set of function pointers. Changing a mode means changing the
set of function pointers. One of those function pointers is the *analyzer
function* which runs the state machine that detects lexemes in incoming data
streams.

.. rubric:: Footnotes

.. [#f1] The funny analogy between people's moods and modes is 
         adapted from Donald Knuth's TexBook :cite:`Knuth1986texbook`,
         in his introduction to chapter 13.
