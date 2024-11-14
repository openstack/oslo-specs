..
  This template should be in ReSTructured text.  For help with syntax,
  see http://sphinx-doc.org/rest.html

  To test out your formatting, build the docs using tox, or see:
  http://rst.ninjs.org

  The filename in the git repository should match the launchpad URL,
  for example a URL of
  https://blueprints.launchpad.net/oslo?searchtext=awesome-thing should be
  named awesome-thing.rst.

  For specs targeted at a single project, please prefix the first line
  of your commit message with the name of the project.  For example,
  if you're submitting a new feature for oslo.config, your git commit
  message should start something like: "config: My new feature".

  Wrap text at 79 columns.

  Do not delete any of the sections in this template.  If you have
  nothing to say for a whole section, just write: None

  If you would like to provide a diagram with your spec, ascii diagrams are
  required.  http://asciiflow.com/ is a very nice tool to assist with making
  ascii diagrams.  The reason for this is that the tool used to review specs is
  based purely on plain text.  Plain text will allow review to proceed without
  having to look at additional files which can not be viewed in gerrit.  It
  will also allow inline feedback on the diagram itself.

==================================
 Remove Eventlet From oslo.service
==================================

https://blueprints.launchpad.net/oslo?searchtext=remove-eventlet-from-oslo-service

Oslo.service provides a framework for defining long-running services.
To achieve that goal, oslo.service rely on Eventlet and its coroutines.

Eventlet is the heart of oslo.service.

However, the removal of Eventlet from Openstack is now a `fact
<https://review.opendev.org/c/openstack/governance/+/902585>`_.

Removing Eventlet from oslo.service is now mandatory.

This specification aims to design the removal of eventlet from oslo.service.

The goal of this document is:
1. to identify alternatives to the Eventlet features currently used by oslo.service;
2. to define how to put in place those alternatives;
3. to define the various milestone needed to properly remove Eventlet;
4. to minimize the impact for oslo.service's users.

Problem description
===================

The removal of Eventlet is now a `fact
<https://review.opendev.org/c/openstack/governance/+/902585>`_.
The official Eventlet project will be retired in a near future and the
Openstack T.C officially accepted the community goal proposed to retire
Eventlet from the Openstack runtime.

The main features provided by oslo.service are:

- ``loopingcall``: a module to run a method in a loop;
- ``periodic task``: periodic tasks that can be run in a separate process;
- ``service``: a service manager that can handle workers;
- ``wsgi``: an utility to create and launch wsgi server;
- ``systemd``: an helper module for systemd service readiness notification;
- ``threadgroup``: an helper to create a group of greenthreads and timers.

The problem is that oslo.service heavily rely on Eventlet.
All the oslo.service features listed below are based on Eventlet:

- ``loopingcall``;
- ``periodic task``;
- ``service``;
- ``wsgi``;
- ``threadgroup``.

In parallel of that, oslo.service also provide side features like:

- ``eventlet_backdoor``;
- ``fixture``;
- ``sslutils``.

These side feature are strongly linked to behavioral mechanisms of Eventlet
and are not strictly speaking features of oslo.service.

So if we want to remove Eventlet from oslo.service we have to identify
what to do with the modules listed below:

- ``loopingcall``;
- ``periodic task``;
- ``service``;
- ``wsgi``;
- ``threadgroup``;
- ``eventlet_backdoor``;
- ``fixture``;
- ``sslutils``.

We must identify if all these module could be rewritten by using alternatives
and if the usage of these alternatives would impact the existing API of
oslo.service (additional parameter, default value, etc).

We must decide:
- how to transition from the current version of oslo.service
to the future version of oslo.service, a version free from Eventlet.
- if the future version of oslo.service will again provide all of
these features or if we should remove some of them in the process.

If we decide to remove existing feature, then we must decide how transition
our consumers.

In all the case, at some point will would have to release major version of
oslo.service where the backward compatibility will be definitely broken.

That document aim to answer all these questions.

Constraints
-----------

For the sake of consistency we have to define a couple of constrains. The
goal of these constraints is to keep the migration as transparent as possible
for consumers.

* we cannot abruptly remove Eventlet, so, for all the previously described
  oslo.service features, both implementations will have to cohabit, the
  Eventlet version, and the new one;

* at the oslo.service's consumers level, the transition must be as smooth as
  possible. Meaning that consumers should not have to rewrite all their imports
  to continue using the Eventlet based implementation, or the new version.
  Some oslo.service modules may be abandoned, only those imports would have
  to be removed if imported at the consumers level;

* consumers must decide when to switch from an implementation to an other;

* the removal of the Eventlet implementation should not impact the consumers
  in a random way. If a feature is explicitly removed from oslo.service, then
  an alternative must be documented in a migration guide specific to
  oslo.service. Customers must be informed by deprecation warning of the
  removal of the features;

* non-actively maintained deliverables must not be broken by the removal
  of the Eventlet implementation;

* non-actively maintained deliverables must not block indefinitely the
  removal of the Eventlet implementation. If such case is identified, then
  the Pop Up team dedicated to the migration must be informed of this problem.

Proposed change
===============

Features triagging
------------------

Again, here are the main modules provided by oslo.service:

- ``loopingcall``;
- ``periodic task``;
- ``service``;
- ``wsgi``;
- ``threadgroup``;
- ``systemd``;
- ``eventlet_backdoor``;
- ``fixture``;
- ``sslutils``.

Each module is more or less a feature.

As said previously, some modules are specific to Eventlet:

- ``eventlet_backdoor``: backdoor made to attach an Eventlet based process;
- ``fixture``: a fixture for mocking the ``wait()``;
- ``sslutils``: specific Eventlet wrapper for ssl.

For this reason, the new implementation won't re-implement these modules.
These modules will be simply removed from the new implementation.

The ``wsgi`` module is based on a the `Eventlet wsgi server
<https://eventlet.readthedocs.io/en/latest/examples.html#wsgi-server>`_ for
this reason, we also propose to remove that module from the new
implementation.

We want to encourage consistency across projects. It is crucial to avoid
having multiple ways to start services across different projects. A unified
approach will simplify maintenance and enhance user experience.
We don't want projects looking/running different.
For this reason we advocate for the adoption of one or two of the following
packages which could be credible alternatives to the Eventlet WSGI module
exposed by oslo.service:

* `uWSGI <https://uwsgi-docs.readthedocs.io/en/latest/>`: synchronous WSGI
  server well tested and OpenStack context. Threads based;
* `uvicorn <https://pypi.org/project/uvicorn/>`: an ASGI web server
  implementation for Python;
* `asgiref <https://pypi.org/project/asgiref/>`: allow to wrap or decorate
  async or sync functions to call them from the other style (so you can call
  async functions from a synchronous thread, or vice-versa).

This way we will have an unified approach for all our deliverables. This
approach is compatible with both world (sync, and async).

Both libraries are well and actively maintained by many developers.

At the application layer, we advocate for the usage of
`FastAPI <https://pypi.org/project/fastapi/>` which is
also compatible with both worlds (sync and async), and which is actively
maintained by hundred of people. FastAPI is coming a mainstream library
heavily used in the AI realm, so we think that it is a credible alternative
a long life ahead of him. The considerations about the application layer are
a bit out of the current topic though and or are given here with the sake of
giving tracks for discussions.

The following modules will remains and would have to be transitioned:

- ``loopingcall``;
- ``periodic task``;
- ``service``;
- ``threadgroup``;
- ``systemd``;

The implementation of the ``systemd`` module seems to be a CPython vanilla
implementation, so it may remains untouched.

How to proceed?
---------------

Oslo.service cannot be transitioned in one time. We propose to introduce the
notion of backend into oslo.service to allow the usage of both implementation
in parallel.

Backend will allow to implement the new version of oslo.service while keeping
the existing version handy.

The backend will simplify the life of users during the transition.

We propose the following milestones to juggle between implementations
and with the notion of backend:

- (SLURP) 2025.1: move the current implementation into an ``eventlet`` backend
  (the default backend in the config);
- (SLURP) 2025.1: implement the ``threading`` backend;
- (NON-SLURP) 2025.2: deprecate the ``eventlet`` backend and make
  ``threading`` the default;
- (NON-SLURP) 2026.2: remove the ``eventlet`` implementation and move the
  ``threading`` implementation at the root level, and remove the backend
  notion.

Actually oslo.service is a flatten module. All its sub-modules are
at the root level. Meaning that users imports the features they needs from
the root level of the oslo.service module, example::

    from oslo_service import wsgi
    from oslo_service import service
    from oslo_service import loopingcall
    ...

If we do not introduce the backend notion, all the Openstack services using
oslo.service will have to rewrite all their imports at least twice. The first
time when they will be eager to use the new implementation::

    from oslo_service.threading import service

and the second one when the old implementation will be removed, and, hence,
when the new implementation will be moved at the root level::

    from oslo_service import service

This is not an acceptable scenario because it will lead to many useless back
and forth at the import level, without any additional added value for the
users.

Usaging backends will hide the complexity of this swapping into oslo.service.
Users won't suffer from changing their imports again and again.

Actually, oslo.service looks like to::

    oslo_service
    ├── eventlet_backdoor.py
    ├── fixture.py
    ├── _i18n.py
    ├── __init__.py
    ├── locale
    │   └── .. (ignored)
    ├── loopingcall.py
    ├── _options.py
    ├── periodic_task.py
    ├── service.py
    ├── sslutils.py
    ├── systemd.py
    ├── tests
    │   └── .. (ignored)
    ├── threadgroup.py
    ├── version.py
    └── wsgi.py

Once the backend will be added the structure of oslo.service will looks like
to::

    oslo_service
    ├── backends
    │   ├── eventlet
    │   │   ├── eventlet_backdoor.py
    │   │   ├── fixture.py
    │   │   ├── __init__.py
    │   │   ├── loopingcall.py
    │   │   ├── periodic_task.py
    │   │   ├── service.py
    │   │   ├── sslutils.py
    │   │   ├── threadgroup.py
    │   │   └── wsgi.py
    │   └── threading
    │       ├── __init__.py
    │       ├── loopingcall.py
    │       ├── periodic_task.py
    │       ├── service.py
    │       └── threadgroup.py
    ├── eventlet_backdoor.py
    ├── fixture.py
    ├── _i18n.py
    ├── __init__.py
    ├── locale
    │   └── .. (ignored)
    ├── loopingcall.py
    ├── _options.py
    ├── periodic_task.py
    ├── service.py
    ├── sslutils.py
    ├── systemd.py
    ├── tests
    │   └── .. (ignored)
    ├── threadgroup.py
    ├── version.py
    └── wsgi.py


Each root sub-module will simply import the right backend conditionally,
example with the service sub-module::

    if _options.backend == "threading":
        from oslo_service.threading import service
    else
        from oslo_service.eventlet import service

If a sub-module do not exists in the new implementation, then the root level
sub-module will use debtcollector `to emit a deprecation warning
<https://docs.openstack.org/debtcollector/latest/user/usage.html#deprecating-anything-else>`_
and give instruction to users, example with the wsgi sub-module::

    debtcollector.deprecate(
        """
        The WSGI module is no longer supported
        You see this deprecation warning because you are importing
        the oslo.service wsgi module. This module is deprecated and will
        be soon removed. Please consider using uwsgi and consider following
        the migration path described here:
        https://docs.openstack.org/oslo.service/latest/migration/wsgi.html
        ",
        version="1.0"
    )
    if _options.backend == "eventlet":
        from oslo_service.eventlet import service
    else
        raise ImportError("WSGI module not found in the threading backend...")

Concerning the modules conserved in the ``threading`` implementation, they
will be rewritten by using new underlying libraries, like cotyledon, futurist,
and threading/concurrent from the stdlib. See the dependency and API section
for more details about the usage of these new libraries.

If a sub-module is not impacted by the Eventlet removal and so not
re-implemented, then it could remains at the root level. That's by example
the case of the ``systemd`` sub-module, which in our previous tree example
remains at the root level.

If a consumers do not move its oslo.service backend to the ``threading``
backend in the allotted time, then the T.C should be warned. Then the T.C will
surely inform the Pop Up team created to manage the whole Eventlet removal.
In this case, the Pop Up team may decide to migrate this deliverable or could
propose to retire it if nobody actively maintain it.

Alternatives
------------

It would be also possible to entirely deprecate oslo.service and to point
the available alternatives into the deprecation warnings, therefore,
leaving the charge of the refactor to the consumers.

The problem of this approach is that it would surely spring various approaches
and so a diversity of solution.

The motivation behind the creation of the Oslo projects was to uniformize the
solutions and to reduce the technical debt.

If we delegate the refactor to oslo.service consumers it will lead to an
increase of this technical debt.

Impact on Existing APIs
-----------------------

The temporary backends
~~~~~~~~~~~~~~~~~~~~~~

The existing API will be modified to introduce the temporary backends.
Backends will remains private module not directly importable
by consumers. One or the other backend will be imported by the classic
import and by choosing one backend or the other in the config.

The public API will remains almost the same until the Eventlet backend is not
removed.

Once the Eventlet backend will be removed, then the public API related
to Eventlet will be also removed, see the next section.

Removed sub-modules
~~~~~~~~~~~~~~~~~~~

Once the migration will be terminated, the backend notion will be removed
and the new implementation will be moved at the root level, meaning
that once the migration will be done, oslo.service will looks like to::

    oslo_service
    ├── _i18n.py
    ├── __init__.py
    ├── locale
    │   └── .. (voluntary ignored)
    ├── loopingcall.py
    ├── _options.py
    ├── periodic_task.py
    ├── service.py
    ├── systemd.py
    ├── tests
    │   └── .. (voluntary ignored)
    ├── threadgroup.py
    └── version.py

The following modules won't exists anymore, and so won't be anymore
importable:

- wsgi
- eventlet_backdoor
- fixture
- sslutils

During the time the ``backends`` notion will be present, users will face
import errors until the ``wsgi``, ``eventlet_backdoor``, ``fixture``,
``sslutils`` modules are removed from the user codebase. Indeed, it is
useless to implement a ``NotImplemented`` interface as in all the case
users will have to remove them.

And the transient ``backends`` sub-module and its content, will be also
removed.

Periodic task
~~~~~~~~~~~~~

The ``periodic_task`` sub-module will become a proxy for
the futurist library.

The oslo.service ``periodic_task`` sub-module provide the following
abstractions to manage periodical tasks:

- `oslo_service.periodic_task.periodic_task
  <https://docs.openstack.org/oslo.service/latest/reference/periodic_task.html#oslo_service.periodic_task.periodic_task>`_
  which represent a periodical task;
- `oslo_service.periodic_task.PeriodicTasks
  <https://docs.openstack.org/oslo.service/latest/reference/periodic_task.html#oslo_service.periodic_task.PeriodicTasks>`_
  which is a manager for periodical tasks (one to many). Could be seen as a
  worker where we attach callable to run periodically.

Futurist define the following methods and class to manage periodic tasks:

- `futurist.periodics.PeriodicWorker
  <https://docs.openstack.org/futurist/latest/reference/index.html#futurist.periodics.PeriodicWorker>`_
  which allow to call a collection of callable periodically. This is a worker
  where we attach callable to run periodically;
- `futurist.periodics.periodic
  <https://docs.openstack.org/futurist/latest/reference/index.html#futurist.periodics.periodic>`_
  which allow to tag a method/function as wanting/able to execute periodically;
- `futurist.periodics.Watcher
  <https://docs.openstack.org/futurist/latest/reference/index.html#futurist.periodics.Watcher>`_
  which is a read-only object representing a periodic callback’s activities.

So the following bindings are proposed to use oslo.service as a proxy of
futurist:

- ``oslo_service.periodic_task.periodic_task`` will be bound with
  ``futurist.periodics.periodic``;
- ``oslo_service.periodic_task.PeriodicTasks`` will be bound with
  ``futurist.periodics.PeriodicWorker``;

As our goal is to keep the existing oslo.service API as intact as possible,
we propose to ignore the ``futurist.periodics.Watcher`` class.

The ``futurist.periodics.periodic`` implement the ``enabled`` notion. That
option do not exists in oslo.service. Indeed in oslo.service a periodic task
is disabled if the ``spacing`` parameter is set to a negative number. In this
case, if this number is negative on oslo.service, then, we will have to set
the ``enabled`` parameter of futurist to ``False``.

Futurist periodic tasks `accept an executor parameter
<https://docs.openstack.org/futurist/latest/reference/index.html#periodics>`_.
Futurist `define different kind of executors
<https://docs.openstack.org/futurist/latest/user/features.html#async>`_.

We should provide a way to choose the kind of executor that futurist will
use, for this reason, we will have to implement an abstraction to this notion
to offer to users a way to select one.

Futurist provide an executor based on Eventlet. As our goal is to
remove Eventlet we won't provide access to this executor at the oslo.service
level.

Oslo.service will only allow to use/select the following futurist executors:

- futurist.ProcessPoolExecutor
- futurist.SynchronousExecutor
- futurist.ThreadPoolExecutor

Service
~~~~~~~

To implement the new version of the oslo.service' service sub-module we
propose to use Cotyledon.

The Cotyledon module provide the following public API:

- `cotyledon.Service
  <https://cotyledon.readthedocs.io/en/latest/api.html#cotyledon.Service>`_:
  base class for a service;
- `cotyledon.ServiceManager
  <https://cotyledon.readthedocs.io/en/latest/api.html#cotyledon.ServiceManager>`_:
  manage lifetimes of services.

Where service sub-module of oslo.service provide the following public API:

- `oslo_service.service.Launcher
  <https://docs.openstack.org/oslo.service/latest/reference/service.html#oslo_service.service.Launcher>`_:
  launch one or more services and wait for them to complete;
- `oslo_service.service.ProcessLauncher
  <https://docs.openstack.org/oslo.service/latest/reference/service.html#oslo_service.service.ProcessLauncher>`_:
  launch a service with a given number of workers;
- `oslo_service.service.Service
  <https://docs.openstack.org/oslo.service/latest/reference/service.html#oslo_service.service.Service>`_:
  service object for binaries running on hosts;
- `oslo_service.service.ServiceBase
  <https://docs.openstack.org/oslo.service/latest/reference/service.html#oslo_service.service.ServiceBase>`_:
  base class for all services;
- `oslo_service.service.ServiceLauncher
  <https://docs.openstack.org/oslo.service/latest/reference/service.html#oslo_service.service.ServiceLauncher>`_:
  runs one or more service in a parent process;
- `oslo_service.service.launch
  <https://docs.openstack.org/oslo.service/latest/reference/service.html#oslo_service.service.launch>`_:
  launch a service with a given number of workers.

We propose the following bindings:

- ``oslo_service.service.Launcher`` will delegate to ``cotyledon.ServiceManager``;
- ``oslo_service.service.ServiceLauncher`` will delegate to ``cotyledon.ServiceManager``;
- ``oslo_service.service.Service`` will delegate to ``cotyledon.Service``;

And the ``oslo_service.service.launch`` and
``oslo_service.service.ProcessLauncher`` will remains more or less with
the same logic that is currently implemented, less the monkey patching of
Eventlet.

Unlike oslo.service cotyledon allow only one service workers manager run at a
time. Oslo.service allow to run more than one Service launcher at a time.
This difference should be documented.

Loopingcall & threadgroup
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``loopingcall`` and ``threadgroup`` modules are based on greenthreads,
so we have to re-implement them. We propose to use the CPython ``threading``
module to refactor them.

``loopingcall`` seems to simply needs threads to run methods in loop.

``threadgroup`` use eventlet green pool to manage group of threads. Again
the stdlib ``threading`` module offer ways to attach threads to a defined
group. Possibly it would also require the usage of `ThreadPoolExecutor
<https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor>`_
to allow asynchronous behavior.

These 2 sub-modules should not be really impacted by API changes. Only the
internal mechanisms will change and the public API will surely remains the
same.

Security impact
---------------

None

Performance Impact
------------------

Removing Eventlet would mean moving, in some circumstances, to a native
threading model. Eventlet is based on cooperative coroutines provided by
greenlet, when cotyledon, or even futurist, uses threads, who are preemptive.

Threads tend to be more expensive and slower than coroutines because they
involve context switching. OS will continue to share CPU operations with
all the threads even if they are not ready to works (network IO, etc).

Indeed, depending on the number of workers allocated to services or periodic
tasks, in a context with a lot of threading concurrency, threads can degrade
the flow rate of the machine. This is linked to context-switching which is
resource-intensive.

Threads are preemptive so compared to cooperative coroutines, they are more
prone to lead to race condition.

Configuration Impact
--------------------

This topic will impact the configuration in numerous ways.
The first impact will be related to the addition of a new config option
to allow switching the implementation. Switching the backend to use.

.. code-block:: ini

    [DEFAULT]
    oslo_service_backend = eventlet

This new option will named ``oslo_service_backend`` and it will be a
``cfg.StrOpt``.

It will propose the following choices as valid settings::

    choices=['eventlet', 'threading']

And it will defaulted to ``eventlet``, and users
will move this value to ``threading`` when they will have cleaned-up the usage
of oslo.service deprecated sub-modules from their code base.

This option will be removed once the deprecation period will be over.

As said previously, using the backend notion, and so this option will allow
internal transients states within oslo.service, allowing us to swap the
internal implementations.

The existing configuration related to the wsgi module and to the sslutils
of oslo.service will be removed once the swapping will be done, as these
sub-modules will be retired.

In a first time these config sections (wsgi, sslutils) will be fully deprecated
to warn the user that they have to stop using it.

We should also deprecate the ``backdoor_socket`` and the ``backdoor_port``
from the default config section, as the eventlet_backdoor module will be
removed, as so, these options will be also removed once the swapping will
be done.

Developer Impact
----------------

Removing Eventlet from oslo.service would allow side works, like:
- removing the mutex tricks oslo.log;
- removing the greenlet/eventlet executor from futurist.

Testing Impact
--------------

As the current tests also relies on Eventlet and on monkey patching, all
the new implementation should also introduce its own tests.

The existing tests should remains, and the ``tests`` directory structure
should reflect the new module tree with both backends.

The tests of the removal and the of the deprecation will be at the charge
of the ``eventlet`` backend. We do not want to pollute the new ``threading``
implementation with obsolete artifacts.

Oslo.service do not implement functional tests, so this refactor won't add
ones.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
    Hervé Beraud (hberaud)

Milestones
----------

Target Milestone for completion:

- (SLURP) 2025.1: move the current implementation into an ``eventlet`` backend
  (the default backend in the config);
- (SLURP) 2025.1: implement the ``threading`` backend;
- (NON-SLURP) 2025.2: deprecate the eventlet backend and make ``threading`` the
  default;
- (NON-SLURP) 2026.2: remove the ``eventlet`` implementation and move the
  ``threading`` implementation at the root level, and remove the backend
  notion.

Work Items
----------

#. create an ``eventlet`` sub-module to host the existing implementation
   and plug the root level sub-modules to this new module
#. create a ``threading`` sub-module to host the new implementation
   and add a new backend config defaulting to the ``eventlet`` sub-module
#. deprecate the ``eventlet`` sub-module
#. default the backend config to the ``threading`` implementation
#. remove the ``eventlet`` sub-module and remove the backend config option
#. move the ``threading`` implementation at the root level

Documentation Impact
====================

As the notion of backend will be added, to different documentation
will cohabit for both implementations of the same sub-module.

The documentation structure will reflect the oslo.service module::

    doc/source/backends/

The new option allowing to swap the implementation will be documented.

Each new implementation will have to specify its specificity at the
docstring level.

The documentation should also provide a migration guide to give guidance
about the removed sub-module.

Each time a specific deprecation warning is emitted from a sub-module,
the deprecation message should give a link that refer to the right
section of this migration guide.

This migration guide will be hosted into the following path::

    doc/source/migration

This specific migration guide should at least document the
removals of ``oslo_service.wsgi`` and give tracks to follow (WSGI/ASGI (uwsgi,
uvicorn, etc), application layer (flask, etc), HTTP...). This part of the
documentation will follow the standards defined by `the HTTP SGI working group
<https://wiki.openstack.org/wiki/Eventlet-removal#The_HTTP_SGI_Working_Group>`_

The other removed sub-modules which are specific to Eventlet (
eventlet_backdoor, fixture, etc...) won't have to be documented.

Once the Eventlet backend will be removed, this migration will be also
removed from the documentation.

Dependencies
============

We propose to create two `extra environment markers
<https://docs.openstack.org/pbr/latest/user/using.html#environment-markers>`_.
One related the ``eventlet`` backend and one for the ``threading`` backend.
They would avoid installing useless packages and help to reduce the size
of packaging and disk size. By example, if the user decide to use the
``threading`` package, we do not need building a container that doesn't
require ``eventlet`` to be in it. Indeed, in many place the existence of
eventlet triggers a behavior change, avoid installing eventlet will reduce
the chance of facing this kind of situation.

The extra environment markers will looks like too:

.. code-block:: cfg

   [extras]
   eventlet =
       eventlet>=0.36.1 # MIT
   threading =
       futurist>=3.0.0 # Apache-2.0
       cotyledon>=1.7.3 # Apache-2.0

See the section below for further details and context about ``futurist`` and
``cotyledon``.

Periodic task
-------------

For the ``periodic task`` module, we propose to use `Futurist
<https://docs.openstack.org/futurist/latest/>`_ to replace Eventlet.
Indeed, Futurist is a library that provide periodic tasks management.

The ``oslo_service.periodic_task`` module will began a proxy of futurist.

Service
-------

`Cotyledon <https://github.com/sileht/cotyledon>`_ was created years ago
to offer an alternative to the Service module of oslo.service. An alternative
free from Eventlet. We propose to use cotyledon as underlying library for
the new implementation of the Service module of oslo.service.

In other words, the ``oslo_service.service`` module will began a proxy of
cotyledon.

References
==========

* https://review.opendev.org/c/openstack/governance/+/902585

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
