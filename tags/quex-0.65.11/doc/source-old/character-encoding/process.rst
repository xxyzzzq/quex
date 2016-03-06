The Process of Buffer Filling
=============================


This section discusses how a generated lexical analyzer reads data from a file or, more
generally, from a stream. Figure :ref:`Process of loading data from a data stream<fig_load_data>` 
shows an overview over the process.  It all starts with a character stream. The content
is read via an input policy which basically abstracts the interface of the stream for the *buffer
filler*. For the buffer filler, there is no difference between a stream coming from a ``FILE``
handle, and ``ifstream`` or an ``istringstream``. The buffer filler has the following two
tasks:

* Optionally convert incoming data appropriate for the character encoding of the lexical
  analyzer engine (Unicode).

* Fill the buffer with characters that are of *fixed* size.

Some character encodings, such as UTF-8, use a different number of bytes for the
encoding of different characters. For the performance of the lexical analyzer engine
it is essential that the characters have *constant* width. Iteration over
elements of constant size is faster than over elements of dynamic size. Also
the detection of content borders is very simple, fast, and not error-prone.

It becomes clear that the transfer of streaming data to the buffer memory can
happen in different ways. This is reflected in the existence of multiple types
of buffer fillers.

.. _fig_load_data:

.. figure:: ../figures/character-converting-process.*
   
   Loading data from a stream into the buffer memory.

As mentioned earlier, the usage of character encodings is supported by the
plug-in of converter libraries, and by adaptations made to the analyzer engine.
The following points should be kept in mind with respect to these two
alternatives:

.. describe:: Adapting the internal engine

    * Pro: Faster run-time performance, since no conversion needs to be done.

    * Contra: Freezing the design to a particular coding. If more than
              one coding is to be dealt with, multiple engines need to be created.

.. describe:: Using plugged-in converter libraries

    * Pro: Libraries provide a wider range of encodings to be used. 

    * Contra: Using a converter implies a certain overhead with 
              respect to the memory footprint and run-time performance of an
              application.

Let the following terms be defined for the sake of clarity of the subsequent
discussion:

* Character Width

  This determines the fixed number of bytes that each single character occupies
  in the buffer memory. It can be set via the command-line options ``-b`` or 
  ``--bytes-per-ucs-codepoint``. Directly related to it the the *character type*,
  i.e. the real C-type that is used to represent this entity. For example, ``uint8_t``
  would be used to setup a buffer with one byte characters. 

  .. note::

     The character type is a C-type and does not make any assumptions about the
     encoding which is used. It is a means to specify the number of bytes
     that are used for a character in the buffer memory--not more.

* Data Stream Codec

  This is the character encoding of the input data stream. If Non-Unicode (or ASCII)
  streams are to be used, then a string must be passed to the buffer filler that
  tells from what encoding it has to convert.

* Lexical Analyzer Codec

  This is the character encoding of the analyzer engine. The encoding determines
  what numeric value represents what character. For example, the greek letter α has a
  different numeric value in the encoding 'UCS4' than it has in 'ISO8859-7'.
  By means of the command line flag ``--encoding`` the engine's internal
  character encoding can be specified.

The next section focusses on the adaption of the internal analyzer engine to a
particular encoding. The following sections discuss the alternative usage of
converters such as ICU and IConv to fill the analyzer buffer.
