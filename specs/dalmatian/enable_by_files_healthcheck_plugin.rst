===================================
 Enable By Files Healthcheck Plugin
===================================

https://blueprints.launchpad.net/oslo.middleware/+spec/enable-by-files-healthcheck

A generic healthcheck plugin to verify specific file path is available.

Problem description
===================

The filesystem backend of glance can be used to mount NFS share as local
filesystem, so it does not required to store any special configs at
glance side. Glance does not care about NFS server address or NFS share
path at all, it just assumes that each image is stored in the local
filesystem. The downside of this assumption is that glance is not
aware whether NFS server is connected/available or not, NFS share
is mounted or not and just keeps performing add/delete operations
on local filesystem directory which later might causes problem
in synchronization when NFS is back online.

Proposed change
===============

We are planning to add new plugin `enable_by_files` to `healthcheck`
wsgi middleware which can be used by all openstack components to check
if desired path is not present then report `503 <REASON>` error or
`200 OK` if everything is OK.

.. code-block:: ini

  [app:healthcheck]
  paste.app_factory = oslo_middleware:Healthcheck.app_factory
  backends = enable_by_files (optional, default: empty)
  # used by the 'enable_by_files' backend
  enable_by_file_paths = /var/lib/glance/images,/var/lib/glance/cache (optional, default: empty)

  # Use this composite for keystone auth with caching and cache management
  [composite:glance-api-keystone+cachemanagement]
  paste.composite_factory = glance.api:root_app_factory
  /: api-keystone+cachemanagement
  /healthcheck: healthcheck

The middleware will return "200 OK" if everything is OK,
or "503 <REASON>" if not with the reason of why this API should not be used.

"backends" will the name of a stevedore extentions in the namespace
"oslo.middleware.healthcheck".

In addition we will also add a check to verify if both backends i.e.
`disable_by_file` or `enable_by_files` are mentioned then we will
raise appropriate exception which will exit the process with
failure.

Alternatives
------------

None

Impact on Existing APIs
-----------------------

This new healthcheck plugin is exactly opposite of existing plugin
`disable_by_file`. So operator needs to make sure that `disable_by_file`
plugin should not be configured along with `enable_by_files` plugin.

Security impact
---------------

None

Performance Impact
------------------

None

Configuration Impact
--------------------

The middleware needs to be configured as shown in `Proposed Change`
section.

Developer Impact
----------------

None

Testing Impact
--------------

Middleware will be covered by the unittest
And also have a tempest test for each services that have integrated it.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Abhishek Kekane (abhishek-kekane)

Other contributors:
  None

Milestones
----------

Target Milestone for completion:

* Dalmatian-3

Work Items
----------

* Write the `enable_by_files` healthcheck plugin
* Update the applications to use it

Documentation Impact
====================

N/A

Dependencies
============

N/A

References
==========

* Glance NFS improvement spec - https://review.opendev.org/917284
* EnableByFiles plugin PoC - https://review.opendev.org/919666

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
