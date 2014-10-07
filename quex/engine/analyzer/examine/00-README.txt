Action Reduction/Action Postponing

(C) Frank-Rene Schaefer
-------------------------------------------------------------------------------
ABSTRACT:

This file describes the theoretical background for the process applied by Quex
used to reduce the number of actions or to postpone actions. Any write action
that can be avoided during state transitions may bring a strong performance
increase (due to avoided cache misses, for example). Every action is preferred
to be postponed, because earlier states are passed more often than later
states.

-------------------------------------------------------------------------------
SITUATION:

Incoming characters cause state transitions. Those transitions are adorned with
actions, such as 'store last acceptance'. At some point, the incoming character
does not fit a transition map of the current state and the state machine exits.
Upon exit, a value is computed based on the passed actions and the current 
state. This is depicted in figure 1.

             .-------<-----------.
             |                   |
   Begin ------->Actions -----> Transitions -----> Exit_i
                                              value = history(Actions, state)
                                              => A_i = set of actions required 
                                                       for exit from state i

   Figure 1: A 'value' is computed upon exit from the state machine.


The goal of the descriptions is to lay the groundwork for algorithms that
optimize state machines by the reduction of transition actions. This section
derives precise terms for further discussions.

DEFINITION: SOV -- Setting of Variables

    The term 'setting of variables' SOV shall stand for the setting of all
    variables which are relevant to the investigated behavior. 

The SOV can be 'line count' and 'column count' or 'acceptance', for example.
Each SOV requires a different document and different procedure. This document
discusses common concepts.
   
Analysis consists of a walk through the state machine which is controlled by
the incoming characters. Each character controls a state transition. During
these transitions 'actions' happen which influence the SOV.

DEFINITION: Action

    The term 'action' shall indicate a write operation to a variable from
    the SOV during state transitions.

At some point in time the transitions come to an end--either through a
character or the end of the character stream. At this point in time ends an
analyzer step.  From outside the state machine, only the SOV at the end of this
analyzer step is of interest. 

DEFINITION: history(Transitions, SOV)

    Shall determine the computation of SOV due to actions along transitions
    through the state machine.

The goals is to find a method so that the actions along the state machine can
be omitted in favor of an operation at the end of the analyzer step. This has
obvious efficiency advantages. Consider, for example, the lexeme length as SOV.
If the number of transitions from begin to end is fix for a given state, then
the lexeme length does not have to be incremented at each transition. Instead,
it can be set upon exit to a constant. 

DEFINITION: f(Ci, SOV)

    For a given state 'i', the function 'f(Ci, SOV)' represents a method to 
    determine the value of SOV from a set of constants 'Ci'.

The set of constants 'Ci' is specific to state 'i' and must be known at
compile-time. The role of this function is to cheaply replace 'history()'.
As a result, the actions along the transitions that produce 'history()'
in that state are no longer required for state 'i'.

DEFINITION: Ai

    Let Ai denote the set of required actions to compute the SOV at the 
    exit of state 'i'. 

The replacement of 'history()' by a function 'f(Ci, COV)' in a state reduces
the set Ai. If an action that is not mentioned in any Ai, then it can be
completely removed from the state machine.

-------------------------------------------------------------------------------

LINEAR STATES AND MOUTH STATES:

Two central concept of the analysis algorithms are 'linear states' and 'mouth
states' as the are defined in the paragraphs to follow.

DEFINITION: Linear State

    A linear state is a state that is entered only through one state.

                                    .---> ...
                                   /
                        ... --->( 0 )---> ...

                Figure 1: The concept of a linear state.

Since there is only one predecessor state to a linear state the SOV be derived
from the SOV at the predecessor and the actions of the linear state itself
at--compile time.

                 SOV(i) = Action(i) on SOV(predecessor(i))

Actions along a sequence of linear states can be pre-determined--at compile 
time. Consider the linear state sequence in figure 2.

                     x=x+1       x=x+1       x=x+1        
           ... ( a )------>( b )------>( c )------>( d )------>


             Figure 2: A string of linear states

For an exit in state 'd' the actions can be described in general terms as

                SOV(b) = Action(b) on SOV(a)
                SOV(c) = Action(c) on SOV(b)
                SOV(d) = Action(d) on SOV(c)
                SOV(e) = Action(e) on SOV(d)
                 
The SOV in figure 2 is 'x' and the action in figure 2 is 'x = x + 1'. Thus,
the sequence in the becomes concretely with 'x(i)' as the 'x' in state 'i':
    
                          x(b) = x(a) + 1
                          x(c) = x(b) + 1
                          x(d) = x(c) + 1
                          x(e) = x(d) + 1
                         
Or, shortly              
                         
                          x(e) = x(a) + 4
       
This highlights that along a sequence of linear states actions can be
accumulated efficiently in order to achieve the reduction of operations long
the state transitions. The contrary to linear states are mouth states.

DEFINITION: Mouth State

    A mouth state is a state that is entered from more than one state. An 
    example is depicted in figure 1.

                        ... --->--.   .---> ...
                                   \ /
                        ... --->--( 4 )---> ...
                                   /
                        ... --->--'

                Figure 3: The concept of a mouth state.

Depending on the state from which a mouth state is entered different actions
may have appeared along the path. The actual path taken to a mouth state is
something that is only determined at run-time. The one and only possibility to
propagate actions through a mouth state is if they are uniform. The following
statement can be made.

STATEMENT: Run-time dependence.

    Linear state sequences do never depend on run-time. Their behavior is 
    determined by the state from where they start.

    Mouth states may depend on run-time. The path by which they are entered
    determines what actions have been applied. 

All analysis described in these sections exploit the ability of sequences of
linear states to accumulate actions. For that, a recursive walk along sequences
of linear states is part of any analysis. The termination criteria for the
walk along linear states may be defined as follows.

DEFINITION: Termination criteria for walk along sequence of linear states.

    A recursive walk along sequences of linear states does not enter the
    state ahead, if 

       (i)   there is no state. The current state is a terminal.
       (ii)  the state ahead is a mouth state.
       (iii) a specific condition on transition actions is met.

The specific condition (iii) on transition actions depends on the procedure to
be applied.

-------------------------------------------------------------------------------

GENERAL PROCESS:

For a given state 'i' find a function 'f(state, Ci)' with 'Ci' as a set of
constants so that 

                f(Ci, state) == history(Actions, state)

That is, when using f(Ci, state) the Actions are no longer required. Instead
only the current state is used and some constants which are specific to state
'i'. However, for the replacement of 'history' by 'f' conditions must be 
clearly defined on the transitions and the actions on the path between the
state where actions appear and state 'i'. Thus, for the reduction process
to start the following things must be described precisely:

    (1) The actions required for 'history(Actions, state)'.

    (2) 'history(Actions, state)'.

    (3) 'f(Ci, state)'.

    (4) Condition for 'f(Ci, state) == history(Actions, state)'.

    (5) Procedure description

    (6) Doubt discussion

All .txt files in this directory that describe action reductions are following
this scheme. The 'doubt' discussion shall demonstrate the deepness of thought
that has been put into the development. All doubts, of course, should be
debunked.

-------------------------------------------------------------------------------





