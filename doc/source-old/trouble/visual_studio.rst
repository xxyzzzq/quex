Visual Studio(tm) 
=================

At the time of this writing a development tool called 'Visual Studio' by a
company called Microsoft(tm) is very popular. It provides a graphical user
interface and its users tend to be more graphical-oriented. This section tries
to overcome initial troubles related to the usage of Visual Studio.

Quex comes with a variety of demos located in subdirectories of
``$QUEX_PATH/demo``. To start, one of the project files must be loaded into
Visual Studio. Then, under 'Project' or 'Debug' a choice allows to 'Build the
Project'. If this works, it can be run by clicking on a green triangle that
points to the right in the top tool bar. The first thing that might fail, is
that the build process reports that python cannot be found::

    1>------ Build started: Project: demo003, Configuration: Debug Win32 ------
    1>  'python' is not recognized as an internal or external command,
    1>  operable program or batch file.
    ...

To fix this, open your browser (Explorer(tm), Firefox(tm), Opera(tm), or so)
and type``www.python.org`` in the address line. Then follow the menus that
guide to a download page. Download the latest python version of the 2.*
series. Do **not** download anything of version 3.0 or higher. Double click
on the downloaded package and follow the instructions. Then open the
Microsoft Windows Control Panel. Open the 'Systems' menu.  Click on the
'Advanced Tab'; and from there click on 'Environment Variables'.  Choose
the environment variable 'PATH' and click 'EDIT'. Make sure that the
Python's path is included as shown in figure :ref:`python_path`.  If not,
please add the directory where you installed python, e.g.
``C:\Python27\;``. The semicolon is the delimiter between directories in
the ``PATH`` variable. 

.. _fig-python_path:

.. figure:: ../figures/visual-studio/python_path_variable-nice.png
   
   Adding python's path to the environment PATH variable.

Make sure that a ".qx" file, that contains some quex code, is included in the
source file of your project. To involve Quex's code generation in the build
process, right click on the ".qx" file and choose 'Properties'.  Now, a window
opens that shows its properties as shown in :ref:`fig-qx-file-compile`. The
command line tells how Quex is to be called in order to generate the source
files. In the example, Quex generates ``EasyLexer`` and ``EasyLexer.cpp``.

.. _fig-qx-file-compile:

.. figure:: ../figures/visual-studio/qx_file_properties-nice.png
   
   Setting up Quex as code generator.

If no external components are required the aforementioned explanation should be
sufficient. When using an external converter, such as ICU for example, some
more work remains to be done.  It might happen, that Visual Studio cannot find
certain header files, such as ``unicode/uconv.h`` which is actually an ICU
header. The compiler searches for include files in include directories. They
search directories can be modified by right-clicking on the project (e.g.
'demo003'). A new window pops up. In the menu for C/C++, click into the field 
right to 'Additional Include Directories' as show in figure :ref:`fig-include-dir`.  
Add the additional include directory; In the example it is::

   "C:\Program Files\icu\include"; 
   
because the user wishes to use ICU together with Quex and installed ICU at this
place.

.. _fig-include-dir:

.. figure:: ../figures/visual-studio/include_dir-nice.png  
   
   External include directory.

Configuration parameters of the analyzer can be set in the Menu 'C/C++'
at item 'Command Line'. There should be a large text field in the bottom
right corner. In the example of demo003, the macro ``ENCODING_NAME``
must be defined for the file ``example.cpp``. In order to let the 
lexical analyzer run at full speed, asserts must be disabled, so that
at least the following options must added::

    -DENCODING_NAME=\"UTF8\" -DQUEX_OPTION_ASSERTS_DISABLED

The ``-D`` flag is used to define the macros. A directly following '='
allows to define a value for the macro.

Analyzers might also rely on other libraries. For this the library itself, as
well as the library path must be specified. In the same property window as
before, under 'Linker/Input', there is a field called 'Additional Dependencies'
that allows to add those libraries.  In the example of figure
:ref:`fig-additional-libs` the libraryis::

    icuuc.lib

is added, which is the library entry for ICU's character encoding converters. The
paths where the Visual Studio searches for additional libraries can be
influenced by the entry 'Additional Library Directories' under 'Linker/General'
in the same property window. With this setup the example projects should
compile and link properly into an executable file.

.. _fig-additional-libs:

.. figure:: ../figures/visual-studio/link_dir-nice.png     
   
   Adding an external library.

What remains may be issues with dynamic link libraries (DLLs) that cannot be
found at run time. To solve this, the directory where the dynamic link library
is located may either be added to the system's path variable, as was done for
the python installation path.  Or, they might be copied directly into the
directory where the compiled program is located (e.g. ``demo\003\Debug``).
The later is a good solution for a 'first shot' in case that the development
environment shadows the PATH variable.

As a final hint, it might be a good idea to introduce a break point at 
the last line of the example lexical analyzer. This way to command line
window which displays the results remains active. In the command line
window, the results of the lexical analysis may be examined. 

