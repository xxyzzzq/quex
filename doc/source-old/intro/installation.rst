Installation
============

On sourceforge there are a variety of Quex packages supporting the major
operating systems and distributions at the time of this writing as they are:
Microsoft Windows (tm), Mac OS (tm), and Linux (.deb and .rpm based
distributions).

This section discusses the major 'pillars' of an installation. It is explains
how to install Quex from one of the source packages on an arbitrary platform.
At the same time, it may provide first hints for troubleshooting. The pillars
of a Quex installation are the following:

.. describe:: Python

    Before beginning the installation of Quex, make sure that
    Python (http://www.python.org) is installed. Most Linux distributions provide
    handy .rpm or .deb packages.

    .. warning:: 

       Do not install a Python version >= 3.0! Python 3.x is a language
       different from Python < 3.0. Quex is programmed towards version
       2.6.

    In order to verify that Python is installed you may open a 
    console (``cmd.exe``, ``xterm`` or a shell/terminal under Unix).
    Then type ``python`` and the output should be similar to::

        > python
        Python 2.6.4 (r264:75706, Jan 30 2010, 22:50:05) 
        ...
        >>> 

    Type ``quit()`` to leave the shell. If you do not get this interactive
    python shell, then most likely the PATH variable does not contain 
    the path where Python is installed. On the console review the setting
    of the PATH by::

        C:\> echo %PATH%

    on Windows, or::

        > echo $PATH

    on Unix. If Python's path is not in the list, then add it. Consult your
    the documentation of your operating system for further instructions
    about how to do this.

.. describe:: Quex Distribution

   Get a source distribution from ``quex.org`` or ``quex.sourceforge.net``.
   That is, select a file with the ending '.tgz', '.zip', or '.7z' from the
   download directory.  Extract the files to a directory of your choice.

.. describe:: The ``QUEX_PATH``

   Quex knows about where it is installed through the environment variable
   ``QUEX_PATH``. If you are using a Unix system and the bash-shell, add 
   the following line to your ``.bashrc``-file::
  
       export QUEX_PATH=the/directory/where/quex/was/installed/

   To do the same thing on Windows, go to Control Panel, System, Advanced,
   Environment Variables. Then add the variable ``QUEX_PATH`` with the
   value ``C:\Programs\Quex``, provided that Quex is installed there.

   For clarity, the path must point to the place where ``quex-exe.py`` 
   is located.

.. describe:: The Quex Executable

   The safest way to do this is to add the content of the ``QUEX_PATH``
   variable to the PATH variable. Thus the systems will search for
   executables in Quex's installation directory. Or, on operating systems
   that can provide links, make a link::
   
      > ln -s $QUEX_PATH/quex-exe.py $EXECUTABLE_PATH/quex
     
   where ``$EXECUTABLE_PATH`` is a path where executables can be found by 
   your system.  On a Unix system an appropriate directory is::
   
           /usr/local/bin/quex 
           
   To access this directory, you should be either root or use ``sudo``. 
   You can ensure executable rights with::
       
      > chmod a+rx $QUEX_PATH/quex-exe.py
      > chmod a+rx /usr/local/bin/quex

   On Windows, the file ``quex.bat`` should be copied into ``C:\WINDOWS\SYSTEM``
   where most probably executable files can be found.

.. describe:: Quex Man-Page

   Along with the distribution comes q file ``quex.1`` which is a man page.
   I should be copied into the ``$MANPATH``.

This is all for the installation of Quex. Your should now be able 
to type on the command line::

  > quex --version

and get a result similar to::

    Quex - Fast Universal Lexical Analyzer Generator
    Version 0.57.1
    (C) 2006-2011 Frank-Rene Schaefer
    ABSOLUTELY NO WARRANTY

Note, that with the operating system installers there might be problems
occurring with previous installations. Thus, when updating better better 
move any older installation to a place where the system can find them
(e.g. in the trash can). 

.. describe:: Compilation

    When compiling Quex-generated code the ``QUEX_PATH``
    must be provided as an include path, i.e. you must add 
    an ``-I`` option ``-I$QUEX_PATH`` on the command line
    or ``-I$(QUEX_PATH)`` in a Makefile.

    In the sub directories of ``$QUEX_PATH/demo`` there are many
    examples of how to do that.

.. describe:: IConv, or ICU

    If you want to use character set conversion, you need to install one of the
    supported libraries--currently IBM's ICU <http://icu-project.org/userguide/intro.html>
    or GNU IConv <http://www.gnu.org/software/libiconv/>[#f1]_.

That is all. Now, you should either copy the directories ``./demo/*`` to a
place where you want to work on it, or simply change directory to there.  These
directories contain sample applications 000, 001, etc. Change to the directory of the
sample applications and type ``make``. If everything is setup properly,
you will get your first Quex-made lexical analyzer executable in a matter
of seconds. 

.. note::

   It was reported that a certain development environment called 'VisualStudio'
   from a company called 'Microsoft' requires the path to python
   to be set explicitly. Development environments may have their own set
   of variables that need to be adapted.

The example applications depict easy ways to specify
traditional lexical analyzers, they show some special features of Quex such
as mode transitions, and more. Each demo-application deals with a particular
feature of Quex: 

.. data:: demo/000

          A very simple a lexical analyzer to get started.

.. data:: demo/001

          An example that shows basics on modes and mode transitions.

.. data:: demo/002

          An indentation based lexical analyzer relying on implicitly generated
          tokens ``INDENT``, ``DEDENT``, and ``NODENT``. 

.. data:: demo/003

          Analyzers running on several encodings using converters, either ICU or
          IConv. This is in contrast to the example in ``demo/011`` where the
          internal engine directly runs on the desired encoding.

.. data:: demo/004

          A lexical analyzer for the 'C' language.  

.. data:: demo/005

          An application that demonstrates how the inclusion of files and the 
          return from included files is handled by Quex's feature of include
          stacks.

.. data:: demo/006

          An example that treats *pseudo ambiguous post contexts* (or,
          'dangerous trailing contexts) which are difficult to deal with by
          means of traditional lexical analyzer generators.

.. data:: demo/007

          Lexical analyzer specifications showing pattern prioritization between
          base and derived modes as well as applications of ``PRIORITY-MARK``
          and ``DELETION``.

.. data:: demo/008

          A Quex generated lexer is linked to a bison generated parser. 

.. data:: demo/009

          Analyzers receiving directly from sockets, standard input (pipes), and 
          a command line.

.. data:: demo/010

          Examples of this directory treat manual buffer filling in contrast to
          the default automatic filling.

.. data:: demo/011

          Examples where the internal engine runs on a character encoding different
          from Unicode. This is in contrast to using a converter. 
          
.. data:: demo/012

          Multiple lexical analyzers linked into a single application. 

.. data:: demo/012b

          Multiple lexical analyzers linked into a single application while 
          sharing the same token type.

.. data:: benchmark

          Benchmark suite to measure the performance of the lexical analyzer.
          As an example a benchmark for a C-lexer is implemented. The suite can
          build lexical analyzers based on Quex, but also as a comparison the
          same analyzers generated by flex and re2c.

The author of this document suggests that the user looks at these sample
applications first before continuing with the remainder of this text.  With the
background of easy-to-use examples to serve as starting point for their own
efforts, it should be natural to get a feeling for the ease of Quex.

Please, consider the section 'trouble shooting' for further hints.

.. rubric:: Footnotes

.. [#f1] If you are glad to work on a Linux system, the probability that your 
         distribution provides pre-configured installation packages for those 
         libraries is very high. Nevertheless, there are also wellness packages for other
         operating systems.
