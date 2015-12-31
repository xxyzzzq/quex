The Flow of Data
================

Quex strives for being the most convenient and most general solution for text
analysis. For that, the input provision must be handled. It must cope with
input from any source and through any interaction scenarios.  Also, different
incoming encodings must be treated seamlessly. To achieve that a two-step
loading process is implemented (Figure :ref:`fig:byte-lexatom-buffer`), as they are

    #. Loading raw bytes from whatsoever source. 

    #. Filling the engine's buffer with lexatoms.

The raw byte source may be the Standard C or C++ file handling interface, or
that of POSIX, RTOS, or any other customized interface. A byte loader
communicates with its client in terms of bytes. Its current input position
and the size of content to be loaded is specified in bytes.  A buffer filler
takes bytes from the byte loader, may be, converts it and provides lexatoms.
Its current input position and the size of the content to be loaded is
specified in lexatoms.

Technically, there are two base classes ``ByteLoader`` and ``BufferFiller``
that implement the interfaces for byte loading and buffer filling. Any concrete
implementation is derived from those two. While the default API of a generated
analyzer hides their existence, they become important when the input provision
must be customized :ref:`sec:input-provision`.

.. NOTE figures are setup with 'sdedit'. As for version 4.01 a NullPointer
   exception prevents exporting to png. So that has been postponed.
   Consider files: "buffer-automatic-load.sdx" and "buffer-manual-load.sdx"

Another distinction must be made with respect to loading scenarios: *automatic*
and *manual* buffer filling. By default, a generate analyzer detects that the
end of a buffer has been reached and loads content automatically. In some
cases, this may not be possible or not practical. A command line interpreter
might want to pass a chunk of memory and get a list of tokens, without an
intermediate storing of data in a file system. Or, it might be expected that
the analyzer actively produces tokens when content is received through a
messaging framework. In such cases, manual buffer filling must be applied.
During manual buffer filling the same infrastructure is used, only that the
input comes from the user.
