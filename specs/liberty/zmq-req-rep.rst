==================================================
Change ZeroMQ driver underlying pattern to REQ/REP
==================================================

https://blueprints.launchpad.net/oslo.messaging/+spec/zmq-req-rep

Because of too many changes are proposed lately (not only pattern substitution)
this spec actually proposes to provide a parallel implementation of ZeroMQ
driver (zmqv2). The recommended underlying pattern is REQ/REP + ROUTER/DEALER
which will simplify drivers implementation and improve its reliability.
After the implementation there will be a possibility to compare both implementations.

The key advantage of the legacy zmq driver will be it's backwards compatibility
and compatibility with older versions of ZeroMQ library (after some fixes).


Problem description
===================

Currently ZeroMQ driver actually implements request-reply pattern,
but do it on top of more primitive and less reliable PUSH/PULL.

The main lack is that PUSH/PULL have no backwards connection for
replying to sender. We send message one way and forget. If we would like
to receive reply we need to establish one more connection.
In current driver implementation it is done over PUB/SUB.
It results in a need of serving for one more socket connection pipeline.
More code to make things work. More probability of connection fails.

The main reason to change to REQ/REP is that it do all things "out of the box".


Proposed change
===============

Current ZeroMQ driver implementation uses cross-service zmq_receiver
daemon as a proxy to have a single TCP connection (port) per node.
All messages come to the TCP connection and then are spreading between
services via IPC. The new version will stick to this general architecture.

So we have three parts to connect:

rpc_client (REQ) <=> (ROUTER) zmq_receiver (DEALER) <=> (REP) rpc_server

That is enough for CALL method.

The advantage of REQ/REP socket is that it implements state machine to
manage requests/replies and sending request when socket is in
"waiting for reply" state causes an exception. So it ideally matches
CALL requirements which should block awaiting reply.

But this is bad for CAST. Here we can substitute REQ with DEALER which is
async equivalent for REQ. We do not need to wait for reply when we use DEALER,
but we still can receive replies. We even do not need to ignore them, but
use as acknowledge signal that CAST message is delivered successfully.
We also have a possibility to track unacknowledged messages and report
about them if needed. So on this step we can see that reliability of REQ/REP
is higher than with PUSH/PULL. There is some magic needed with REQ envelope
when work with DEALER, but that is not a problem and it is clearly described
in zmq-guide.

So a chain for CAST will look like the following:

rpc_client (DEALER) <=> (ROUTER) zmq_receiver (DEALER) <=> (REP) rpc_server

DEALER is also suits perfectly for CAST with fanout. Message chain remains
the same. And also the same for notifier.

The rule is simple: if we need to block waiting for request then we use REQ,
otherwise DEALER for sending asynchronous requests. ROUTER is an async
substitution for REP.


As we are talking about a new driver implementation it's worth mention that
matchmaking for fanout topics, message formats, proxy daemon will stay,
but refactored. We are going to address such proposals like [1], [2], [3], [4].
[5] Should also be applied here, but as an optimisation, after implementation
is done.

Configuration options and messaging API should not change, so we could have
possibility to easily use new driver instead of current driver on devstack
(and any other deployment).


Alternatives
------------

It is also possible to substitute the pattern inside the current implementation.


Impact on Existing APIs
-----------------------

None.

Security impact
---------------

None.

Performance Impact
------------------

Number of connections will be reduced so it may increase performance.

Configuration Impact
--------------------

None.

Developer Impact
----------------

Less code for supporting replies.

Testing Impact
--------------

Existing functional tests should cover this change.


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

- Implement CALL pipeline and surrounding modules
    - package hierarchy according to [1]
    - move message serialization, topics manipulations etc.
      from existing implementation to appropriate modules
    - rpc_client part
    - broker_part
    - rpc_server part
    - replies handling
- Implement CAST
- Implement fanout
- Implement notifier

Incubation
==========

None.

Adoption
--------

None.

Library
-------

oslo.messaging.

Anticipated API Stabilization
-----------------------------

None.

Documentation Impact
====================

None.

Dependencies
============

None.

References
==========

1. https://blueprints.launchpad.net/oslo.messaging/+spec/zmq-driver-folder

2. https://blueprints.launchpad.net/oslo.messaging/+spec/zmq-context-per-driver-instance

3. https://blueprints.launchpad.net/oslo.messaging/+spec/zmq-work-without-eventlet

4. https://blueprints.launchpad.net/oslo.messaging/+spec/zmq-topic-object

5. https://blueprints.launchpad.net/oslo.messaging/+spec/zmq-socket-reuse

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
