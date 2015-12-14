====================================
 Unstable APIs without an incubator
====================================

We want to get rid of the incubator, but there is no replacement process for
stabilising new APIs.

Problem description
===================

The incubator with its copy-paste approach to code has a harmful side to it -
we end up with copied code in a bunch of projects that needs to be updated and
can skew - in particular we not uncommonly find that projects have edited
their local copies and synchronisation is tricky.

Proposed change
===============

When a new project is started, create the library immediately. Use an API
namespace within the library to offer concurrent access to multiple API
versions during the early evolution of the library, with graduation involving
exposing the API at the top of the library. CI checks will let us evaluate the
impact of removing the interim API versions when consumers no longer use them.

Project versions that release while using interim versions will cause us to
retain the interim version for some time - in line with normal backward
compatibility concerns.

Once projects have finished early evolution and are ready to stabilise their
API, they will release a 1.0.0 version a non-namespaced API.

API update policy
-----------------

Non-breaking changes will proceed as normal. Breaking changes during the early
evolution period will create a new API namespace, using a serial number - 1,
2, 3 etc.

Code structure
--------------

Each unstable API version will be in a subdirectory of the project along with
its tests.

E.g. if a new library fred has had two unstable API versions, the code tree
would look like::

    fred/
    fred/v1
    fred/v1/tests
    fred/v2
    fred/v2/tests

Where v2 starts as a copy of v1, and v1 is frozen from that point on.

Using a namespaced version
--------------------------

Code should be imported as follows::

    from fred import v1 as fred

Entrypoints
-----------

Where a library consumes entrypoints as part of its API, while the API is
being namespaced, so must the entrypoints, in the same way::

    fred.v1.extensionname

Alternatives
------------

Stable-from-start
+++++++++++++++++

We could just apply semver from the very first commit. Folk have expressed
great concern about the impact of development that this would have.

Use library name namespaces
+++++++++++++++++++++++++++

Rather than having multiple versions inside one distribution, we could version
the name of the library. E.g. fred0, fred1, fred2 etc until the API
stabilises. This pollutes the global namespace though, and will require lots
of changes to global-requirements, making it high friction.

Impact on Existing APIs
-----------------------

We'll want a tool to warn on the use of older-than-latest api versions in oslo
projects: much like the automated update-from-incubator scripts do today.

Security impact
---------------

It may be slightly easier to keep using old versions of in-incubation code.

Performance Impact
------------------

Packages will git a little bigger (multiple copies of similar code), but the
number of copies on disk will reduce (since they won't be copied into each
project).

Configuration Impact
--------------------

None

Developer Impact
----------------

Projects will no longer be able to make local changes to incubated projects
and will instead need to work with oslo to get their changes done centrally
from the start.

Existing workflows will change, so we need to socialise and communicate
effectively about the change.

Testing Impact
--------------

No impact.

Implementation
==============

Assignee(s)
-----------

Written at Dims' request, no current volunteers to execute.

Primary assignee:
  <launchpad-id or None>

Other contributors:
  <launchpad-id or None>

Milestones
----------

Target Milestone for completion:

Work Items
----------

1. Document this somewhere in olso docs
2. Write the update / lint thing to check for the latest version being used.
3. Profit.

Incubation
==========

N/A - replaces Incubation entirely.

Documentation Impact
====================

None that I know of.

Dependencies
============

No dependencies, though a mild interaction with the deprecation policy will
happen - in that we'll be releasing things we want to delete as soon as
possible. See above for details.

References
==========

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

