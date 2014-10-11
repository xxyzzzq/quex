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

The goal of the descriptions is to lay out the groundwork for algorithms that
optimize state machines by means of reductions of transition actions. This
section derives precise terms for further discussions.

Incoming characters cause state transitions. Those transitions are adorned with
actions, such as 'store last acceptance'. At some point, the incoming character
does not fit a transition map of the current state and the state machine exits.
Upon exit, a value is computed based on the passed actions and the current 
state. This is depicted in figure 1.


                 .-------<-----------.
                 |                   |
       Begin ------->Actions -----> Transitions -----> Exit_i
                                                       consq(i, SOV)

       Figure 1: A 'value' is computed upon exit from the state machine.

When the state machine exits, some consequences 'consq(i, SOV)' are drawn
depending on the current state 'i' and the setting of variables 'SOV' as
defined below. 

DEFINITION: SOV -- Setting of Variables

    The term 'setting of variables' SOV shall stand for the setting of all
    variables which are relevant to the investigated behavior. 

The SOV can be 'line count' and 'column count' or 'acceptance', for example.
Each SOV requires a different different procedure. This section discusses
common concepts. First let the term 'action' be defined as follows.

DEFINITION: Action -- 'Act(i)'

    An action, in this context, denotes an operation which is to be performed
    and the state in which it is to be performed.  The operation is a write or
    change operation to a variable from the SOV. 


-------------------------------------------------------------------------------

LINEAR STATES AND MOUTH STATES:

Two central concept of the analysis algorithms are 'linear states' and 'mouth
states' as the are defined in the paragraphs to follow. They differ in the way
that the influence of actions can be determined beyond them.

DEFINITION: Linear State

    A linear state is a state that is entered only through one state.

                                    .---> ...
                                   /
                        ... --->( 0 )---> ...

                Figure 1: The concept of a linear state.

Since there is only one predecessor state to a linear state the SOV can be
derived from the SOV at the predecessor and the actions of the linear state
itself--at compile time.

                 SOV(i) = Action(i) on SOV(predecessor(i))

Actions along a sequence of linear states can be pre-determined--at compile 
time. Consider the linear state sequence in figure 2.

                     x=x+1       x=x+1       x=x+1        
           ... ( a )------>( b )------>( c )------>( d )------>


             Figure 2: A string of linear states

For an exit in state 'd' the actions can be described in general terms as

       SOV(b) = Act(b) on SOV(a)
       SOV(c) = Act(c) on SOV(b)
       SOV(d) = Act(d) on SOV(c)
       SOV(e) = Act(e) on SOV(d)
              = Act(e) on (Act(d) on (Act(c) on (Act(b) on SOV(a))))
                 
The SOV in figure 2 is 'x' and the action in figure 2 is 'x = x + 1'. Thus,
with 'x(i)' as the 'x' in state 'i' the sequence in the becomes:
    
                          x(b) = x(a) + 1
                          x(c) = x(b) + 1
                          x(d) = x(c) + 1
                          x(e) = x(d) + 1
                         
Or, shortly              
                         
                          x(e) = x(a) + 4
       
This highlights that along a sequence of linear states actions can be
accumulated efficiently in order to achieve the reduction of operations long
the state transitions. 

DEFINITION: Accumulated Action 'Accu(i, k)'

   An Accumulated Action 'Accu(i)' describes how the setting of SOV in the
   state 'i' can be determined based on some initial setting of SOV in another
   state and the sequence of actions which influences the SOV in state.

   An 'Accu(i)' also maintains information about which of its elementary
   operations require what action in previous states.

Accumulated actions can be developed along linear states, because for each
linear state there is only one previous setting of SOV. The accumulated action
provides a procedure to implement the effect of actions of previous states,
without requiring the actions in the states itself.

The development of accumulated actions along linear states is called the 'walk
along linear states'. It can only start at states 'i' where Accu(i), AA(i), and
PA(i) art determined. The particular procedure according to the SOV must
provide the begin states for this walk.

Accumulated actions are associated with *absolutely necessary* actions
and *potentially necessary* actions. An absolutely necessary action in the
example of figure 2 would be that the value of 'x' is stored 'x(a) upon entry
in state 'a'. Only then the subsequent actions may operator 'x = x(a) +
constant'. Potentially necessary actions, are the increments 'x = x + 1' in
each state. The become necessary, if no other simplification is possible.

DEFINITION: Absolutely necessary action -- AA(i)

    An absolutely necessary action AA(i) of an accumulated action in state 
    i is the set of actions in a state machine which are absolutely required
    for Accu(i) to work.

DEFINITION: Potentially necessary action -- PA(i, x)

    A potentially necessary action is an action which becomes necessary if a
    simplification 'x' in an accumulated action 'Accu(i)' can no longer be
    used.

A special accumulated action is the 'void' action, where nothing can be
pre-determined. For this action, there is solely a set of absolutely necessary
actions. No Accu(i) can exist where PA(i, x) is not known for all of its
elements. If the action that can be avoided was unknown, then there would 
be no point in an Acc(i).

The contrary to linear states are mouth states.

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
may have appeared along the path. An example is shown in figure 4.

                              x=x+1
                       .---------->-----------. [x=x(0)+1]
                      /                        \
                   ( 0 )                      ( 3 )---> ...
                      \                        /
                       '--->( 1 )----->( 2 )--' [x=x(0)+2]
                       x=x+1      x=x+1

                 Figure 4: Accumulated Actions meet in mouth state 3.

At the entry to state 3, there are two accumulated actions on 'x'. First, 
directly from state 0, where 'x=x+1'. Second, there is an entry from state
2. There, the accumulated action is 'x=x+2'. The setting of 'x' depends
on the path taken to state 3, it can be either 'x(0)+1' or 'x(0)+2'. In
state 3, it cannot beforehand, how much on has to add to 'x(0)'. In this
example, one cannot derive an accumulated action from before state 3 to
states beyond it.

The actual path taken to a mouth state is something that is only determined at
run-time. Thus, in general the outgoing accumulated action can only be different
from 'void' if there is some type of uniformity. Let the process of 'action
interference' be defined as follows.

DEFINITION: Action Interference

    The process of 'action interference' develops an accumulated action based
    on multiple accumulated actions at the entries of a mouth state. The output
    accumulated action is either void or specific.

    The output can be determined to be void, as soon as two entries are not of
    'sufficient uniformity'. However, in that case, the AA(i) remain
    undetermined as long as not all entries are considered.

    A specific output can only be determined if all accumulated actions at
    all entries share a 'sufficient uniformity'.

DEFINITION: Sufficient Uniformity for Action Interference

    A set of accumulated actions { Accu(k), for some k } contains sufficient
    uniformity if there is a procedure that can translate the set into a single
    accumulated action Accu(i). Further, the AA(i) and PA(i) must be determined.

As soon as an accumulated action interference has been performed in a mouth
state, it can also act as the begin for a walk along linear states.

-------------------------------------------------------------------------------

THE WALK ALONG LINEAR STATES

There is a duality between linear states and mouth states with respect to 
run-time dependency. It is expressed as follows.

STATEMENT: Run-time dependence.

    Linear state sequences do never depend on run-time. Their behavior is 
    determined by the state from where they start.

    Mouth states may depend on run-time. The path by which they are entered
    determines what actions have been applied. 

A recursive walk along sequences of linear states is part of any analysis.
Linear states can have transitions to more than one state. So, the walk along
linear states is a recursive 'tree-walk'. The termination criteria for the walk
along linear states may be defined as follows.

DEFINITION: Termination criteria for walk along sequence of linear states.

    A recursive walk along sequences of linear states does not enter the
    state ahead, if 

       (i)   there is no state. The current state is a terminal.
       (ii)  the state ahead is a mouth state.
       (iii) the state ahead imposes a specific Accu(i), AA(i), and PA(i).

The first condition comes natural. The second condition exists, because 
actions cannot be accumulated beyond mouth states. The third condition 
tells that the walk stops where another walk begins.

With these concepts, a first draft of an algorithm for the determination of
accumulated actions can be defined.

             (*) Start.
             (*) begin_list = get list of begin states for linear state 
                 sequences.
   .-------->(*) perform linear walks starting from each state in begin_list.
   |             --> accumulated actions for linear states until terminal, 
   |                 mouth, or specific states.
   |             --> entries of mouth states receive accumulated actions.
   |         (*) perform action interference in mouth states where possible.
   '-- yes --(*) are there specific mouth states?
             (*) Stop.

When this algorithm comes to an end, there might be still mouth states with 
undetermined entries. This may be the case due to mutual dependence between
mouth states. Such dead-locks are handled in the next section.

-------------------------------------------------------------------------------

DEAD-LOCK STATES

It may occur, that there are still mouth states remaining. Those are dead-lock
states. An example is shown in Figure 4.

                           .------------>( 2 )
                     A     |             /   \
                ... ---->( 1 )          (     )
                           |             \   /
                           '------------>( 3 )
         
        Figure 4: A dead-lock of mouth states 2 and 3.

The human can judge easily, that for both states only pattern A can occur. 
This, however, must be formally described.

    DEFINITION: Dead-lock state.

    A dead-lock state is a mouth state with an unresolved output accept
    sequence. In particular:

      -- it has at least one unresolved entry accept sequence.

      -- all of the other entries are uniform (if there are other entries).

      -- it depends on other dead-lock states.

A group of dead-lock states are states which are mutually dependent. They all
have unresolved entries which depend on outputs of other dead lock states. About
such a group, it can be said that:

    (i) If all entries of this group have the same accept sequence, then 
        they can only propagate this accept sequence between each other.
        Thus, all of their outputs are determined to have this accept 
        sequence. Figure 4 showed such an example.

    (ii) If one entry of a state in that group has a different accept 
        sequence, it will interfere with the other. Then, all mouth states
        have their output to be determined as 'void'.

                                           .---->----.      B
                         .------------>( 2 )        ( 4 )<------
                   A     |              / \'----<----'
              ... ---->( 1 )           (   )
                         |              \ /
                         '------------>( 3 )
         
            Figure 5: Dead lock states with differing accept sequence.

        In figure 5, for example, the 'B' may come through state 4 and
        and interfere with the 'A' in state 2. Thus, the output from state 2
        is void. Since state 2 has inputs into state 3 and 4, the outputs 
        of 3 and 4 will also be void.

        This effect does not change when linear states in between are 
        involved.
-------------------------------------------------------------------------------
At some point in time the transitions come to an end--either through a
character or the end of the character stream. This is the end of an analyzer
step.  From outside the state machine, only the SOV at the end of this analyzer
step is of interest. 

DEFINITION: consq(i, SOV)

    The function 'consq(i, SOV)' describes what is supposed to happen upon exit
    from the state machine. It may also express what the SOV is supposed to
    contain. It is specific to its state 'i'. Further, it depends on the SOV as
    it results from the history of transitions along the state machine. 

The goals is to find a method so that the actions along the state machine can
be omitted by an adapted handling at the end of the analyzer step, or by a
postponing as until the actions influence can no further be determined.  This
has obvious efficiency advantages. Consider, for example, the lexeme length
as SOV.  The 'consq(i, SOV)' function simply provides the lexeme length as
the value that has been accumulated.  If the number of transitions from begin
to end is fix for a given state, then the lexeme length does not have to be
incremented at each transition. Instead, it can be set upon exit to a
constant. 

DEFINITION: f(Ci, SOV)

    The representative function 'f(Ci, SOV)' does two operations:

        (1) it derives actions from SOV independent from actions 
            on the transition path.
        (2) it implements what consq(i, SOV) does.

The set of constants 'Ci' is specific to state 'i' and must be known at
compile-time. The role of this function is to replace 'consq()' by 'f(Ci, SOV)' 
and therefore omit the actions which 'consq()' would require.  

DEFINITION: Ai

    Let Ai denote the set of required actions to compute the SOV at the 
    exit of state 'i'. 

The replacement of 'consq()' by a function 'f(Ci, COV)' in a state reduces the
set Ai. If an action is not mentioned in any Ai, then it can be completely
removed from the state machine.


GENERAL DOCUMENT STRUCTURE:

Documents describing state machine analysis shall follow the following scheme:

  (1) Specification of SOV, Actions, and 'consq(i, SOV)'.

  (2.1) Action Accumulation in linear states.

  (2.2) Action Interference in mouth states. 

  (3.1) Specify 'f(Ci, SOV)'

  (3.2) Specify how Ai is reduced due if 'f(Ci, SOV)' replaces 'consq(i, SOV)'.

  (4) Procedure description

  (5) Doubt discussion

All .txt files in this directory that describe action reductions are following
this scheme. The 'doubt' discussion shall demonstrate the deepness of thought
that has been put into the development. All doubts, of course, should be
debunked.

-------------------------------------------------------------------------------





