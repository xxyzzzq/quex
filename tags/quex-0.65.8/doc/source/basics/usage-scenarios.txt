.. _sec-usage-scenarios:

Usage Scenerios
===============

Generated lexical analyzers might be used in different environments and
scenarios. Depending on the particular use case, a different way of interaction
with the engine is required. In this section, a set of scenarios is identified.
The reader is encourage to compare his use case with the ones mentioned below
and to apply the appropriate interaction scheme.


#. **File**: The whole stream of data is present at the time where the engine
   starts its analysis. This is the typical case when the input consists of
   files provided by some type of file system.

   **Interaction**: The generator needs to be instantiated with one of the
   following constructors.

   .. code-block:: cpp

        CLASS(const std::string&  Filename,       
              const char*         InputCodingName     = 0x0, 
              bool                ByteOrderReversionF = false); 
        CLASS(std::istream*       p_input_stream, 
              const char*         InputCodingName     = 0x0,
              bool                ByteOrderReversionF = false); 
        CLASS(std::wistream*      p_input_stream, 
              const char*         InputCodingName     = 0x0, 
              bool                ByteOrderReversionF = false); 
        CLASS(std::FILE*          input_fh,       
              const char*         InputCodingName     = 0x0, 
              bool                ByteOrderReversionF = false); 

   Tokens are received with the functions:

   .. code-block:: cpp

          QUEX_TYPE_TOKEN*  receive(QUEX_TYPE_TOKEN*  begin, 
                                    QUEX_TYPE_TOKEN*  end);

   in case that a 'users_queue' token policy is applied. Or, with
   
   .. code-block:: cpp

          void              receive();
          void              receive(QUEX_TYPE_TOKEN*   result_p);

   in case that a 'users_token' token policy is applied. Or, in the default
   case where a 'queue' token policy is applied the following functions
   are available: 

   .. code-block:: cpp

          void              receive(QUEX_TYPE_TOKEN*   result_p);
          void              receive(QUEX_TYPE_TOKEN**  result_pp);

   More about token policies can be reviewed in :ref:`Token Policy
   <sec-token-policies>`. 

   For file inclusion, include stacks can be implemented based on
   *memento chains* (see :ref:`Include Stacks <sec-include-stack>`).
  
    .. note::

       Care might be taken with some implementations of ``std:istream``. The number of 
       characters read might not always correspond to the increase of the numeric value 
       of the stream position. Opening files in binary mode, mostly, helps. If not
       then the engine needs to operate in *strange stream* mode. Then, the compile line option::

         QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION

       needs to be defined.

   For this scenerio, it is actually not essential that there is a file from which
   the data is supplied. Likewise, data can be read from a ``stringstream`` or any
   other derivate of ``istream`` or ``FILE*``. Essential is that all data is available
   as soon at the moment the engine expects it.

.. _sec-syntax-chunks:
       
#. **Syntactically Chunked Input**: In this scenario, the engine is fed with
    chunks of character streams which appear in a time separate manner. Thus,
    the engine does not necessarily get a reply when it asks to refill its
    buffer. In the syntactically chunked case, though, it is assumed that the 
    frame itself is sufficient to categorize the stream into tokens.
    There are no tails to be appended, so that a lexeme is completed.
    This may be a frame sequence which is fed to a command line interpreter:::

       frame[time=0]:  [print "hello world"]
       frame[time=1]:  [plot "myfile.dat" u 1:4] 
       frame[time=2]:  [display on screen 45, 32 pri] 

    The command line from start to end is passed to the
    analyzer engine. If there is a keyword ``print`` and the line ends with
    "``pri``", then the engine does not have to wait for the next line in order
    to check whether it completes the ``print`` keyword. It is imposed that each
    line is syntactically complete, and thus, ``pri`` can be considered as an
    identifier or whatsoever the language proposes (most likely 'error').

    This scenario requires direct buffer access. It can be treated by means
    of :ref:`sec-copying`, :ref:`sec-filling`, or :ref:`sec-pointing` as mentioned in the
    dedicated sections.

.. _sec-arbitrary-chunks:

#. **Arbitrarily Chunked Input**: In this scenario, the analyzer needs to wait
    at the point it reaches the end of a character frame because there might be
    a tail that completes the lexeme::

       frame[time=0]:  [print "hello world"; plo]
       frame[time=1]:  [t "myfile.dat" u 1:4; di] 
       frame[time=2]:  [splay on screen 45, 32]

    This might happen when input comes through a network connection and the
    frame content is not synchronized with the frame size.  This scenario,
    also, requires direct buffer access. It can be treated by means of
    :ref:`sec-copying`, :ref:`sec-filling`, but not with :ref:`sec-pointing`.

In the view of the author, these use case cover all possible scenarios. However,
do not hesitate to write a email if there is a scenario which cannot be handled 
by one of the aforementioned interaction schemes.
