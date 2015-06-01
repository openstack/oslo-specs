========================================
New ZeroMQ driver implementation details
========================================

https://blueprints.launchpad.net/oslo.messaging/+spec/zmq-patterns-usage

This specification proposes new ZeroMQ driver implementation details.
This proposal may be considered as extension of [1]_ and further
driver development road-map. Drawings and charts are presented in [2]_.


Problem description
===================

Oslo.messaging provides a few patterns of communication between components.
These patterns are CAST(FANOUT), CALL and NOTIFY.

ZeroMQ driver may be implemented in several ways.
Existing driver implementation sticks to a universal socket pipeline approach.
This means that all messaging patterns are implemented over a single socket
pipeline.

In [1]_ there were proposed to switch from a splitted universal
forward(PUSH/PULL)+backward(PUB/SUB) pipeline to a unified REQ/REP
bidirectional pipeline. The change simplifies the driver implementation and
makes it more reliable but the pipeline still remains universal.

The main drawback of the universal pipeline is that it can not be optimized
for some specific messaging pattern. For example, if we would like to
make a FANOUT cast over a universal pipeline (PUSH/PULL or REQ/REP does not matter)
we have to emulate it over a number of direct casts while it could be
done over PUB/SUB zeromq pattern using a single api call.

This specification proposes to extend new zmq driver implementation
with several specific socket pipelines according to each messaging pattern.


Proposed change
===============

ZMQ Proxy
---------

The main reason to have a proxy entity between the client and server
is lack of ability in zmq library to bind several sockets to a single
IP port.

The alternative path is to use dynamic port binding which in terms of zmq API
means using of a :meth:`zmq.Socket.bind_to_random_port` method.

Despite the fact that brokerless dynamic port binding seems attractive,
the following serious pitfalls show that the proxy solution is actually
simpler and more reliable.

    1. Dynamic port binding consumes more time to establish a connection.
       Time exceeding may happen if too many ports in a system are busy
       and the function needs a lot of retries.

    2. Number of ports is limited to a number of 16-bit integer 2^16 = 65535.
       So a number of unoccupied ports may also come to the end especially for
       a large-scale clouds.

    3. Less critical but significant complexity is a necessity to notify a
       client about the chosen port somehow. Such mechanism may be implemented
       using Redis to pass information between nodes. Time for Redis to
       sync tables has to be added to a connection time in 1. Here the delay
       may be even greater than in 1, because of the network latency.

All these points makes us to give preference to a proxy solution. It also
has its drawbacks, but advantages are:

    1. More predictable time to establish a connection.

    2. Fixed number of ports to allocate for the driver.

Important point is the proxy should stay as close to the rpc-server as possible
and should be considered as a part of an rpc-server. The proxy is not a central broker
to run it on a separate host even if it would be some kind of a virtual host.

The proxy communicates with rpc-servers over IPC protocol and shields them from TCP network.
To implement the concept of a `Dedicated socket pipeline` we can use a separate proxy for
each pipeline to keep them independent.


Dedicated Socket Pipelines
--------------------------

The main part of a change proposal which complements to [1]_.
The purpose is to use the most appropriate zmq pattern for oslo.messaging pattern
implementation.


1. REQ/REP (ROUTER/DEALER) for CALL

In [1]_ spec there was proposed to use a socket pipeline built over REQ/REP.
We do not change our mind here and keep this pipeline, but use it only for
CALL pattern purposes.


2. PUB/SUB for FANOUT CAST

PUB socket provides a possibility to publish to a number of connected hosts.
SUB allows to subscribe to a number of publishers listening to a specific topic.
Having a proxy in the middle we actually have 2 steps of FANOUT message passing.
First is TCP between nodes. And the other is local per node between rpc-servers
subscribed to a topic.

rpc-client(PUB:TCP) -> (XSUB:TCP)proxy(XPUB:IPC) -> (SUB:IPC)rpc-server

To exactly know which host listens to which topic we need a kind of a directory service (DS)
in the middle of a cloud. The service will most likely reside on a controller node(s).
It may be distributed or stay standalone. Address(es) of the DS should be
passed over config option to the driver.

Rpc-server listener puts a record to DS about host + topic it listens to.
Rpc-client gets all hosts by topic and publishes a message to them.

In some sense DS becomes a single point of failure, because FANOUT will not work properly
without DS up and running. So for real-life deployments all standard HA
methods should be applied for the service.

The first candidate for DS implementation is Redis, but it is not necessarily so.

It worth noting that using of a DS doesn't mimic a central-broker concept.
All messages go from node to node directly, therefore we still stay
peer-to-peer on messages level which is important for scalability.
We also don't waste time requesting DS while using a direct messaging patterns like CALL.
DS state caching on local brokers (proxy) may also help to reduce dependency
on a central node(s). But latter is a kind of optimization matter.


3. PUSH/PULL for direct CAST

This is optional, but PUSH/PULL is exact pattern for direct CAST,
so should be the most optimal. Technically direct CAST could be implemented
over any available zmq socket type.


4. PUB/SUB for Notifier

The PUB/SUB zeromq pattern well suited for Notifier implementation.
In order to keep socket pipelines as well as messaging patterns implementation independent
from each other we need to make this in a separate pipeline in spite of 2 also uses PUB/SUB.

Notifier is not as widely used as an RPC (1-3), so this item may be optionally implemented
in next iterations. Ceilometer seems to be the main client of the pattern.


Heartbeats
----------

As we use TCP transport in all patterns we can use ZMQ_TCP_KEEPALIVE
zmq option to detect dead connections.


Alternatives
------------

All things may be implemented over universal socket pipeline as described in [1]_.


Impact on Existing APIs
-----------------------

None.

Security impact
---------------

For the sake of secure message passing some features from [3]_ may be used.


Performance Impact
------------------

None.


Configuration Impact
--------------------

Configuration options should be added to setup pre-allocated ports.

9501 - zmq REQ/REP pipeline port
9502 - zmq PUB/SUB CAST+FANOUT port
9503 - zmq PUB/SUB Notifier port
9504 - probably direct CAST port

fanout_ds_address - address of the name service used by the driver.


Developer Impact
----------------

None.


Testing Impact
--------------

Unit tests should be rewritten because driver internals will change significantly.

Existing functional tests should pass without changes.
Maybe we can extend them by adding some more tricky cases.

We also have py27-func-zeromq configuration to run as CI gate job.
This gate should be used for the new driver to check it.

We also need some kind of multi-node deployment testing.
Some HA scenarios testing is also needed.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
    ozamiatin


Milestones
----------

Target Milestone for completion: liberty-3

Work Items
----------

Modified work items from [1]_

- Implement CALL (REQ/REP) pipeline and surrounding modules
    - move message serialization, topics manipulations etc.
      from existing implementation to appropriate modules
    - rpc_client part
    - broker_part
    - rpc_server part
    - replies handling
- Implement CAST over PUSH/PULL pipeline (client-proxy-server)
- Implement FANOUT and its PUB/SUB pipeline
- Implement Notifier separate PUB/SUB pipeline


Incubation
==========

None.


Adoption
--------

Deployment guide may slightly differ because of some new config options added
(e.g. additional ports allocated for each pipeline).

It worth noting that during stabilization period both drivers the old and the
new one will stay in repos. After stabilization is over the old driver will
be deprecated over a standard deprecation path.


Library
-------

oslo.messaging


Anticipated API Stabilization
-----------------------------

The new driver should successfully run with devstack.
Existing oslo.messaging functional tests should successfully pass in devstack-gate.


Documentation Impact
====================

We need to cover all aspects of the new driver with detailed documentation and UML charts.
We need to update zmq deployment guide [4]_ for the new driver as well.


Dependencies
============

None.

References
==========

.. [1] https://review.openstack.org/#/c/171131/
.. [2] http://www.slideshare.net/davanum/oslomessaging-new-0mq-driver-proposal
.. [3] http://rfc.zeromq.org/spec:26
.. [4] http://docs.openstack.org/developer/oslo.messaging/zmq_driver.html

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
