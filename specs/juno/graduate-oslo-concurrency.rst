=============================
 Graduating oslo.concurrency
=============================

https://blueprints.launchpad.net/oslo/+spec/graduate-oslo-concurrency

A library for managing threads and processes.

Library Name
============

oslo.concurrency

Contents
========

lockutils.py
tests/unit/test_lockutils.py
fixture/lockutils.py

processutils.py
tests/unit/test_processutils.py

Early Adopters
==============

Neutron - there was a note from the summit session that some changes in the
Neutron rootwrap calling code needed to be addressed as part of this work,
but no one remembers the details so we'll start with it to make sure any
issues are addressed before cutting a final release.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  bnemec

Primary Maintainer
------------------

Primary Maintainer:
  bnemec

Security Contact
----------------

Security Contact:
  bnemec

Milestones
----------

Target Milestone for completion:
  Juno-2

Work Items
----------

https://wiki.openstack.org/wiki/Oslo/CreatingANewLibrary#Checklist

* Make lockutils.main() a console script entry point

* Clean up processutils use of greenthreads and random sleeps

* Rename fixture/lockutils.py to fixture.py in the lib

* Fix PosixLock problem with program termination:
  https://bugs.launchpad.net/oslo/+bug/1327946

* Open a bug about this lib's use of fileutils so it can be converted when
  oslo.io graduates

Adoption Notes
==============

None

Dependencies
============

* https://blueprints.launchpad.net/oslo/+spec/graduate-oslo-log

* https://blueprints.launchpad.net/oslo/+spec/cleanup-processutils-for-graduation

* lockutils uses fileutils, so that module will be copied from oslo-incubator
  until oslo.io graduates.

References
==========

https://etherpad.openstack.org/p/juno-oslo-release-plan


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

