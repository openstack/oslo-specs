================
 Feature Freeze
================

Because Oslo does releases on a different schedule from many of the rest of
the OpenStack projects, it is helpful to have some modified policies around
feature freeze as well.

Problem Description
===================

Oslo wants to respect the feature freeze date that is set for the OpenStack
community as a whole, but due to the nature of libraries it can be
problematic for us to continue adding new features right up until the official
feature freeze.

Proposed Policy
===============

Projects in the Oslo program will observe their own feature freeze, which will
occur one week before the overall OpenStack feature freeze and continue until
all of the consuming OpenStack projects have made their releases for the
cycle.  This is a hard freeze, and as such only critical bug fixes should
merge during the freeze period.

Freezing early will provide time to release any pending changes in the Oslo
libraries before the consuming projects enter feature freeze.

Note that this policy also applies to oslo-incubator.  Feature freezing the
incubator code means that if a bug in incubator is found by a consuming
project, the sync of the fix to that project will not include any new
features that may have been added to incubator in the meantime.

Exceptions
----------

This policy will not apply to libraries that have not yet been released.
Any in-progress graduation work on those can continue through feature
freeze as it will not affect any frozen projects.

Alternatives & History
======================

We could simply observe the overall feature freeze date, but due to library
release cycles that may result in new features being released during feature
freeze.

Another option would be to not observe feature freeze at all and rely on our
release-to-release compatibility requirements to handle any issues.  This
would not only make it more likely for us to release a buggy version of a lib
during feature freeze, but it should be unnecessary as our consumers would be
unable to implement any new features exposed in Oslo libraries during that
time anyway.

Implementation
==============

Author(s)
---------

Primary author:
  bnemec

Other contributors:
  dhellmann

Milestones
----------

One week before OpenStack feature freeze

Work Items
----------

* Make an announcement on the mailing list on the date of Oslo feature freeze

References
==========

* http://eavesdrop.openstack.org/meetings/oslo/2015/oslo.2015-01-26-16.00.log.html#l-180
* Library stable branches: https://review.openstack.org/#/c/155072/

Revision History
================

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - 
     - Introduced

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

