Input
=====

This section describes the process of input provision.  A well-rounded input
procedure must cope with input from any source and through any interaction
scenarios.  Also, different incoming encodings must be treated seamlessly. To
achieve that a two-step loading process is implemented as shown in Figure
:ref:`fig:byte-lexatom-buffer`. The two steps are

    #. Loading raw bytes from whatsoever source. 

    #. Filling the engine's buffer with lexatoms.

The 'outside world' may provide data in a variety of different ways.  The raw
byte source may be the Standard C or C++ file handling interface, or that of
POSIX, RTOS, or any other customized interface. A 'byte loader' has implements
an common API through which any outside data is communicated. The byte loader
produces a byte stream. The byte loader performs stream navigation (tell&seek)
on byte level.  The analyzer's buffer, though, requires lexatoms. 

The buffer's cells to store lexatoms have a specific size (8bit, 16bit, 32bit,
...), a specific type (``uint8_t``, ``uint16_t``, ...), and they follow a
specific encoding (ASCII, UTF8, UTF16, ...). It is the task of the lexatom
loader to transform the incoming byte stream into an lexatom stream. The lexatom
loader performs stream navigation on lexatom level. The lexatoms are finally
stored in some chunk of memory: the buffer. The analyzer then access the content
of the buffer iterating through it with a pointer and accessing lexatoms by
dereferencing the pointer.

.. _fig:byte-lexatom-buffer:

.. figure:: ../figures/byte-lexatom-buffer.png
   
   The path of data from the outside world until it arrives in the analyzer's
   lexatom buffer.

Technically, there are two base classes ``ByteLoader`` and ``LexatomLoader``
that implement the interfaces for byte and lexatom loading. Any concrete
implementation is derived from those two. While the default API of a generated
analyzer hides their existence, they become important when the input provision
must be customized :ref:`sec:input-provision`.

This two-step input provision is flexible enough to cope with the constraints
of tiny embedded systems, where there is even no Standard C I/O library
available, up to complex systems where input streams are decrypted and
converted by complex algorithms.


.. NOTE figures are setup with 'sdedit'. As for version 4.01 a NullPointer
   exception prevents exporting to png. So that has been postponed.
   Consider files: "buffer-automatic-load.sdx" and "buffer-manual-load.sdx"

The buffer filling process may happen in two ways: *automatically* or
*manually*. By default, a generated analyzer detects that the end of a buffer
has been reached and loads content automatically. In some cases, this may not
be possible or not practical. A command line interpreter might want to pass a
chunk of memory and get a list of tokens, without an intermediate storing of
data in a file system. Or, it might be expected that the analyzer actively
produces tokens when content is received through a messaging framework. In such
cases, manual buffer filling must be applied.  During manual buffer filling the
same infrastructure is used, only that the input comes from the user.

