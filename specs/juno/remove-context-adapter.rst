====================================
 Remove ContextAdapter from logging
====================================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/oslo/+spec/remove-context-adapter

We want to remove the :class:`openstack.common.log.ContextAdapter`
class as part of graduating ``oslo.log``, to reduce the API footprint.

Problem description
===================

We use :class:`ContextAdapter` to add request context information to
log messages we output. Requiring a specially adapted logging handle
limits the scope of where that context information can be added, and
unnecessarily funnels all logging calls through the oslo logging
modules.

Proposed change
===============

1. Ensure :class:`ContextHandler` implements all of the same behaviors
   as :class:`ContextAdapter`, with respect to the values being
   output and their sources.
2. Update :func:`getLogger` to return a :class:`BaseLoggerAdapter`
   (probably renamed to something like :class:`LoggerAdapter` in the
   process). This will allow modules that use the :meth:`audit`,
   :meth:`warn`, and :meth:`deprecated` methods to still work until we
   can update the callers.
3. Remove the :class:`ContextAdapter` class.
4. Remove the :func:`getLazyLogger` function.

Alternatives
------------

None

Impact on Existing APIs
-----------------------

By changing :func:`getLogger` to return a different adapter type, we
can keep the API as it is for now to buy time to update the callers
that use the methods that would otherwise be removed. Modules that do
not use those methods can switch to using the Python standard library
:mod:`logging` module to get a logger.

Security impact
---------------

None

Performance Impact
------------------

None

Configuration Impact
--------------------

None

Developer Impact
----------------

See "Impact on Existing APIs" above.

Implementation
==============

Assignee(s)
-----------

Who is leading the writing of the code? Or is this a blueprint where you're
throwing it out there to see who picks it up?

If more than one person is working on the implementation, please designate the
primary author and contact.

Primary assignee:
  Doug Hellmann (doug-hellmann)

Other contributors:
  None

Milestones
----------

Target Milestone for completion:
  Juno-2

Work Items
----------

1. Verify that the :class:`ContextHandler` works properly with
:class:`Message`, and update it to make it work if it does not.
2. See "Proposed Change" above.

Incubation
==========

None

Adoption
--------

None

Library
-------

oslo.log

Anticipated API Stabilization
-----------------------------

This change is part of stabilizing the API for oslo.log before
graduation.

Documentation Impact
====================

None

Dependencies
============

* We need to remove the import cycle between log and versionutils
  before implementing this
  change. https://blueprints.launchpad.net/oslo/+spec/app-agnostic-logging-parameters

References
==========

* Discussion from the Juno summit: https://etherpad.openstack.org/p/juno-oslo-release-plan
* Related blueprint on using our context as a base class: https://blueprints.launchpad.net/oslo/+spec/app-agnostic-logging-parameters
* Related blueprint for graduating oslo.log: https://blueprints.launchpad.net/oslo/+spec/graduate-oslo-log

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

