Overview
========

.. role:: red
.. role:: orange
.. role:: green

.. image:: ../_static/images/overview.drawio.svg
  :alt: overview diagram

The metaphoric model is the agent (the brain) is trying to solve the rubric (proof state). Of one step, the agent do actions allowed by the proof state. The proof state can be observed by the agent.

Example of match rule action:
r34 AA Similarity of triangles (Direct)
eqangle B A B C Q P Q R, eqangle C A C B R P R Q, sameclock A B C P Q R => simtri A B C P Q R

It does the same procedure to each premise. For example to eqangle B A B C Q P Q R, it has a predicate, the functions in the predicate eqangle class is responsible for checking it, and construct explicitly the dependency to support it. Note that the premises in the new dependency may not be explicit in the dependency graph before, whence the whole story of symbolic graph and AR module.

Now if all premises are checked, they can be constructed into a dependency, i.e. a hyper edge that can be added into the hyper graph.

Proof State
-----------

implementation: :class:`newclid.proof.ProofState`

The :green:`Proof State` is the main body of Newclid,
it allows to build a proof step by step.
Each :red:`Action` type will trigger a different kind of step (apply, match, aux, ...),
and each step will use sub-components of the :green:`Proof State` that represent its internal state.

The main sub-components of the :green:`Proof State` are listed here:

- :ref:`Dependency Graph` stores all discovered statements and their dependencies (why are they true).
- :ref:`Symbols Graph` stores all symbols (points, lines, circles)
  and their potential equalities.
- :ref:`Trace Back` uses the :ref:`Dependencies` to build and print the final proof.
- Construction


Deductive Agent
---------------

There is a :ref:`Run Loop` that is making the :ref:`Agent` manipluating the proof state and gathering statistics.

How is a Problem Built
----------------------

With given problem in JGEX,
Newclid will load the definitions (default to :code:`src/default_configs/defs.txt`)
and the rules to be used (default to :code:`src/default_configs/rules.txt`).

Next, the builder will construct the problem itself.
This means compiling the information of the problem in two directions:
the symbolic statements (proof state, dependency graph, and symbols graph)
and the numerical representation (numerical coordinates of points).

Symbolically, the builder checks if the symbolic conditions for each definition are satisfied,
and adds the predicates assigned to each point to the proof state.

The numerical representation is built by calling the functions on the :ref:`Sketch` module.
It will then be used in the construction of the pictures in the problem,
but also for checking numerically for some predicates
(non-collinearity, non-parallelism, non-perpendicularity, different points).
Specifically, when building a problem, the goal will numerically check to validate the problem.

This serves two purposes:

1. A sanity check for the user, that tells if the problem is well-written or not.
2. the construction functions have intrinsic degrees of freedom, some of which may not be compatible with the problem (non-degeneracy conditions).
   If one of those is randomly hit by a construction, the goal will not be satisfied and the builder will start building again from scratch.
   This will be attempted a fixed number of times (max_attempts) before the program decides that the goal is not reacheable,
   on the assumption that the probability of a failure at random is low.


With given problem in Geogebra, Newclid uses then the definitions of Geogebra, translates the symbolic construction to premises and symbols graph elements and gets the numerical coordinates from the :code:`.ggb` file.

Usage of the numerical coordinates:
- numerical predicates
- graphics

Problem Solving
---------------

The agent has access to the proof state object. It can thus make observations on it (e.g. rules matching, graphics, ...) and apply dependencies to modify the proof state for it to reach the goals.

Matching and Caching
^^^^^^^^^^^^^^^^^^^^

c.f. awd

Writing the Proof
-----------------

Once the goal statement is check symbolically by the solver,
in general it will have covered a wide graph of statements that do not necessarily contribute to the proof.
To have a clean and coherently written proof, the newclid uses a traceback,
that tries to find the shortest straight path from the premises to the goal through the proof graph
(for more details see :ref:`Trace back`).

To be able to keep track of the connection between the steps taken on the graph,
an important part of the proof construction is the dependency structure,
that assigns to each statement a list of reasons for why that statement was added to the graph.
More info on :ref:`Dependencies`.


Translating to natural language
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After the traceback structures the proof,
the predicates are translated into (pseudo) natural language by a script
(see :ref:`Proof writing` and the :code:`pretty` function for each predicate).

The written proof constains the hypothesis ("From theorem premises"),
which are the points effectively present in the goal,
intermediary points ("Auxiliary Constructions") used in the proof,
and the proof steps.

Constructions given in the statement of the problem but that do not show up in the proof will not be present.

Each proof step lists the premises used for the step, the consequence,
and the reason (dependency) that makes it true.
All steps are numerated to help follow the proof.
