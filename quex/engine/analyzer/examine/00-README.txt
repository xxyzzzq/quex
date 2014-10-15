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

This document provides the groundwork for algorithms that optimize state
machines by means of reductions of transition actions. It defines precise terms
for further discussions.

Incoming characters cause state transitions. Transitions are adorned with
operations, such as 'store last acceptance'. At some point, an incoming
character does not fit a transition map of the current state and the state
machine exits.  Upon exit, some consequences are derived  based on the passed
operations and the current state. The steps in the run through a state machine
are depicted in figure 1.


                         .----------<---------------.
                         |                          |
               Begin -------> Operations -----> Transitions -----> Exit
                                                       

           Figure 1: The run through a state machine

Each phenomenon can be associated with a set of variables by which it is
determined. The line and column numbers are determined by the current line and
column number and the previous line and current number, for example. The sets
of variables which are associated with an investigated procedure, is called
SOV.

DEFINITION: SOV -- Set of Variables

    The term 'set of variables' SOV shall stand for the set of all
    variables which are relevant to the investigated behavior. 

A state machine changes variables of the SOV. These changes are consequences of
operations that happen in states. Let an 'action' be defined as follows.

DEFINITION: Action -- '(op, i)'

    An action '(op, i)' this context, denotes an *operation* 'op' which is to
    be performed and the *state* 'i' in which it is to be performed.  The
    operation is a write or change operation to a variable from the SOV. 


-------------------------------------------------------------------------------

LINEAR STATES AND MOUTH STATES:

Two central concept of the analysis algorithms are 'linear states' and 'mouth
states' as they are defined in the paragraphs to follow. They differ in the way
how actions that happen before influence the SOV behind them.

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

       SOV(b) = (op, b) on SOV(a)
       SOV(c) = (op, c) on SOV(b)
       SOV(d) = (op, d) on SOV(c)
       SOV(e) = (op, e) on SOV(d)
              = (op, e) on ((op, d) on ((op, c) on ((op, b) on SOV(a))))
                 
The SOV in figure 2 is 'x' and the action in figure 2 is 'x = x + 1'. Thus,
with 'x(i)' as the 'x' in state 'i' the sequence in the becomes:
    
                          x(b) = x(a) + 1
                          x(c) = x(b) + 1
                          x(d) = x(c) + 1
                          x(e) = x(d) + 1
                         
Or, shortly              
                         
                          x(e) = x(a) + 4
       
This highlights that along a sequence of linear states operations can be
accumulated efficiently. In the example above, a longer sequence of additions
was transformed into a single transition at exit. The accumulated action
'Accu(i,k)' description of what actions are required in a state in order to
compensate for previous actions. 

DEFINITION: Accumulated Action 'Accu(i, k)'

   An Accumulated Action 'Accu(i)' describes how the setting of SOV in the
   state 'i' can be determined based on some initial setting of SOV in another
   state and the sequence of actions which influences the SOV in state.

   An 'Accu(i)' also maintains information about which of its elementary
   operations require what action in previous states.

If upon entry into state 'i' operations according to Accu(i) are performed,
than any history of transactions before is unimportant.

Accumulated actions are associated with *absolutely necessary* actions
and *potentially necessary* actions. An absolutely necessary action in the
example of figure 2 would be that the value of 'x' is stored 'x(a) upon entry
in state 'a'. Only then, the subsequent operations reduce to 'x = x(a) +
constant'. Potentially necessary actions, are the increments 'x = x + 1' in
each state. They become necessary, if no other simplification is possible.

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
elements. If PA(i, x), the action to be avoided, was unknown, then there would
be no point in an Accu(i).

Accumulated actions can be developed along linear states, because for each
linear state there is only one predecessor SOV. The accumulated action provides
represents the effect of actions of previous states, thus not requiring the
actions in the states along the ransitions.

Let the development of accumulated actions along linear states be called the
'walk along linear states'. It can only start at states 'i' where Accu(i),
AA(i), and PA(i) are determined. Let the term spring denote a state that
can act as the begin for a walk along a sequence of linear states.

DEFINITION: Spring

    A spring is a state where a walk along a sequence of linear states can
    begin. For a state to act as a spring Accu(i), AA(i), and PA(i,x) must be
    completely determined. 

Whatever preceded the entry into a spring state, it is reflected in Accu(i),
AA(i), and PA(i,x). Thus, it can be treated without knowing the exact history
of state transitions. The same is true for all linear states that branch from
it--until a so called mouth state is reached. Mouth states are the counterpart
to linear states. 

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
directly from state 0, where 'x=x(0)+1'. Second, there is an entry from
state 2. There, the accumulated action is 'x=x(0)+2'. The setting of 'x'
depends on the path that is taken.  In state 3, it cannot be known
beforehand, how much on has to add to 'x(0)'.  In the example, one cannot
derive an accumulated action from the entries. The incremental actions can
now either be implemented at their original positions, or at the entry into
the mouth state. The later, requires less computational effort, and is
therefore preferable.


                  [x=x(0)+1]
                 ------------. 
                              \  x(3)=x         [x=x(3)+1]
                               >--------->( 3 )------------> 
                              /
                 ------------' 
                  [x=x(0)+2]

         Figure 5: Interference of accumulated actions in mouth states.


The actual path taken to a mouth state is something that is only determined at
run-time. Thus, in general the outgoing accumulated action can only be different
from 'void' if there is some type of uniformity. Let the process of 'action
interference' be defined as follows.

DEFINITION: Action Interference

    The process of 'action interference' develops an accumulated action based
    on multiple accumulated actions at the entries of a mouth state. The output
    accumulated action is either void or specific.

    The output can be determined to be void, as soon as two entries are not of
    'sufficient uniformity'. 

    A specific output can only be determined if all accumulated actions at
    all entries share a 'sufficient uniformity'.

DEFINITION: Sufficient Uniformity for Action Interference

    A set of accumulated actions { Accu(k), for some k } contains sufficient
    uniformity if there is a procedure that can translate the set into a single
    accumulated action Accu(i). Further, the AA(i) and PA(i) must be determined.

I follows, that if entries in a mouth state share sufficient uniformity they
can be considered as springs. The determined accumulated actions is achieved
by interference. As springs, they become begin states for the walk along a
sequence of linear states, as described in the next section.

-------------------------------------------------------------------------------

THE WALK ALONG LINEAR STATES

There is a duality between linear states and mouth states with respect to 
run-time dependency. It is expressed as follows.

STATEMENT: Run-time dependence.

    Linear state sequences do never depend on run-time. Their behavior is 
    determined by their predecessor state and the operation at entry into
    the state.

    Mouth states may depend on run-time. The path by which they are entered
    determines what actions have been applied. 

A recursive walk along sequences of linear states is part of any analysis.
Linear states can have transitions to more than one state. So, the walk along
linear states is a recursive 'tree-walk'. The termination criteria for
the walk along linear states is defined as follows.

DEFINITION: Termination criteria for walk along sequence of linear states.

    A recursive walk along sequences of linear states does not enter the
    state ahead, if 

       (i)   there is no state. The current state is a terminal.
       (ii)  the state ahead is a mouth state.
       (iii) the state ahead complies to the conditions of a spring.

The first condition comes natural. The second condition exists, because actions
cannot be accumulated beyond mouth states. The third condition tells that the
walk stops where another walk begins. The tree cannot contain loops, since a
loop requires a state with more than one entry. 

With these concepts, a first draft of an algorithm for the determination of
accumulated actions can be defined.

             (*) Start.
             (*) begin_list = springs extracted from state machine.
   .-------->(*) perform linear walks starting from each spring.
   |             --> Accu(i) linear states until terminal, mouth, or specific 
   |                 states.
   |             --> entries of mouth states receive accumulated actions.
   |         (*) perform interference in mouth states where all entries are
   |             determined.
   '-- yes --(*) are there specific mouth states? --> new springs.
             (*) Stop.

        Algorithm 1: Accu(i) derived in states by action accumulation 
                     and interference.

When this algorithm comes to an end, there might be still mouth states with
undetermined entries. The only possible reason for that are mutual dependencies
between mouth states. Such dead-locks are handled in the next section.

-------------------------------------------------------------------------------

DEAD-LOCK STATES

Dead-lock states are states with undetermined entries. Their entries are 
undetermined, because they depend on states, which in turn depend on them.
An example is shown in Figure 4.

                           .------------>( 2 )
                     A     |             /   \
                ... ---->( 1 )          (     )
                           |             \   /
                           '------------>( 3 )
         
        Figure 4: A dead-lock of mouth states 2 and 3.

The human can judge easily, that for both states only pattern A can occur.  The
following paragraphs, however, formally describe a precise procedure to
determine the entries and the output of dead-lock states.

DEFINITION: Dead-lock state.

    A dead-lock state is a mouth state for which there is no Accu(i) and AA(i)
    when algorithm 1 came to end end. 

      -- it has at least one unresolved entry.

      -- it depends on other dead-lock states.

An entry of any mouth state, in particular a dead-lock state, is the terminal
of a sequence of linear states. The linear states originate in a state that is
part of the dead-lock state set, or not. If it originates in a non-dead-lock
state, then the entry into the mouth state is determined, otherwise not. Thus,

DEFINITION: Group of Dead-Lock States.

    A set of mouth states where each state 'i' from the set depends on all 
    other states, is called a 'group of dead-lock' states.

STATEMENT:

    An entry into a dead-lock state which is undetermined originates 
    by a sequence of linear states from another dead-lock state.

If the other dead-lock state may belong to the same group of dead lock states,
or to another group. In the case that the entry depends on the output of a
dead-lock state of another group, the other group must be determined first.
A circular dependency, such as "group A depends on group B, depends on group
C, which depends on group A", is impossible, because this would make all
states of A, B, and C mutually dependent, and therefore build a group
altogether.

STATEMENT:

    Groups of dead-lock states can be organized hierarchically.  Groups on
    which others depend can be determined before groups which depend on them.
    
    As a direct consequence, for any set of groups of dead-lock states there
    is a sequence of resolution so that all groups become determined.

From the existence of a non-cyclic hierarchy of dependence between dead-lock
state groups, it can be concluded that there is always at least one dead-lock
group with no dependency to another. Once this dead-lock group is resolved, 
another group becomes independent, and can be resolved. Thus, it is safe to
assume that by iteratative resolution of independent groups, finally all 
dead-lock states end up being determined.

                          dead-lock group
                         .----------------------.
                 Accu(1) :      .---->----.     : Accu(4)
            .-------------->( 2 )        ( 4 )<-------
            |            :   / \'----<----'     :
      --->( 1 )          :  (   )               :
            |  Accu(3,1) :   \ /                : Accu(3,5)
            '-------------->( 3 )<----------------------------( 5 )<--- 
                         :                      :
                         '----------------------' 

         Figure 5: Dead lock states and their entries.

Figure 5 shows a dead-lock group where all entries into it are determined. The
only influence from outside this group comes through 'Accu(2)', 'Accu(3,1)',
'Accu(3,5)' and 'Accu(4)'. Since states are mutually dependent, there
necessarily exist loops inside a dead-lock group. Thus, the number of
transitions inside the group can only be determined at run-time. The process
of specification of an inherent accumulated action inside a dead-lock group,
can be defined similar to interference as follows.

DEFINITION: Inherent Accumulated Action -- Accu(group)

   The 'inherent accumulated action' Accu(group) is the accumulated action
   that appears at any entry into a dead-lock state from another dead-lock
   state. 

   Accu(group) is determined from the set of specified accumulated actions, at
   specific entries of states of the group. 

   Accu(group) can either not rely on transition numbers at all, or they must
   be relative to the first state through which the group is entered.

   Accu(group) is specified at each entry of the group, except for the specific
   entries which are previously determined.

An issue remains. What if on the linear paths between the dead-lock mouth
states there is an action? This action can only be *undetermined*, otherwise it
was a spring and, therefore, the resulting entry to the mouth state at the end
was determined. The consequences of this undetermined action can propagate
through all states of the dead-lock group. Further, it is not determined
whether it influences the SOV before run-time, or how many times it influences
the SOV. This influences from outside the group are captured by the Accu(i) of
the specific entries. The safest way, to maintain the state machine's behavior,
is by leaving the action in place, implemeting Accu(i) at each entry into
the dead-end state group, and propagating Accu(void) inside the dead-lock
group.

STATEMENT:


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





