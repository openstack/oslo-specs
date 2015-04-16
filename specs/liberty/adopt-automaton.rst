..

==============================
 Creating/adopting automaton
==============================

https://blueprints.launchpad.net/oslo.utils/+spec/adopt-automaton

The goal of this library would be to provide a well documented
state machine classes/utilities that start off with the a basic set and
can expand into a larger set as time goes on. The state machine pattern (or
the implemented variation there-of) is a commonly used pattern and has a
multitude of various usages.

Some of the current usages for it (that are being actively pursued):

* Provided state & transition validation for `ironic`_.
* Providing state & transition validation & running/scheduling/analysis of
  the execution of `taskflow`_ engines.

The code for this library was extracted from taskflow and has been copied into
ironic and appears to be a key part of that projects states work where it is
now serving a useful purpose there; so I would consider the API mostly
stable (ironic is not currently using the FSM runner properties while taskflow
would be/is). The code/mini-library was recently split off into
https://github.com/harlowja/automaton where it has been developed and
isolated (the tests extracted for example, a ``setup.py`` added and `pbr`_
integrated...) and it has `travis-ci`_ running against it for testing
integration (this would no longer be needed as the openstackci serves a
similar/equivalent purpose).

Library Name
============

*automaton*

Contents
========

* ``automaton/__init__.py``
* ``automaton/exceptions.py``
* ``automaton/machines.py``

  * This is the *main file* that contains a finite state machine and a
    hierarchical state machine and associated run classes that can be used to
    run the state machines until they terminate; this usage of these runners
    is optional and is not necessary to use the machines for state and
    transition processing and/or validation.

For those wondering what a hierarchical state machine is the following
can be referred to about it (the concepts are similar to what is described
in the following slide-set).

- http://www.cis.upenn.edu/~lee/06cse480/lec-HSM.pdf

Early Adopters
==============

* Taskflow
* Ironic
* Others?

Public API
==========

Currently the machine *public* API is the following:

::

    FiniteMachine
        - runner (read-only property)
        - default_start_state (read/write property)
        - current_state (read-only property)
        - terminated (read-only property)
        - add_state(state, terminal=False, on_enter=None, on_exit=None)
        - add_reaction(state, event, reaction, *args, **kwargs)
        - add_transition(start, end, event)
        - process_event(event) -- main function/method!!
        - initialize(start_state=None)
        - copy(shallow=False, unfreeze=False)
        - freeze()
        - frozen (read/write property)
        - states (read-only property)
        - events (read-only property)
        - pformat(sort=True, empty='.')

    HierarchicalFiniteMachine(FiniteMachine)
        - runner (read-only property)
        - add_state(state, terminal=False,
                    on_enter=None, on_exit=None, machine=None)

The runners of each state machine have the following *public* API:

- ``run(event, initialize=True)``
- ``run_iter(event, initialize=True)``

Further API documentation (that is likely more readable and better commented)
can be found at:

https://github.com/harlowja/automaton

Or from the live taskflow docs (that are using a slightly older
version of the machines, minus a couple API adjustments; nothing major
changed though):

http://docs.openstack.org/developer/taskflow/types.html#module-taskflow.types.fsm

Implementation
==============

Assignee(s)
-----------

Primary assignee:

* Harlowja

Other contributors:

* You?

Primary maintainer
------------------

Primary maintainer:

* Harlowja (until further notice).

Other contributors:

* Praneshp (@yahoo)
* You?

Security Contact
----------------

Security Contact: harlowja

Milestones
----------

Target Milestone for completion: liberty-1

Work Items
----------

* Create launchpad project
* Change owner of Launchpad project (make it part of the Oslo projectgroup)
* Give openstackci Owner permissions on PyPI
* Create Initial Repository
* Make the library do something
* Update the README.rst
* Publish git repo
* Oslo team review new repository
* Infra project configuration
* Update Gerrit Groups and ACLs
* openstack-infra/devstack-gate adjustments
* openstack/requirements projects.txt adjustments
* Update project list on docs.openstack.org
* Tag a release
* Profit!

Adoption Notes
==============

N/A

Dependencies
============

Requirements
------------

* python 2.6 --> 3.4 (and beyond!)
* ordereddict (only needed on python 2.6)
* pbr
* prettytable
* six

.. note::

 All of the currently planned dependencies are in the requirements repository.

References
==========

N/A

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

.. _pbr: http://docs.openstack.org/developer/pbr/
.. _taskflow: http://docs.openstack.org/developer/taskflow/
.. _ironic: https://github.com/openstack/ironic/blob/master/ironic/common/states.py
.. _travis-ci: https://travis-ci.org/harlowja/automaton
.. _warnings: https://docs.python.org/2/library/warnings.html
