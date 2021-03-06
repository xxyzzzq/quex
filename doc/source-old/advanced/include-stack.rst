.. _sec-include-stack:

Include Stack
=============

A useful feature of many programming languages is the ability to *include*
files into a file. It has the effect that the content of the included file is
treated as if it is pasted into the including file. For example, let
``my_header.h`` be a 'C' file with the content

.. code-block:: cpp

   #define TEXT_WIDTH 80
   typedef short      my_size_t;

Then, a C-file ``main.c`` containing

.. code-block:: cpp
   
   /* (C) 2009 Someone */
   #include "my_header.h"
   int main(int argc, char** argv)
   {
       ...
   }

produces the same token sequence as the following code fragment where
``my_header.h`` is pasted into ``main.c`` 

.. code-block:: cpp

   /* (C) 2009 Someone */
   #define WIDTH 80
   typedef short my_size_t;

   int main(int argc, char** argv)
   {
       ...
   }

What happens internally is that the following:

   1. An ``#include`` statement is found.
   2. The analyzer switches to the included file
   3. Analyzis continues in the included file until 'End of File'.
   4. The analyzer switches back to the including file and continues
      the analyzes after the ``#include`` statement.

The ability to include files prevents users from writing the same code
multiple times.  Moreover, it supports centralized organization of the code.
Scripts or configurations that are referred to in many files can be put into a
central place that is maintained by trustworthy personal ensuring robustness of
the overall configuration. The advantages of the simple ``include`` feature are
many. In this section it is described how quex supports the inclusion of files.

.. _fig-include-stack-example:

.. figure:: ../figures/include-stack-sdedit.*

   Inclusion of content from other files.

Figure :ref:`fig-include-stack-example` shows what happens behind the scenes.
The lexical analyzer first reads the file ``main.c`` until it hits on an
include statement. This statement tells it to read the content of file
``my_header.h`` and then continue again with the remainder of ``main.c``. In
order to do this the lexical analyzer needs to store his state-relevant variables [#f1]_
in a so called *memento* [#f2]_. When the analysis of ``my_header.h``
terminates on 'end of file' the memento can be unpacked and the old state
revived. The analysis can continue in the file ``main.c``. 

.. _fig-include-stack-N-example:

.. figure:: ../figures/include-stack-N-sdedit.*

   Recursive inclusion of files.

If an included file includes another file, then the memento needs to know that
there is some 'parent'. Thus the chain of mementos acts like a stack where the
last memento put onto it is the first to be popped from it. An example is shown
in figure :ref:`fig-include-stack-N-example` where a file A includes a file B
which includes a file C which includes a file D. Whenever a file returns the correct
memento is unpacked and the lexical analyzer can continue in the including file.
The mementos are lined up as a list linked by 'parent' pointers as shown
in :ref:`List of Mementos <fig-memento-queue>`. The parent pointers are required
to find the state of the including file on return from the included file.

.. _fig-memento-queue:

.. figure:: ../figures/memento-queue.*

   List of Mementos implementing the Include Stack.

The task of packing the generated analyzer state into a memento and putting
the memento on the include stack is done by the ``include_push`` function
group. Such a function needs to be called upon the detection of a 'include' keyword
in the input stream. When the include files ends, the ``include_pop`` function
needs to be called. The packing and unpacking of mementos can be adapted
by the specification of 'memento_pack' and 'memento_unpack' handlers. A complete
include procedure looks as follows.

    # An 'include' keyword token and the input specification is detected in an 
      input source A.

    # A ``include_push`` function is called that opens the input source B and packs
      the analyzers state into a memento.

    # The user's dedicated ``memento_pack`` section is executed.

    # The memento is put on the stack.

    # Lexical analysis continues from the beginning of the included input source B.

    # The memento is taken from the stack and the previous analyzer state is
      restored.

    # The user's ``memento_unpack`` is executed.

    # Lexical analysis continues in input A right after where the 'include' was
      triggered.

The complete include-push function group in C++ consists of the following list:

.. code-block::cpp

    bool include_push(const char* FileName, CodecName)

    bool include_push(const char* InputName, FILE*, CodecName); 
    bool include_push(const char* InputName, std::istream*, CodecName);      
    bool include_push(const char* InputName, std::wistream*, CodecName);    

    bool include_push(const char* InputName, 
                      ByteLoader* byte_loader, 
                      const char* CodecName = 0x0);

    bool include_push(const char* InputName, 
                      QUEX_NAME(LexatomLoader)*  filler); 

    bool include_push(const char* InputName, 
                      QUEX_TYPE_LEXATOM* BufferMemoryBegin, 
                      size_t               BufferMemorySize,
                      QUEX_TYPE_LEXATOM* BufferEndOfContentP);  

The corresponding C API is the following.

.. code-block::cpp

    bool QUEX_NAME(include_push_file_name)(QUEX_TYPE_ANALYZER*,
                                           const char* FileName, CodecName)

    bool QUEX_NAME(include_push_FILE(QUEX_TYPE_ANALYZER*,
                                     const char* InputName, 
                                     FILE*, CodecName); 

    bool QUEX_NAME(include_push_ByteLoader)(QUEX_TYPE_ANALYZER*,
                                            const char* InputName, 
                                            ByteLoader* byte_loader, 
                                            const char* CodecName = 0x0);

    bool QUEX_NAME(include_push_LexatomLoader)(QUEX_TYPE_ANALYZER*,
                                              const char* InputName, 
                                              QUEX_NAME(LexatomLoader)*  filler); 

    bool QUEX_NAME(include_push_memory)(QUEX_TYPE_ANALYZER*,
                                        const char*          InputName, 
                                        QUEX_TYPE_LEXATOM* BufferMemoryBegin, 
                                        size_t               BufferMemorySize,
                                        QUEX_TYPE_LEXATOM* BufferEndOfContentP);  

Notably, all functions take an input name as the first argument. When a file
name is provided it automatically identifies the input source. In all other
cases the user should provide a unique name of the input. The input name may be
used internally for infinite recursion detection. If this is not an issue the
input name can be passed as ``NULL`` or any meaningless string. 

The include-push functions return a verdict that tells whether the initiation
of the inclusion was successful. If a function returns ``false`` it may be
necessary to free any resource that was allocated and passed as an arguments.
If it returns ``true`` the resources are used for analysis. Then, the 
resources must only be freed upon the termination of the included input. This
is the moment where the 'on_end_of_stream' is invoked. Any resource that
is implicitly allocated by the include-push functions is automatically freed 
upon the return to the including file. To trigger the proper return the 
include-pop function needs to be called, i.e. the member function

.. cfunction:: bool  include_pop()

in C++, or in C

.. cfunction:: bool  QUEX_NAME(include_pop)(QUEX_TYPE_ANALYZER*)

This function unpacks a memento from the stack and puts the analyzer in the state in
which it was before the inclusion. The return values of this function are

.. data:: true

  if there was a memento and the old state was restored.

.. data:: false

  if there was no memento. The analyzer is in the root of all files. The most
  appropriate reaction to this return value is to stop analysis--at least for
  the given file.


.. note:: 

   If the analyzer object has been constructed with another constructor than
   the 'from-file-name' constructor, then the input name can still be specified
   manually by calling directly after construction the member function

   .. code-block:: cpp

      void set_input_name(const char*);

   or, respectively 

   .. code-block:: cpp

      void QUEX_NAME(set_input_name)(QUEX_TYPE_ANALYZER*, 
                                     const char*);

   This way the input name of the original input is determined.
   

.. note::

   The ownership of the provided input name remainsat the user. The user is
   responsible that it remains allocated from the time of inclusion until the
   inclusion ends.

Example
-------

In this section, an example usage is shown where white space per file is
counted.  The sections or mementos, namely ``memento``, ``memento_pack``, and
``memento_unpack`` are already explained in :ref:`sec-basics-sections`.  Let
the variable to count white space in each file be part of the lexical analyzer
object using the global ``body`` section to declare a new member, ``init``
to extend the constructor, and ``memento`` to extend the memento class.::

    body {
        int   white space_count;
    }
    init {
        white space_count = 0;
    }
    memento {
        int   white space_count;
    }

Let the pattern to include content from another file be the C-like ``#inlude "file"``
pattern. That is, for the mode that detects inclusion, there must be a pattern-action
pair such as shown below.

.. code-block::cpp

   mode X {
       ...

       "#include"[ ]*\"[^\"]+\" {
             const char* file_name;
             int         length = extract_include_file_name(Lexeme, &file_name);
             if( ! length ) RETURN;
             self.include_push(file_name);
       }

       ...
   }

The ``include_push`` call with the given file name will try to open the file,
create a byte loader and buffer filler and pack the engine's state into a 
memento. Then, the user's memento packer is called. It is defined in thea
global section ``memento_pack``.::

  memento_pack {
      /* Error Detection */
      if( self.include_detect_recursion(InputName) ) {
          error_on_recursive_inclusion(InputName, self._parent_memento);
          return false;
      }

      /* Packing */
      memento->white space_count = self.white space_count;

      /* Re-Initialize packed variables! */
      this->white space_count = 0;
      return true;
  }

Memento packing consists of three main actions: *error detection*, *packing*,
and *re-initialization*.  To prevent infinite recursion the member function
``include_detect_recursion`` is called.  An error initiates the return of
``false`` which would trigger the include-push function to signalize that the
inclusion failed.  The packing, in this example is implemented by storing the
current white space count in the memento object. White space counting is file
local so it make sense to re-initialize the counter to zero when a new file is
included.  

When the included file ends, the engine's state must be restored as it was
before the file was included. This is done by a 'include-pop' in the
end-of-stream handler. ::

   mode X {
       ...

        on_end_of_stream {
           if( self.include_pop() ) RETURN;
           /* Send an empty lexeme to overwrite token content. */
           self_send1(QUEX_TKN_TERMINATION, LexemeNull);
        }

       ...
   }

The member function ``include_pop`` takes the last memento from the stack and
restores the analyzer state. All objects that where created internally are
destructed and deleted. When include pop returns ``false`` it signalizes that
there was no including file. In other words, the end-of-stream event appeared
in the original stream. Thus, the ``TERMINATION`` token can be send. Upon 
normal return from an included file or stream the analyzer must restore also
the user's extra content. This is done in the memento unpacker.::

    memento_unpack {
        this->white space_count = memento->white space_count;
    }

With this behavior, it is now safe to assume that the white space count happens
per file basis. When a file is included the current white space is stored away
and counting starts from zero with the new file. When the included file ends,
the old white space count is restored and continues from where it left.


.. _sec-include-stack-howto:

HOWTO
-----

There are two basic ways to handle the inclusion of files during analysis.
First, files can be included from within analyzer actions, i.e. as consequence
of a pattern match or an incidence. Second, they can be included from outside when
the ``.receive(...)`` function returns some user define ``INCLUDE`` token.  If
the token policy ``users_token`` is used there is no problem with the second
solution. Nevertheless, the first solution is more straightforward, causes less
code fragmentation and involves less complexity. This section explains how to
do include handling by means of analyzer actions, i.e. from 'inside'.  The
second solution is mentioned in the :ref:`Caveats <sec-include-stack-caveat>`
section at the end of this chapter.

The 'usual' case in a programming language is that there is some keyword
triggering a file inclusion, plus a string that identifies the stream
to be included, e.g. ::

    \input{math.tex}

or::

    include header.txt

The include pattern, i.e. ``\input`` or ``include`` triggers the 
inclusion. But, when it triggers the file name is not yet present. One
cannot trigger a file inclusion whenever a string matches, since it
may also occur in other expressions. This is a case for a dedicated
mode to be entered when the include pattern triggers. This dedicated
mode triggers an inclusion as soon as a string came in. In practical
this looks like this:

.. code-block:: cpp

    mode MAIN : BASE
    {
        "include"       => GOSUB(OPEN_INCLUDED_FILE); 
        [_a-zA-Z0-9.]+  => QUEX_TKN_IDENTIFIER(Lexeme); 
        [ \t\r\n]+      {}
    }

When the trigger ``include`` matches in mode ``MAIN``, then it transits into
mode ``OPEN_INCLUDED_FILE``. It handles strings differently from the ``MAIN``
mode. Its string handling includes an ``include_push`` when the string has
matched.  Notice, that mode ``MAIN`` is derived from ``BASE`` which is to be
discussed later on. The mode ``OPEN_INCLUDED_FILE`` is defined as

.. code-block:: cpp

    mode OPEN_INCLUDED_FILE : BASE 
    {
        [a-zA-Z0-9_.]+ { 
            /* We want to be revived in 'MAIN' mode, so pop it up before freezing. */
            self.pop_mode();
            /* Freeze the lexer state */
            self.include_push<std::ifstream>(Lexeme);
        }

        . { 
            printf("Missing file name after 'include'.");
            exit(-1);
        }
    }

As soon as a filename is matched the previous mode is popped from the mode
stack, and then the analyzer state is packed into a memento using the function
``include_push``. The memento will provide an object of class ``ifstream``, so
it has to be told via the template parameter. The default match of this mode
simply tells that no file name has been found. When the included file
hits the end-of-file, one needs to return to the including file. This
is done using the ``include_pop`` function. And, here comes the ``BASE``
mode that all modes implement: 

.. code-block:: cpp

    mode BASE {
        <<EOF>> { 
           if( self.include_pop() ) return;
           /* Send an empty lexeme to overwrite token content. */
           self_send1(QUEX_TKN_TERMINATION, LexemeNull);
           return;
        }

        [ \t\r\n]+  { }
    }

The ``include_pop()`` function returns ``true`` if there was actually a file
from which one had to return. It returns ``false``, if not. In the latter case
we reached the 'end-of-file' of the root file. So, the lexical analysis is over
and the ``TERMINATION`` token can be sent. This is all to say about the
framework.  We can now step on to defining the actions for packing an unpacking
mementos. First, let the memento be extended to carry a stream handle:

.. code-block:: cpp

    memento {
        std::ifstream*  included_sh;
    }

When the analyzer state is frozen and a new input stream is initialized, the
``memento_pack`` section is executed. It must provide an input handle in the
variable ``input_handle`` and receives the name of the input as a
``QUEX_TYPE_LEXATOM`` string. The memento packer takes responsibility over
the memory management of the stream handle, so it stores it in ``included_sh``.

.. code-block:: cpp

    memento_pack {
        *input_handle = new std::ifstream((const char*)InputName, std::ios::binary);

        if( (*input_handle)->fail() ) {
            delete *input_handle;
            return 0x0;
        }
        memento->included_sh = *input_handle;
    }

.. note:: If ``*input_handle`` points to something different from ``0x0`` this
          means that the ``include_push`` has already provided the input handle
          and it must not be made available by the ``memento_pack`` section.

At the time that the analyzer state is restored, the input stream must be closed
and the stream object must be deleted. This happens in the ``memento_unpack`` section

.. code-block:: cpp

    memento_unpack {
        memento->included_sh->close();
        delete (memento->included_sh);
    }

The closing of the stream needs to happen in the ``memento_unpack`` section.
The analyzer cannot do it on its own for a very simple reason: not every input
handle provides a 'close' functionality. Symetrically to the ``memento_pack``
section where the input handle is created, it is deleted in the
``memento_unpack`` section, when the inclusion is terminated and the analyzer
state is restored.

TODO: Note about the filename which is in the buffer but should be better
      stored in a safe place.

Infinite Recursion Protection
-----------------------------

When a file is included, this happens from the beginning of the file. But, what
happens if a file includes itself? The answer is that the lexical analyzer
keeps including this file over and over again, i.e. in hangs in an *infinite
recursion*. If there is no terminating condition specified by the implementer,
then at some point in time the system on which it executes runs out of
resources and terminates after its fancy.

The case that a file includes itself is easily detectable. But the same 
mentioned scenario evolves if some file in the include chain is included 
twice, e.g. file A includes B which includes C which includes D which includes E
which includes F which includes G which includes C. In this case the analyzer
would loop over the files C, D, E, F, G over and over again.

Quex does not make any assumptions about what is actually included. It may be a
file in the file system accessed by a ``FILE`` pointer or ``ifstream`` object,
or it may be a stream coming from a specific port. Nevertheless, the
solution to the above problem is fairly simple: Detect whether the current
thing to be included is in the chain that includes it. This can be done by
iteration over the memento chain. The member ``stream_id`` in figure
:ref:`fig-memento-queue` is a placeholder for something that identifies an
input stream. For example let it be the name of the included file. Then,
the memento class extension must contain its definition

.. code-block:: cpp

   memento {
       ...
       std::string   file_name; // ... is more intuitive than 'stream_id'
       ...
   }

The lexical analyzer needs to contain the filename of the root
file, thus the analyzer's class body must be extended.

.. code-block:: cpp

    body {
        ...
        std::string   file_name;
        ...
    }

Then, at each inclusion it must be iterated over all including files, i.e.
the preceding mementos. The first memento, i.e. the root file has a
parent pointer of ``0x0`` which provides the loop termination condition.

.. code-block:: cpp

    ...
    MyLexer  my_lexer("example.txt");
    my_lexer.file_name = "example.txt";
    ...

.. code-block:: cpp

    memento_pack {
        /* Detect infinite recursion, i.e. re-occurence of file name           */
        for(MyLexerMemento* iterator = my_analyzer._memento_parent;
            iterator ; iterator = iterator->parent ) {
            /* Check whether the current file name already appears in the chain */
            if( iterator->file_name == (const char*)InputName ) {
                REACTION_ON_INFINITE_RECURSION(Filename);
            }
        }
        /* Open the file and include */
        FILE*  fh = open((const char*)InputName, "rb");
        if( fh == NULL ) MY_REACTION_ON_FILE_NOT_FOUND(Filename);

        /* Set the filename, so that it is available, in case that further
         * inclusion is triggered.                                             */

        memento->file_name = self.file_name;
        self.file_name     = (const char*)InputName;
    }

All that remains is to reset the filename on return from the included file. Here is
the correspondent ``memento_unpack`` section:

.. code-block:: cpp

   memento_unpack {
       ...
       self.file_name = memento->file_name;
       ...
   }

.. note:: 

   Do not be surprised if the ``memento_unpack`` handler is called upon
   deletion of the lexical analyzer or upon reset. This is required in order to
   give the user a chance to clean up his memory properly.

.. sec-include-stack-caveats:

Caveats
-------

Section :ref:`sec-include-stack-howto` explained a safe and sound way to do
the inclusion of other files. It does so by handling the inclusion from 
inside the pattern actions. This has the advantage that, independent of
the token policy, the token stream looks as if the tokens appear in 
one single file.

The alternative method is to handle the inclusion from outside the 
analyzer, i.e. as a reaction to the return value of the ``.receive(...)``
functions. The 'trick' is to check for a token sequence consisting
of the token trigger and and an input stream name. This method, together,
with a queue token policy requires some precaution to be taken. The 
'outer' code fragment to handle inclusion looks like

.. code-block:: cpp

    do {
        qlex.receive(&Token);

        if( Token.type_id() == QUEX_TKN_INCLUDE ) {
             qlex.receive(&Token);
             if( Token.type_id() != QUEX_TKN_FILE_NAME ) break;
             qlex.include_push((const char*)Token.get_text().c_str());
        } 

    } while( Token.type_id() != QUEX_TKN_TERMINATION );

The important thing to keep in mind is:

.. warning::

   The state of the lexical analyzer corresponds to the last token in the 
   token queue! The ``.receive()`` functions only take one token from the
   queue which is not necessarily the last one.

In particular, the token queue might already be filled with many tokens after
the input name token. If this is desired, quex provides functions to save away
the token queue remainder and restore it. They are discussed later on in this
chapter.  The problem with the remaining token queue, however, can be avoided
if it is ensured that the ``FILE_NAME`` token comes at the end of a token
sequence.  This can be done similarly to what was shown in section
:ref:`sec-include-stack-howto`. The analyzer needs to transit into a dedicated
mode for reading the file name. On the incidence of matching the filename, the
lexical analyzer needs to explicitly ``return``. 

An explicit ``return`` stops the analysis and the ``.receive(...)`` functions
return only tokens from the stack until the stack is empty. Since the last
token on the stack is the ``FILE_NAME`` token, it is safe to assume that the
token stack is empty when the file name comes in. Thus, no token queue
needs to be stored away.

If, for some reason, this solution is not practical, then the remainder of the
token queue needs to be stored away on inclusion, and re-inserted after the
inclusion finished. Quex supports such a management and provides two functions
that store the token queue in a back-memory and restore it. To use them, the
memento needs to contain a ``QuexTokenQueueRemainder`` member, i.e.

.. code-block:: cpp

   memento {
       ...
       QuexTokenQueueRemainder  token_list;
       ...
   }

.. cfunction:: void QuexTokenQueueRemainder_save(...);

    This function allocates a chunk of memory and stores the remaining tokens
    of a token queue in it. The remaining tokens of the token queue are detached
    from their content. Any reference to related object exists only inside the
    saved away chunk. The remaining tokens are initialized with the placement new
    operator, so that the queue can be deleted as usual. 
    
    Arguments:

    .. data:: QuexTokenQueueRemainder* me

       Pointer to the ``QuexTokenQueueRemainder`` struct inside the memento. 
   
    .. data:: QuexTokenQueue* token_queue

       Token queue to be saved away. This should be ``self._token_queue`` which
       is the token queue of the analyzer.

.. cfunction:: void QuexTokenQueueRemainder_restore(...);

    Restores the content of a token queue remainder into a token queue. The virtual
    destructor is called for all overwritten tokens in the token queue. The tokens
    copied in from the remainder are copied via plain memory copy. The place where
    the remainder is stored is plain memory and, thus, is not subject to destructor
    and constructor calls. The references to the related objects now resist only
    in the restored tokens.

    Arguments: Same as for ``QuexTokenQueueRemainder_save``.

The two functions for saving and restoring a token queue remainder are designed
for one sole purpose: Handling include mechanisms. This means, in particular,
that the function ``QuexTokenQueueRemainder_restore`` is to be called
*only* when the analyzer state is restored from a memento. This happens at
the end of file of an included file. It is essential that the analyzer
returns at this point, i.e. the ``<<EOF>>`` action ends with a ``return``
statement. Then, when the user detects the ``END_OF_FILE`` token, it is
safe to assume that the token queue is empty. The restore function only
works on empty token queues and throws an exception if it is called in a
different condition.

The handling from outside the analyzer never brings an advantage in terms of
computational speed or memory consumption with respect to the solution
presented in :ref:`sec-include-stack-howto`.  The only scenario where the
'outside' solution might make sense is when the inclusion is to be handled by
the parser. Since the straightforward solution is trivial, the demo/005
directory contains an example of the 'outer' solution. The code displayed there
is a good starting point for this dangerous path.

.. rubric:: Footnotes

.. [#f1] There are also variables that describe structure and which are not
         concerned with the current file being analyzed. For example the 
         set of lexer modes does not change from file to file. Thus, it makes
         sense to pack relevant state data into some smaller object. 


.. [#f2] The name memento shall pinpoint that what is implemented
         here is the so called 'Memento Pattern'. See also 
         <<cite: DesignPatterns>>.

.. note::

   The memento class always carries the name of the lexical analyzer with the
   suffix ``Memento``. If for example an analyzer is called ``Tester``, then
   the memento is called ``TesterMemento``. The name of this class might be
   needed when iterating over mementos, see :ref:`Infinite Recursion Protection
   <sec-infinite-recursion>`.

