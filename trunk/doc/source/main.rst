.. Quex documentation master file

The Quex Manual
###############

Contents:

.. toctree::

   :maxdepth: 4

   introduction/main.rst
   .. 
      Background story, what it does, how to install, and a minimalist example.
      Goal is to let user grab the idea and get first experiences with the
      tool.

   basic-concepts/main.rst
   .. 
      Terminology of lexical analysis & Quex: Analyzer, State Machine,
      Buffer, Stream, Lexeme and Lexatom, Patterns and REs Actions, Tokens.
      Goal: User learns language of what follows.

   quex-syntax/main.rst
   ..
      Syntax explained: The '.qx' files and their content.

   modes/main.rst
   .. 
      1st/3 important concepts: How an analyzer behaves.

   tokens/main.rst
   ..
      2nd/3 important concepts: How an analyzer reports results.
        
   buffers-and-streams/main.rst
   .. 
      3rd/3 important concepts: How an analyzer is stimulated.

   life-cycle/main.rst
   .. 
      Construct, Destruct, Include (freeze/unfreeze memento), Reset.

   engine/main.rst
   ..
      Internal engine and how it is tuned.

   appendix/main.rst
   ..
      Several things that did not fit elsewhere.

.. bibliography:: citations.bib

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

