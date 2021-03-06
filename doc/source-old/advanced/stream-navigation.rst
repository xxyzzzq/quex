Stream Navigation
=================

Independent of the underlying character encoding :ref:`sec-character-encodings`
quex's generated lexical analyzers are equiped with functions for stream
navigation on character basis. All required mechanisms of buffer loading and
stream positioning is taking care of in the background. The current character
index can be accessed by the member function:

.. code-block:: cpp

    size_t  tell();

The plain C versions of all mentioned functions are mentioned at the end of
this section. The function ``tell()`` reports the current character index where
the lexical analyzer is going to continue its next step. The lexical analyzer
can be set to a certain position by means of the following member functions:

.. code-block:: cpp

    void    seek(const size_t CharacterIndex);
    void    seek_forward(const size_t CharacterIndex);
    void    seek_backward(const size_t CharacterIndex);

The first function moves the input pointer to an absolute position. The
remaining two functions move the input pointer relative to its current
position. 

.. warning:: The usage of the above functions is similar to the usage of 'goto' in 
   many popular programming languages. In particular it is possible to stall the 
   lexical analyzer by un-coordinatedly ``seek``-ing backwards. 
   
   Also, the ``seek`` functions *do not* take care of the line and column number
   adaption. This must be done manually, if desired. That is somehow the new line 
   and column numbers must be determined and then set explicitly:

   .. code-block:: cpp

       here = self.tell();
       self.seek(Somewhere);

       my_computation_of_line_and_column(here, Somewhere, 
                                         &line_n, &column_n);

       self.column_number_set(column_n);
       self.line_number_set(line_n);

   Note, that ``column_number_set(...)`` and ``line_number_set(...)`` define 
   the column and line numbers of the next pattern to match.

The reading of the current lexeme can be undone by

.. code-block:: cpp

    void    undo();
    void    undo_n(size_t DeltaN);

The function ``undo()`` sets the input pointer to where it was before the
current lexeme was matched.  With ``undo_n(...)`` it is possible to go only a
specified number of characters backwards. However, it is not possible to 
go back more then the length of the current lexeme.

The undo functions have several advantages over the seek functions.  First of
all they are very fast. Since the lexical analyzer knows that no buffer
reloading is involved, it can do the operation very quickly. Second, it can
take care of the line and column numbers. The user does not have to compute
anything manually. Nevertheless, they should be used with care. For example, if
``undo()`` is not combined with a mode change, it is possible to stall the analyzer.

In plain C, the stream navigation functions are available as

.. code-block:: cpp

    size_t  QUEX_NAME(tell)(QUEX_TYPE_ANALYZER* me);
    void    QUEX_NAME(seek)(QUEX_TYPE_ANALYZER* me, const size_t);
    void    QUEX_NAME(seek_forward)(QUEX_TYPE_ANALYZER*  me, const size_t);
    void    QUEX_NAME(seek_backward)(QUEX_TYPE_ANALYZER* me, const size_t);
    void    QUEX_NAME(undo)(QUEX_TYPE_ANALYZER* me);
    void    QUEX_NAME(undo_n)(QUEX_TYPE_ANALYZER* me, size_t DeltaN_Backward);

where the ``me`` pointer is a pointer to the analyzer, e.g. ``&self``. This
follows the general scheme, that a member function ``self.xxx(...)`` in C++ is
available in plain C as ``QUEX_NAME(xxx)(me, ...)``.
