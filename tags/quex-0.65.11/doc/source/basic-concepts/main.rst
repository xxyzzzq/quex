**************
Basic Concepts
**************

This chapter is about concepts and terminology. The discussions setup the the
foundation for the subsequent chapters.  Partly, the discussions partly peek
behind the curtain of what Quex is doing--only for the reader to relax knowing
that Quex deals with the details. 

The first section elaborates on *state machines* as approach being used for
pattern matching. In the second section the analyzer's complete *input* food
chain is presented. Based on this setup a maxium flexibility with respect to
input source and input content is achieved. The third section discusses an
analyzer's *output*: tokens. The last section explains the idea of a *mode* which
circumscribes how a generated analyzer produces output from input at a given
point in time.

.. toctree::

   lexical-state-machine.rst
   input.rst
   output.rst
   modes.rst
   summary.rst
