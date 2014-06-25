===============================
 Graduating oslo.serialization
===============================

https://blueprints.launchpad.net/oslo/+spec/graduate-oslo-serialization

OpenStack-specific serialization tools

Library Name
============

oslo.serialization

Contents
========

jsonutils.py
tests/unit/test_jsonutils.py

Early Adopters
==============

?

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

* Adopt oslo.i18n in jsonutils

Adoption Notes
==============

* Adopting projects will need to have switched to oslo.i18n before using this
  library because it references the Message class, so the project needs to be
  using the same one.

Dependencies
============

* oslo.i18n

* oslo.utils (for timeutils)

* importutils from incubator.  That may be moving to oslo.utils, however.

References
==========

https://etherpad.openstack.org/p/juno-oslo-release-plan

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

