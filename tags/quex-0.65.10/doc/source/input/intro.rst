Input Configuration
===================

The goal of this chapter is to provide sufficientknowledge to take full control
over the input which is fed into the lexical analyzer. For this, in a first
section the engine's input procedure is explained. This section equips the
reader with basic concepts applied upon input and gives a first oversight over
the flexibility. Second, a section introduces the level of details upon
construction. It explains how different constructors may be applied dependent
on the deepness at which one tries to adapt the input behavior. The term
construction is extended for procedures of inclusion and reset. Third, some
explanations are done for the usage of converters upon input. This is
particularily interesting if other codecs are converted to plain Unicode.  In a
final section, it is explained how a lexical analyzer engine can be transformed
so that it directly runs on a codec different from Unicode.

Input Procedure
===============

Lexical analysis happens by means of a state machine. State transitions in the
state machine are triggered by events. In lexical analysis those events are
characters from an input stream. To efficiently handle input streams, quex
loads them into a chunk in memory. An input pointer points to the currently
treated character. Dependent on the character, a state transition happens.
Then, the input pointer is increased, so that the character at the next
position may be used as event for the subsequent state. This procedure
continues until either an acceptance state is reached, where a pattern matched,
or the end of the buffer is reached. In the later case, new data must be loaded
into the buffer. The input pointer must be set to the beginning of the data and
the analysis continues. Figure 'X' depicts this principle idea. The engine
only requires a means to 1) read the current character, 2) increment the input
pointer, and 3) reload new content into the buffer. This is the horizon of
the engine's buffer.

The buffer filling procedure must cope with the specialities of operating
systems, input stream procedures, and a variety of codecs. For this, the
filling process is divided into two steps: byte loading and filling.
Accordingly, there are two base classes ``ByteLoader`` and ``BufferFiller``.
The task of a byte loader is to grab plain byte streams from an input source.
The task of a filler is to deliver this data so that it fits the engine's
buffer codec and character width.

TODO: When to use dedicated ByteLoader, BufferFiller (byte order reversion, 
start position).
  
Starting from a position X while not taking it as zero position:

