============================================
 Add Support for a Router-based Message Bus
============================================

https://blueprints.launchpad.net/oslo?searchtext=amqp-dispatch-router

This specification proposes changes to the existing AMQP 1.0 driver
that will allow message transport over a brokerless AMQP 1.0 message
bus.  The blueprint for the original driver can be found here [1]_ and
the original architecture is described in [2]_.  The changes described
by this specification are a refactoring of the original design.  The
modified driver will still adhere to the AMQP 1.0 protocol standard in
order to remain agnostic to the particular message bus implementation.
Therefore support for existing AMQP 1.0 broker-based messaging
backends will be preserved.

Problem description
===================

The Qpid C++ Broker was the only messaging service that supported the
AMQP 1.0 protocol when the original driver was developed.  As such,
the original driver was designed and tested only against a
broker-based message bus deployment.

The AMQP 1.0 standard differs from its predecessors in that a broker
intermediary is no longer required.  This makes possible non-broker
based AMQP 1.0 messaging systems.  One such brokerless messaging
solution is a *message routed mesh*. This messaging solution is
composed of multiple interconnected *message routers* which route
messages to their destination using a shortest path algorithm.  Think
of it as an internet router, but at the message address level instead
of IP address.

The message router is **not a broker**.  It differs from broker
in the following significant ways:

* it is deployed with other routers in a mesh topology

* the router is queue-less

* it never accepts ownership of a message

  * any acknowledgment is end-to-end

* availability is provided by redundancy, not clustering

  * it aims for availability of the communication pathways rather than of individual messages

* it allows other message services to plug into the mesh

  * this includes brokers

Unlike a broker a messaging mesh composed of a single router is
sub-optimal. The router is designed to be deployed as a mesh of
inter-connected router nodes.  Each router has dedicated TCP
connections to one or more of its peers.  Clients connect to the
mesh by connecting to one of the routers using a single TCP
connection.  When a client creates a subscription the address used
for the subscription is propagated beyond the locally-connected
router.  All routers in the mesh become aware of the subscription
and compute an optimal path from each router back to the consuming
client.  When another client publishes to that subscription the
routers forward the message along the appropriate path to the
subscriber which consumes the message.

The following is a depiction of a four router mesh::

  +-----------+       +-----------+
  |RPC Server1|       |RPC Caller1|
  +-----+-----+       +----+------+
        |                  |
        |                  |
    +---v----+         +---v----+
    |Router A+#########+Router B|
    +---+----+         +----+---+ <------+
        #    ##       ##    #            |
        #      ##   ##      #        +---+--+
        #        ##         #        |Broker|
        #      ##  ##       #        +------+
        #    ##       ##    #
    +---+----+         +-----+--+ <------+
    |Router C+#########+Router D|  +-----+-----+
    +---+----+         +-----+--+  |RPC Caller2|
        ^                    ^     +-----------+
        |                    |
        |                    |
 +------+----+              ++----------+
 |RPC Caller3|              |RPC Server2|
 +-----------+              +-----------+

The '#' denote the inter-router TCP connections among Router A, B, C,
and D.  Router A has a single RPC server client attached.  Router B
has both an RPC caller and a broker attached.  Another RPC caller is
attached to Router C. An RPC server and an RPC caller are attached to
Router D.

Since shortest path routing is used RPC call/cast messages from RPC
Caller3 to RPC Server1 would only transit Router A and Router C.
Likewise RPC calls from Caller1 to Server2 would transit Router B and
Router D.  RPC Caller2 invoking a method on Server2 would only transit
Router D.  In this example notice that only those routers along the
shortest path between two communicating endpoints are involved in the
message transfer.  This provides for a degree of parallelism not
possible when using a single broker messaging service.

Note well that when a message transits a router on its way to its
final destination no queueing is done.  To be specific, none of the
routers along the path claim ownership of the message - i.e. the
routers do not acknowledge the message.  Instead the ack from the
consuming client is propagated back through the mesh to the origin
sender.  In other words, the router mesh does *end-to-end
acknowledgment*. In contrast a broker *does* claim ownership of the
message. However, an ack coming from the broker does not guarantee
that the message will be consumed.  It merely indicates that the
message has been queued.

Since routers compute the optimal path for a message it is possible to
configure redundant paths across the messaging mesh. By deploying
the routers over a physically redundant network it becomes possible to
suffer a degree of infrastructure loss without affecting the messaging
service.  Given that the routers themselves are stateless there is no
need for a clustering capability as there is in broker deployments.
While the mesh may be partitioned due to infrastructure failure,
there is no possibility of 'split-brain' occurring as there is no
master/slave relationship among connected routers.  All routers are
equal peers.

One limitation of a router mesh is that it cannot provide a message
store-and-forward service since the routers are queue-less.  However
brokers provide excellent store-and-forward capabilities and can be
integrated into the router mesh for exactly that purpose.

Support for integrated brokers are not a target for the Newton
release.  Therefore only limited support for Notification traffic will
be provided when using a routed mesh as a messaging backend.  Since
the mesh cannot store a notification message any attempt to publish a
notification for which there is no active subscriber will result in a
message delivery failure. For those applications which cannot tolerate
loss of a notification message it is recommended to use a broker as
the messaging backend for the notification service.  Since it is
possible to configure different messaging backends for RPC and
Notifications, it is possible to use a mesh for RPC traffic and a
broker for Notification traffic.


Proposed change
===============

Three issues need to be resolved in the driver in order to support RPC
over a routed messaging mesh:

* optimal message addressing
* credit management
* undeliverable messages

Addressing
----------

The current addressing scheme embeds the message delivery semantics
into the prefix of the address.  This prefix is used by the Qpid C++
Broker to automatically provision the proper node - either queue or
topic - for a given publish/subscribe request.  For more detail refer
to [2]_.

The qpidd broker identifies itself during connection set up it will be
possible to introduce a new addressing syntax while preserving the
existing syntax for backward compatibility. The original address
syntax used when connected to qpidd will remain unchanged to allow for
rolling upgrades.  The new address syntax will only be used when the
driver connects to a router mesh.  A configuration option will be
provided to manually select between the two addressing modes if
desired.

When comparing addresses the router employs a *longest prefix match*
algorithm. In contrast traditional brokers tend to use either a
pattern match or a simple exact match.  The router address syntax will
use the prefix of the address as an address space classification.

There are a few additional points to consider for routable addressing
that do not apply for broker addressing:

* Other applications may reside on the same mesh.  The addressing
  scheme should be designed to avoid collisions with an address space
  in use by a completely separate set of applications.
* Application aware routing.  It should be possible to distinguish
  RPC-related traffic from Notification traffic at the address level.
  This will allow the routers to route notification traffic to a
  broker(s) while RPC messages can travel point to point.
* Configurable routing subdomains.  It should be possible to further
  partition traffic on a per-project basis.  This could provide some
  traffic isolation between projects as well as allow for parallel
  oslo.messaging buses on the same mesh.

And like the existing address structure the delivery semantics
(e.g. fanout, direct, shared, etc.) must be provided to the mesh in
order to ensure the desired delivery pattern is used.

For RPC services there are 4 message delivery patterns that addressing
must allow:

* fanout
* direct to a given RPC server
* a shared subscription (e.g. shared queue)
* RPC reply

For Notification services there is only one delivery pattern: shared
subscription.

The following address syntax is proposed for the above patterns with
the exception of RPC reply:

+----------------+------------------------------------------------------------+
| Use            | Format                                                     |
+----------------+------------------------------------------------------------+
| RPC Fanout     | openstack.org/om/rpc/multicast/$EXCHANGE/$TOPIC            |
+----------------+------------------------------------------------------------+
| RPC Server     | openstack.org/om/rpc/unicast/$EXCHANGE/$TOPIC/$SERVER      |
+----------------+------------------------------------------------------------+
| RPC Shared     | openstack.org/om/rpc/anycast/$EXCHANGE/$TOPIC              |
+----------------+------------------------------------------------------------+
| Notifications  | openstack.org/om/notify/anycast/$EXCHANGE/$TOPIC.$PRIORITY |
+----------------+------------------------------------------------------------+

The prefix 'openstack.org' establishes the root domain of the address
space and is reserved for use only by OpenStack applications.  The
'om' tag further classifies this address as belonging to the
oslo.messaging service.  Reserving the address space prefixed by the
string 'openstack.org/om' for oslo.messaging's use will avoid
collisions should other applications also use the routing mesh.

The 'rpc' and 'notify' segments classify the service address space.
The 'rpc' and 'notify' tags will be used by the mesh to identify the
service.  This means that the mesh may send notification traffic to a
broker while RPC traffic issent point to point.

The 'unicast', 'multicast', and 'anycast' keywords determine the
messaging semantics that need to be applied when delivering a message.
'unicast' causes the message is to be delivered to one subscriber.
'anycast' causes the message to be delivered to one subscriber among
many [Scheduling]_.  For 'multicast' the router(s) will deliver a copy
of the message to all subscribers.

.. [Scheduling] When serving multiple subscribers to a given queue
         most brokers employ a *round-robin* distribution policy. A
         broker can guarantee that messages are evenly distributed to
         each subscriber since the broker is the single point of
         distribution.  There is no single 'central distributer' in a
         messaging mesh, so a mesh employs a different approach to
         'anycast' distribution. For example, a mesh will prioritize
         deliveries based on the lowest path cost.  This means that
         messages will be distributed to those subscribers with the
         lowest link cost/fewer inter-router hops first.  A mesh may
         also monitor credit levels across all consumers and detect
         when individual consumers are not keeping up with the message
         arrival rate (due to message processing delays).  This allows
         the router to deliver the message to a different client - one
         that is not exhibiting such a high backlog.

The values for $EXCHANGE, $TOPIC, and $SERVER are all taken from the
Target used for the subscription (or the destination when
call/casting).  It is possible to use the $EXCHANGE value to provide
further isolation of traffic based on the application's configuration.

The addressing for the RPC Reply will not use any of the above address
formats. RPC Reply addressing will work as it does today: the RPC
Reply address is dynamically assigned to the driver by the message bus
(broker or router) and is considered an opaque value.  The driver will
simply set the RPC Call message's reply-to field to this value before
sending the message. The IncomingMessage will use this reply-to value
as the reply message's address.

A single reply address will be used per TCP connection to the
bus as is done today. RPC Call messages will be assigned a unique
message identifier that will be written to the 'id' field of the
message header.  The RPC Server will place this identifier in the
reply message's 'content-id' field before sending it.  Received reply
messages will be de-muxed using the message's 'content-id' value and
sent to the proper waiter.

Credit Management
-----------------

Since the router mesh is unable to queue messages it must not accept
messages from publishers unless there is a consumer ready to accept
that message.  The mesh can limit the number of messages a publisher can
send to the mesh by controlling the amount of *message credit* that is
granted to the publisher.  The mesh will provide one credit for each
message it will accept from the publisher. The publisher cannot send a
message to the mesh unless it has credit to do so.

The mesh itself does not create credit as it has no capacity to store
messages.  Credit is made available to the mesh by the subscribing
clients.  A subscriber grants credit to the mesh - one credit for each
message it is willing to consume.  The mesh "proxies" the credit to
the client(s) that want to publish to the address the subscriber is
consuming from.  Therefore the router will not grant credit to a
message publisher unless there is at least one consumer subscribed to
the message's address that has granted credit to the mesh.  This
allows the mesh to block a sender until the consumer is ready to
consume from it.

The driver will provide credit for each subscription that is created.
Each server maintains its own subscriptions for its Target.  There is
also the per-transport shared RPC reply address subscription.  Each
subscription will make credit available to the router mesh which will
in turn distribute it among clients publishing to those addresses.

It is critical that the shared RPC reply subscription always has credit
available for replies coming from the RPC Servers.  Otherwise an RPC
Server can block attempting to send a reply to one particular client.
This would result in all RPC calls to that server also blocking
(i.e. head-of-line blocking). Fortunately the RPC call pattern is
self-limiting: a caller is blocked from sending any further requests
until a reply is received (or the call times out).  This means that
back pressuring the RPC callers via reply subscription credit is
probably unnecessary. Therefore the driver will grant a large batch of
credit to the reply subscription.  The driver will monitor the credit
level as messages arrive and are passed up to the client, replenishing
credit as needed. The amount of credit will be configurable with a default
of 200 credits.  This default may be altered in the course of tuning
the driver's performance.

RPC Server and Notification subscriptions cannot be as generous with
credit as the reply subscription.  A server needs to apply some
backpressure in the event that it fails to keep up with the incoming
message flow. Otherwise too many incoming messages will be buffered in
the driver. The goal will be to limit the amount of internal message
buffering per subscription while minimizing the performance impact.

Each RPC Server and Notification subscription will be granted a batch
of 100 credits by default.  This default is configurable and may be
adjusted in the course of tuning. The driver will replenish credit
back to the default level once credit drops below one half of the
default level.  The credit level check will be performed at the point
where the client acknowledges the message.  This will limit the worst
case buffering to about 300 messages per RPC server (direct, fanout,
and shared) and 100 messages per Notification topic and priority
(shared).

For tuning purposes the driver will maintain a count of detected
credit stalls - when the amount of outstanding credit hits zero before
the driver can replenish it.  The driver will issue a debug log
message when this event is detected.

The credit levels must also be accounted for at the publisher's
side. If no credit is available the driver must not allow the
publisher to send a message. Otherwise there would be no way to
prevent an unlimited number of messages from being buffered in the
driver waiting to be sent to the mesh.  Therefore the driver will
honor the credit limits imposed by the mesh and block senders until
credit is made available.

An RPC caller already blocks until the reply is received or the call
times out. If no credit is made available during the timeout period
the driver will simply fail the call operation as it would if no reply
were received in time.

Unlike an RPC call an RPC cast does not wait for a reply. When casting
the client will also be blocked if no credit is available.  In the
case of a *non-fanout* cast the caller will also wait until an
acknowledgment is received from the destination (not the mesh).

A *fanout* cast will behave just like the cast case, except that the
acknowledgement comes from the mesh itself rather than the
destination.  This is a behavior of the mesh meant to prevent a return
acknowledgement "storm".

The driver will also obey the credit rules when RPC replies are sent.
The RPC Server will block when responding if no credit is available.

There is one other credit-related issue that must be addressed by the
driver: what if credit is not made available in a timely manner?  Or
credit never arrives due to the lack of a consumer?

The existing broker-based solutions address the lack of a consumer by
automatically creating a queue in response to a publish request. By
auto-creating a queue the broker allows the application to 'ride out'
any delay in the arrival of a legitimate consumer.  Even if the
consumer never arrives the broker will accept the message.  This means
that as long as a broker is present a publisher will not have to wait
for a consumer to arrive.

There is no telling how many applications have come to rely on this
behavior.  Unless the driver compensates for this in some way it is
likely that things will break badly.

The driver will account for this by mandating a timeout for *every
message that is sent to the router mesh*. If credit does not arrive
within the timeout an exception will be raised indicating that the
operation failed.

The only caveat to the above is that the oslo.messaging API does not
*enforce* use of a timeout when sending messages.  There are two send
methods in the base **Driver** class: *send()* and
*send_notification()*.  In addition the **IncomingMessage** class has
a *reply()* method that is used to send RPC replies.  Only the
*send()* method accepts a timeout parameter, the rest do not. In the
cases where a timeout value is not provided via the API the driver
will apply a default value. If the *send()* method is invoked without
supplying a timeout value then the default timeout will be applied by
the driver.

The proposed default timeout for RPC calls and casts (either with or
without fanout) will be 30 seconds.  If no credit arrives before the
timeout expires either a **MessagingTimeout** or a
**MessageDeliveryFailure** exception will be raised.  The
**MessagingTimeout** exception will only be thrown in the case of a
*send()* call that provided a timeout value.  The
**MessageDeliveryFailure** will be raised in all other cases.

Note also that the timeout will also encompass the time spent waiting
for the RPC reply to arrive.

When sending a reply via the *reply()* method it is critical that the
RPC Server never block indefinitely waiting for credit from the RPC
client.  This will cause the entire RPC server to hang, affecting other
clients with pending requests.

Although the RPC client's driver will grant a large amount of credit to
the reply subscription there still exists the possibility that the
client has become unreachable since the RPC call was processed.  The
client may have crashed or the mesh may have lost connectivity.  To
prevent this a default timeout will also be applied to the RPC
*reply()* call.  Like an RPC cast, if no credit is made available or
no acknowledgment is received from the peer before the timeout expires
the reply will fail.  Unlike an RPC cast no exception will be thrown
since there is no way for the application to recover.  Instead an
error will be logged.

Undeliverable Messages
----------------------

It is possible that the destination of a message may become
unreachable while the message transits the router mesh.  The consumer
may have crashed or a network failure may occur leaving the message
with nowhere to go.  In this case the router mesh will send a negative
acknowledgment back to the original sender.  This takes the form of an
AMQP 1.0 disposition performative with a terminal delivery state of
either MODIFIED or RELEASED.  These states notify the original sender
that the message was never delivered.  Thus the message can be
retransmitted at a later time without risk of duplication.  However
there is no guarantee that *message order* will be preserved on
retransmit.

Re-delivery will not be a goal of the Newton release.  The driver will
simply treat the reception of a RELEASED or MODIFIED disposition as a
message delivery failure.  This may be addressed in a different
fashion in a future release.

[Actually, it may be possible to safely resend RPC casts since cast
does *not* guarantee strict message ordering. For now this is TBD]

The disposition will be used by the driver to implement the optional
'requeue' feature defined by oslo.messaging.  When a consumer invokes
the requeue method on an incoming message the driver will send a
disposition with terminal state RELEASED back to the publisher.

What actually happens to the released message depends on the
capability of the message bus.  A broker will simply re-queue the
message.  A mesh may either forward the message to another consumer
(if present), or proxy the RELEASED state back to the publisher.  As
described earlier the driver will treat a RELEASED state as a message
delivery failure in Newton.


Alternatives
------------

There are other alternative messaging backends that at first glance
appear to offer similar capabilities as a routed mesh.  ZeroMQ, for
example, is also a non-brokered solution.  ZeroMQ also provides a
point to point messaging pattern that can be used for RPC services.
However, there are some significant differences between ZeroMQ and a
routed mesh.

First, clients of a routed mesh only require a single TCP
connection to the router mesh, whereas the ZeroMQ implementation
uses a TCP connection per destination.  In other words a ZeroMQ RPC
Server will require a TCP connection to every RPC client it
communicates with.  Therefore ZeroMQ will require more TCP-related
resources as the number of RPC Servers and clients scale up.

Second, in a router mesh there is no need to have all clients
reachable via TCP as is required by ZeroMQ.  The router mesh does
message-layer routing, not IP address routing. This allows clients and
servers on separate private IP subnets to interoperate using the
router mesh as a bridge.  These subnets do not need to be visible
to each other over an IP mesh.  For example, RPC Servers may reside
on a private subnet in Company A, while the RPC Clients reside on a
different private subnet in Company B.  This can be accomplished by
ZeroMQ but would require proper configuration of firewalls and
NAT'ing.

It also provides for better load-balancing where a call is made on a
service group. The client is not responsible for determining which
service instance in the group should get the message.

Lastly, the router mesh inherently provides service discovery.  A
dedicated service discovery component is not needed.

A federated broker network is another messaging bus that is somewhat
like the router mesh.  However a routed mesh is a much better
solution for distributed messaging. In fact message routing was
developed explicitly to provide a better solution than broker
federation for distributed messaging.  Versions of AMQP previous to
1.0 *required* a broker intermediary. Therefore the only way to
distribute messages prior to 1.0 was to develop a broker-based routing
solution.  The 1.0 version of the protocol drops this broker
intermediary requirement and makes a routed messaging mesh
possible. A network of lightweight, stateless message switches
augmented by brokers only where store and forward is needed can
completely supplant a federated broker deployment in terms of
functionality.

Messages travelling through a broker federation are queued at each
node, unlike a routed mesh.  This increases latency, hurts
throughput, and removes the possibility of end-to-end
acknowledgment. This makes it harder for the ‘client’ to know when to
resend the request and for the ‘service’ to know when to resend a
response. It can lead to trying to make the broker replicate all
messages which makes scaling harder.

The router mesh is not the right solution for all deployments.  A
single broker is a much simpler solution if it can meet a deployment's
messaging requirements.  ZeroMQ will be a good choice for those
distributed deployments not bound by routing or TCP resource
constraints.  Likewise there will be deployments where a router
mesh will be the optimal messaging backend.

Impact on Existing APIs
-----------------------

The existing API should not require any changes.  These changes will
preserve compatibility with existing qpidd-based deployments.

Security impact
---------------

From the driver point-of-view there will be no change in the security
model.  The driver already supports both TLS server and client
authentication. It also supports SASL-based authentication, which
includes Kerberos support.  The driver conforms to the security model
as defined by the AMQP 1.0 specification and will work with any
compliant messaging service.

Performance Impact
------------------

Any performance impact should be limited to the users of the AMQP 1.0
driver.  Users of other drivers such as RabbitMQ will not be affected.
There may be an effect on the performance as it now stands with the
Qpid broker, however every effort will be made to minimize this.

Configuration Impact
--------------------

New configuration items for credit and timeout duration will be added.
The default values for these options will be determined as the driver
is tuned for performance.  These items include:

* Credit limit for Reply subscription (Default: 200)
* Credit limit for Server subscriptions (Default: 100 per subscription)
* Driver-level default RPC call/cast timeout (Default: 30 seconds)
* Driver-level default RPC response timeout (Default: 10 seconds)
* Driver-level default Notification timeout (Default: 30 seconds)
* Addressing Mode (Default: dynamic)

Developer Impact
----------------

Any new features added to oslo.messaging that must be implemented via
driver modification would need to be implemented in this driver as
well. If such new features require behavior unique to a broker
backend it may be impossible to support them when using a routed
mesh.

Testing Impact
--------------

The Qpid Dispatch Router will be used as the messaging backend for
testing.  More information about this router can be found here [3]_.

The Qpid Dispatch Router will need to be available in the CI
environment in order to fully test this driver.  This is gated by
inclusion of the router packages and its dependencies into Debian
testing.  The Apache Qpid community is in the process of submitting
the following packages for inclusion in Debian:

* qpid-dispatch-router
* qpid-dispatch-router-tools
* python-qpid-proton
* qpid-proton-c
* pyngus

These packages are already available in the EPEL repositories.

The driver must pass the existing amqp1 driver tests.

The driver must pass the gate-oslo.messaging-src-dsvm-full and
gate-oslo.messaging-dsvm-functional tests.

Devstack already supports using a standalone router [4]_.  It may be
necessary to add the qpidd broker as the notification transport in
order to pass the above gate tests.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  kgiusti@gmail.com  (kgiusti on IRC)

Other contributors:
  ansmith@redhat.com

Milestones
----------

Target Milestone for completion: newton

Work Items
----------

* Implement new addressing syntax
* Implement credit handling
* Implement new configuration items
* Update documentation
* Functional test integration
* Upstream CI integration


Incubation
==========

None.


Adoption
--------

It is unlikely that this driver will be adopted in the majority of use
cases as a single broker is usually sufficient. Adoption is more
likely among those deployments that have medium to large clouds
deployed across a distributed mesh topology.

Library
-------

oslo.messaging

Anticipated API Stabilization
-----------------------------

None

Documentation Impact
====================

The library's AMQP 1.0 documentation will need to be updated for the new backend [5]_.

Dependencies
============

The driver will require no additional dependencies.

References
==========

.. [1] https://blueprints.launchpad.net/oslo.messaging/+spec/amqp10-driver-implementation
.. [2] https://git.openstack.org/cgit/openstack/oslo-specs/tree/specs/juno/amqp10-driver-implementation.rst
.. [3] http://qpid.apache.org/components/dispatch-router/index.html
.. [4] https://git.openstack.org/cgit/openstack/devstack-plugin-amqp1/commit/?id=142d975ac38a6a22c3a1eee6f43009d2098b270d
.. [5] http://docs.openstack.org/developer/oslo.messaging/AMQP1.0.html

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

