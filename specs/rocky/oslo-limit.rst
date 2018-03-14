===============================
Proposed new library oslo.limit
===============================

This is a proposal to create a new library dedicated to enabling moreconsistent
quota and limit enforcement across OpenStack.

Proposed library mission
=========================

Enforcing quotas and limits across OpenStack has traditionally been a tough
problem to solve. Determining enforcement requires quota knowledge from the
service along with information about the project owning the resource. Up until
the Queens release, quota calculation and enforcement has been left to the
services to implement, forcing them to understand complexities of keystone
project structure. During the Pike and Queens PTG, there were several
productive discussions towards redesigning the current approach to quota
enforcement.

Because keystone is the authority of project structure, it makes sense to allow
keystone to hold the association between a resource limit and a project. This
means services still need to calculate quota and usage, but the problem should
be easier for services to implement since developers shouldn't need to
re-implement possible hierarchies of projects and their associated limits.
Instead, we can offload some of that work to a common library for services to
consume that handles enforcing quota calculation based on limits associated to
projects in keystone. This proposal is to have a new library called oslo.limit
that fills that need.

Consuming projects
==================

The services consuming this work will be any service that currently implements
a quota system, or plans to implement one. Since keystone already supports
unified limits and association of limits to projects, the implementation for
consuming projects is easier. instead of having to re-write that
implementation, developers need to ensure quota calculation to passed to the
oslo.limit library somewhere in the API's validation layer. The pattern
described here is very similar to the pattern currently used by services that
leverage oslo.policy for authorization decisions.

Alternatives library
====================

It looks like there was an existing library that attempted to solve some of
these problems, called `delimiter <https://github.com/openstack/delimiter>`_.
It looks like delimiter could be used to talk to keystone about quota
enforcement, where as the existing approach with oslo.limit would be to use
keystone directly.

Proposed adoption model/plan
============================

The `unified limit API
<https://docs.openstack.org/keystone/latest/admin/identity-unified-limits.html>`_
in keystone is currently marked as experimental, but the keystone team is
actively collecting and addressing feedback that will result in stabilizing the
API. Stabilization changes that effect the oslo.limit library will also be
addressed before version 1.0.0 is released. From there, we can look to
incorporate the library into various services that either have an existing
quota implementation, or services that have a quota requirement but no
implementation.

This should help us refine the interfaces between services and oslo.limit,
while providing a facade to handle complexities of project hierarchies. This
should enable adoption by simplifying the process and making it easier for
quota to be implemented in a consistent way across services.

Reviewer activity
=================

At first thought, it makes sense to model the reviewer structure after the
oslo.policy library, where the core team consists of people not only interested
in limits and quota, but also people familiar with the keystone implementation
of the unified limits API.

Implementation
==============

Author(s)
---------

Who is leading the proposal of the new library? Must have at least two
individuals from the community committed to triaging and fixing bugs, and
responding to test failures in a timely manner.

Primary authors:
  Lance Bragstad (lbragstad@gmail.com) lbragstad
  XiYuan Wang (wangxiyuan@huawei.com) wxy
Other contributors:
  <launchpad-id or None>

Work Items
----------

* Create a new library called oslo.limit
* Create a core group for the project
* Define the minimum we need to enforce quota calculations in oslo.limit
* Propose an implementation that allows services to test out quota
  enforcement via unified limits

References
==========

Rocky PTG `etherpad
<https://etherpad.openstack.org/p/unified-limits-rocky-ptg>`_ for unified
limits. This is where we discussed the interaction between services and
keystone, ultimately agreeing on the inclusion of a library to handle quota
enforcement.

Revision History
================

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Rocky
     - Introduced

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

