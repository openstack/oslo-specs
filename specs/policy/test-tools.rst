======================
 Providing Test Tools
======================

Each Oslo library needs to provide support tools for testing code that
uses the library. Over time we have found some patterns that work and
others that do not work, and this policy document describes our
general approach.

Problem Description
===================

We originally created oslotest as a place to include the base class
for all unit tests across all projects, to give the projects common
behaviors in their test suites. Using a common base class is not
always possible, however, when applications want to use their own base
class and test fixture classes in ways that do not mix well. Multiple
inheritance, in particular, is a problem because the order of setup
and tear-down for test cases is harder to reason about.

Proposed Policy
===============

Most libraries include fixtures, rather than test base
classes. Fixtures are more isolated, easier to test, and generally
prove less complex to combine in unforeseen ways. Based on this
experience, and the issues with inheritance in test classes, we should
limit unit test tools to fixtures and avoid using base classes or
mix-in classes.

Alternatives & History
======================

As mentioned above, the original plan was to create base classes in
oslotest.

Implementation
==============

Author(s)
---------

Primary author:
  Doug Hellmann

Other contributors:
  None

Milestones
----------

This policy will go into effect during the Liberty cycle.

Work Items
----------

* Deprecate the test base class in oslotest and replicate its features
  in fixtures (see :doc:`/specs/liberty/oslotest-refactor-test-base-class`).
* Deprecate the test base class(es) in oslo.db and replicate their
  features in fixtures (see
  https://blueprints.launchpad.net/oslo.db/+spec/make-db-fixture-public).

References
==========

* IRC discussion of issues with oslo.db and nova, starting around
  ``2015-02-24T11:36:58`` in
  http://eavesdrop.openstack.org/irclogs/%23openstack-oslo/%23openstack-oslo.2015-02-24.log
* :doc:`/specs/liberty/oslotest-refactor-test-base-class`
* https://blueprints.launchpad.net/oslo.db/+spec/make-db-fixture-public

Revision History
================

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Liberty
     - Introduced

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

