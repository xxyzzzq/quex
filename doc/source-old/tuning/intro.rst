.. _sec-tuning:

Tuning
------

This chapter is dedicated to the subject of how to improve a lexical analyzer
in terms of computational speed and memory footprint. It is not intended as a 
'silver bullet' that guides ultimately to the optimal configuration. However,
it introduces some basic thoughts which are crucial for optimization. This
chapter starts by the introduction of two mechanisms that reduce the code
size of the lexical analyzer: template and path compression. Then the influence
of the token queue is discussed. Finally, the involvement of converters via
engine based encodings is investigated. Were possible the findings are supported
by data accessed by some sample applications which are available in the quex
distribution package directory 'demo/tuning/'. 

Before any measurements can be made the following points need to be assumed:

.# Asserts are disabled, i.e the compile option ``QUEX_OPTION_ASSERTS_DISABLED``
   is in place.

.# Avoid printing through system calls, i.e avoid ``fprintf``, ``cout << ``
   and their likes. If such a system call is performed for each token, 
   the analyzer's overhead is negligible and the results only measure
   the performance of the input/output stream library and its implementation
   on the operating system.

.# The buffer size must be set to something reasonable. Define 
   ``QUEX_SETTING_BUFFER_SIZE=X`` where ``X`` should be something in the
   range of at least 32Kb. 

.# Avoid any compiler flag that produces additional code such as ``-ggdb``
   for debugging, ``--coverage`` for test coverage, or ``--fprofile-arcs``
   for profiling.

A tuning setup is mostly the contrary of a debug scenario. For debugging all
asserts should be active, print-outs prosper, and the buffer size is as small
as possible to check out reload scenarios. Using a debug setup for tuning,
though, safely drives the development into nonsensical directions.

Template Compression
====================

Quex introduces a powerful feature to reduce the code size of a lexical analyzer
of a lexical analyzer: Template Compression. Template compression combines multiple
states into a single state that changes slightly dependent on the particular 
state that is represents. It can be activated with the command line option::

   > quex ... --template-compression

The aggressiveness of the compression can be controlled by the template compression
'min-gain' to be set by the command line argument::

   > quex ... --template-compression-min-gain [number]

It represents the minimum of estimated bytes that could be spared before
two states are considered for combination into a template state. If only
states with the same entry and drop out section should be considered then
the following option can be specified::

   > quex ... --template-compression-uniform

Especially Unicode lexical analyzer with their large transition maps can profit
tremendously from template compression. If your compiler supports computed
gotos try to set ``QUEX_OPTION_COMPUTED_GOTOS`` on the compilers' command
line, e.g. with GNU C++::

   > g++ -DQUEX_OPTION_COMPUTED_GOTOS ... MyLexer.cpp -c -o MyLexer.o


Principle of Template Compression
#################################

This is displayed in the figures :ref:`fig-template-compression-before` and
:ref:`fig-template-compression-after`.  The first figure displays three states
which have a somehow similar transition map, that is they trigger on similar
states to similar target states. A so called 'template state' must be able to
detect all character ranges involved. An additional matrix helps to find the
particular target state for the represented state.

.. _fig-template-compression-before:

.. figure:: ../figures/template-compression-before.*

   Three states to be compressed by Template compression.

Figure :ref:`fig-template-compression-after` displays a template state that
shall represent state 0, 1, and 2 from figure
:ref:`fig-template-compression-before`. Every state is replaced by a small stub
that defines a 'state key'. The role of the state key is to define the behavior
of the template state.  In particular, it defines the target states that belong
to certain trigger sets.  State 0, 1, and 2 differ with respect to the
character ranges ``[f-m]`` and ``[o-s]``. For these ranges the transitions
differ. The target states for these ranges are stored in the arrays ``X0`` and
``X1``.  ``X0[i]`` represents the target state for ``[f-m]`` if the template
needs to represent the state ``i``. Analogously, ``X1[i]`` helps to mimik the
transitions for ``[o-s]``.

.. _fig-template-compression-after:

.. figure:: ../figures/template-compression-after.*

   Template state representing states 0, 1, and 2 from figure :ref:`fig-template-compression-before`.

Template compression can combine any set of states but its efficiency depends
on the similarity. For this reason the template compression coefficient (see
option ``--template-compression-coefficient``)
has been introduced that defines how aggressively states shall be combined.
That means how much lack of similarity can is tolerated and states can still be
combined into sets. 


Path Compression
================

Quex introduces another way of compression that profits from the sequential
order of similar states. It identifies paths of single character sequences in
the state machine. The command line argument::

   --path-compression

activates the analysis and compression. With this compression all states are
considered to be combined into a path. As a result some special handling is
implemented to distinguish the particularities of each state. If only uniform
states shall be considered, the command line flag::

   --path-compression-uniform

may be provided. Then the overhead of particularities is avoided, but less
states may be combined. Path compression requires a path-end character. By
default it is set to the character code 0x16 (38 decimal, 'SYNCHRONOUS IDLE')
assuming that this never occurs in the data stream. If this character occurs in
the stream to be analyzed, then the path termination character must be defined
explicitly by::

   --path-termination [number]

Where the specified number must be different from the buffer limit code.

It applies if a sequence of single characters can be identified that guide
along a path of states with matching transition maps.  This requirement seems
very rigid and thus the chance of hitting a state machine that contains such
states may appear low. However, in practical applications this exactly the case
where keywords, such as ``for``, ``while``, etc.  intersect with the pattern of
identifiers, e.g. ``[a-z]+``. In other words, languages with many keywords may
profit from this approach.

Instead of implementing for each state of the path a full state, only one state
is implemented a so called 'pathwalker'. A pathwalker consists of the
transition map which is common to all states of the path and the path itself. 

As with template compression using the computed feature of your compiler
might improve performance and code size.

Principle of Path Compression
#################################

.. _fig-path-compression-before:

.. figure:: ../figures/path-compression-before.*

   State sequence to be compressed by path compression.

.. _fig-path-compression-after:

.. figure:: ../figures/path-compression-after.*

    State sequence from figure :ref:`fig-path-compression-before` 
    implemented by pathwalker.

Combining Multiple Compression Types
====================================

It is possible to combine multiple compression types simply by defining
multiple of them on the command line. The result of applying path compression
before or after template compression may be significantly different. The 
sequence of analysis corresponds to the sequence that the activating
command line options appear, i.e.::

   > quex ... --template-compression ... --path-compression ...

determines that template compression is performed before path compression.
Uniform and non-uniform compression can be treated as separate procedures.
Thus, it is possible to say for example::

   > quex ... --template-compression-uniform \
              --path-compression \
              --template-compression

which first does a template compression of very similar states, then a 
general path compression of the remainder. Then whatever remains of 
states is tried to be combined by aggressive template compression.

Token Queues
============

Memory Management
=================

Additional Hints
================

It follows a list of general hints for performance tuning:

.. note::

   The three most important things to consider when improving performance are
   the CPU's cache, the CPU's cache, and the CPU's cache. At the time of this
   writing (2010 C.E.) a cache-miss is by factors slower then a normal cache
   read. A fast program can be slowed down to 'snail speed' simply by 
   excessive cache miss scenarios.

   Practically, this means that the data that is access frequently is best
   kept close together, so that cache misses are less probable.

.. note::

   The fourth important thing about improving performance is to avoid frequent
   system calls. For example, allocate memory in a chunk and then cut from it
   when needed, instead of calling ``new``, ``delete``, ``malloc`` or ``free``
   all the time. You might also consider to implement containers yourself
   instead of relying in STL or similar libraries, if this allows you to 
   control memory placement.

.. note::

   The fifth important thing is to use ``memcpy`` and ``memmove`` for copying
   of content--especially for larger amounts of data. Few people can compete
   with the insight expert knowledge that is put into this functions. Simply
   compare a ``memcpy`` operation with a ``for`` loop doing the same thing. It
   is not seldom a factor of 40 between the two. Use ``memmove`` when source
   and destination may overlap.

[to be continued]

