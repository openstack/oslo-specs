===========================
 Graduating Oslo Middleware
===========================

https://blueprints.launchpad.net/oslo.middleware/+spec/graduate-oslo-middleware

The new oslo.middleware library will provide a common library for wsgi
middleware currently contained in oslo-incubator.

Library Name
============

oslo.middleware

Contents
========

* openstack/common/middleware/base.py
* openstack/common/middleware/catch_errors.py
* openstack/common/middleware/correlation_id.py
* openstack/common/middleware/debug.py
* openstack/common/middleware/request_id.py
* openstack/common/middleware/sizelimit.py
* tests/unit/middleware/test_catch_errors.py
* tests/unit/middleware/test_correlation_id.py
* tests/unit/middleware/test_request_id.py
* tests/unit/middleware/test_sizelimit.py


Early Adopters
==============

None

Public API
==========

oslo.middleware library provides access to the following middleware
('middleware' suffix will be dropped from original naming)::

    * CatchErrors
    * CorrelationId
    * Debug
    * RequestId
    * RequestBodySizeLimiter

To utilise the new middleware, after including oslo.middleware library,
projects can declare the new middleware in wsgi pipeline as such::

    [filter:<middleware>]
    paste.filter_factory = oslo.middleware:<ClassName>.factory

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  chungg

Other contributors:
  None

Primary Maintainer
------------------

Primary Maintainer:
  dims

Other Contributors:
  chungg

Security Contact
----------------

Security Contact:
  dims

Milestones
----------

Target Milestone for completion: Juno-3

Work Items
----------

* https://wiki.openstack.org/wiki/Oslo/CreatingANewLibrary#Checklist
* add deprecated decorator to current incubator classes
* drop middleware suffix from class names
* import middleware classes into middleware/__init__.py
* audit middleware will not be included. it will be included in
  keystonemiddleware as part of keystone's adoption of audit
* notifier middleware will not be included. it will be included in
  oslo.messaging to minimise dependencies in oslo.middleware.

Adoption Notes
==============

General use of middleware remains the same. The only change in usage would be
to reference middlware in oslo.middleware library rather than openstack/common.

A deprecated decorator will be added to existing incubator classes so when
the incubator version is used, log will notify of current oslo.middleware
version.

Dependencies
============

None

References
==========

https://etherpad.openstack.org/p/oslo-middleware-dependency

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

