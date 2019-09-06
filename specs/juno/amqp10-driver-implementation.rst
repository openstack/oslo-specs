====================================================
Provide a AMQP 1.0 implementation for oslo.messaging
====================================================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/oslo.messaging/+spec/amqp10-driver-implementation

We already have rabbit and qpid drivers for earlier (and different!)
versions of AMQP, the proposal would be to add an additional driver
for a _protocol_ not a particular broker.

Problem description
===================

The purpose of allowing for different drivers is to give users
choice. However every driver supported increases the maintenance
burden.

By targeting a clear mapping on to a protocol, rather than a specific
implementation, we would simplify the task in the future for anyone
wishing to move to any other system that spoke AMQP 1.0[1]. That would no
longer require a new driver, merely different configuration and
deployment. That would then allow openstack to more easily take
advantage of any emerging innovations in this space.

As an example, this would allow the use of the Dispatch Router from
the Apache Qpid project to be used. This has been designed as a
distributed router rather than a single-process, store-and-forward
broker and offers simple scalability and redundancy.

Proposed change
===============

A new driver will be added to oslo.messaging (a patch for this has
been available for review at https://review.openstack.org/75815).

The mapping outlined below considers the inter-mediated case
(i.e. where the driver connects to a message broker or network of
brokers). AMQP 1.0 would allow communication (in part or as a whole)
to be conducted directly between peers, without the use of
intermediaries. Development of this aspect however is considered a future
extension (see Appendix A for some more detailed discussion).

The aim is to support as many of the existing 1.0 enabled
intermediaries as we can without overly distorting the use of the AMQP
1.0 protocol.

In AMQP 1.0, addressable entities within a broker (or similar) are
called 'nodes' (e.g. queues or topics). Nodes are message 'sinks' or
'sources', to which messages are then typically sent by establishing a
sending or receiving 'link' to or from the given node. AMQP 1.0 does
not provide any standard configuration mechanism for configuring such
nodes on the fly (with the exception of dynamic reply queues). However
by allowing deployment specific prefixes to the addresses specified in
the source and target for receiving and sending links respectively, it
should be possible to get the required functionality working with a
variety of implementations and offer considerable flexibility to
deployers.

In RPC, there are three patterns for invocations, and a different
address format will be used for each.

(A) For invocations on a specific server the address will be formed by
concatenating the topic name and the server name and will be prefixed
by the exchange if specified and/or by a deployment specific
'server_request_prefix' string. The default value for this prefix is
'exclusive'.

(B) For invocations on one of a group of servers the address will be
the topic name and will be prefixed by the exchange if specified
and/or by a deployment specific 'group_request_prefix' string. The
default value for this prefix is 'unicast'.

(C) For invocations on all of a group of servers the address will be
the topic name, prefixed by the exchange if specified and also
prefixed with a configurable 'broadcast_prefix' string. The default
value of this prefix is '/broadcast/'.

Each pattern of communication is therefore identifiable through a
customisable pattern of address. This allows either the broker (or
equivalent) to be configured to match what the driver is using, or it
allows the driver to be configured to take account of built-in (and
non-configurable) conventions for a given broker.

So for example, Qpid Dispatch Router could be configured to recognise
three patterns based on the default prefixes. Any message for an
address starting with 'unicast' (or 'exclusive') would be routed to
only one subscriber for that address. Any message for an address
starting with 'broadcast' would be sent to all subscribers for that
address. [Some more detail on configuration is provided in Appendix B
for Qpid Dispatch Router and Appendix C for qpidd.]

Some other broker might not be configurable in this way, but might
have built in conventions around address patterns. E.g. all address of
the form '/queues/foo' would be treated as queues and messages sent to
them would be allocated to only one consumer. Addresses of the form
'/topics/bar' (or '/exchanges/bar') would be considered pub-sub topics
and the message would be distributed to all subscribers.

For each send request, the appropriate address will be deduced from
the specified target. If the server value on the target is specified,
it implies an invocation on a specific server and the address format
described above in (A) is used. If the server is not specified then
the fanout flag is considered. If that is specified it implies an
invocation on the entire group of servers identified by the topic and
the address format described in (C) is used. If neither the server
nor the fanout flag is specified it implies an invocation on one of
the group of servers identified by the topic and the address format
described in (B) is used.

A cache of sender links per target will be maintained to avoid the
overhead of recreating them on each request. (The alternative of using
a single sending link and setting the 'to' field is also a
possibility, but not all intermediaries might support that so it would
be an unnecessary limitation on choice). If there is no sender link
yet for the specified address one will be created and added to the
cache. The cache will be cleared on reconnect.

A single connection and session will be used for all the sender
links. If a timeout is specified for the request, this will be set as
a ttl on the request. The request will also have the 'to' field set to
the value used in the target for the link. This accommodates any
intermediary that may expect or prefer that means of addressing.

There will be a single receiver link per driver instance for replies,
this will have the dynamic flag set on the source.  Each request will
have the reply-to address set to the address to which this listener
is subscribed.  Each request will have a message-id set. This will be
echoed back in the correlation-id of any response message allowing it
to be correlated back to the waiting send request.

A server will subscribe for messages by creating three receiving
links: one to subscribe to requests specific to the server, one to
subscribe to requests for one of the servers group and one to
subscribe to broadcasts for all the servers in the group (i.e. one for
each form of address described in A, B and C above).  The first two
receiver links will have the distribution mode set to move, the third
will have the distribution mode set to copy. (Note: the distribution
mode is defined by the AMQP 1.0 specification to determine if/how
message are distributed between multiple subscribers).

Requests and responses for RPC will be sent pre-settled, meaning that
they are not explicitly acknowledged and therefore may be lost on
failover. Ideally notifications would be acknowledged both when
published and when received by a listener. (Note: at present the
rabbit driver acknowledges notifications when delivered, but published
notifications are not aknowledged. For the current qpid driver
notifications are not acknowledged either on publication or delivery).

Alternatives
------------

The rabbit driver is the only one that appears to be adequately
maintained at present. The qpid driver suffers from an impedance
mismatch between the API offered by qpid.messaging and that used for
the rabbit driver. The attempt to use a common architecture for these
two quite different APIs has led to the qpid driver being hard to
understand and inefficient in its mapping to AMQP 0-10.

One alternative to adding a new driver is to only support the rabbit
driver. That reduces the maintenance burden and gives clarity to
users. It does however restrict choice.

Another alternative would be to choose a different protocol as the
basis of the new driver. MQTT is focused on a pub-sub pattern and
doesn't incorporate competing consumers as is required for the current
oslo.messaging semantics. STOMP doesn't define interoperable
mechanisms for request-response. Since two of the existing drivers use
earlier versions of AMQP, AMQP supports all the patterns needed and
AMQP is an open standard (now standardised under ISO) it seems a
fairly obvious candidate.

Though this driver is not being suggested as a replacement for existing
drivers (merely an alternative), it does offer a path to greater
consolidation as it could also accommodate the non-intermediated style
of communication embraced by ZeroMQ. Perhaps even more powerful would
be a hybrid approach, where again the use of a common, standard
protocol would be advantageous.

Impact on Existing APIs
-----------------------

None

Security impact
---------------

The security implications are identical to that of the other
drivers. SSL will be supported as an option to secure the messaging
traffic where desired.

Performance Impact
------------------

There would be no impact whatsoever unless the driver is selected for
use. The overall performance will depend on which server components
are selected for use with the driver (unlike the existing drivers,
selection of this driver doesn't restrict the choice to a single
broker implementation).

Initial experience with the code[2] indicate that this driver in
conjunction with either qpidd or Qpid Dispatch Router compares very
favourably with existing drivers.


Configuration Impact
--------------------

The driver would be selected via the existing transport_url
option. The 'amqp' scheme in the url is used to select the AMQP
protocol.

There would be further configuration options to tailor the behaviour
of the driver to different deployments if desired, such as the various
prefix options described above. The defaults have been selected to
make broker configuration simple. In general configuration of the
messaging infrastructure is preferred to configuration of the driver
as it allows for more transparent, centralised changes.

Developer Impact
----------------

Any future changes to the driver API would need to be reflected in
another driver if this one were added.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  kgiusti@redhat.com

Other contributors:
  gsim@redhat.com
  fpercoco@redhat.com

Milestones
----------

Target Milestone for completion:
  Juno-1

Work Items
----------

Code review; the driver has been available for review via Gerritt for
some time. There is quite a lot of code in this that is in fact very
generic, and would be applicable beyond the use in olso.messaging. It
has been suggested (requested?) that this should be moved out of the
driver into its own library. There is in fact already a library that
contains this generic code, pyngus, and one task would be to update
the driver patch to rely on that as a dependency.

Automated testing should be set up. I have submitted a patch for
functional tests of the oslo.messaging API (which I used to test the
driver during development). In addition any relevant tests from
Tempest could be run using this driver and an appropriately configured
backend.

I have tested against both qpidd and Qpid dispatch router. Based on my
experience with other applications, I believe the driver would work
against the current ActiveMQ release (as well as ApolloMQ). For
RabbitMQ, the lack of support for the 'dynamic' flag on link source is
the main issue at present (which could be worked around if
desired). In theory it should also work against Microsofts ServiceBus
and IITs SwiftMQ as they support the aspects of the protocol
used. Those might require much more manual configuration at present, I
haven't used them so am unable to say for sure.

Allowing for reliable delivery of notifications by having publication
and delivery to consumers acknowledged.

Incubation
==========

Though this does not add a new (public) module, it would be prudent to
allow some time for the new driver to mature. Having some sort of
'beta' phase would be good, where the driver could be selected for
testing by interested parties and feedback provided.

Adoption
--------

The driver should be usable by any service using oslo.messaging

Library
-------

oslo.messaging

Anticipated API Stabilization
-----------------------------

There is no API impact. Stabilization of the new driver option itself
will take some time.

Documentation Impact
====================

The availability of an alternative option would at some point need to
be documented.

Dependencies
============

This driver depends on the qpid-proton python library for AMQP 1.0
support. Pyngus may be added as dependency, see Work Items above.

Appendix A: Some discussion of direct communication
===================================================

Supporting direct communication, where messages do not go through an
application layer intermediary user process, requires that
communicants accept incoming connections and can determine the correct
hostname and port to connect to.

Though this can be done by convention, e.g. using the server name as
the hostname and agreeing well-known ports, that can be restrictive
and cumbersome. A better approach is to have a registry of servers and
the host and ports they listen on.

This registry is much like the matchmaker used for 0MQ and the choices
applicable there would also be applicable to this driver.

However since there is already support for communication through n
intermediary, that can be used to dynamically distribute the data for
the registry to all communicants. This keeps configuration simple and
allows the system to adapt to changes.

Different schemes would be possible. One example would be to add a
configuration option that caused servers to start listenting on a
particular port. They would then advertise this fact by attaching a
property to any reply sent back for a request that identifies them
directly. The RPC clients could then cache these alternate addresses
and use them for any subsequent requests to the same server. In this
approach the communicants use the messaging intermediaries to locate
each other, but having done so they then 'offload' further
communication to a direct connection to reduce the load on the
intermediaries.

Another approach would be to have a special 'matchmaker' topic that
clients would subscribe to and servers would announce themselves
over. This would allow direct comunication even from the first request
to a given server.

These and indeed other schemes could be easily accomplished in a backward
compatible manner.

Appendix B: Configuring Qpid Dispatch Router
============================================

Using the default prefixes, the following address configuration, if
added to the configuration file for Dispatch Router, would setup the
required semantics for openstack::

  fixed-address {
      prefix: /unicast
      fanout: single
      bias: closest
  }

  fixed-address {
      prefix: /exclusive
      fanout: single
      bias: closest
  }

  fixed-address {
      prefix: /broadcast
      fanout: multiple
  }


Appendix C: Configuring Qpidd
=============================

Using the default prefixes, passing the following options to qpidd
(0.28 or later) would setup the required semantics for openstack::

  --queue-patterns exclusive --queue-patterns unicast --topic-patterns broadcast


References
==========

[1] http://docs.oasis-open.org/amqp/core/v1.0/amqp-core-complete-v1.0.pdf

[2] http://people.apache.org/~gsim/oslo.messaging_scalability.pdf

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

