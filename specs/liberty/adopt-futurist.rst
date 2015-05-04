..

===================
 Adopting futurist
===================

https://blueprints.launchpad.net/oslo.utils/+spec/adopt-futurist

The goal of this library would be to provide a well documented
`futures`_ classes/utilities/additions that start of with the a basic set
and can expand into a larger set as time goes on. This library (and the
futures library/module in general) allows for providing a level of
transparency in how asynchronous work gets executed.

This library currently adds on the following (going above and beyond
the built-in futures library in python 3.2 or newer and
the `futures backport`_ that is commonly used on python 2.6 or 2.7).

- Statistics gathering (number of futures ran, average failure rate, average
  run time...)
- An eventlet executor (aka a ``GreenThreadPoolExecutor``) that uses a
  `eventlet`_ greenpool and greenthreads (making the same futures/executor
  interface work when running in an eventlet environment). This kind of
  addition makes it eas(ier) to move from eventlet to another style of
  executor (since the interface that is provided/used is the same as the
  other executor types).
- A synchronous executor (aka a ``SynchronousExecutor``) that does **not**
  using any pools, threads, or processes but executes the submitted function
  in the calling thread (or program) and returns a future with the result or
  exception set. This allows for blocking usage where for whatever reason the
  same executor/futures interface is desired but executing in
  threads, processes (or other) is **not** desired.

Some of the current/planned usages for it (that are being actively pursued):

* Internal usage in `taskflow`_ (when no executor object is provided
  by a user). Also used for *internal* retry activation (that itself uses a
  synchronous executor).
* Internal usage in `oslo.messaging`_ (replacing/augmenting/unifying the
  executor interface inside that codebase).

The code for this library was/has been extracted from `taskflow`_ and is
desired to be used by `oslo.messaging`_ (and hopefully others)?

Library Name
============

*futurist*

Contents
========

* ``futurist/__init__.py``
* ``futurist/futures.py``
* ``futurist/utils.py`` (internal usage only)

Early Adopters
==============

* Taskflow
* Oslo.messaging
* Others?

Public API
==========

Currently the *public* API (in pseudo-code) is the following:

Actual code can be found `here`_.

::

    from concurrent import futures as _futures
    from concurrent.futures import process as _process
    from concurrent.futures import thread as _thread

    ThreadPoolExecutor(_thread.ThreadPoolExecutor)
        """
        Executor that uses a thread pool to execute calls asynchronously.
        It gathers statistics about the submissions executed for
        post-analysis...

        See: https://docs.python.org/dev/library/concurrent.futures.html
        """
        - statistics (read-only property)
        - alive (read-only property)
        - submit (same as parent class)
        - shutdown (same as parent class)

    ProcessPoolExecutor(_process.ProcessPoolExecutor)
        """
        Executor that uses a process pool to execute calls asynchronously.
        It gathers statistics about the submissions executed for
        post-analysis...

        See: https://docs.python.org/dev/library/concurrent.futures.html
        """
        - statistics (read-only property)
        - alive (read-only property)
        - submit (same as parent class)
        - shutdown (same as parent class)

    SynchronousExecutor(_futures.Executor)
        """Executor that uses the caller to execute calls synchronously.
        This provides an interface to a caller that looks like an executor but
        will execute the calls inside the caller thread instead of executing it
        in a external process/thread for when this type of functionality is
        useful to provide... It gathers statistics about the submissions
        executed for post-analysis...
        """
        - statistics (read-only property)
        - alive (read-only property)
        - submit (same as parent class)
        - restart (Restarts this executor (*iff* previously shutoff/shutdown))
        - shutdown (same as parent class)

    GreenFuture(Future)
        """Future that ensures internal condition is a green(ed) condition."""

    GreenThreadPoolExecutor(_futures.Executor)
        """Executor that uses a green thread pool to execute calls
        asynchronously.

        See: https://docs.python.org/dev/library/concurrent.futures.html
        and http://eventlet.net/doc/modules/greenpool.html for information on
        how this works.

        It gathers statistics about the submissions executed for
        post-analysis...
        """
        - statistics (read-only property)
        - alive (read-only property)
        - submit (same as parent class)
        - shutdown (same as parent class)

    ExecutorStatistics(object)
        """Holds *immutable* information about a executors executions."""
        - failures (read-only property)
        - executed (read-only property)
        - runtime (read-only property)
        - cancelled (read-only property)
        - average_runtime (read-only property)

Implementation
==============

Assignee(s)
-----------

Primary assignee:

* Harlowja

Other contributors:

* Sileht

Primary maintainer
------------------

Primary maintainer:

* Harlowja

Other contributors:

* Sileht

Security Contact
----------------

Security Contact: harlowja

Milestones
----------

Target Milestone for completion: liberty-1

Work Items
----------

* Create launchpad project
* Change owner of Launchpad project (make it part of the Oslo project group)
* Give openstackci Owner permissions on PyPI
* Create Initial Repository
* Make the library do something ✓
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
* `futures backport`_ (only needed on python < 3.2)
* `pbr`_
* `oslo.utils`_
* `six`_
* `eventlet`_ (**optionally** required for green futures/executors)

.. note::

 All of the currently planned dependencies are in the requirements repository.

References
==========

N/A

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

.. _eventlet: http://eventlet.net/
.. _here: https://github.com/harlowja/futurist
.. _six: https://pypi.python.org/pypi/six
.. _oslo.messaging: https://pypi.python.org/pypi/oslo.messaging
.. _oslo.utils: https://pypi.python.org/pypi/oslo.utils
.. _pbr: http://docs.openstack.org/developer/pbr/
.. _taskflow: http://docs.openstack.org/developer/taskflow/
.. _futures backport: https://pypi.python.org/pypi/futures
.. _futures: https://docs.python.org/dev/library/concurrent.futures.html
