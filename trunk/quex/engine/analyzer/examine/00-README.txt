Action Reduction/Action Postponing

(C) Frank-Rene Schaefer
-------------------------------------------------------------------------------
ABSTRACT:

This file describes the theoretical background for the process applied by 
Quex used to reduce the number of actions or to postpone actions. Any write
action that can be avoided may bring heave performance increase, due to
avoided cache misses. Every action is preferred to be postponed, because
earlier states are passed more often than later states.

-------------------------------------------------------------------------------
SITUATION:

Incoming characters cause state transitions. Those transitions are adorned with
actions, such as 'store last acceptance'. At some point, the incoming character
does not fit a transition map of the current state and the state machine exits.
Upon exit, a value is computed based on the passed actions and the current 
state. This is depicted in figure 1.


               .----<-----------.
               |                |
            Actions -----> Transitions -----> Exit_i
                                              value = history(Actions, state)
                                              => A_i = set of actions required 
                                                       for exit from state i

   Figure 1: A 'value' is computed upon exit from the state machine.


GOAL: 

Make the computation of 'value' independent of the Actions.  Any action that is
not required to compute 'value' can be removed from A_i.  Once the sets A_i of
all states have been reduced, the following may be performed:
  
   (1) An action that does not appear in any A_i can be completely removed
       from the state machine.

   (2) If an action happens right before a state 'k' but is not element 
       of A_k, then it can be postponed after that state.
-------------------------------------------------------------------------------

GENERAL PROCESS:

For a given state 'i' find a function 'f(state, c_i)' with 'c_i' as a set of
constants so that 

                f(c_i, state) == history(Actions, state)

That is, when using f(c_i, state) the Actions are no longer required. Instead
only the current state is used and some constants which are specific to state
'i'. However, for the replacement of 'history' by 'f' conditions must be 
clearly defined on the transitions and the actions on the path between the
state where actions appear and state 'i'. Thus, for the reduction process
to start the following things must be described precisely:

    (1) The actions required for 'history(Actions, state)'.

    (2) 'history(Actions, state)'.

    (3) 'f(c_i, state)'.

    (4) Condition for 'f(c_i, state) == history(Actions, state)'.

    (5) Procedure description

All .txt files in this directory that describe action reductions are following
this scheme.

-------------------------------------------------------------------------------






