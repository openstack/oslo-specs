====================================
 Remove ContextAdapter from logging
====================================

https://blueprints.launchpad.net/oslo.log/+spec/remove-context-adapter

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
2. Create :class:`KeywordArgumentAdapater` to take named keyword
   arguments to logging methods and insert them into the 'extra'
   values for the log record (see below for details).
3. Change :func:`getLogger` to return :class:`KeywordArgumentAdapter`
   instances instead of :class:`ContextAdapter`.
4. Remove the :class:`ContextAdapter` class.
5. Remove the :func:`getLazyLogger` function.

Alternatives
------------

The previous version of this spec suggested changing :func:`getLogger`
to return a different adapter type with :meth:`audit` and
:meth:`deprecated` methods, allowing us to keep the API as it is for
now to buy time to update the callers that use the methods that would
otherwise be removed. Since we are starting this work at the beginning
of a cycle, I have updated the proposal to move us directly to the
sort of API we want to keep.

Impact on Existing APIs
-----------------------

We remove some APIs, but most of them have equivalent forms available from
other libraries. There are three cases that do not.

ContextAdapter.audit
~~~~~~~~~~~~~~~~~~~~

The :class:`ContextAdapter` provides an :meth:`audit` method for
logging at INFO+1 level. This will be removed, and the log messages
updated to either use the INFO level or use the :meth:`log` method
with the audit level.

::

  $ for d in ceilometer cinder glance heat ironic keystone neutron nova sahara trove swift;
  do echo $d; ack LOG.audit $d/$d | wc -l; done
  ceilometer
  0
  cinder
  4
  glance
  0
  heat
  0
  ironic
  0
  keystone
  0
  neutron
  0
  nova
  101
  sahara
  0
  trove
  0
  swift
  0

ContextAdapter.deprecated
~~~~~~~~~~~~~~~~~~~~~~~~~

The :meth:`deprecated` method of the :class:`ContextAdapter` is
replaced with a new function in ``versionutils``. See
`fix-import-cycle-log-and-versionutils`_.

ContextAdapter keyword argument handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`ContextAdapter` API supports doing::

  LOG.info('some message: %(named_arg)s', named_arg=val, context=context)

The standard logger methods don't accept arbitrary keyword arguments
to be part of the 'extra', but we have enough cases of this that we
need to continue to support the pattern to avoid churn and breaking
things in the other projects. We will implement a
:class:`KeywordArgumentAdapter` to be returned by :func:`getLogger`.

.. warning::

   Oslo libraries should not use this feature, to avoid circular
   dependencies between the libraries and oslo.log.

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

Primary assignee:
  Doug Hellmann (doug-hellmann)

Other contributors:
  None

Milestones
----------

Target Milestone for completion:
  Kilo-1

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

As apps that use the incubated version of oslo.log are updated, they
will need to be changed to get loggers directly from the standard
library module and to use ``versionutils`` for :meth:`deprecated`.

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
* Related blueprint on using our context as a base class: https://blueprints.launchpad.net/oslo.log/+spec/app-agnostic-logging-parameters
* Related blueprint for graduating oslo.log: https://blueprints.launchpad.net/oslo.log/+spec/graduate-oslo-log
* Related blueprint for fixing the import cycle between logging and versionutils: https://blueprints.launchpad.net/oslo-incubator/+spec/fix-import-cycle-log-and-versionutils

.. _fix-import-cycle-log-and-versionutils: https://blueprints.launchpad.net/oslo-incubator/+spec/fix-import-cycle-log-and-versionutils

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

