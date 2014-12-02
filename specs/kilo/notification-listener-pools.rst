
===========================================
oslo.messaging: Notification listener pools
===========================================

https://blueprints.launchpad.net/oslo.messaging/+spec/notification-listener-pools

The idea is that you can have multiple groups/pools of listeners
consuming notifications and that each group/pool only receives one
copy of each notification.

Problem description
===================

Currently if two applications use the oslo.messaging notification listener
and want to subscribe to the same topic, they steal messages from each other.

The current workaround is to configure the notifier part to publish the message
twice on different topic. This confuses a lot of people and this is
undocumented.

Proposed change
===============

So part of the purpose of this BP is a bit hardcoded into oslo.messaging and
have bad side effect. The proposal will fix that.

We need to add a pool parameter for the messaging.get_notification_listener()
API in order to support this.

In all AMQP drivers, this is implemented by using the pool name as the queue
name for consume from the topic. To keep backward compatibility, by default,
the topic name will continue to be used as the pool/queue name.

Alternatives
------------

Documents the workaround.

Impact on Existing APIs
-----------------------

oslo.messaging.get_notification_listener will get a new parameter 'pool' to
configure the pool name.

Security impact
---------------

None.

Performance Impact
------------------

None.

Configuration Impact
--------------------

None.

Developer Impact
----------------

None.

Testing Impact
--------------

None.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  sileht

Other contributors:
  None

Milestones
----------

K-1

Work Items
----------

Works already done: https://review.openstack.org/125112

Incubation
==========

None.

Adoption
--------

None.

Library
-------

None.

Anticipated API Stabilization
-----------------------------

None.

Documentation Impact
====================

The new pool parameter will be documented.

Dependencies
============

None.

References
==========


Code in review: https://review.openstack.org/#/c/125112/


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

