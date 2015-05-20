=====================================================
 oslo.messaging: remove ending message for rpc reply
=====================================================

https://blueprints.launchpad.net/oslo.messaging?searchtext=remove-double-reply

We are going to send a single message for RPC reply.

Problem description
===================

Currently, when we wait for a RPC reply, for each msg_id we receive two AMQP
messages - first one with the payload, a second one to ensure the other have
finish to send the payload. This was made because a long time ago 'reply'
allowed generator as payload to send multiple messages on one 'rpc.call' -
see [1]_.

Oslo.messaging do not support providing a generator as the payload - it send
reply with data and then reply with ending - so it becomes useless to double
RPC messages for each call. Based on this suggestions, so we are going to
remove the second AMQP message sending.

This change will be not backward compatible, so we have to choice how we handle
this backward compatibility and the deprecation. This spec is the proposed
change about that.

Proposed change
===============

This change is not backward compatible, so we need to make sure that there is
some way to run mixed versions of services, where version N can always talk to
N+1 and the reverse, so that we can do rolling upgrades.


Plan for the rolling upgrade:
-----------------------------

In Kilo:
````````
The old behavior, fully compatible with Liberty and older versions.

RPC-server sends reply in two messages, can reply to clients, versions <= L+1.
RPC-client expects replies in two messages, can receive replies from servers
with versions <= L.

In Liberty:
```````````
We are going to implement a new behavior, but keep the old one by default.
Fully compatible with Kilo and older versions.

We change the ReplyWaiters to handle reply in one message and two messages,
like it does [2]_.

We create a boolean configuration option, defaulted to False. If this one is
True, we sent the reply in one message otherwise we keep the current behavior
of two messages. This config option will allow us to test the both - old and
new - behavior into our tests suite and allow to enable this new behavior
earlier. So this is only dedicated for early adopter and testing.
This options is not need in normal upgrade workflow and must be removed as soon
as we enable the new behavior by default to be sure that deployed cloud with
L+1 will not break when they are upgraded to L+2 because cloud operator
enforced the old behavior.

RPC-server sends reply in two messages, can reply to <= L+1
RPC-client expects replies in two messages or one message, can receive replies
from all versions

In M release cycle:
```````````````````
We are going to enable the new behavior by default, remove the config option
and support only the reply in one message. This will break backward
compatibility with oslo.messaging <= kilo and oslo-incubator RPC legacy code.

rpc-server sends reply in one messages, can reply to >= L
rpc-client expects replies in two messages or one messages from all versions

In N release cycle:
```````````````````
We are going to remove legacy code that allow to receive replies from <= L.

rpc-server sends reply in one messages, can reply to >= L+1
rpc-client expects replies in one messages, can receive replies from >= L+1


Alternatives
------------

Using the oslo.messaging payload version.
But this have been designed for the content of the message itself.
Not really for this purpose. And the deserialization occurs in the lower
layer of oslo.messaging. When we handle the reply the version fields have
already been removed.

This breaks backward compatibility too.

We can already track the old and the new format because the old format has
the attribute "result" OR "ending" the new one will have "result" AND
"ending".

Note that issue is in the RPC call replies code. In case of rolling upgrade, we
have to think about the fact that the client will wait message that can
come from same or upper version of oslo.messaging. We already do not support
lower versions from the application PoV.

Or from the server point of view, we will send reply that must be
understandable by a wide panel of versions.

This is the first time (I guess), we encounter this kind of issue, some other
bugs need to break the backward compatibility to be fixed, too.
(Because we need to change RabbitMQ queue attributes or move a queue to
another exchange)

The main goal is to choose the backward compatible versions count and use
the same kind of deprecation in other changes like this one.

Impact on Existing APIs
-----------------------

NA

Security impact
---------------

NA

Performance Impact
------------------

This will reduce by 2 the number of reply messages that will transit on a
RabbitMQ/QPID cluster.
Local performance tests shows, that this change brings nearly 30 percent
increase in the number of RPC `call` messages per second.

Configuration Impact
--------------------

A hidden configuration option will allow to switch to the future behavior
for early adopter and for testing purpose.

Developer Impact
----------------

NA

Testing Impact
--------------

We must test that the new ReplyWaiters code can handle reply that come from
a oslo.messaging version that sent reply in one message and from the one
that sent the reply into two messages. This is driver specific change, so we
should implement this in unittests.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  vsergeyev

Other contributors:
  sileht

Milestones
----------

Target Milestone for completion:
  Liberty for the step 1
  M or N for the step 2

Work Items
----------

1. Change the ReplyWaiters to handle reply in one message and two messages.
2. Add a config option and change the _send_reply() method to allow sent reply
   and `ending` in a single message, based on config option.
3. Remove the config option and enable the new behavior by default.
4. Remove the `ending` parameter procession from the ReplyWaiters.

Incubation
==========

NA

Documentation Impact
====================

Inform deployer about future incompatibility with a too old oslo.messaging
version

Dependencies
============

NA

References
==========

.. [1] Legacy oslo rpc behavior: https://github.com/openstack/oslo-incubator/blob/stable/icehouse/openstack/common/rpc/amqp.py#L461-L470
.. [2] Refactor processing reply in ReplyWaiter: https://review.openstack.org/#/c/180583/

WIP reviews:

* https://review.openstack.org/#/c/180542/
* https://review.openstack.org/#/c/180583/


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

