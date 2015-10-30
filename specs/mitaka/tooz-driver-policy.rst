====================
 Tooz Driver Policy
====================

OpenStack project teams have identified a number of opportunities for making
use of distributed lock managers and the primitives that they provide. Tooz
has traditionally included a number of drivers which meet the bare minimum
requirements for some of these, but are deficient in many ways.

Problem description
===================

Given the weight that in-tree drivers will carry with users of OpenStack,
there is a desire to ensure that users deploying will only be presented with
choices of high quality that meet all of the requirements of the projects
in OpenStack that consume tooz.

Proposed change
===============

Drivers that are not sufficient must be deprecated and eventually removed
from tooz. They will still be consumable for downstreams of tooz that do
not have the same requirements of all of the OpenStack projects.

In order to identify which drivers are sufficient, a policy will be added to
the documentation of tooz which provides the requirements for inclusion. This
policy will be modeled on the oslo.messaging drivers policy.

Alternatives
------------

Drivers could be classified in documentation, but kept in-tree. This would
have minimum impact on tooz downstreams, but also add some risk to OpenStack
deployers who might select tooz.

The API of tooz could also be changed to force callers to express their
needs and allow drivers to specify their assumptions aroune the capabilities
of the tooz backend in use. This would be extremely complex and make tooz
harder to consume.

Impact on Existing APIs
-----------------------

The API will be unchanged, but the configuration options available to
downstreams of tooz will be more limited.

Security impact
---------------

This will lower the surface area of tooz slightly.

Performance Impact
------------------

Some backends are deficient entirely because they are non-performant or
non-scalable. So this reduces the risk of a user of OpenStack encountering
performance problems.

Configuration Impact
--------------------

Some backends will not be available anymore, or will cause deprecation
warnings. The drivers will not be removed for several cycles after
deprecation, so this is a long-term impact.

Developer Impact
----------------

Testing requirements on backends will be elevated, so developers will need
to spend more effort on backends, especially on new drivers.

Testing Impact
--------------

Drivers will need to have a higher level of test coverage.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  clint-fewbar (SpamapS)

Milestones
----------

Target Milestone for completion:

mitaka-1

Work Items
----------

 * Write policy in tooz documentation

Documentation Impact
====================

N/A

Dependencies
============

N/A

References
==========

https://etherpad.openstack.org/p/mitaka-cross-project-dlm


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
