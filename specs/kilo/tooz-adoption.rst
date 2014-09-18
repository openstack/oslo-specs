==================
 Adoption of tooz
==================

https://blueprints.launchpad.net/oslo/+spec/tooz-adoption


Problem description
===================

The tooz library started its development phase on Stackforge in order to be used
by the OpenStack project. Now that this library is starting to get adoption and
is being used by OpenStack projects (Ceilometer), having the Oslo program taking
responsibility for it would help its maintenance in the future.

Proposed change
===============

The proposed change is to adopt this library under the Oslo program so we
can maintain it.

Alternatives
------------

Do nothing.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  jdanjou

Other contributors:
  harlowja

Milestones
----------

kilo-1

Work Items
----------

- Move the repository stackforge/tooz to openstack/tooz
- Change driver and maintainer of https://launchpad.net/python-tooz
- Add oslo-core to tooz-core on Gerrit
- Add the python-tooz Launchpad project to the "oslo" project group so it will
  show up in bug queries, etc.

References
==========

None

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

