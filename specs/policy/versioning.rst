..
  This document is based on the text of
  https://wiki.openstack.org/wiki/Oslo/VersioningPolicy, which will be
  replaced with a link to the published version of this policy when it
  is approved.

==========================
 Choosing Version Numbers
==========================

As part of the push to release code from the oslo incubator in
stand-alone libraries, we have had several different discussions about
versioning and release schedules. This is an attempt to collect all of
the decisions we have made in those discussions and to lay out the
rationale for the approach we are taking.

Problem Description
===================

We have two types of Oslo libraries. Libraries like ``oslo.config``
and ``oslo.messaging`` were created by extracting incubated code,
updating the public API, and packaging it. Libraries like ``cliff``
and ``taskflow`` were created as standalone packages from the
beginning, and later adopted by the Oslo team to manage their
development and maintenance.

Incubated libraries have been released at the end of a release cycle,
as with the rest of the integrated packages. Adopted libraries have
historically been released "as needed" during their development.

The first release of ``oslo.config`` was 1.1.0, as part of the grizzly
release. The first release of ``oslo.messaging`` was 1.2.0, as part of
the havana release. ``oslo.config`` was also updated to 1.2.0 during
havana. All "adopted" libraries (created elsewhere and brought into
the Oslo project) had release numbers less than 1.0.0 when the
original draft of this policy was written.

Proposed Policy
===============

At the Juno summit, Josh Harlow `proposed
<https://etherpad.openstack.org/p/juno-oslo-semantic-versioning>`__
that we use semantic versioning (SemVer) for oslo libraries. Part of
that proposal also included ideas for allowing breaking backwards
compatibility at some release boundaries, and this policy does not yet
address that issue. The first step is choosing a rational release
versioning scheme.

SemVer is widely used and gives us relatively clear guidelines about
choosing new version numbers. Oslo started using `pbr's modified
SemVer`_ for new releases, beginning in the Juno cycle.

.. _pbr's modified SemVer: http://docs.openstack.org/developer/pbr/semver.html

SemVer Life Cycle
-----------------

New libraries should start with version 0.1.0, incrementing following
the SemVer policies through the end of the cycle with the goal of
reaching 1.0.0 by the end of their first full development cycle.

Existing libraries will follow SemVer, incrementing from the version
they had at the start of Kilo.

Frequent Releases
-----------------

While we can run gate jobs using the master branch of Oslo libraries,
developers will have to take extra steps to run unit tests this way
locally. To reduce this process overhead, while still ensuring that
developers use current versions of the code, we produce releases of
libraries during the release cycle fairly frequently. We have a weekly
check-up during the Oslo team meetings, and tag releases early on
Mondays when deemed necessary. Waiting until Monday prevents us from
introducing a gate issue just before the weekend starts.

Patch Releases for Stable Branches
----------------------------------

Updates to existing library releases can be made from stable
branches. Checking out ``stable/icehouse`` of ``oslo.config`` for
example would allow a release 1.3.1. We don't have a formal policy
about whether we will create patch releases, or whether applications
are better off using the latest release of the library.

All libraries will need to maintain stable branches to support these
patch releases. We will cap the versions of Oslo libs used in stable
branches to allow patch releases but not updates with minor version
number changes.

Alternatives & History
======================

Synchronizing with the Rest of OpenStack
----------------------------------------

The Oslo team could release libraries at any point, without concern
for the release schedule of the rest of OpenStack. We have to be
prepared for libraries we do not maintain to be updated at any point,
so this wouldn't be adding a new aspect to our release and testing
processes. However, Oslo is part of OpenStack and so we initially
wanted to be on the same schedule.

Mark McLoughlin has written `a good justificiation for this
<http://lists.openstack.org/pipermail/openstack-dev/2012-November/003345.html>`__,
which is summarized as "my instinct is to do everything just like any
of the other core projects except in those cases where Oslo really is
a special case." With Oslo following the release schedule of the other
projects, we get all of the benefits (shifting focus from features to
bugs; stable branches; synchronization with the users of our
libraries; the OpenStack release manager).

When we stopped creating Alpha releases, we stopped full release
synchronization. We do still release a final version for a given major
and minor version number at the end of a release, and we do still
follow the feature freeze process.

Alpha Releases
--------------

In the past, alpha releases of Oslo libraries have been distributed as
tarballs on an openstack server, with official releases going to
PyPI. Applications that required the alpha release specified the
tarball in their requirements list, followed by a version
specifier. This allowed us to prepare alpha releases, without worrying
that their release would break continuous-deployment systems by making
new library releases available to pip. This approach still made it
difficult for an application developer to rely on new features of an
oslo library, until an alpha version was produced.

When the PyPI mirror was introduced in our CI system, relying on
tarballs not available on the mirror conflicted with our desire to
have the gate system install *only* from the package mirror. When we
started installing only from the mirror, we needed to publish our
alpha releases in a format that will work with the mirror, and so we
started using alpha version numbers of predicted final versions during
a release.

At the Kilo summit, a vocal group of consumers of Oslo libraries
requested that we stop using alpha versioning and switch to simple
SemVer. We started doing that in Kilo, with mixed results (breaking
changes made it into the stable branch test environments). At this
point, there is no sense in going back to alpha releases during Kilo,
so we will stick with the current plan and work through the resulting
issues.

https://etherpad.openstack.org/p/kilo-oslo-alpha-versioning

We decided that new libraries should start with version 0.1.0,
incrementing following the SemVer policies through the end of the
cycle with the goal of reaching 1.0.0 by that time.

Existing libraries will follow SemVer, incrementing from the version
they had at the start of Kilo.

Juno Policy
-----------

The versions for existing libraries oslo.config and oslo.messaging
will be incremented from their Icehouse versions but updating the
minor number (1.x.0) at the end of the Juno cycle.

All adopted libraries using numbers less than 1.0 will be released as
1.0.0 at the end of the Juno cycle, based on the fact that we expect
deployers to use them in production.

Releases of new libraries graduated during Juno will be tagged with
regular release numbers < 1.0. This allows us to add them to our
requirements list (which won't accept alphas of packages with no other
release). At the end of Juno, we will tag the libraries 1.0.0.

Releases of existing libraries during Juno should *all* be marked as
alphas of the anticipated upcoming SemVer-based release number
(1.0.0.0aN or 1.2.0.0aN or whatever). The new CI system can create
packages as Python wheels and publish them to the appropriate servers,
which means projects will no longer need to refer explicitly to
pre-release tarballs. pip won't install alpha libraries unless you
explicitly request them with a command line flag to install any alphas
available or you explicitly require the alpha version. pip <= 1.3
didn't support the flag for controlling alphas (they were always seen
and installed), but also didn't support wheels, so we publish alphas
only as wheels to ensure that older pips don't see them.

Cross-Project Unit Testing in the Gate
--------------------------------------

We had a blueprint for Juno to `add cross-project unit test gating
<https://blueprints.launchpad.net/openstack-ci/+spec/testing-pre-releases-of-oslo-libs-with-apps>`__
for applications and oslo libraries. This would have allowed us to
verify that tests for applications do not break then Oslo libraries
change, but also that those tests do not make assumptions about Oslo
library implementation details. However, this level of testing was
deemed too expensive in terms of test servers, and so the plan was
dropped.

Capping Requirements in Stable Branches
---------------------------------------

We do not typically use upper bounds on the requirements
specifications for Oslo libraries, so new releases may automatically
be adopted by continuous-deployment systems building packages for
stable branches of OpenStack applications. Although we have been
careful about API compatibility in the past, there is a chance that a
new release could break an older application. Applications could add
an upper bound using SemVer numbering if they choose, although that
may prevent them from seeing bug fixes so it is not recommended.

During the Kilo summit we discussed capping versions of requirements
in stable branches. The initial attempt to do this right after the
summit failed because it prevented some upgrades from working
correctly. Work to apply caps is ongoing, and is outside of the scope
of this policy.

Tagging milestones in libraries
-------------------------------

We don't tag libraries at the milestones like we do with applications,
since the tags we use for milestones (e.g., 2014.2.b1) aren't valid
versions for libraries and would be out of order with other releases
anyway. We may tag an alpha release around the time of the milestone,
but since we do those on demand anyway there's no strict rule that we
must do it at that time.

Implementation
==============

Author(s)
---------

Primary author: doug-hellmann

Other contributors: markmc

Milestones
----------

The current policy was put into place for Kilo.

Work Items
----------

N/A

References
==========

* http://lists.openstack.org/pipermail/openstack-dev/2012-November/003345.html
* http://lists.openstack.org/pipermail/openstack-dev/2014-June/037159.html
* `pbr's modified SemVer`_

Revision History
================

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Juno
     - Introduced


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

