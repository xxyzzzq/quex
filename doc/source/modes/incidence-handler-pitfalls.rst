Incidence Handler Pitfalls
==========================

Note, that initiating explicitly mode transition inside ``on_exit`` *will* cause
an infinite recursion! If this is intended the mode transition mechanism should
be circumvented using the member function ``set_mode_brutally()``. Note also,
that initiating an explicit mode transition inside ``on_entry`` *may* cause an
infinite recursion, if one initiates a transit into the entered mode.
Certainly, such a mode transition does not make sense. In general, mode
transitions inside *on_entry* or *on_exit* incidence handlers are best avoided.
Consider the code fragment

.. code-block:: cpp

    mode MODE_A {
       ...
       {P_SOMETHING} {
            self << MODE_B;
            self.send(TKN_EVENT_MODE_TRANSITION);
            return;
       }
       ...
    }

meaning that one desires to enter MODE_B if pattern ``P_SOMETHING`` is
detected. Imagine, now, because of some twisted mode transitions in the
transition incidence handlers one ends up in a mode ``MODE_K``! Not to mention the
chain of mode transition incidence handler calls - such a design makes it hard to
conclude from written code to the functionality that it implements. To repeat
it: *explicit mode transitions inside ``on_entry`` and ``on_exit`` are best avoided!*

One might recall how uncomfortable one would feel if one mounts a train in
Munich, leading to Cologne, and because of some redirections the trains ends up
in Warsaw or in Moscow. In a same way that train companies should better not do
this to theirs customers, a programmer should not do to himself mode
transitions inside ``on_entry`` and ``on_exit``.

Another issue has to do with optimization. Queχ is aware of transition handlers
being implemented or not. If no transition handlers are implemented at all then
no incidence handling code is executed. Note, that each entry and exit transition
handler requires a dereferencing and a function call--even if the function itself
is empty. For fine tuning of speed it is advisable to use only entry handlers
or only exit handlers. The gain in computation time can be computed simply as::

    delta_t =   probability_of_mode_switch 
              * time_for_dereferencing_empty_function_call / 2;

For reasonable languages (probability of mode change < 1 / 25
characters) consider the speed gain in a range of less than 2%. The dereferencing, 
though, can come costly if the mode change is seldom enough that is causes a 
cache-miss. Thus, for compilers that compile large fragments of code, 
this optimization should be considered.
