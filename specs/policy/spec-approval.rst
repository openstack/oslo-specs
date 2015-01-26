===============
 Spec Approval
===============

This document describes the process for having a specification
approved in Oslo.

Problem Description
===================

Specification approval for Oslo is managed a little differently than
other projects, because although Oslo has a single core/driver team we
also have core reviewer teams for each of the libraries.

Proposed Policy
===============

Rather than a simple majority vote of the driver team, we look for
consensus among the important contributors to that part of the code.

Specifications related to oslo-incubator are reviewed by oslo-core.

Specifications related to an existing library are reviewed by
oslo-core and the core review team for the library.

When consensus is reached on a spec, the Oslo PTL gives the
workflow +1 vote to merge the change and publish the spec.

Alternatives & History
======================

Two +2
------

Using two +2 votes as we do with code review would be faster, but we
do not necessarily strive for speed when managing specification
reviews. We want the team to have time to consider the implications of
the change, the proposed API, and otherwise contemplate the spec.

Separate Specs Repositories
---------------------------

We could use separate a specs repository for each library, to allow
the core team of that library to manage reviews directly. We have not
yet had so many specs related to a given library that we have felt the
need to do this. We also want the API generalists on the oslo-core
team to be able to participate easily, without having to track reviews
in the large number of different specs repositories we would have.

Implementation
==============

Author(s)
---------

Primary author: Doug Hellmann

Other contributors: None

Milestones
----------

We adopted this policy starting with Juno.

Work Items
----------

None

References
==========

N/A


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

