.. _sec-direct-buffer-access:

Input Policies
==============

Besides memory management (see section :ref:`memory-management`), the only
external dependency of a quex generated lexical analyzer is the policy of
how input is provided. The environment may restrict the way how data is
delivered or how the lexical analyzer is invoked. This chapter describes how
input may be provided in the best possible way depending on given
circumstances. In a first section basic concepts are discussed to describe a
input policy situation. The remaining sections explain how to implement
aspects of input policies that deviate from the default handling.

TODO: Setting the 'end_of_stream_f' is essential in 'unidirectional streams'
      where a reload is impossible! Then, the 'end_of_stream_f' initiates
      the 'end_of_stream_character_index' which prevents a reload.

Basic Concepts of Input Policies
################################

A major goal of quex is to provide a maximum flexibility of how input is fed. That
is, the user shall be enabled to provide the input character stream in the most
efficient and most appropriate way as possible in his particular application.
Before features and APIs can be discussed a few fundamental concepts must be
explained. First of all there are two timing schemes for the delivery of 
data: 

#. *Complete* is an input stream that is present in its entirety at the time 
   of analysis. The typical case is file based input, where the file is completely
   stored on a storage device before it is lexically analyzed.  The 'end-of-stream' 
   is determined by the no more data being available. 

#. *Segmented* is an input stream that is received in segments. When the
   analysis starts, not necessarily the whole content is present. Instead, it
   may happen that the analyzer needs to wait for new content.  An
   'end-of-stream' event may have to be specified explicitly inside the stream.

In case of segmented there are three levels of 'granularity' by which the input
chunks can be delivered.

#. *Syntactical* chunks never break inside a lexeme.

#. *Character* chunks never break inside a character representing byte sequence.

#. *Arbitrarily* chunked data may break inside a lexeme or even inside a
   character representing byte sequence. 

Lexical analysis runs on some a linear storage: the engine's buffer.  It can be
filled in two manners.

#. *Automatic* filling means that the engine's buffer is automatically filled
   as soon as more data is required to continue analysis. No user interaction
   is required.

#. *Manual* means that the engine's buffer is filled manually by a user's calls
   to an API for buffer access.

For manual filling, the analyzer does not need to know how to load new data.
For automatic filling a 'ByteLoader' object provides the interface to the
underlying operating system's file input/output API. The current version of
quex provides classes for Standard C ``FILE`` objects, Standard C++
``std::stream`` objects, a POSIX layer, and an RTOS layer. Section ``xxx``
explains how to derive a customized interface.

Independently of manual or automatic filling, the input may be processed
before being filled into the engines buffer, or not. 

#. *Direct* filling means that data is directly used as the data on which the
   engine runs. In this case, the engine's buffer is the only buffer that is
   required.

#. *Converterted* filling means that the incoming data is converted, for
   example from some encoding to a unicode encoding, such as ASCII or UCS32. When
   conversion is involved a 'raw buffer' might be necessary to store incoming
   data before it is converted and stored in the engine's buffer.

A buffer is an array. The raw buffer, in case of converted filling, is always
an array of bytes. The engine's buffer element type is diverse. In case of an
engine running on ASCII encoding, it may be an array of bytes (e.g. of type
``uint8_t``). In case of UTF16, the engine's array may be an array of 2-byte
chunks (e.g. of type ``uint16_t``). On very small, or very optimized systems
the memory placement may be an issue and whether dynamic allocation is allowed
or not.

The aforementioned concepts constitute the pillars of an input policy design. 
Once, a user has a concrete idea about those for his particular setup, the
following sections provide guidance to find a dedicated solution.

Input Streams
#############

File-based input is the easiest and most common use case as it appears in
compilers or interpreters. In C, the related handle is a ``FILE`` pointer and
in C++ it is a ``std::ifstream`` object. A generated lexical analyzer class
may, of course, be applied to an *arbitrary* number of files. However, an
analyzer's instance is bound to a *specific* file. If another file is to be
parsed, it either needs to be included (see include stack handling), or another
analyzer instance needs to be initialized. When relying on files, then the
input buffer can either be filled up to its limits, or the end-of-file has
been reached.

Relying on pipes needs some elaborate consideration. When pipes are used
no assumptions can be made about how long one needs to wait for an 
incoming chunk of data. Further, no assumptions can be made how big that
chunk is. Thus, the automatic filling approach may result in dead-locks
waiting for input and the input buffer may not always be filled to its
limits. Data may be absorbed from a pipe byte-wise, or line-wise.

difference between files and pipes is that the ... TODO

A generated lexical analyzer runs its analysis on data located in a buffer. In
general, this buffer is filled automatically by the underlying buffer
management which relies on some type of input stream. It is, however, possible
to access the buffer directly which, in some cases may be advantageous. In
particular parsing the standard input, i.e. ``cin`` in C++ or ``stdin`` in C
must rely on these mechanisms (see example in ``demo/010/stdinlexer.cpp``). The
following methods can be supplied to setup the analyzer's character buffer. The
term 'framework' is used to refer to some kind of entity that delivers the
data.

#. *Copying* content into the buffer.

   The framework provides its data in chunks and specifies itself the data's
   memory location. The location is possibly different for each received frame.

   **Example**: ``demo/010/lexer.cpp``.

   Copying content into the engine's buffer happens by means of the buffer
   filler's member function ``fill()``. If the buffer filler is 'plain' it
   directly copies the content into the engine's buffer. If it is a converter
   it copies only converted contend. The filler takes care of trailing bytes
   etc. An exemplary call in C++ or C looks like:

        lexer.buffer.fill(&lexer.buffer, Begin, End);

   Where ``Begin`` points to the beginning of the data to be copied and ``End``
   points to the first address behind the content to be copied. Both pointers
   are of type ``void*`` so that the interface is homogeneous across any
   type of buffer fillers. 


#. *Immediate Filling* of the buffer.

   The framework writes its data in chunks into a memory location which is
   specified by the user.

   **Example**: ``demo/010/lexer.cpp``.

   In this case, the buffer needs to be prepared calling ``fill_prepare()``.
   During preparation, quex determines the begin and end pointers of the region
   which might be filled.  After the buffer is filled the ``fill_finish()``
   function needs to be called. It performs all necessary to initiate the
   analysis process.  An immediate filling sequence looks like::

        lexer.buffer.filler->fill_prepare(&qlex.buffer, 
                                          (void**)&begin_p, 
                                          (const void**)&end_p);

        receive_n = my_receive_to_buffer(begin_p, end_p - begin_p); 

        lexer.buffer.filler->fill_finish(&qlex.buffer, &begin_p[receive_n]);

   The process is indifferent of the type of buffer filling. Procedures
   such as converting happen behind the scenes. Again, the pointers to
   specify the begin and end of the regions are converted to ``void**``
   and ``const void**`` for the sake of homogeneity.

#. *Pointing* to a memory address where the buffer shall analyze data.

   The (hardware level) framework writes data into some
   pre-defined address space which is the same for each received frame.

   **Example**: ``demo/010/point.cpp``.

.. note::

   In some frameworks, the buffer filling implies that a terminating
   zero character is set. This can cause an error::

        exception: ... Buffer limit code character appeared as normal 
                   text content.

   To avoid this, report one character less when using ``buffer_fill_region_finish``,
   or make sure that the terminating zero is not copied.

TODO: Mention usage of 'BufferFiller*' constructor where the filler needs
      to be deleted manually. Or, better construct with (ByteLoader*)0.

TODO: When 'reset' make sure that the right token is 'swapped' into the analyzer!
      In doubt, set to zero.
      
In case of interrupted character streams, there is no direct way for the
analyzer engine to determine whether a stream is terminated or not. Thus, either
an 'end of analysis' pattern must be introduced, or the analysis is to be
supervised by another thread which may end the analysis based on time-out
conditions. In the following description it is assumed that there exists a
pattern that tells the analyzer that the stream is ended.  It produces a
``BYE`` token.  

Direct buffer access can be performed by means of the following member
functions of the filler

    .. code-block:: cpp

        QUEX_TYPE_CHARACTER*  fill_prepare(ContentBegin, ContentEnd);
        void                  fill_finish();

Analyzers that work directly on user managed memory should use 
the following constructor:

    .. code-block:: cpp

        MyLexer(QUEX_TYPE_CHARACTER* MemoryBegin, size_t Size, 
                const char*  CharacterEncodingName       = 0x0,
                const sizt_t TranslationBufferMemorySize = 0);

where ``MyLexer`` is the user specified engine name. The arguments
``MemoryBegin`` and ``Size`` may be set to zero, if the analyzer shall allocate
the memory on its own. The last two arguments are only of interest if the
incoming input is to be converted from a non-unicode character set to
unicode/ASCII. 

The input navigation when using direct memory access is fundamentally different
from the navigation for file based input. For file based input the analyzer can navigate
backwards in an arbitrary manner. This is not possible if the buffer is filled
by the user. The maximum amount that can be navigated backwars [#f1]_ is determined 
by the fallback region. Its size is determined by the macro

        QUEX_SETTING_BUFFER_MIN_FALLBACK_N

determines the maximum length of the pre-condition pattern. If no pre-condition
pattern is used, this might be neglected. 

.. note:: 

   The presented methods are based on the token policy *User's Token*, i.e.
   the command line must contain ``--token-policy users_token`` when quex
   is called. Queue based policies might also be used, once the basic 
   principles have been understood.

.. warning::

   Is is highly recommdedable to define an ``on_failure`` handler for each
   lexical analyzer mode which sends something different from ``TERMINATION``.
   The ``TERMINATION`` token is used in the strategies below to indicate the
   end of the currently present content. By default, a quex engine sends a
   ``TERMINATION`` token on failure, and thus the strategies below might hang
   up in an endless loop as soon as something is parsed which is not expected.
   A line such as 

   .. code-block:: cpp

      mode X {
         ...
         on_failure  => QUEX_TKN_MY_FAILURE_ID(Lexeme);
         ...
      }

   helps to avoid such subtle and confusing misbehavior.


.. _sec-copying:

Copying Content
...............

The method of copying content into the analyzer's buffer can be used
for the 'syntactically chunked input' (see :ref:`syntax-chunks`) and
the 'arbitrarily chunked input' (see :ref:`arbitrary-chunks`). Copying
of content implies two steps:

  #. Copy 'used' content to the front of the buffer so that space
     becomes free for new content.

  #. Copy the new content to the end of the current content of the
     buffer.

First, let us treat the case that the incoming frames are considered to be be
*syntactically complete* entities--such as a command line, for example. This case
is less complicated than the case where frame borders appear arbitrarily, because
any trailing lexeme can be considered terminated and the analyzer does not need
to wait for the next frame to possibly complete what started at the end of the last
frame. 

Syntactically Chunked Input Frames
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

The following paragraphs discuss the implementation of this use case. First,
two pointers are required that keep track of the memory positions which
are copied to the buffer.

.. code-block:: cpp

    typedef struct {
        QUEX_TYPE_CHARACTER* begin;
        QUEX_TYPE_CHARACTER* end;
    } MemoryChunk;

A ``chunk`` of type ``MemoryChunk`` later contains information about the
current content to be copied into the analyzer's buffer. ``.begin`` designates
the beginning of the remaining content to be copied into the analyzer's buffer.
``.end`` points to the end of the currently available content as received from
the messaging framework. The following segment shows which variables are
required for the analysis process.

.. code-block:: cpp

    int
    main(int argc, char** argv)
    {
        quex::tiny_lexer      qlex((QUEX_TYPE_CHARACTER*)0x0, 0); 
        quex::Token*          token = 0x0;           
        QUEX_TYPE_CHARACTER*  rx_buffer = 0x0; // receive buffer
        MemoryChunk           chunk;

        ...

The analysis start with the following:

.. code-block:: cpp

    // -- trigger reload at loop start
    chunk.end = chunk.begin;

    // -- LOOP until 'bye' token arrives
    token = qlex.token_p_swap(&token);
    while( 1 + 1 == 2 ) {
        // -- Receive content from a messaging framework
        if( chunk.begin == chunk.end ) {
            // -- If the receive buffer has been read, it can be released.
            if( rx_buffer != 0x0 ) my_release(rx_buffer);
            // -- Setup the pointers 
            const size_t Size  = my_receive_syntax_chunk(&rx_buffer);
            chunk.begin = rx_buffer;
            chunk.end   = chunk.begin + Size;
        }
        ...

At the beginning of the loop it is checked whether it is necessary to get
new content from the messaging framework. If so, the previously received
'receive buffer' may be released for ulterior use. Then the messaging
framework is called and it returns information about the memory position
and the size where the received data has been stored. Now, the content
needs to be copied into the analyzer's buffer.

.. code-block:: cpp

           chunk.begin = qlex.buffer_fill_region_append(chunk.begin, chunk.end);

This function call ensures that 'old content' is moved out of the buffer. Then,
it tries to copy as much content as possible from ``chunk.begin`` to ``chunk.end``.
If there is not enough space to copy all of it, it returns the pointer to the
end of the copied region. This value is stored in ``chunk.begin`` so that it
triggers the copying of the remainder the next time of this function call.
Now, the buffer is filled and the real analysis can start. 

.. code-block:: cpp

            // -- Loop until the 'termination' token arrives
            while( 1 + 1 == 2 ) {
                const QUEX_TYPE_TOKEN_ID TokenID = qlex.receive();

                if( TokenID == QUEX_TKN_TERMINATION ) break;
                if( TokenID == QUEX_TKN_BYE )         return 0;

                cout << "Consider: " << string(*token) << endl;
            }

When a ``TERMINATION`` token is detected a new frame must be loaded. The
inner analysis loop is left and the outer loop loads new content. If the
``BYE`` token appears the analysis is done. Any token that is not one
of the two aforementioned ones is a token to be considered by the parser.
It follows the complete code of the analyzer for syntactically chunked
input frames:

.. code-block:: cpp

    #include "tiny_lexer"
    #include "messaging-framework.h"

    typedef struct {
        QUEX_TYPE_CHARACTER* begin;
        QUEX_TYPE_CHARACTER* end;
    } MemoryChunk;

    int 
    main(int argc, char** argv) 
    {        
        using namespace std;

        // Zero pointer to constructor --> memory managed by user
        quex::tiny_lexer      qlex((QUEX_TYPE_CHARACTER*)0x0, 0);   
        quex::Token*          token = 0x0;           
        QUEX_TYPE_CHARACTER*  rx_buffer = 0x0; // receive buffer
        MemoryChunk           chunk;

        // -- trigger reload of memory
        chunk.begin = chunk.end;

        // -- LOOP until 'bye' token arrives
        token = qlex.token_p();
        while( 1 + 1 == 2 ) {
            // -- Receive content from a messaging framework
            if( chunk.begin == chunk.end ) {
                // -- If the receive buffer has been read, it can be released.
                if( rx_buffer != 0x0 ) my_release(rx_buffer);
                // -- Setup the pointers 
                const size_t Size  = my_receive_syntax_chunk(&rx_buffer);
                chunk.begin = rx_buffer;
                chunk.end   = chunk.begin + Size;
            } else {
                // If chunk.begin != chunk.end, this means that there are still
                // some characters in the pipeline. Let us use them first.
            }

            // -- Copy buffer content into the analyzer's buffer
            chunk.begin = qlex.buffer_fill_region_append(chunk.begin, chunk.end);

            // -- Loop until the 'termination' token arrives
            while( 1 + 1 == 2 ) {
                const QUEX_TYPE_TOKEN_ID TokenID = qlex.receive();

                // TERMINATION => possible reload
                // BYE         => end of game
                if( TokenID == QUEX_TKN_TERMINATION ) break;
                if( TokenID == QUEX_TKN_BYE )         return 0;

                cout << "Consider: " << string(*token) << endl;
            }
        }
        return 0;
    }

Arbitrarily Chunked Input Frames
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

In case that frames can be broken *in between* syntactical entities, more
consideration is required. The fact that a pattern is matched does not
necessarily mean, that it is the 'winning' pattern. For example, the frame
at time '0'::

    frame[time=0]  [for name in print]

matches at the end ``print`` which might be a keyword. The lexical analyzer
will return a KEYWORD token followed by a TERMINATION token. Let the above
frame be continued as::

    frame[time=0]  [for name in print]
    frame[time=1]  [er_list: send file to name;]

which makes clear the actually the lexeme ``printer_list`` is to be matched.
To deal with such cases one look-ahead token is required. A token is only to be
considered, if the following token is not the TERMINATION token. If a
TERMINATION token is returned by the ``receive()`` function, then the border of
a frame has been reached. To match the last lexeme again after the appended
content, the input pointer must be reset to the beginning of the previous
lexeme. The procedure is demonstrated in detail in the following paragraphs.
The following code fragment shows all required variables and their initialization.

.. code-block:: cpp

    int
    main(int argc, char**) {
    
        quex::tiny_lexer  qlex((QUEX_TYPE_CHARACTER*)0x0, 0); 

        quex::Token    token_bank[2];     // Two tokens required, one for look-ahead
        quex::Token*   prev_token;        // Use pointers to swap quickly.

        QUEX_TYPE_CHARACTER*  rx_buffer = 0x0;  // A pointer to the receive buffer that
        //                                      // the messaging framework provides.

        MemoryChunk           chunk;      // Pointers to the memory positions under
        //                                // consideration.

        QUEX_TYPE_CHARACTER*  prev_lexeme_start_p = 0x0; // Store the start of the 
        //                                               // lexeme for possible 
        //                                               // backup.

        // -- initialize the token pointers
        prev_token = &(token_bank[1]);
        token_bank[0].set(QUEX_TKN_TERMINATION);
        qlex.token_p_swap(&token_bank[0]);

        //
        // -- trigger reload of memory
        chunk.begin = chunk.end;

Two token pointers are used to play the role of look-ahead alternatingly. The
tokens to which these pointers point are in the ``token_array``. The
current token id is set to ``TERMINATION`` to indicate that a reload
occurred. The loading of new frame content happens exactly the same way
as for syntactically chunked input frames.

.. code-block:: cpp
    
    while( 1 + 1 == 2 ) {
        if( chunk.begin == chunk.end ) {
            if( rx_buffer != 0x0 ) my_release(rx_buffer);
            const size_t  Size = my_receive(&rx_buffer);
            chunk.begin = rx_buffer;
            chunk.end   = chunk.begin + Size;
        } 

The inner analysis loop, though, differs because a look-ahead token
must be considered.

.. code-block:: cpp

        while( 1 + 1 == 2 ) {
            prev_lexeme_start_p = qlex.buffer_lexeme_start_pointer_get();
            
            // Let the previous token be the current token of the previous run.
            prev_token = qlex.token_p_swap(prev_token);

            const int TokenID = qlex.receive();

            // TERMINATION => possible reload
            // BYE         => end of game
            if( TokenID == QUEX_TKN_TERMINATION || TokenID == QUEX_TKN_BYE )
                break;

            // If the previous token was not a TERMINATION, it can be considered
            // by the syntactical analyzer (parser).
            if( prev_token->type_id() != QUEX_TKN_TERMINATION )
                cout << "Consider: " << string(*prev_token) << endl;
        }

At the beginning of the loop the lexeme position is stored, because it might be
needed to backup if a frame border is reached. The switch lets the
current token become the look-ahead token and the previous token becomes
the token to which the current token is to be stored. The end of the frame
is detected with the ``TERMINATION`` token. The end of the analysis is
triggered by some ``BYE`` token which must appear in the stream. Both
trigger a loop exit. If the current token (the 'look-ahead' token) is not a
``TERMINATION`` token, then the previous token can be considered by the parser.

The loop is exited either on 'end of frame' or 'end of analysis' as shown above.
If the end of a frame was reached, the position of the last lexeme needs to be 
setup. The handling of the loop exit is shown below.

.. code-block:: cpp

        // -- If the 'bye' token appeared, leave!
        if( current_token->type_id() == QUEX_TKN_BYE ) break;

        // -- Reset the input pointer, so that the last lexeme before TERMINATION
        //    enters the matching game again.
        qlex.buffer_read_pointer_set(prev_lexeme_start_p);
    }

.. warning::

    The procedure with one look-ahead token might fail in case that a pattern
    contains potentially a sequence of other patterns. Consider the mode

    .. code-block:: cpp

            mode {
                "le"       => QUEX_TKN_ARTICLE;
                "monde"    => QUEX_TKN_WORLD;
                " "        => QUEX_TKN_SPACE;
                "le monde" => QUEX_TKN_NEWSPAPER;
            }

    Where the begin of the ``NEWSPAPER`` pattern ``le`` can be made
    up of a sequence ``le``  (as ``ARTICLE``) and `` `` (as ``WHITESPACE``).
    Consider the frame sequence::

        frame[time=0] [le ]
        frame[time=1] [monde]

    When the first frame border is reached now, the longest complete match
    holds, which is ``le`` (``ARTICLE``) and the analysis continues with the ``  ``
    (``WHITESPACE``). Thus, ``WHITESPACE`` will be the last token before the
    TERMINATION token. The reconsideration triggered by the ``TERMINATION`` token
    is only concerned with the last token, i.e. ``WHITESPACE``, but does not go
    back to the start of ``le``.  Incidenceually, the token sequence will be:
    ``ARTICLE``, ``SPACE``, ``WORLD`` instead of a single token ``NEWSPAPER``
    which matches ``le monde``.
    
    A safe solution requires therefore *N* look-ahead tokens plus one, the
    current token. The *N* can be computed as the maximum number of
    sub-patterns into which a pattern in the analyzer might be broken down.
    The usual 'keyword'-'identifier' race can be solved with one look-ahead
    token as explained above in this section.

The complete code to do the analysis of arbitrarily chunked input frames is
shown below.

.. code-block:: cpp

    #include "tiny_lexer"
    #include "messaging-framework.h"

    typedef struct {
        QUEX_TYPE_CHARACTER* begin;
        QUEX_TYPE_CHARACTER* end;
    } MemoryChunk;

    int 
    main(int argc, char** argv) 
    {        
        using namespace std;

        quex::tiny_lexer  qlex((QUEX_TYPE_CHARACTER*)0x0, 0); 
        quex::Token       token_bank[2]; // 2 tokens--one for look-ahead
        quex::Token*      prev_token;    // Token swap helper.

        QUEX_TYPE_CHARACTER*  rx_buffer = 0x0;  // Pointer to receive buffer 
        //                                      // of messaging framework.
        MemoryChunk           chunk;  // Pointers indicating the range 
        //                            // of the content.
        QUEX_TYPE_CHARACTER*  prev_lexeme_start_p = 0x0; // Backup start of 
        //                                               // current lexeme.

        // -- initialize the token pointers
        prev_token = &(token_bank[1]);
        token_bank[0].set(QUEX_TKN_TERMINATION);
        qlex.token_p_swap(&token_bank[0]);

        // -- trigger reload of memory
        chunk.begin = chunk.end;

        // -- LOOP until 'bye' token arrives
        while( 1 + 1 == 2 ) {
            // -- Receive content from a messaging framework
            if( chunk.begin == chunk.end ) {
                // -- If receive buffer is read => release!
                if( rx_buffer != 0x0 ) my_release(rx_buffer);
                // -- Setup the pointers around the content
                const size_t Size  = my_receive(&rx_buffer);
                chunk.begin = rx_buffer;
                chunk.end   = chunk.begin + Size;
            }

            // -- Copy buffer content into the analyzer's buffer
            chunk.begin = qlex.buffer.fill(&qlex.buffer, chunk.begin, chunk.end);

            // -- Loop until the 'termination' token arrives
            QUEX_TYPE_TOKEN_ID token_id = 0;
            while( 1 + 1 == 2 ) {
                prev_lexeme_start_p = qlex.buffer_lexeme_start_pointer_get();
                
                // Previous token = current token of the previous run.
                prev_token = qlex.token_p_swap(prev_token);

                token_id = qlex.receive();

                // TERMINATION => possible reload
                // BYE         => end of game
                if( token_id == QUEX_TKN_TERMINATION ) break;
                if( token_id == QUEX_TKN_BYE )         return 0;

                // If the previous token was not a TERMINATION, it can 
                // be considered by the syntactical analyzer (parser).
                if( prev_token->type_id() != QUEX_TKN_TERMINATION )
                    cout << "Consider: " << string(*prev_token) << endl;
            }

            // -- If the 'bye' token appeared, leave!
            if( token_id == QUEX_TKN_BYE ) break;

            // -- Reset input pointer, 
            //    => Restart analysis from where it started before reload
            qlex.buffer_read_pointer_set(prev_lexeme_start_p);
        }

        return 0;
    }


.. _sec-filling:

Direct Filling
..............

Instead of copying the input, the memory of the lexical analyzer can be filled
directly. The address and size of the current region to be filled can be
accessed via the member functions:

.. code-block:: cpp

        QUEX_TYPE_CHARACTER*  buffer_fill_region_begin();
        QUEX_TYPE_CHARACTER*  buffer_fill_region_end();
        size_t                buffer_fill_region_size();

In order to get rid of content that has already been treated the function

.. code-block:: cpp

        qlex.buffer.fill_prepare(...);

must be called before filling. As in the Copying case, it moves used
content out of the buffer and, thus, creates space for new content. Finally,
after new content has been filled in, the analyzer must be informed
about the new 'end of memory'. This happens via a call to the
function

.. code-block:: cpp

        qlex.buffer.fill_region_finish(...);

The core of an analysis process based on direct filling looks like the
following:

.. code-block:: cpp

        // -- Initialize the filling of the fill region
        qlex.buffer_fill_region_prepare();

        // -- Call the low lever driver to fill the fill region
        size_t receive_n = receive_into_buffer(qlex.buffer_fill_region_begin(), 
                                               qlex.buffer_fill_region_size());

        // -- Inform the buffer about the number of loaded characters 
        //    NOT NUMBER OF BYTES!
        qlex.buffer.fill_region_finish(receive_n);

Note, that there is no ``chunk.begin`` information to be updated as in the
case of Copying. The remaining framework for syntactically chunked and arbitrary
chunked input is exactly the same as for the copying case. Source code examples
can be reviewed in the ``demo/010`` directory. 

.. _sec-pointing:

Pointing
........

The 'Pointing' method implies that the user *owns* the piece of memory which is
used by the lexical analyzer. A constructor call

.. code-block:: cpp

    quex::MyLexer   qlex((QUEX_TYPE_CHARACTER*)BeginOfMemory, 
                         MemorySize,
                         (QUEX_TYPE_CHARACTER*)EndOfContent); 

announces the memory to be used by the engine. Note, that the first position to
be written to must be ``BeginOfMemory + 1``, because the first element of
the memory is filled with the buffer limit code. The buffer can, but does
not have to, be filled initially. The third argument to the constructor
must tell the end of the content. If the buffer is empty at construction
time the end of content must point to ``BeginOfMemory + 1``. The meaning
of the arguments is again displayed in figure :ref:`fig-memory-pointing`.


.. _fig-memory-pointing:

.. figure:: ../figures/memory-pointing.* 
   
   User provided memory and its content.

It is conceivable that the user fills this very same memory chunk with new
content, so there must be a difference between the end of memory and the end of
the content. The end of memory is communicated with the argument ``MemorySize``
and the end of content via ``EndOfContent``.  When the content of the buffer is
filled a code fragment like

.. code-block:: cpp

    qlex.buffer_fill_region_finish(receive_n);
    qlex.buffer_read_pointer_set(BeginOfMemory + 1);

tells the analyzer about the number of characters that make up the content.
Also, it resets the input position to the start of the buffer.  Now, the
analysis may start. The file ``point.cpp`` in the ``demo/010`` directory
implements an example. 

.. note::

   The ``Pointing`` method is very seductive to be used in the context of
   hardware input buffers or shared memory. In such cases care is to be taken.
   The quex engine may put a terminating zero at the end of each a lexeme
   in order to facilitate the string processing. The definition of the 
   macro 

                QUEX_OPTION_TERMINATION_ZERO_DISABLED

   prevents this, but the buffer limit code must still be set at the borders
   or the end of the content.


Character Conversions
.....................

It is very well possible to do character set conversions combined with direct
buffer access. This enables the implementation command lines with UTF-8 encoding,
for example. To enable character set conversion, the constructor must receive
the name of the character set as the third argument, e.g.

    .. code-block:: cpp

        quex::MyLexer  qlex((QUEX_TYPE_CHARACTER*)0x0, 0, "UTF-8");

And the engine must be created with a converter flag (``--iconv`` or ``--icu``)
or one of the macros ``-DQUEX_OPTION_CONVERTER_ICONV`` or
``-DQUEX_OPTION_CONVERTER_ICU`` must be defined for compilation. Customized
converters might also be used (see section
                               :ref:`sec-customized-converters`). The
process of analysis is the same, except for one single line in the code.
Instead of appending plain content to the fill region it has to be
converted. The interface functions take 'byte' pointers, since it is
assumed that the input is raw. There are two possible cases:

#. The input is chunked arbitrarily and encoded characters might be cut at
   frame border. In this case, the function 

   .. code-block:: cpp

        buffer_fill_region_append_conversion(uint8_t* Begin, uint8_t* End);

    has to be used. This is the *safe* way of doing character conversion. The
    content from ``Begin`` to ``End`` is pasted into an internal raw buffer. So,
    incomplete characters 'wait' until the rest is pasted.

#. The input chunks never cut in between an encoded character.  In this case,
   the function

   .. code-block:: cpp

        uint8_t*
        buffer_fill_region_append_conversion_direct(uint8_t* Begin, uint8_t* End);

   might be used. It does not use an intermediate buffer that stocks
   incoming data. Thus, it is faster and uses less memory. The raw 
   buffer size of the converter can be set to zero, i.e. you
   can compile with ``-DQUEX_SETTING_TRANSLATION_BUFFER_SIZE=0``.

   The returned pointer corresponds to what has been said about the previous
   function.

   This function is only to be used in case of 100% certainty that input frames
   only contain complete characters.

The two mentioned functions above are for the handling via 'copying'. On the 
other hand it is possible to use conversion with direct filling. Correspondent
to the functions introduced in :ref:`Filling`, the following function group
allows to fill the conversion buffer directly and perform the conversions.

   .. code-block:: cpp

        void       buffer_conversion_fill_region_prepare(); 
        uint8_t*   buffer_conversion_fill_region_begin();
        uint8_t*   buffer_conversion_fill_region_end();
        size_t     buffer_conversion_fill_region_size();
        void       buffer_conversion_fill_region_finish(const size_t ByteN);

The functions work on ``uint8_t`` data, i.e. 'bytes' rather than
``QUEX_TYPE_CHARACTER``.  The interact directly with the 'raw' buffer on
which the converter works.

For all three methods, there a sample applications in the ``demo/010``
directory.

.. rubric:: Footnotes

.. [#f1] Backward navigation may appear due to calls to ``seek()``, but also when pre-conditions require a
         backward lexical analysis (see :ref:`sec-pre-and-post-conditions`). 

