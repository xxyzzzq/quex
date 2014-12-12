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

The resulting state machine is described in terms of 'multi-entry states'.
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

    A linear state is a state that is entered only from one predecessor state.

The concept of a linear state is shown in figure 3. The operation 'op(i)' works
on the 'SCR(k)' before entry and produces 'SCR(i)'. Note, that a linear state
may have transitions to multiple successor states, but only on predecessor state.


                                                      .---> 
                                                     /
                                                   .-.
                      --------[ op(i) ]---------->( i )---> 
                     SCR(k)              SCR(i)    '-'

                    Figure 3: The concept of a linear state.


DEFINITION: Mouth State

    A mouth state is a state that is entered from more than one predecessor 
    state. 
    
Figure 4 displays the concept of a mouth state and the development of the
'SCR(i)' based on the SCRs of predecessor states.

                  ------>--.  
                 SCR(a)     \ 
                             \                       .-.
                  ------>-----+---[ op(i) ]---------( i )---> 
                 SCR(b)      /               SCR(i)  '-'
                            /
                 ...       :
                  ------>--'
                 SCR(z)

                    Figure 4: The concept of a mouth state.

In a linear state the 'SCR(i)' can be determined based on the predecessor's
SCR and the 'op(i)'

            SCR(i) = op(i)(SCR(k))                                          (1)

with 'k' as the one and only predecessor state. If 'SCR(k)' is known, then
'SCR(i)' of a linear state is known off-line purely from the consideration of
the state machine.  In a mouth state 'SCR(i)' is be determined depending on the
state from where the transition originates.

                      /  op(i)(SCR(a))  if entry from state 'a'
                      |  op(i)(SCR(b))  if entry from state 'b'             (2)
            SCR(i) =  |   ...
                      |  
                      \  op(i)(SCR(z))  if entry from state 'z'

Let 'recipe' be the procedure to determine the SCR in a state without
considering any previous operation. That is, if for all states all recipes are
known, then all operations along the state machine transitions can be removed.
Let the term recipe be defined as follows.

DEFINITION: R(i,k), R(i) -- Recipe 

   Let 'i' indidate a state and 'k' its predecessor state. A recipe R(i,k)
   allows to determine 'SCR(i)' without execution of operations along the
   transitions. It is derived from the operation 'op(i)' and 'SCR(k)'.  The
   recipe's procedure uses solely the following inputs:

          * 'h(i)', the hidden variables of the current state,
          * 'Aux', the setting of auxiliary registers

   It implements the mapping

                  (h(i), Aux) ---> SCR(i)                                   (3)

   Let 'R(i)' indicate the recipe which appears to the successor states of
   state 'i'.

Hidden variables are, for example, the input position of the current stream or
the lexeme start position. Auxiliary registers may contain data that has been
stored in previous states. To express SCR(i,k) in equation (2) by means of a
recipe 'SCR(k)' must have been stored in auxliary registers. The recipe 'R(i)'
may be used to replace 'SCR(i)'. For linear states is is identical to 'R(i,k)';
for mouth states it is not. This is discussed in the next section.

The fundamental difference between 'R(i)' and 'SCR(i)' is that former is a 
procedure and the latter represents the values which are produced.

The simplest form of a recipe is the setting of the SCR with constant values.
For example, at a state entered by the newline character the recipe for 'column
number' may be 'column number = 0', because a new line begins. The advantage
of recipes is demonstrated figure 5.


    a)        op(1) =             op(2) =          
                'la = 10'           'la = 12'        

       ...  -------------->( 1 )-------------->( 2 )----> ...
                             :                   :
                     goto Terminal(la)   goto Terminal(la)


    b)                    SCR(i) =            SCR(2) =              
                     'acceptance = 10'   'acceptance = 12'                     

       ...  -------------->( 1 )-------------->( 2 )----> ...
                             :                   :
                         goto T10            goto T12

     Figure 5: Equivalent state sequences. a) Relying on operations along
               transitions. b) With SCRs determined by recipes.

In figure 5.a operations are executed at each transition step. They assign
identifiers to the 'last acceptance' register 'la'. This assignment happens
even if states '1' and '2' are passed by and later states may detect another
acceptance. Upon drop-out from state 1 or 2 a conditional goto to a terminal is
applied based on the setting of 'la'. 

In figure 5.b the operations along transitions are completely removed. The
recipes determined the acceptance apriori, so that a direct goto to the
correspondent terminal can be applied.  Clearly, the second approach requires
less computational effort during transitions and at drop-out.

-------------------------------------------------------------------------------

BASICS ON PROPAGATION OF RECIPES

A recipe for one state may be the basis for the development of the recipe of
its successor state. For a linear state, equation (1) described how 'SCR(i)' is
determined from the predecessor's 'SCR(k)' and the entry operation 'op(i)'. If
'SCR(k)' can be determined by a recipe 'R(k)', then 'SCR(i)' becomes

                     SCR(i) = op(i)(R(k))                                   (4)

Since, a recipe 'R(k)' is already independent of operations along transitions,
the recipe for 'SCR(i)' becomes nothing else than the expression that
determines it. That is,

                     R(i) := op(i)(R(k))                                    (5)
                 
The derivation of a recipe based on a predecessor's recipe is defined here as
'accumulation'.

DEFINITION: Accumulation

    Given a state 'i', its predecessor state 'k', the entry operation 'op(i)'
    the predecessor's recipe 'R(k)', the recipe to 'R(i,k)' is equivalent
    to the concatenated operations of 'op(i)' and 'R(k)'.

    A prerequisit for accumulation is that 'R(k)' of the predecessor is 
    determined.

EXAMPLE:
 
                  op(b)=        op(c) =      op(d) =
                    x=x+1         x=x+1         x=x+1        
            ( a )-------->( b )-------->( c )-------->( d )--------> ...


                  Figure 6: A sequence of linear states.


Figure 6 displays an example of an SCR containing a single variabe 'x'. The
operations 'op(i)' upon transition are for all transitions 'x = x + 1', i.e.
increment 'x' by 1. Let the SCR in state 'a' be known as a register of 'Aux'
and let it be called 'xa'. The simplest form of a recipe is here represented
by 'R(a)':

               R(a) = { x := xa }                                           (6)

The recipe 'R(b,a)' must be equivalent to the concatenated execution of 
'op(b)' and 'R(a,*)', i.e.

                   { x := xa }
                   { x := x + 1 }
So, 
               R(b) = { x := xa + 1 }                                       (7)

and through iteration

               R(c) = { x := xa + 2 }
               R(d) = { x := xa + 3 }                                       (8)

If the state machine exits at 'a', 'b', 'c' or 'd' the content of 'x' can be
determined without relying on the intermediate operations { x:=x+1 }. This
is shown in figure 7.
 
          ( a )-------->( b )-------->( c )-------->( d )--------> ...
                          :             :             :
                        x = xa+1      x = xa+2      x = xa+3


          Figure 7: Recipes upon exit replace transition operations.

The repeated accumulation of recipes along linear states comes to an end at
mouth states.  Equation (2) described the development of the SCR in mouth
state. Using the concept of a recipe, the equation can be rewritten as

                     /  R(i,p)  if entry from state 'p'
                     |  R(i,q)  if entry from state 'q'
            SCR(i) = |   ...                                                (9)
                     |  
                     \  R(i,z)  if entry from state 'z'

The applied recipy depends on the origin state of the transition which is only
determined at run-time. However, a recipe 'R(i)' for a mouth state can be
determined as follows. For each register of the SCR there are two
possibilities:

   Homogeneity:   All entry recipes apply the exact same process to
                  determine the register's content.

   Inhomogeneity: Two or more entry recipes apply a different process
                  to determine the register's content.

If a register is determined homogeneously, then the part of the recipes that
determines the register can be overtaken into 'R(i)'. Otherwise, the value
must be computed upon entry and stored in an auxiliary register. The recipe
'R(i)' must then rely on the stored value in the auxiliary register. Let this
process be defined as 'interference'.

DEFINITION: Interference

    The process of 'interference' develops a recipe 'R(i)' for a mouth state
    'i' based on incoming recipes 
    
                  IR = { R(i,k): k = 1...N }. 
                  
    An incoming recipe 'R(i,k)' implements the concatination of 'op(i)(R(k))'.

        * Procedure elements that are the same for all recipes in 'IR'
          *can* be overtaken into 'R(i)'.

        * Procedure elements producing different register settings 
          *must not* be overtaken. Their results need to be stored in 
          auxiliary variables and 'R(i)' *must* refer to those.

Interference requires that all incoming recipes are determined. As long as this
is not the case, 'R(i)' cannot be determined. Further, no successor state's
recipe can be determined through accumulation. In other words,  a mouth state 
blocks any propagation of recipes as long as not all incoming recipes are
determined. To the contrary, the propagation of recipes may only start at
states with determined recipes. 

DEFINITION: Spring

    A state with a determined recipe is a spring. A spring is the basis
    for accumulation of recipes.
    
To start developing recipes, one must first determine the 'springs' in the
state machine. In practical applications, it requires a very detailed and
subtle investigation to determine spring states. A safe approach is to 
consider only the initial state as an initial spring.

-------------------------------------------------------------------------------

THE WALK ALONG LINEAR STATES

The recipes for states are determined by a 'walk' along linear states. While
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
entry. The third condition tells that the walk stops where another walk begins
or began.  With these concepts, a first draft of an algorithm for the
determination of recipes can be defined.

          (*) Start.
          (1) springs = initial springs of state machine.
   .----->(2) perform linear walks starting from each spring.
   |          --> determine R(i) along linear states until terminal,
   |              mouth, or springs.
   |          --> entries of mouth states receive entry recipes.
   |      (3) interference in mouth states with complete sets of entry
   |          recipes.
   |      (4) springs = determined mouth states
   '- no -(5) springs empty?
          (*) Stop.

        Algorithm 1: Determination of recipes.

When this algorithm comes to an end, there might be still mouth states with
undetermined entries. The only possible reason for that are circular
dependencies between mouth states. 

PROOF: Unresolved mouth states inhibit circular dependency.

Let 

        U := set of unresolved mouth states after algorithm 1 ended.       (10)

An unresolved mouth state 'i' must have at least one unresolved incoming
recipe. Thus one of its predecessor states, let it be named 'k', must be
unresolved. If 'k' is a mouth state, then it must be unresolved.  If state 'k'
is a linear state, then its predecessor must be unresolved, the same holds for
k's predecessor, etc. until a mouth state is reached. Thus, the unresolvedness
of a mouth state has its reason in the unresolvedness of at least one other
mouth state. 

Let the fact that a mouth state 'i' is unresolved because of another unresolved
mouth state 'k' be noted as "i depends on k". 

DEFINITION: D(i) -- Dependency Set 

    If 'i' is a dead-lock state, then the dependency set 'D(i)' contains
    all states that 'i' requires to be determined, before it can be determined.

If any state 'k' in 'D(i)' depends on another state 'p' then 'i' also depends
on it, i.e.

                   k in D(i) <=> D(k) is subset of D(i)                    (11)

The number of states in a state machine is finite, thus 'D(i)' is finite. Since
every state in 'D(i)' is unresolved, every state in 'D(i)' must depend to
another state that is unresolved. All of those states are equally in 'D(i)'.
Let the number of elements in 'D(i)' be 'n'. If the states of 'D(i)' were
displayed as dots in a plane, and the dependencies between states as arrows,
then there would be 'n' arrows between 'n' dots. This is only
possible, if there is at least one loop (proof is trivial). Thus, 

         U is not empty <=> there is at least one circular dependency      (12)

what was to be proven.  

It is this circular dependency that cause algorithm 1 to finish without
terminating the job. The following section considers the resolution of those
circular dependencies.

-------------------------------------------------------------------------------

DEAD-LOCK STATES

Dead-lock states are states with undetermined entries and circular
dependencies.  


DEFINITION: Dead-lock state.

    A dead-lock state is a mouth state 'i' which could not be resolved with 
    algorithm 1. It either directly or indirectly depends on a mouth state
    that depends on a circular dependency. 


An example is shown in Figure 4 where state '2' and '3' block each other from
being determined. For a human observer, it is obvious that the group is
effected by the same recipe 'R(1)' and therefore 'R(2)' and 'R(3)' are
trivially defined. The following discussion, presents a formal and general
solution for dead-lock states.

                                   R(1)
                           .------------>( 2 )
                           |             /   \
                ... ---->( 1 )          (     )
                           |       R(1)  \   /
                           '------------>( 3 )
         
        Figure 8: A dead-lock of mouth states 2 and 3.

Dependencies correspond to paths of linear states between mouth states. If
there are circular dependencies, then this corresponds to loops in the graph
model.

DEFINITION: Dead-Lock Group.

    A dead-lock group is a set of mouth states that were undetermined
    after algorithm 1. It further holds that if and only if two states
    'i' and 'k' depend mutually on each other, i.e.

              i \in D(k)    and     k \in D(i)                             (13)

    then both states are part of the same dead-lock group.


If 'k' depends on 'p' and 'i' depends on 'k' then 'i' also depends on 'p'.
Thus, if 'i' and 'k' are in a dead-lock group 'L' and for a state 'p' 
  
              p \in D(k)    and    k \in D(p)
 
then 'p \in D(i)'. Vice versa, it can be proven that 'i in \D(p)'. It follows
that for a dead-lock group 'L'

                 i \in L  =>  i \in D(k) for all k \in L

This proofs the following statement.

STATEMENT 1:

    Every state 'i' of a dead-lock group 'L' is element of all dependency sets
    'D(k)' for 'k  \in L'. More concisely:
    
                 D(i) is superset of L, for all i in L                      (14)

An example may be observed in figure 9. 

                     .---->---.             .---->---.
                  ( i )      ( k )<------( p )      ( q )
                     '----<---'             '----<---'

                  Figure 9: Example two dead-lock groups.

The dependency groups for i, k, p, and q are as follows

           D(q) = { p, q }
           D(p) = { p, q }
           D(k) = { i, k, p, q }
           D(i) = { i, k, p, q }

A first dead-lock group would be 'L0 = { p, q }'. It holds

           L0 is subset of D(p) and D(q)

The second dead-lock group is 'L1 = { i, k }', because and it holds

           L1 is subset of D(i) and D(k)

The group '{i, k, p}' cannot be a dead-lock group, because

           D(p) is not a superset of {i, k, p}.

STATEMENT 2:

    From condition (13) it follows that any to states 'p' and 'q' in a dead-
    lock group are related by 

              p \in D(q)    and     p \in D(q)                            (15)
    
PROOF 2: 

If any two states 'i' and 'k' belong to a dead-lock group L0 = {i, k, ...},
then it must hold

                       D(k) is superset of L0

and by definition 

                       i \in D(k)

If 'k' was found in another group L1 = {k, ...} with 

                       i not \in L1
                       
then it could never hold 'D(k) is superset of L1' which is a straight
contradiction to the proofs first assumption. If any two states 'i' and 'k'
which belong to the same dead-lock group cannot exist in separate 
dead-lock groups, then groups cannot be devided--which was to be proven.

From (15) it follows that dead-lock groups cannot be devided. In particular,
there cannot be sub-groups of dead-lock groups.

STATEMENT 3:

    A state can only belong to one dead-lock group.

If there was a state 'i' belonging to two dead-lock groups L0 and L1, then
there must be a 'p \in L0' and a 'q \in L1' with

            i \in D(p)     and      p \in D(i)
and
            i \in D(q)     and      q \in D(i)

If 'p depends on i' and 'i depends on q', then 'p depends on q'. Analogously,
it follows 'q depends on p'. That is,

             p \in D(q)    and     q in D(p)

which requires that 'p' and 'q' are in the same dead-lock group. This
contradicts the initial assumption. Thus, a state can only belong to one
dead-lock group--which was to be proven.

PROOF 3: 

As has been shown, if any two states 'i' and 'k' belong to a dead-lock group,
then


Let two states 'i' and 'k' belong to a dead-lock group DLG0 = {i, k, ...}.
If two dead-lock groups DLG0 and DLG1 are different, then there must be a 'k'
where

              k is element DLG0    and    k is not element DLG1
    
Let 'k' be one of the k-s that makes DGL0 and DLG1 different.  Let 'i' be the
candidate to belong to DLG0 and DLG1. From 'i element of DGL0', it follows

              k is element D(i)

For 'i element of DLG1' one must require

              for all p in DLG1: i is element of D(p)

But if 'i is element of D(p)' and 'i' depends on 'k', then 'k is element of
D(p)'.



If 'i' is in group DLG0, then 'k is element 'D(i)'. For 'i' to be in another
group DLG1, one must require that 'D(i) is superset of DLG1'. This is impossible
because 'DLG1' lacks 'k'.
    
    Assume 'i' belongs to a group of states on which it depends, then it
? cannot belong to a group that does not have all those other states. Otherwise,
? the other group would not be complete. Since there can be no groups which are
? sub groups of others, a state can therefore only belong to one group.

However, there may be more than one dead-lock group where one group depends on
the other. Consider a dead-lock group where states 'i' and 'k' are circularly
dependent. State 'k' depends on a state 'p', but 'p' not on 'k'. However, 'p'
is circularly dependent on 'q'. This is depicted in figure 6.

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

