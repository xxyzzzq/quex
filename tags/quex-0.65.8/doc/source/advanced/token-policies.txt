.. _sec-token-policies:

Token Passing Policies
======================

This section discusses how the generated analyzer communicates its results to
its user.  The primary result result of a lexical analysis step is a so called
'token identifier', that tells how the current input can be catagorized, e.g.
as a 'KEYWORD', a 'NUMBER', or an 'IP_ADDRESS'. Additionally some information
about the actual stream content might have to be stored. For example when a
'STRING' is identified the content of the string might be interesting for the
caller of the lexical analyzer. This basic information needs to be passed to
the user of the lexical analyzer. Token passing in quex can be characterized by 

  .. describe:: Memory managements 
  
     Memory management of the token or token queue can be either be
     accomplished by the analyzer engine or by the user.

     By default the analyzer engine takes over memory management for the token
     or token queue. Also, it calls constructors and destructors as required.

  .. describe:: Token passing policy
 
     Possible policies are 'queue' and 'single'.  Tokens can be stored in a
     *queue* to be able to produce more than one token per analysis step. If
     this is not required a *single* token instance may be used to communicate
     analysis results.

     The default policy is 'queue' since it is the easiest and safest to handle
     during analysis and incidence handlers.

The following two sections discuss automatic and user controlled token memory
management separately. For each memory management type the two token passing
policies 'single' and 'queue' are described.


Automatic Token Memory Management
---------------------------------

Automatic token memory management is active by default. It relieves the user
from anything related to memory management of the internal token or token
queues. It is the seamless nature which makes it possible to introduce the
concepts of token passing policies without much distractive comments. 


Queue
.....

The default token policy is 'queue'. Explicitly it can be activated
via the command line option ``--token-policy``, i.e.::

   > quex ... --token-policy queue ...

This policy is the safe choice and requires a minimum of programming effort.
It has the following advantages:

   * Using a token queue enables the sending of multiple
     tokens as response to a single pattern match. 
      
   * The incidences ``on_entry``, ``on_exit``, and ``on_indentation`` 
     can be used without much consideration of what happens to the 
     tokens. 
      
   * Multiple pattern matches can be performed without 
     returning from the lexical analyzer function.

However, there is a significant drawback:

   * The state of the analyzer is not syncronized with the currently 
     reported token, but with the token currently on top of the queue.

A direct consequence of this is that parameters like line number, stream
position etc.  must be stored inside the token at the time it is created, i.e.
inside the pattern action (see :ref:`sec-token-stamping`). For the above
reason, the line number reported by the analyzer is not necessarily the line
number of the token which is currently taken from the queue.

Figure :ref:`fig-token-queue` shows the mechanism of the token queue policy.
The lexical analyzer fills the tokens in the queue and is only limited by the
queue's size. The user maintains a pointer to the currently considered token
``token_p``. As a result to the call to 'receive()' this pointer bent so that
it points to the next token to be considered. The receive function itself
does the following:

   * if there are tokens left inside the queue, it returns a pointer
     to the next token.

   * if not, then a call to the analyzer function is performed. The analyzer
     function fills some tokens in the queue, and the first token from the queue
     is returned to the user. 

An application that applies a 'queue' token policy needs to implement
a code fragment like the following

.. code-block:: cpp

    QUEX_TYPE_TOKEN*  token_p = 0x0; 
    ...
    while( analysis ) {
        lexer.receive(&token_p);
        ...
        if( content_is_important_f ) {
            safe_token = new QUEX_TYPE_TOKEN(*token_p);
        }
    }

All tokens primarily live inside the analyzer's token queue and the user
only owns a reference to a token object ``token_p``. The next call to
'receive()' may potentially overwrite the content to which ``token_p`` points.
Thus, if the content of the token is of interest for a longer term, then it
must be stored safely away.

.. note:: The usage of ``malloc`` or ``new`` to allocate memory for 
          each token may have a major influence on performance. Consider
          a memory pool instead, which is allocated at once and which
          is able to provide token objects quickly without interaction
          with the operating system.

The size of the token queue is constant during run-time. Quex generates the size
based on the the command line option ``--token-queue-size``. An overflow of the
queue is prevented since the analyser returns as soon as the queue is full. 

Then the ``--token-queue-safety-border`` command line flag allows to define a
safety region. Now, the analyzer returns as soon as the remaining free places
in the queue are less then the specified number. This ensures that for each
analysis step there is a minimum of places in the queue to which it can write
tokens. In other words, the safety-border corresponds to the maximum number of
tokens send as reaction to a pattern match, including indentation incidences and
mode transitions.  

For low level interaction with the token queue the following functions are
provided

   .. code-block:: cpp

      bool   token_queue_is_empty();
      void   token_queue_remainder_get(QUEX_TYPE_TOKEN**  begin_p, 
                                       QUEX_TYPE_TOKEN**  end_p);

The first function informs tells whether there are tokens in the queue. The
second function empties the queue. Two pointers as first and second argument
must be provided. At function return, the pointers will point to the begin and
end of the list of remaining tokens. Again, end means the first token after the
last token. Note, that the content from ``begin`` to ``end`` may be overwritten
at the next call to receive(). The following code fragment displays the usage 
of this function:

    QUEX_TYPE_TOKEN*  iterator = 0x0; 
    QUEX_TYPE_TOKEN*  begin_p  = 0x0;
    QUEX_TYPE_TOKEN*  end_p    = 0;
    ...
    while( analysis ) {
        qlex.receive(&iterator);
        if( content_is_important_f ) {
            store_away(iterator);
        }

        token_queue_take_remainder(&iterator; &end_p);
        while( iterator != end_p ) {
            ...
            if( content_is_important_f ) {
                store_away(iterator);
            }
            ++iterator;
        }
    }

Such a setup may be helpful if the lexical analyzer and the parse run in two
different threads. Then the token tokens that are communicated between the
threads could be copied in greater chunks. 


Single
......

The policy 'single' is an alternative to the 'queue' policy. Explicitly it can
be activated via the command line option ``--token-policy single``, i.e.::

   > quex ... --token-policy single ...

The advantages of a token queue are all lost, i.e. 

   -- No more than one token can be sent per pattern match.
   
   -- Incidence handlers better not send any token or it must be sure
      that the surrounding patterns do not send token.

   -- Only one pattern match can be performed per call to the analyzer
      function. The usage of ``CONTINUE`` in a pattern action is 
      generally not advisable.

On the other hand, there is a major advantage:

   -- The state of the analyzer conforms to the currently reported
      token.

Thus, line numbers stream positions and even the current lexeme can be
determined from outside the analyzer function. The analyzer function does not
have to send a whole token. Actually, it is only required to send a token id.
This token id is the functions return value and, with most compilers, stored in
a CPU register. Since only one token object is stored inside the analyzer the data
locality is improved and cache misses are less probable.  The token passing
policy 'single' is designed to support a minimal setup, which may 
improve the performance of an analyzer.

.. note:: Even with the token passing policy 'single' the ability to send
          multiple repeated tokens (using ``self_send_n()``) at the same time 
          remains intact. The repetition is implemented via a repetition counter
          not by duplication of tokens.

In contrast to the policy 'queue' a with 'single' the call to ``receive()``
does not bend any token pointer to a current token. Instead, the one 
token inside the analyzer can be referred to once. The receive function
returns only the token id as a basis for later analysis. If necessary, the
application may rely on the token's content by dereferencing the pointer
at any time. A code fragment for policy 'single' is shown below:

.. code-block:: cpp

    QUEX_TYPE_TOKEN*  token_p = 0x0; 
    ...
    token_p = qlex.token_p();
    ...
    while( analysis ) {
        token_id = qlex.receive();
        ...
        if( content_is_important_f ) {
            safe_token = new QUEX_TYPE_TOKEN(*token_p);
        }
    }

Again, the next call to ``receive()`` may overwrite the content of the token.
If it is needed on a longer term, then it must be copied to a safe place.

Note, that the function signature for the receive functions in 'queue' and 'single'
are incompatible. The receive function for 'queue' has the following signature

.. code-block:: cpp

    void  receive(QUEX_TYPE_TOKEN**);  // 'queue' bends a pointer

where the signature in case of token passing policy 'single' is

.. code-block:: cpp

    QUEX_TYPE_TOKEN_ID  receive();     // 'single' only reports token id

This choice has been made so that user code breaks if the token policy is switched.
Both policies require a different handling and a compile error forces the user
to rethink his strategy[#f1]_.  It is expected that the compiler reacts to a
mismatching function call by pointing to a location where a matching candidate
can be found. At this location, the user will find a hint that the token policy
is not appropriate. 


User Controlled Token Memory Management
---------------------------------------

The previous discussion has revealed a major drawback in automatic token memory
management: Whenever the content of a token is of interest for a longer term,
it must be copied. This could be spared, if the lexical analyzer is told
were to write the token information. When an analysis step is done the user
takes the pointer to the finished token, and provides the analyzer with a
pointer to an empty token.  This token-switching  reduces the need for
memory allocation and disposes the need of copying. As a disadvantage, the
user is now responsible for allocating and freeing of memory, as well as
constructing and destructing of the involved tokens. User controlled memory
management is activated via the command line option
``--token-memory-management-by-user``, or ``--tmmbu``, i.e. quex has to 
be called with::

   > quex ... --token-memory-management-by-user ...

The following paragraphs will first discuss the 'single' token passing policy
and then 'queue', because it is straight forward for the former and a little
more involved for the later. The function signatures for both policies 
remain the same as with automatic token memory management. Depending whether
the received token is of interest, the token inside the analyzer can be 
switched with the new token. This can be done by the functions

.. code-block:: cpp

    void              token_p_set(QUEX_TYPE_TOKEN*);

The first function only sets a new token. The currently set token pointer
is overwritten. This is dangerous, since one might loose the reference
to an allocated object. To avoid this the current token pointer can be
read out using 

.. code-block:: cpp

    QUEX_TYPE_TOKEN*  token_p();
    
To do the read-out and set operation in one step the function 

.. code-block:: cpp

    QUEX_TYPE_TOKEN*  token_p_swap(QUEX_TYPE_TOKEN*);

is provided. It returns the a pointer to the currently set token inside the
analyzer and sets the token pointer to what is provided as a second argument.
It must point to a constructed, token object.  A typical code fragment for this
scenerio looks like

.. code-block:: cpp

    QUEX_TYPE_TOKEN  token_bank[2]; 
    QUEX_TYPE_TOKEN* token_p = &token_bank[1];
    ...
    lexer.set_token_p(&token_bank[0]);
    ...
    while( analysis ) {
        /* call to receive(...) switches token pointer */
        token_id = lexer.receive();
        ...
        if( content_is_important_f ) {
            store_away(lexer.token_p_swap(get_new_token());
        }
    }

The idea of 'switching the thing on which the analyzer writes' can also be
applied to the 'queue' token passing policy. The user provides a chunk of
allocated and constructed tokens. The receive function fills this token queue
during the call to ``receive``. If the token queue is of interest, it can be taken
out and the lexer gets a new, ready-to-rumble token queue. This actions 
can be take by means of the functions

.. code-block:: cpp

       void  token_queue_get(QUEX_TYPE_TOKEN** begin, size_t* size);
       void  token_queue_set(QUEX_TYPE_TOKEN* Begin, size_t Size);
       void  token_queue_swap(QUEX_TYPE_TOKEN** queue, 
                                size_t*           size); 


The following code fragment displays a sample application of this approach:

.. code-block:: cpp

    QUEX_TYPE_TOKEN*  iterator   = 0x0; 
    QUEX_TYPE_TOKEN*  queue      = 0x0;
    size_t            queue_size = (size_t)16;
    ...
    queue = get_new_token_queue(queue_size);
    qlex.token_queue_set(queue, queue_size);
    ...
    while( analysis ) {
        iterator    = qlex.receive();
        /* consider the first token, the remainder is in the queue.
        ...
        qlex.token_queue_swap(&queue);

        /* Manual iteration over received token queue */
        for(iterator = queue; iterator != queue_watermark ; ++iterator) {
            ...
            if( content_is_important_f ) {
                store_away(iterator);
            }
        }
    }


Token Construction and Destruction
..................................

As mentioned for user token memory management, the user owns the token's memory
and is responsible for construction and destruction.  In C++ construction and
destruction happen implicitly, when on calls the ``new`` and ``delete``
operator, or if one defines a local variable and this variable runs out of
scope, e.g.

.. code-block:: cpp

   QUEX_TYPE_TOKEN*   queue = QUEX_TYPE_TOKEN[16];

allocates space for 16 tokens, and calls their constructors. A call to delete,
e.g.

.. code-block:: cpp

   delete [] queue;

invoques the token destructor and deletes all related memory. In C, however,
construction and destruction must happen by hand, i.e.

.. code-block:: cpp

   QUEX_TYPE_TOKEN*   queue = (QUEX_TYPE_TOKEN*)malloc(sizeof(QUEX_TYPE_TOKEN) * 16);

   for(iterator = queue; iterator != queue QueueSize; ++iterator) 
       QUEX_NAME_TOKEN(construct)(iterator);

and 
     
.. code-block:: cpp

   for(iterator = queue; iterator != queue QueueSize; ++iterator) 
       QUEX_NAME_TOKEN(destruct)(iterator);

   free(queue);


Remark on Token Passing
-----------------------

The user initiates an analysis step by his call to ``.receive()``. The analyzer
tries to make sense out of the following sequence of characters, i.e.
characterizes it as being a number, a keyword, etc. The character sequence that
constitutes the pattern, i.e. the lexeme, has a begin and an end. Now, comes
the point where this information has to be passed to the caller of
``.receive()`` through a token.

.. note:: 

   The concept of a 'token' is that of a container that carries some
   information from the analyzer to the user. No tokens shall be allocated
   in a pattern action. During analysis it is only filled, not created, and when
   ``receive()`` returns the user reads it what is in it. 
  
   Token allocation, construction, destruction, and deallocation is either
   done by the analyzer itself (default automatic token memory management), 
   or by the caller of ``.receive()`` (user token memory management). It
   is not element of an analyzer step.

Token passing is something with happens notoriously often, and thus it is
crucial for the performance of the lexical analyzer. During the pattern-match
action the lexeme is referred to by means of a character pointer. This pointer
is safe, as long as no buffer reload happens. Buffer reloads are triggered 
by analysis steps. Depending on the token passing policy, the lexeme pointer 
is safe to be used without copying:

 .. describe:: Single

    The pointer to the lexeme is safe from the moment that it is provided in
    the matching pattern action and while the function returns from
    ``receive()``. When ``receive()`` is called the next time, a buffer reload
    may happen. If string to which the lexeme pointer points is important, then
    it must be copied before this next call to receive.

    .. note:: When ``CONTINUE`` is used, this initiates an analysis step
              during which a buffer reload may happen.


 .. describe:: Queue

    As with 'single', a lexeme pointer must be copied away before the next
    call to ``receive()``. However, potentially multiple tokens are sent,
    and analysis continues after a pattern has matched, then the lexeme
    pointer may be invalid after each step.

The default token implementation ensures, that the lexeme is stored away
in  safe place, during the pattern match action. However, for things that
can be interpreted, such as numbers it may be advantageous to interpret
them directly and store only the result inside the token. 

The above mentioned copy operations are done, because the buffer content
*might* change while the lexeme content is of interest. A very sophisticated
management of lexemes triggers on the actual buffer content change and
safes all trailing lexemes at on single beat into a safe place. This is
possible by registering a callback on buffer content change. The 
function to do this is

.. code-block:: cpp

    void  set_callback_on_buffer_content_change(
                void (*callback)(QUEX_TYPE_CHARACTER* ContentBegin, 
                                 QUEX_TYPE_CHARACTER* ContentEnd));

As long as the provided callback is not called, all lexeme pointers 
are safe. If the callback is called, then the current buffer content
is overwritten and thus all related lexeme pointers will be invalid. 
To help with the decision which lexemes need to be stored away, the
callback is called with pointers to the begin and end of the related
content.

Summary
-------

Token policies enable a fine grain adaption of the lexical analyzer. They
differ in their efficiency in terms of computation speed and memory
consumption. Which particular policy is preferable depends on the particular
application. Token queues are easier to handle since no care has to be 
taken about tokens being sent from inside incidence handlers and multiple tokens
can be sent from inside a single action without much worries. Token queues
require a little more memory and a little more computation time than 
single tokens. Token queue can reduce the number of function calls since
the analysis can continue without returning until the queue is filled.
Nevertheless, only benchmark tests can produce quantitative statements
about which policy is preferable for a particular application.

.. note:: 

   The implicit repetition of tokens is available for both policies.  That is,
   ``self_send_n()`` is always available. The requirement that a multiple same
   tokens may be sent repeatedly does *not* imply that a token queue policy must be
   used.

.. rubric:: Footnotes

   [#f1] Previous designs where both setups compiled for both policies had
   let to wrong and confusing results; and only in depth analysis revealed the
   inappropriate token policy being applied. 

