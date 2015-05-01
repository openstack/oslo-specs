======================================
 Refactor Test Base Class in oslotest
======================================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/oslo?searchtext=oslotest-refactor

As a general policy we want to avoid requiring projects to use test
base classes defined in libraries they do not control. Test fixtures
are more composable, and easier to test themselves.

Problem description
===================

Copied from :doc:`/specs/policy/test-tools`:

    We originally created oslotest as a place to include the base
    class for all unit tests across all projects, to give the projects
    common behaviors in their test suites. Using a common base class
    is not always possible, however, when applications want to use
    their own base class and test fixture classes in ways that do not
    mix well. Multiple inheritance, in particular, is a problem
    because the order of setup and tear-down for test cases is harder
    to reason about.

Proposed change
===============

1. Provide a fixture to change the ``maxDiff`` attribute of a test
   case, with a default of 10,000 as in BaseTestCase.

2. Provide a fixture to wrap :class:`fixtures.Timeout` using an environment
   variable to set the actual timeout, based on
   :py:meth:`BaseTestCase._set_timeout`.

3. Provide a fixture to mock stdout and stderr, based on
   :py:meth:`BaseTestCase._fake_output`.

4. Provide a fixture to wrap :class:`fixtures.FakeLogger` using an
   environment variable to set the actual timeout, based on
   :py:meth:`BaseTestCase._fake_logs`.

5. Provide a fixture to create a temporary file with content to
   replicate the features of
   :py:meth:`BaseTestCase.create_tempfiles`. We should use one fixture
   per file, and provide the full path to the resulting file as an
   attribute of the fixture.

6. Add :class:`DeprecationWarning` to :py:meth:`BaseTestCase.setUp`.

Alternatives
------------

Leave Everything Alone
~~~~~~~~~~~~~~~~~~~~~~

Leaving :class:`BaseTestCase` alone risks making it completely
obsolete as projects drop its use due to issues with multiple
inheritance.

Impact on Existing APIs
-----------------------

The existing :class:`DeprecationWarning` will not be changed other
than to add the deprecation warning, so all existing users will
continue to be able to use it until they move to the new fixtures.

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

Developers will need to create or update their own test base classes
to use the desired fixtures. The old test case will not be removed for
at least one cycle, to allow for migration time.

Testing Impact
--------------

We will need unit tests for the new fixtures.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Doug Hellmann

Milestones
----------

Target Milestone for completion: Liberty-2

Work Items
----------

See "Proposed change" above.

Incubation
==========

N/A

Adoption
--------

N/A

Library
-------

N/A

Anticipated API Stabilization
-----------------------------

N/A

Documentation Impact
====================

Each change will require updates to the API documentation for oslotest.

Dependencies
============

* :doc:`/specs/policy/test-tools`

References
==========

* :doc:`/specs/policy/test-tools`


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
