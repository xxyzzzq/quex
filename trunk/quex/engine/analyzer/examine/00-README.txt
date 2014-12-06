Operation Reduction/Operation Postponing

(C) Frank-Rene Schaefer
-------------------------------------------------------------------------------

ABSTRACT:

This file describes the theoretical background for the process applied by Quex
used to reduce the number of operations or to postpone operations. Any write
operation that can be avoided during state transitions may bring a strong
performance increase (due to avoided cache misses, for example). 

The analysis requires a state machine which is composed of 'single-entry
states'. That is, upon entry into a state the same operations are executed
independently from where it is entered or through which transition.  The
analysis tries to exploit predictable sequence of operations along state
transitions. This is done by compensating them through a single operation or by
postponing them to a state as late as possible.  Operations are preferably
postponed, because earlier states are passed more often than later states.

The optimized state machine will be described in terms of 'multi-entry states'.
That is, the operations applied upon entry into a state may be different
dependent from which state or through which transition the entry happens.
Figure 1 shows a single-entry state and a multi-entry state.

           a)
     
                  ---------.
                            \                       .-----.
                  -----------+---[ operations ]----( state )----->   
                            /                       '-----'
                  ---------'       
     
           b)
     
                  ---[ operations 0 ]----.
                                          \         .-----.
                  ---[ operations 1 ]------+-------( state )----->  
                                          /         '-----'
                  ---[ operations 2 ]----'       


      Figure 1: Two approaches of state modelling: a) Single entry state. 
                b) Multi-entry state. 
                
-------------------------------------------------------------------------------

SITUATION:

Incoming characters cause state transitions. Transitions are adorned with
operations, such as 'store last acceptance'. At some point, an incoming
character does not fit a transition map of the current state and the state
machine exits.  Upon such a 'drop-out', some consequences are derived  based on
the passed operations and the current state. The steps in the run through a
state machine are depicted in figure 2.


                    .----------<---------------.
                    |                          |
          Begin -------> Operations -----> Transition -----> Drop-Out
                                                  

              Figure 2: The run through a state machine.

Along the transitions of a state machine many different operations may occur
which do not necessarily share the same subject. Some operations determine the
last accepted pattern, the input position to be restored upon acceptance, the
line and column numbers, the checksum value of a lexeme, or the sum of grapheme
widths of the lexeme's characters, and so on. 

DEFINITION: Investigated Behavior 

   Let the term 'investigated behavior' represent a set of operations and the
   registers on which they operate together with their nominal behavior.

For example, line number counting as an investigated behavior is concerned of
the line number register and any operation that modifies its content. The
nominal behavior is that the line number register should be increased upon
newline and remain the same upon the occurrence of any other character.  Let
the sets of registers which are associated with an investigated behavior be
called SCR.

DEFINITION: SCR -- Set of Concerned Registers

    The term 'set of concerned registers' SCR shall stand for the set of 
    all registers which are relevant to the investigated behavior. 

As a consequence of transitions, a state machine changes the content of
registers. However, not all registers of an SCR are necessarily relevant for
all states. Let the set of required registers be defined as

DEFINITION: RR(i) -- Set of Required Registers

    'RR(i)' defines the registers which are required in state 'i'. The
    registers must be sufficient

      (i)  to implement the investigated behavior upon drop-out and
      (ii) to develop the SCR settings of all successor states.

For example, if the lexeme length is not required in a terminal, then no state
on the path to the terminal is required to contribute to the development of
that register--except that another successor state requires it.  

Let setting of concerned registers be defined as follows.

DEFINITION: SCR(i) -- Setting of SCR registers in state 'i'.

    The term 'SCR(i)' represents the settings of all SCR registers after
    a state 'i' is entered and before it transits further. 

    Only those values of the SCR must be present in 'SCR(i)' which are
    element of 'RR(i)'.
    
An elementary unit that modifies the content of a register is called an
'operation', as defined here:

DEFINITION: op(i) -- Operation 

    A modification to a one or more register of the SCR upon entry into a state
    'i' is called an operation 'op(i)'. 
    
With 'SCR(before)' as the setting of the SCR before entry into a state 'i' and
'SCR(i)' as the setting of the SCR in state the operation 'op(i)' describes the
change in SCR as in the following equation

                         SCR(i) = op(i)(SCR(before))

With the definition of the RR(i) the set of considered operations can be
defined. Given a state 'i', then any operation which directly or indirectly
influences the modification of a register in 'RR(i)' is subject to
consideration of the investigated behavior.
    
The 'RR(i)' for each state can be determined by *back-propagation* of needs. A
state or a terminal which requires a specific register tags all of its
predecessor states with this requirement. That is, if a state 'k' requires a
register 'x', then 'x is element of 'RR(i)' for every state 'i' that lies on
the path to 'k'.

-------------------------------------------------------------------------------

LINEAR STATES AND MOUTH STATES:

Two central concept of the analysis algorithms are 'linear states' and 'mouth
states' as they are defined in the paragraphs to follow. 

DEFINITION: Linear State

    A linear state is a state that is entered only through one predecessor 
    state, i.e. it has only one entry.

                                           .---> 
                                          /
                      ----[ op(i) ]--->( i )---> 

                Figure 3: The concept of a linear state.

Since there is only one predecessor state to a linear state, the SCR can be
derived from the SCR at the predecessor and the single operation at the entry
of the linear state itself. Let 'k' denote the predecessor state of 'i'.  Then,
the characteristic equation for a linear state demonstrates the development
of the SCR

                     SCR(i) = op(i)(SCR(k))                                 (1)

if 'k' is also a linear state with a single predecessor 'p', then the right 
hand of the above equation can be expanded to

                     SCR(i) = op(i)(op(k)(SCR(p)))                          (2)
                 
Thus, the concatenation of operations op(i) and op(k) together with knowledge
about the SCR in state 'k' makes it possible to determine the setting of SCR(i)
without executing each operation along the state transitions. This
concatenation can be continued along an arbitrary sequence of linear states.

The process that allows to determine 'SCR(i)' upon exit without having to 
consider previous operations is defined in this document as 'recipe'.

DEFINITION: R(i,k) -- Recipe 

   Given a state 'i' and its predecessor state 'k', a recipe 'R(i,k)' describes 
   the process to determine 'SCR(i)' based on 

          * 'h(i)', the hidden variables of the current state,
          * 'Aux', the setting of auxiliary registers

   Or, briefly it implements

                  (h(i), Aux) ---> SCR(i)                                   (3)

Hidden variables are, for example, the input position of the current stream, or the
lexeme start position, or other members of the state machine. Auxiliary registers
may contain data that has been stored in previous states. To express SCR(i,k) in
equation (2) by means of a recipe, the setting of SCR(p) must have been stored
in auxliary registers. 

The mapping in (3) does not contain any direct reference to a predecessor state
or its operations.  This expresses essential idea of a recipe which is that it
can determine settings of the SCR for a state without relying on operations
along the path--except for storage in 'Aux'.  It also contains enough
information for successor states to determine their recipes.

The counterpart to linear states are 'mouth states' as defined below.

DEFINITION: Mouth State

    A mouth state is a state that is entered from more than one state. An 
    example is depicted in figure 4.

                     --->--.  
                            \ 
                     --->----+---[ op(i) ]--( i )---> 
                            /
                     --->--'

                Figure 4: The concept of a mouth state.

The characteristic equation for a mouth state expressing the development of the
SCR is

                      .' op(i)(SCR(p))  if entry from state 'p'
                      |  op(i)(SCR(q))  if entry from state 'q'
            SCR(i) = <   ...                                                (4)
                      |  
                      '. op(i)(SCR(z))  if entry from state 'z'

or, in terms of recipies

                      .' R(i,p)  if entry from state 'p'
                      |  R(i,q)  if entry from state 'q'
            SCR(i) = <   ...                                                (5)
                      |  
                      '. R(i,z)  if entry from state 'z'

The state from where the state is entered is only determined at run-time. Thus,
the value of 'SCR(i)' in a mouth state cannot be determined from
considering the state machine alone. Also, if the mouth state's behavior
needs to be expressed through the incoming SCRs, then the single-entry
approach is no longer possible. The characteristic equation (2) imposes a
multi-entry approach for a state description. 

If a recipe is to be defined for a mouth state, then it may be necessary to
store content in auxiliary registers upon entry. 

For that however, the 'SCR(h)' must be determined.

DEFINITION: Determined SCR(i)

   The SCR(i) in a state 'i' is *determined* if, either
   
   (i)  The complete setting of the SCR is known, or
   
   (ii) A procedure is found that allows to determine SCR at runtime.

DEFINITION: Spring

    A state with a determined SCR is a spring.
    
To start developing recipes, one must first determine the 'springs' in the
state machine. In practical applications, it requires a very detailed and
subtle investigation to determine spring states. A safe approach is to 
consider only the initial state as an initial spring.

Any spring 'h' with a linear state successor 'i' can be used to develop the
simplest form of a recipe 'op(i)( SCR(h) )'. Along linear states, there is
always only one distinct entry action. Thus recipes can be developed through an
iterative process. Using the previous recipe, the current operation may be used
to develop the recipe for the current state.

DEFINITION: Accumulation

    The process 'accumulation' determines a recipe 'R(i)' for a linear 
    state 'i'. The recipe is derived from 
    
       (i)  the recipe 'R(k)' of a predecessor state 'k', and
    
       (ii) the entry operation 'op(i)' 
    

EXAMPLE:

Figure 2 displays an example. It demonstrates the aforementioned introduced 
concepts and demonstrates how they can be used to reduce computational effort.

 
                  op(b)=        op(c) =      op(d) =
                    x=x+1         x=x+1         x=x+1        
        ... ( a )-------->( b )-------->( c )-------->( d )--------> ...


                  Figure 2: A sequence of linear states.


The SCR in figure 2 is 'x'. The operation 'op(i)' for all states is the same, 
i.e. 

                      op(b)(x): x = x + 1
                      op(c)(x): x = x + 1
                      op(d)(x): x = x + 1

The simplest form of a recipe could be specified assuming that 'x(a)' is 
determined ('a' is a spring). Then, the recipe for state 'b' is

                      R(b) = op(b)(x(a))
                           = x(a) + 1
  
State 'b' has a linear successor state, so the subsequent recipe can be 
determined by accumulation.

                      R(c) = op(c)(R(b))
                           = op(c)(x(a) + 1) = x(a) + 1 + 1
                           
A repeated application of accumulation results in a recipe for R(d) as

                      R(d) = x(a) + 3

The operations at each transition of the state sequence of figure 2 can now 
be replaced. Instead of computing values at each transition, the recipes are
applied upon exit from the state machine. This is shown in figure 3.
 
 
      ... ( a )-------->( b )-------->( c )-------->( d )--------> ...
                          :             :             :
                        x = R(b)      x = R(c)      x = R(d)


          Figure 3: Recipes upon exit replace transition operations.

The repeated accumulation of operation along linear states comes to an end
at states where there is more than one entry. Let the term 'mouth state' be
defined as follows.


analysis.  As a result of (2) the incoming recipes at the entries may differ.
An example is shown in figure 5. The operation 'op(i)' for each state is
'x=x+1'.  State '2' is reached from state '1' and state '0'. The accumulated
recipe for 'x' differs depending on the entry from which '2' is entered.

                              
                   .------->-----------.  R(2 from 0) = x(0) + 1
                  /   x=x+1             \
                 /                       \
              ( 0 )                     ( 2 )---> ...
                 \                       /
                  \                     /
                   '--->( 1 )----->----'  R(2 from 1) = x(0) + 2
                  x=x+1       x=x+1


       Figure 5: Different recipes at different entries of a mouth state.

Further, in order to cut off the previous history the operations now, must
depend on the entry from where the state is entered. The resulting state
machine must therefore be built upon multi-entry states.

So, there is only one way to determine 'x': it must be computed  upon entry
into the state. Analogously, to accumulation the let 'interference' in mouth
state be defined as follows

DEFINITION: Interference

    The process of 'interference' develops a recipe 'R(i)' for a mouth 
    state 'i'. The interference is based on the recipes for each entry
    into the mouth state. There are two cases:

       (i) For each register of SCR(i) that is treated the same in all 
           recipes, the elements of the recipes CAN be taken in 'R(i)'.

       (i) For any register of SCR(i) where the entry recipes in the 
           entries contain different procedures, the register MUST be
           stored as a reference. 

    In both cases, the mouth state becomes determined and as a result it can
    act as a 'spring'. The option of storing registers as a reference is open
    in any case.

Example: linear successor states of state 2 from figure 5 may develop recipes
based on the stored values in SCR(2). This is shown in figure 6, where state 4
A recipe for state 3 which can be a basis for subsequent linear states must
rely on the stored value for it.

                    x(3):=x(0)+1 
                ... ------. 
                           \        x=x+1       
                          ( 3 )----------->( 4 )------- ...
                           /                 :
                ... ------'             R(4) = x(3) + 1
                    x(3):=x(0)+1 

                   Figure 4: Recipes in a mouth state.

Note, that the register 'x(3)' is not part of the SCR ('x' is, however). Thus,
the newly entered computations 'x(3):=x(0)+1' and 'x(3):=x(0)+3' are not
operations 'op(i)' as defined earlier and are not subject to further
considerations.  

Interference cannot happen, if the set of entry recipes is incomplete. That is,
if for one entry the recipe cannot be determined, then the interference of 
the mouth state cannot be accomplished.


     a)                           b)

           r0                     
          -----.                   ----[ op(r0) ]---.
           r1   \                                    \     rA
          -----( A )---- ?         ----[ op(r1) ]---( A )-----
           r2   /                                    /
          -----'                   ----[ op(r2) ]---'

      Figure 5: Interference.
     
     
Figure 5 shows the effect of interference. It starts the consideration on
incoming recipes (Figure 5.a). If for a register of the SCR there are two
recipes producing a different value, then any operation of incoming recipe
with respect to this register must be executed. The computed value is stored
as a reference. The recipe of the mouth state must refer to this stored
reference.
                 
Once, a mouth state has a determined recipe, it can act as a spring for the
walk along linear states.

-------------------------------------------------------------------------------

THE WALK ALONG LINEAR STATES

The recipes for states are determined by a walk along linear states. While
linear states have only one entry, they may have transitions to more than one
state. So, the walk along linear states is a recursive 'tree-walk'. The
termination criteria for the walk along linear states is defined as follows.

DEFINITION: Termination criteria for walk along linear states.

    A recursive walk along linear states does not enter the
    state ahead, if 

       (i)   there is no state. The current state is a terminal.
       (ii)  the state ahead is a mouth state.
       (iii) the state ahead complies to the conditions of a spring.

The first condition comes natural. The second condition exists, because recipes
cannot be accumulated beyond mouth states. As a direct consequence, the walk
can never go along loops, since a loop requires a state with more than one
entry. A mouth state, however, is never part of the walk according to condition
(ii). The third condition tells that the walk stops where another walk begins or
began.  With these concepts, a first draft of an algorithm for the
determination of recipes can be defined.

          (*) Start.
          (*) begin_list = springs extracted from state machine.
   .----->(*) perform linear walks starting from each spring.
   |          --> determine R(i) along linear states until terminal,
   |              mouth, or springs.
   |          --> entries of mouth states receive entry recipes.
   |      (*) interference in mouth states with complete sets of entry
   |          recipes.
   |          begin_list = determined mouth states
   '- no -(*) begin_list empty?
          (*) Stop.

        Algorithm 1: Determination of recipes.

When this algorithm comes to an end, there might be still mouth states with
undetermined entries. The only possible reason for that are circular dependencies
between mouth states. 

PROOF: 
    
begin_list in algorithm 1 empty <=> there are no new springs.

=> Either: (i) All mouth states were resolved (-> would be springs), or 
           (ii) There are unresolved mouth states, because not all entries
                of those states could be determined.                        (1)

From case (i) no statement about unresolved mouth states can be derived. Case
(ii) makes the first usable statement. Let

        U := set of unresolved mouth states after algorithm 1 ended.        (2)

An entry into a mouth state which is undetermined must be connected through a
linear state sequence, or directly, with a mouth state which is undetermined.
Let the fact that a state 'p' has an undetermined entry originating from 'q' be
called a dependency of 'p' on 'q' and let it be written as 

                               p <-- q

'q' must be undetermined, so it follows

                      p <-- q and p in U => q in U                          (3)

If 'q' depends on 'u', then logically 'u' influences 'q' and 'p'. Thus, 

               p <-- q  and q <-- u   <=>   p <-- { q, u }                  (4)


Let the set of dependencies for a state 'p' be defined as 

                          D(p) = { q, u, ...}                               (5)

which includes every state on which 'p' depends with its 'unresolvedness'. The
number of states in a state machine is finite, thus the size of U is finite. 
It follows 

                         size of D(p) = finite                              (6)
         
From (3) follows that any state 'i in D(p)' must be unresolved, thus it must
be dependent on an unresolved state 'k'. From (4), it follows that if 'p'
depends on 'i', then it also depends on 'k', i.e. 'k in 'D(p)'. 

               i in D(a) and i <-- k => k in D(a)

If the states of 'D(a)' were displayed as dots in a plane, and the dependencies
between elements of 'D(a)' as arrows, then there would be 'n+1' arrows on 'n'
dots. This is only possible, if there is at least one loop. A loop is a circular
dependency.

    size of U is not empty <=> there is at least one circular dependency    (7)

what was to be proven.  However, not every unresolved state is locked into a
circular dependency. An example is shown in figure 6. There, state 2 is
unresolved because it depends on state 1. However, state 2 is not circularly
dependent on state 1. State 1, on the other hand, is unresolved, because it
is mutually depends on state 0.

                             .---->---.             
                          ( 0 )      ( 1 )------>( 2 ) 
                             '----<---'            
                     
     Figure 6: Unresolved state 2 depends on unresolved state 1, but is 
               itself not part of a circular dependency.

-------------------------------------------------------------------------------

DEAD-LOCK STATES

Dead-lock states are states with undetermined entries and circular
dependencies.  An example is shown in Figure 4.

                           .------------>( 2 )
                   op(1)   |             /   \
                ... ---->( 1 )          (     )
                           |             \   /
                           '------------>( 3 )
         
        Figure 4: A dead-lock of mouth states 2 and 3.

In the example shown in figure 4, both states 2 and 3 only experience the
effects of operation 'op(i)'. 

DEFINITION: Dead-lock state.

    A dead-lock state is a mouth state 'i' which could not be resolved with 
    algorithm 1. Additionally, it is part of a circular dependency with at least
    one other unresolved mouth state. As a direct consequence, it follows

       (i)   There is at least one entry to state 'i' with no associated 
             recipe 'R(p(i))'.
      
       (ii)  'i in D(i)', state 'i' is element of the set of states on which
             it depends.

The first characteristic is a tautology to the fact that algorithm 1 was not
able to resolve it. The second characteristic is a reformulation of the finding
of the PROOF of the last section.  Dependencies correspond to paths of linear
states between mouth states. If there are circular dependencies, then, this
corresponds to loops in the graph model.

DEFINITION: Dead-Lock Group.

    A set of mouth states where each state from the set depends on all other
    states, is called a dead-lock group. As a direct consequence of circular
    dependencies, each state in a dead-lock group is connected to at least one
    loop.

STATEMENT:

    A dead-lock group cannot be divided into two sub-groups. 
    
Proof: If any two states 'i' and 'k' belong to a group of dead-locks states,
then they depend on each other circularly. If either one belonged to a
group without the other, then this group cannot be a dead-lock group. It
would be missing a circular dependency. 

STATEMENT:

    A state can only belong to one dead-lock group.

Proof: If a state 'i' belongs to a group of states on which it depends, then it
cannot belong to a group that does not have all those other states. Otherwise,
the other group would not be complete. Since there can be no groups which are
sub groups of others, a state can therefore only belong to one group.

However, there may be more than one dead-lock group where one group depends on
the other. Consider a dead-lock group where states 'i' and 'k' are circularly
dependent. State 'k' depends on a state 'p', but 'p' not on 'k'. However, 'p'
is circularly dependent on 'q'. This is depicted in figure 6.

                     .---->---.             .---->---.
                  ( i )      ( k )<------( p )      ( q )
                     '----<---'             '----<---'

                  Figure 6: Dependent dead-lock groups.

The 'p' an 'q' build a dead-lock group, and so does 'i' and 'k'. All four
states do not build a dead lock group. 'i' and 'k' depend on 'p' and 'q'.
However, 'p' and 'q' do not depend neither on 'i' nor on 'k'.  In the case that
the entry depends on the output of a dead-lock state of another group, then
that other group must be determined first.  

A circular dependency, such as "group A depends on group B, depends on group C,
which depends on group A", is impossible, because this would make all states
of A, B, and C circularly dependent. Therefore, the states of those groups
were, actually, a dead-lock group on their own. Since dead-lock groups are
not divisible, 'A', 'B', and 'C' cannot exist as independent groups.

STATEMENT:

    Groups of dead-lock states can be organized hierarchically.  Groups on
    which others depend can be determined before groups which depend on them.
    
    As a direct consequence, for any set of groups of dead-lock states there
    is a sequence of resolution so that all groups become determined.

From the existence of a non-cyclic hierarchy of dependencies between dead-lock
state groups, it can be concluded that there is always at least one dead-lock
group with no dependency to another. Once this dead-lock group is resolved,
another group becomes resolvable. Thus, by iterative resolution of
independent groups, finally all dead-lock states end up being determined.

                          dead-lock group
                         .----------------------.
                R(1)op(2)|      .---->----.     | R(6)op(4)
            .-------------->( 2 )        ( 4 )<---------------( 6 )<---- 
            |            |   / \'----<----'     |
      --->( 1 )          |  (   )               |
            |   R(1)op(3)|   \ /                | R(5)op(3)
            '-------------->( 3 )<----------------------------( 5 )<--- 
                         |                      |
                         '----------------------' 

               Figure 5: Dead lock states and their entries.

Figure 5 shows a dead-lock group where all entries into it are determined. The
only influence from outside this group comes through 'R(1)', 'R(5)', and
'R(6)'.  Due to the loops in the graph, one cannot preview for any of the
states '2', '3', or '4' in what order or combination the recipes are applied.
Further, no assumptions can be made about the number of transitions which are
made from the entry into the group until a specific state is reached. These
constraints are stronger than the constraints for interference at mouth states.

DEFINITION: Dead-Lock Group Interference

    The process of 'dead-lock group interference' develops a recipe 'R(i)' for
    all unresolved mouth states that are part of a dead-lock group. 
   
    All determined entries are collected into the 'mega-set' of entry recipes.
    Those values of the SCR which are not uniform must be stored in register.
    The resulting recipe 'R(group)' rely on those stored values.
   

An issue remains: What if on the linear paths between the dead-lock mouth
states there is a state with an operation? Clearly, this state cannot be a
spring, otherwise, the mouth state's entry on the other end would be determined
which it is not. Operations of linear states which are not springs accumulate.
Further, dead-lock groups incorporate loops. So, The position where the
operation occurs in the sequence and in what sequence with other operations
cannot be determined. There is only one way to deal with that: The resulting
recipe must be included into the dead-lock state interference. In the state
itself, non-uniform values of the SCR must be stored in registers.

-------------------------------------------------------------------------------

