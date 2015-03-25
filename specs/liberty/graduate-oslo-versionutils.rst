=====================================
 Graduating versionutils to oslo.log
=====================================

https://blueprints.launchpad.net/oslo?searchtext=graduate-oslo-versionutils

The versionutils module contains tools for reporting deprecations of
features at OpenStack release cycle boundaries. It is being added to
oslo.log because it is not large enough to make sense to manage as a
library on its own, and the primary use is as a logging helper
function.

Library Name
============

What is the name of the new library?: oslo.log and oslo.utils

Contents
========

- openstack/common/versionutils.py
- tests/unit/test_versionutils.py

Early Adopters
==============

None

Public API
==========

The :func:`deprecated` decorator and :func:`report_deprecated_feature`
will be available through :mod:`oslo_log.versionutils`.

:func:`is_compatible` will be added to :mod:`oslo_utils.versionutils`.

Implementation
==============

Assignee(s)
-----------

Primary assignee: Doug Hellmann

Other contributors: None

Primary Maintainer
------------------

Primary Maintainer: Existing library maintainers

Other Contributors: None

Security Contact
----------------

Security Contact: Existing contacts

Milestones
----------

Target Milestone for completion: liberty-1

Work Items
----------

#. Extract the history for the versionutils code into a new
   repository.
#. Import that history into a branch of the oslo.log repo. The changes
   in the branch will need to be submitted to gerrit for review, but
   we can fast-approve them because they have already been reviewed in
   the incubator.
#. Merge the branch into master, with accompanying fixes to make the
   tests work.
#. Remove :func:`is_compatible` from oslo.log.
#. Import that history into a branch of the oslo.utils repo. The changes
   in the branch will need to be submitted to gerrit for review, but
   we can fast-approve them because they have already been reviewed in
   the incubator.
#. Merge the branch into master, with accompanying fixes to make the
   tests work.
#. Remove the parts of versionutils not related to
   :func:`is_compatible` from oslo.utils.
#. Release both oslo.log and oslo.utils.
#. Remove versionutils from the incubator.

Adoption Notes
==============

Most applications will already be using versionutils, and the API
won't be changing, so adoption should be fairly straightforward.

Dependencies
============

None

References
==========

* Discussing git/gerrit techniques with the infra team starting at
  2015-03-25T18:48:19 in
  http://eavesdrop.openstack.org/irclogs/%23openstack-infra/%23openstack-infra.2015-03-25.log

* Patches for review in oslo.log: https://review.openstack.org/#/q/project:openstack/oslo.log+topic:bp/graduate-oslo-versionutils,n,z
* Patches for review in oslo.utils: https://review.openstack.org/#/q/project:openstack/oslo.utils+topic:bp/graduate-oslo-versionutils,n,z

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

