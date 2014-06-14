=====================================
 Better scoping for atoms and flows.
=====================================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/taskflow/+spec/improved-scoping

Better scoping for atoms and flows.

Problem description
===================

Currently `atoms`_ in taskflow have the ability to declare, rebind, and receive
automatically needed runtime symbols (see `arguments and results`_) and provide
named output symbols. This feature is required to enable an external entity to
arrange execution ordering as well as to allow for state transfer/retainment
to be performed by a workflow runtime (in this case the `engine`_
concept). This is quite useful to allow for automated resuming (and other
features, such as parallel execution) since when an atom does not
maintain state (or maintains very little) internally, the workflow runtime
can track the execution flow and the output symbols and input
symbols (with associated values) of atoms using
various `persistence strategies`_ (it also allows the engine to notify others
about state transitions and other nifty features...).

**Note:** In a way this externalized state is equivalent to a
workflows *memory* (without actually retaining that state on the runtime stack
and/or heap). This externalization of workflow execution & state enables
many innovative strategies that can be explored in the future and is one of the
key design patterns that taskflow was built in-mind with.

In general though we need to increase the usefulness & usability of the current
mechanism. It currently has some of the following drawbacks (included with
each is an example to make this more clear as to why it's a drawback):

* Overly complicated ``rebinding/requires/provides`` manipulation to avoid
  symbol naming conflicts. For example, when one atom in a `flow`_ produces an
  output that has a name of another atoms input and a third atom in a subflow
  also produces the same output there is required to be
  a `rebinding`_  application to ensure that the right output goes into the
  right input. This results in a bad (not horrible, just bad) user
  interaction & experience.

**Example:**

::

    from taskflow import task
    from taskflow.patterns import linear_flow

    class Dumper(task.Task):
        def execute(self, *args, **kwargs):
            print(self)
            print(args)
            print(kwargs)

    r = linear_flow.Flow("root")
    r.add(
        Dumper(provides=['a']),
        Dumper(requires=['a'],
               provides=['c']),
        Dumper(requires=['c']),
    )

    sr = linear_flow.Flow("subroot")
    sr.add(Dumper(provides=['c']))
    sr.add(Dumper(requires=['c']))

    # This line fails with the following message:
    #
    # subroot provides ['c'] but is already being provided by root and
    # duplicate producers are disallowed
    #
    # It can be resolved by renaming provides=['c'] -> provides=['c_1'] (and
    # subsequently renaming the following requires in the subroot flow) which
    # instead should be resolved by proper lookup & scoping of inputs and
    # outputs.
    r.add(sr)

As can be seen in this example we have created a scoping *like* mechanism via
the nested flow concept & implementation but we have not made it as easy as it
should be to nest flows that have *conflicting* symbols for inputs (aka,
required bound symbols) and outputs (aka, provided bound symbols). This should
be resolved so that it becomes much easier to combine arbitrary flows together
without having to worry about symbol naming errors & associated issues.

**Note:** we can (and certain folks are) using the ability to inject symbols
that are requirements of atoms before running to create a atom local scope.
This helps in avoiding some of the runtime naming issues but does not solve the
full problem.

* Loss of nesting post-compilation/post-runtime. This makes it hard to do
  extraction of results post-execution since it limits how those results can
  be fetched (making it unintuitive to users why they can not extract results
  for a given nesting hierarchy). This results in a bad user experience (and
  likely is not what users expect).

**Example:**

::

    from taskflow.engines.action_engine import engine
    from taskflow.patterns import linear_flow
    from taskflow.persistence.backends import impl_memory
    from taskflow import task
    from taskflow.utils import persistence_utils as pu

    class Dumper(task.Task):
        def execute(self, *args, **kwargs):
            print("Executing: %s" % self)
            print(args)
            print(kwargs)
            return (self.name,)

    r = linear_flow.Flow("root")
    r.add(
        Dumper(name="r-0", provides=['a']),
        Dumper(name="r-1", requires=['a'], provides=['c']),
        Dumper(name="r-2", requires=['c']),
    )
    sr = linear_flow.Flow("subroot")
    sr.add(Dumper(name="sr-0", provides=['c_1']))
    sr.add(Dumper(name="sr-1", requires=['c_1']))
    r.add(sr)

    # Create needed persistence layers/backends...
    storage_backend = impl_memory.MemoryBackend()
    detail_book, flow_detail = pu.temporary_flow_detail(storage_backend)

    # Create an engine and run.
    engine_conf = {}
    e = engine.SingleThreadedActionEngine(
        r, flow_detail, storage_backend, engine_conf)
    e.compile()
    e.run()

    print("Done:")
    print e.storage.fetch_all()

    # Output produced is the following:
    #
    # Executing: r-0==1.0
    # ()
    # {}
    # Executing: r-1==1.0
    # ()
    # {'a': 'r-0'}
    # Executing: r-2==1.0
    # ()
    # {'c': 'r-1'}
    # Executing: sr-0==1.0
    # ()
    # {}
    # Executing: sr-1==1.0
    # ()
    # {'c_1': 'sr-0'}
    # Done:
    # {'a': 'r-0', 'c_1': 'sr-0', 'c': 'r-1'}
    #
    # No exposed API to get just the results of 'subroot', the only exposed
    # API is to get by atom name or all, this makes it hard for users that just
    # want to extract individual results from a given segment of the
    # overall hierarchy.

To increase the usefulness of the storage, persistence and workflow concept
we need to expand the inference, validation, input and output, storage and
runtime  lookup mechanism to better account for the `scope`_ a atom resides
in.

.. _atoms: http://docs.openstack.org/developer/taskflow/atoms.html#atom
.. _arguments and results: http://docs.openstack.org/developer/taskflow/arguments_and_results.html#arguments-specification
.. _engine: http://docs.openstack.org/developer/taskflow/engines.html
.. _scope: https://en.wikipedia.org/wiki/Scope_%28computer_science%29
.. _rebinding: http://docs.openstack.org/developer/taskflow/arguments_and_results.html#rebinding
.. _flow: http://docs.openstack.org/developer/taskflow/patterns.html#taskflow.flow.Flow
.. _persistence strategies: http://docs.openstack.org/developer/taskflow/persistence.html

Proposed user facing change
===========================

To ensure the case where a subflow produces output symbols that conflict with a
contained parent flow we will allow for a subflow to provide the same output
as a prior sibling/parent instead of denying that addition. This means that if
a parent flow contains a atom/flow ``X`` that produces symbol ``a`` and it
contains another atom or subflow ``Y`` that also produces ``a`` the ``a`` which
will be visible to items following ``Y`` will be the ``a`` produced
by ``Y`` and not by ``X``. For the items inside ``Y`` the ``a`` that will be
visible will be determined by the location in ``Y`` where ``a`` is
produced (the items that  use ``a`` before ``a`` is produced in ``Y`` will use
the ``a`` produced by ``X`` and the items after ``a`` is produced in ``Y`` will
use the new ``a``). This type of *shadowing* reflects a concept how people
familiar with programming already use (`variable name shadowing`_).

To allow a flow to retain even *more* control of its exposed input and output
symbols we will introduce the following new flow constructor parameter.

* ``contain=<CONSTANT>``: when set on a flow object this attribute will cause
  the flow to behave differently when intermixed with other flows. One of the
  constants to be will be ``contain=REQUIRES`` which will denote that this
  flow will use only requirements that are produced by the atoms contained
  in itself and **not** try to require any symbols from its parent or prior
  sibling flows or atoms. This attribute literally means the scope of
  the flow will be completly self contained. A second constant (these
  constants can be *ORed* together to combine them in various ways) will
  be ``contain=PROVIDES`` which will denote that the symbols this
  flow *may* produce will **not** be consumable by any subsequent sibling
  flows or atoms. This attribute literally means that the scope of the flow
  will be restricted to **only** using requirements from prior sibling or
  parent flows and the produced output symbols will **not** be visible to
  subsequent sibling flows or atoms.

When no constant is provided we will assume the standard routine of not
restricting input and output symbols and only applying the shadowing rule
defined previously.

**Note:** depending on time constraints we have the ability to just skip the
different ``contain`` constants and just do the shadowing approach (and later
add in the other various constants as time permits).

.. _variable name shadowing: https://en.wikipedia.org/wiki/Variable_shadowing

Proposed runtime change
=======================

During runtime we will be required to create a logical structure which retains
the same user facing constraints. To do this we will retain information about
the atom and flow `symbol table`_ like hierarchy at runtime in a secondary
tree structure (so now instead of *just* retaining a directed graph of the
atoms and flows prior structure we will retain a directed graph and a tree
hierarchical structure).

This tree structure will contain a representation of the hierarchy that
atoms were composed in and the symbols being produced at the different levels.
For example an atom in a top level flow will be at a higher level in that tree
and a atom in a subflow will be at a lower level in that tree. The leaf nodes
of the tree will be the individual atom objects + any associated metadata and
the non-leaf nodes will be the flow objects + any associated metadata (the main
piece of metadata in flow nodes will be a symbol table, also known as a
dictionary). This structure & associated metadata will be constructed
at compilation time where we presently construct the directed graph of
nodes to run.

This approach allows the lookup of an atoms requirements to become a symbol
table & tree traversal problem where the atoms (now a node in the tree) parents
will be traversed until an atom that produces a needed symbol is located (this
information is verified at preparation time, which happens right before
execution, so it can be assumed there are no atoms that have symbols that are
*not* provided by some other atom).

At compilation time the ``contain=<CONSTANT>`` attribute will also be examined
and metadata will be associated with the created tree node to signify what the
visiblity of the symbol table for that node is. This metadata will be used
during the runtime symbol name lookup process to ensure we restrict the lookup
of symbols to the constraints imposed by the selected attribute/s.

At runtime when a symbol is needed for an atom we will locate the node that
is associated with the atom in the tree and walk upwards until we find the
correct symbol (obeying the ``contain`` constraints as needed) and value. When
saving we will save values into the parent flow nodes symbol table instead of
into the single symbol table that is saved into currently.

Finally, this addition makes it possible for post-execution extraction of
individual tree segments (by allowing for fetching a tree nodes symbol table
and allowing for users to traverse it as they desire). This is often useful
for examining the results flows and atoms produced after the workflow runtime
has finished executed (and doing any further function/method... calls that an
application may wish to do with those results).

.. _symbol table: http://en.wikipedia.org/wiki/Symbol_table

Alternatives
------------

The alternative is not to change anything and require that users go through
a painful symbol renaming (and extraction) process. This works *ok* for
workflows that are controlled and where it is possible to define the flow in a
single function where all the various symbol names can be adjusted at flow
creation time. It does not work well for arbitrary gluing of various workflows
together from arbitrary sources (a use-case that would be expected to be common
in the OpenStack projects, where drivers *could* provide components of an
overall workflow). Without this change it would likely mean that there would be
various functions created by users that would have *messy* and
*complicated* symbol renaming algorithms to resolve the issue that taskflow
should instead resolve itself. This results in a bad user experience (and
likely is not what users expect).

Impact on Existing APIs
-----------------------

The existing API's will continue operating as before, when the new options
are set the functionalty will change accordingly to be less strict. Now instead
of duplicate names causing errors a new mode will be enabled by default, the
variable shadowing mode. This will allow flows that would have not been
allowed to be created before now to be created. In general this will be an
additive change that enables new usage that errored out before this change.

Security impact
---------------

N/A

Performance Impact
------------------

N/A

Configuration Impact
--------------------

N/A

Developer Impact
----------------

This scoping should make it easier to implement flows in a manner that
conceptually makes sense for programmers used to the standard scoping
strategies that programming languages come built-in with.

Implementation
==============

Assignee(s)
-----------

Primary assignee:

* harlowja

Other contributors:

* dkrause?

Milestones
----------

J/3

Work Items
----------

* Add a tree type [https://review.openstack.org/#/c/97325/]
* Add ``contains`` constraints to flows and adjust pattern ``add()`` methods
  to accept and verify those constraints at atom/subflow addition time.
* Retain symbol hierarchy at compilation time by constructing a tree instance
  and during the directed graph creation routine adding nodes to this tree as
  needed (along with any other metadata needed).
* Adjust the compilation routine to retain this ``contains`` attribute in the
  tree nodes metadata so that it can be using at runtime.
* Adjust the action engine implementation to use this new source of information
  during symbol lookup so that this new information is used during runtime.
* Expose the results of running via a new api that allows for fetching a named
  atom/flows storage resultant ``node`` (this allows for traversing over the
  symbol tables for children nodes contained there-in).
* Test like crazy.

Future ideas
------------

* In a future change we could support the ability to have automatic symbol
  names that would be populated at compilation time. This would allow the flow
  creator to associate a ``<anonymous>`` like object as the symbol that will
  be transferred between tasks/atoms (which right now is required to be
  a string). The ``<anonymous>`` object instance will be translated into
  a *actual* generated symbol name at compilation time (the runtime symbol
  lookup mechanism will then be unaffected by this change). This would help
  those users that can not use the above new capabilities. It would allow those
  users to have a way to transfer symbols between scopes without
  being *as* restricted by literal string names.

Incubation
==========

N/A

Documentation Impact
====================

Developer docs, examples will be updated to explain the new change and provide
examples of how this new change can be used.

Dependencies
============

N/A

References
==========

N/A

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

