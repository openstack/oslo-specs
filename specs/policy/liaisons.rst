..
  This document includes text from
  https://wiki.openstack.org/wiki/CrossProjectLiaisons#Oslo which will
  be replaced with a reference to the published version of this page
  when it is approved.

==========
 Liaisons
==========

Problem Description
===================

There are now more projects consuming code from the Oslo incubator
than we have Oslo contributors. That means the oslo-core team will
need help to make library adoptions happen.

Proposed Policy
===============

We are asking for one person from each project to serve as a liaison
between the project and Oslo, and to assist with integrating changes
as code moves out of the incubator into libraries or as library API
changes need to be made.

* It is important that the person understand the project well enough
  to be able to make significant changes, especially if the API of a
  library differs from the incubated modules. We prefer the liaison to
  be a core reviewer for the project, but leave that up to the
  project. The liaison does not need to be the PTL (and probably
  should not be).
* The liaison should be prepared to assist with writing and reviewing
  patches in their project as libraries are adopted, and with
  discussions of API changes to the libraries to make them easier to
  use within the project.
* Liaisons should pay attention to ``[Oslo]`` tagged messages on the
  openstack-dev mailing list.
* It is also useful for liaisons to be able to attend the Oslo team
  meeting (`Meetings/Oslo
  <https://wiki.openstack.org/wiki/Meetings/Oslo>`__) to participate
  in discussions and raise issues for real-time discussion.

Alternatives
============

Add more Oslo Core Developers
-----------------------------

We are always watching for candidates to be added to the oslo-core
team. However, we're not able to keep up with the rate of addition of
new projects.

Committer in Oslo Updates Applications
--------------------------------------

This solution does not scale either. A developer changing something in
Oslo will not necessarily also have time or knowledge needed to update
all consuming applications.

Implementation
==============

Author(s)
---------

Primary author: doug-hellmann

Other contributors: None

Milestones
----------

The Liaison program was started in Oslo during Juno, and expanded to
other cross-project teams for Kilo.

Work Items
----------

1. Recruit liaisons from all of the projects.

References
==========

* The Liaison program was original described in
  http://wiki.openstack.org/wiki/Oslo/Liaisons.

* After other projects started using liaisons, the description and
  list of volunteers moved to
  https://wiki.openstack.org/wiki/CrossProjectLiaisons

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
