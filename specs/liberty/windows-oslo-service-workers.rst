================================
Oslo Service Workers for Windows
================================

https://blueprints.launchpad.net/oslo.service/+spec/
windows-oslo-service-workers

The goal of this blueprint is implement a way which will allow OpenStack
services to run under Windows.

Problem description
===================

Currently, oslo_service project has a couple of Linux specific implementations,
which makes it impossible to use under Windows. A few examples would be
service.ProcessLauncher, which uses:

* eventlet.greenio.GreenPipe, which it cannot be used, as it tries to set the
  pipe as non-blocking, mechanism that does not exist in Windows. [1]
* os.fork, which does not exist in Windows. [2]

Proposed change
===============

An alternative option for forking would be spawning subprocesses by using the
multiprocessing module, which avoids the GIL problem. [3]

Multiprocessing module still forks the process on Linux systems, which means
that the behaviour will remain consistent with the current implementation.

The proposed change is that service.ProcessLauncher to spawn
mutliprocessing.Process objects as service workers instead.

Alternatives
------------

Cygwin can be used under Windows [3], which is a collection of tools providing
similar functionality to a "Linux distribution on Windows".

The problem is, forking in Cygwin is known to be problematic and inefficient,
as it does not map well on top of the WIN32 API. [4]

Impact on Existing APIs
-----------------------

None

Security impact
---------------

None

Performance Impact
------------------

None, functionality and performance should not change for Linux.

Configuration Impact
--------------------

None

Developer Impact
----------------

None

Testing Impact
--------------

Unit tests.

CI testing will be performed by Jenkins for Linux and Hyper-V CI for Windows.

Testing should be done for both Python 2.7 and 3.4, as the implementation of
the multiprocessing module differs greatly. Needed in order not to introduce
regressions for a certain Python version.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Claudiu Belu <cbelu@cloudbasesolutions.com>

Milestones
----------

Target Milestone for completion:

Work Items
----------

As per Proposed Change.

Incubation
==========

Adoption
--------

The current services that use the oslo_services module.

Library
-------

oslo_service

Anticipated API Stabilization
-----------------------------

None

Documentation Impact
====================

None

Dependencies
============

multiprocessing

Version might be different for Python 2.7 and 3.4.

References
==========

[1] GreenIO exception
  http://paste.openstack.org/show/284115/

[2] os.fork available only on Unix.
  https://docs.python.org/2/library/os.html#os.fork

[3] multiprocessing module
  http://sebastianraschka.com/Articles/2014_multiprocessing_intro.html

[4] Cygwin
  https://www.cygwin.com/

[5] Cygwin fork issues:
  http://cygwin.com/cygwin-ug-net/highlights.html#ov-hi-process

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

