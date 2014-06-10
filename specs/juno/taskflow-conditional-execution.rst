=======================
 Conditional execution
=======================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/taskflow/+spec/conditional-flow-choices

Allow a level of conditional execution of compiled `atoms`_ (typically
`tasks`_) and associated `flows`_ (aka workflows) that can be used to alter
the execution *path* based on some type of condition and a decided outcome.

.. _atoms: http://docs.openstack.org/developer/taskflow/atoms.html#atom
.. _flows: http://docs.openstack.org/developer/taskflow/patterns.html
.. _tasks: http://docs.openstack.org/developer/taskflow/atoms.html#task

Problem description
===================

Mistral and cinder (and others?) would like to be able to conditionally have
a task or subflow execute based on some type of selection made by either a
prior atom or an error or a function (for example). This kind of
conditional execution right now is difficult currently in taskflow since the
current model is more of a declaratively *fixed* pipeline that is verified
before execution and only completes execution when all atoms have ``EXECUTED``,
``FAILED`` or ``REVERTED`` (when retries are involved an atom or group of
atoms can flip between ``FAILED``, ``REVERTING`` and ``RUNNING`` as
the associated `retry`_ controller tries to resolve the execution
state). Conditional execution alters this since now we cannot, at compile time,
make a decision about whether an atom will or will not execute (since it is
not known until runtime whether the atom will execute) and we will be required
skip parts of the workflow based on a conditional outcome. Due to this these
*skipped* pieces of the workflow will now not have a ``EXECUTED``
or ``REVERTED`` state but will be placed in a new state ``IGNORED``.

Overall, to accommodate this feature we will try to adjust taskflow to provide
at least a *basic* level of support to accomplish a *type* of conditional
execution. In the future this support can be expanded as the idea and
implementation matures and proves itself.

Proposed change
===============

In order to support conditionals we first need to determine what a conditional
means in a workflow, what it looks like and how it would be incorporated into
a user's workflow.

The following is an example of how this *may* look when a user decides to add
a conditional choice into a workflow:

::

    nfs_flow = linear_flow.Flow("nfs-work")
    nfs_flow.add(
        ConfigureNFS(),
        StartNFS(),
        AttachNFS(),
        ...
    )
    nfs_matcher = lambda volume_type: volume_type == 'nfs'

    ceph_flow = linear_flow.Flow("ceph-work")
    ceph_flow.add(
        ConfigureCeph(),
        AttachCeph(),
        ...
    )
    ceph_matcher = lambda volume_type: volume_type == 'ceph'

    root_flow = linear_flow.Flow("my-work")
    root_flow.add(
        PopulateDatabase(),
        # Only one of these two will run (this is equivalent to an if/elif)
        LambdaGate(requires="volume_type",
                   decider=nfs_matcher).add(nfs_flow),
        LambdaGate(requires="volume_type",
                   decider=ceph_matcher).add(ceph_flow),
        SendNotification(),
        ...
    )

**Note:** that after this workflow has been constructed that the user will then
hand it off to taskflow for reliable, consistent execution using one of the
supported `engines`_ types, parallel, threaded or other...

Implementation
--------------

To make it simple (to start) let's limit the scope and suggest that a
conditional (a gate, gate seems to be a common name for these according
to `advances in dataflow programming`_) is restricted to being a runtime
scheduling decision that causes the path of execution to allow (aka pass) or
ignore (aka discard) the components that are contained with-in the gate.

This means that at the `compile time`_ phase when a gate is inserted into a
flow that any output symbols produced by the subgraph under the gate can
not be depended upon by any successors that follow the gate decision.

For example the following will **not** be valid since it introduces a symbol
dependency on a conditional gate (in a future change we could set these
symbols to some defaults when they will not be produced, for now though we
will continue *more* being strict):

::

    nfs_flow = linear_flow.Flow("nfs-work")
    nfs_flow.add(
        ConfigureNFS(provides=["where_configured"]),
        AttachNFS(),
        ...
    )
    nfs_matcher = lambda volume_type: volume_type == 'nfs'

    root_flow = linear_flow.Flow("my-work")
    root_flow.add(
        PopulateDatabase(),
        LambdaGate(requires="volume_type",
                   decider=nfs_matcher).add(nfs_flow),
        SendNotification(requires=['where_configured']),
        ...
    )


The next thing a conditional then needs a mechanism to influence
the *outcome* which should be executed to either allow its subgraph to pass
or to be discarded. When a gate is encountered while executing (assume there
is some way to know that we have *hit* a gate) we need to first freeze
execution of any successors (nothing must execute in any outcomes subgraph
ahead of time, this would violate the conditional constraint).

**Note:** that this does *not* mean that a subgraph executing that is not
connected to this conditional will have to be stopped (its execution is not
dependent on this outcome decision).

So assuming we can freeze dependent execution (which we currently can do, since
taskflow `engines`_ are responsible for scheduling further work) we now need
to provide the gate a way to make a decision; usually the decision will be
based on some prior execution or other external state. We have a mechanism for
doing this already so we will continue using the
existing `inputs and outputs`_ mechanism to communicate any
state (local or otherwise) to the gate. Now the gate just needs to be able to
make a boolean (or `truthy`_ value) decision about whether what is contained
after the gate should run or should not run so that the runtime can continue
down that execution path. To accommodate this we will require the gate object
to provide an ``execute()`` method (this allows gates themselves to
be an `atom`_ derived type) that returns a `truthy`_ value. If the value
returned is ``true`` then the gate will have been determined to have been
passed and the contained subgraph is then eligible for execution and
further scheduling. Otherwise if the value that is
returned is ``false`` (or falsey) then the contained subgraphs nodes will be
put into the ``IGNORE`` state before further scheduling occurs.

**Note:** this occurs *before* further scheduling so that if a failure
occurs (``kill -9`` for example) during saving those atoms ``IGNORE``
states that a resuming entity can attempt to make forward progress in saving
those same ``IGNORE`` states; without having to worry about an outcomes
subgraph having started to execute.

After this completes scheduling will resume and the nodes marked ``IGNORE``
will not be executed by current & future scheduling decisions (and the engine
will continue scheduling and completing atoms and all will be merry...).

Retries
#######

Conditionals have another an interesting interaction with `retry`_ logic, in
that when a subgraph is retried, we must decide what to do about the prior
outcome which may have been traversed and decide if we should allow the prior
outcome decision to be altered. This means that when a execution graph is
retried it can be possible to alter the gates decision and enter a new
subgraph (which may contain its own new set of retry strategies and
so-on). To start we will *clear* the outcome of a gate when a retry
resets/unwinds the graph that a retry object has *control* over (this will
cause the gate to be executed again). It will also be required to flip the
``IGNORED`` state back to the ``PENDING`` state so that the gates contained
nodes *could* be rescheduled. The gate would then have to use whatever provided
symbol inputs to recalculate its decision and decide on a new outcome (this
then could cause a new subgraph to be executed and so-on). This way will allow
for the most natural integration with the existing codebase (and is likely what
users would expect to happen).

.. _engines: http://docs.openstack.org/developer/taskflow/engines.html
.. _advances in dataflow programming: http://www.cs.ucf.edu/~dcm/Teaching/COT4810-Spring2011/Literature/DataFlowProgrammingLanguages.pdf
.. _inputs and outputs: http://docs.openstack.org/developer/taskflow/inputs_and_outputs.html
.. _retry: http://docs.openstack.org/developer/taskflow/atoms.html#retry
.. _truthy: https://docs.python.org/release/2.5.2/lib/truth.html
.. _compile time: http://docs.openstack.org/developer/taskflow/engines.html#compiling
.. _atom: http://docs.openstack.org/developer/taskflow/atoms.html#atom

Alternatives
------------

Some of the current and prior research was investigated to understand the
different strategies others have done to make this kind of conditionals
possible in similar languages and libraries:

* http://www.cs.ucf.edu/~dcm/Teaching/COT4810-Spring2011/Literature/DataFlowProgrammingLanguages.pdf
* http://paginas.fe.up.pt/~prodei/dsie12/papers/paper_17.pdf
* http://dl.acm.org/citation.cfm?id=3885
* And a few others...

Various pipelining/workflow like pypi libraries were looked at. None that I
could find actually provide conditional execution primitives. A not fully
inclusive list:

* https://pypi.python.org/pypi/DAGPype
* https://github.com/SegFaultAX/graffiti
* And a few others...

Impact on Existing APIs
-----------------------

This will require a new type/s that when encountered can be used to decide
which outcome should taken (for now a *gate* type and possibly a *lambda gate*
derived class). These new types will be publicly useable types that can be
depended upon working as expected (observing and operating by the constraints
described above).

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

A new way of using taskflow would be introduced that would hopefully receive
usage and mature as taskflow continues to progress, mature and get more
innovative usage.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  harlowja

Milestones
----------

Juno/2

Work Items
----------

* Introduce new gate types.
* Connect types into compilation routine.
* Connect types into scheduling/runtime routine.
* Test like crazy.

Incubation
==========

N/A

Adoption
--------

N/A

Library
-------

N/A

Anticipated API Stabilization
-----------------------------

N/A

Documentation Impact
====================

New developer docs explaining the concepts, how to use this and examples will
be provided and updated accordingly.

Dependencies
============

None

References
==========

* Brainstorm: https://etherpad.openstack.org/p/BrainstormFlowConditions
* Prototype: https://review.openstack.org/#/c/87417/

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
