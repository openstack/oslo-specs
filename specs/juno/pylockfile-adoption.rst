=============================
 Adoption of pylockfile
=============================

https://blueprints.launchpad.net/pylockfile/+spec/pylockfile-adoption


Problem description
===================

The pylockfile library is used by at least oslo.db instead of
oslo-incubator/lockutils. This library has seen a few maintenance issues in
the last months, which caused problem. The current maintainer is looking for
help to maintain it in the future.

Proposed change
===============

The proposed change is to adopt this library under the Oslo program so we
can maintain it and merge it with oslo-incubator/lockutils.
The goal is to move the feature we have in lockutils and that are not
present in pylockfile such as fcntl() based locking, and then release
oslo.lockutils as a thin-layer of top of it relying on oslo.config and
oslo.log.

Alternatives
------------

Do nothing.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  jdanjou

Other contributors:
  None

Milestones
----------

juno-3

Work Items
----------

- Create a repository on OpenStack infra
- Add oslo-core to pylockfile-core on Gerrit
- Release a new version of pylockutils

References
==========

* Request from current pylockfile maintainer for help:
  https://github.com/smontanaro/pylockfile/issues/11#issuecomment-45634012

* openstack-dev thread: http://lists.openstack.org/pipermail/openstack-dev/2014-June/038387.html

* Review to create pylockfile repository: https://review.openstack.org/#/c/101911/


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

