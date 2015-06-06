=============================================================
 Adding Kafka Driver for Notification Usage in oslo_messaging
=============================================================

https://blueprints.launchpad.net/oslo.messaging/+spec/adding-kafka-support

Apache Kafka is messaging broker which enables to establish nice log-centric communication bus in OpenStack.

Problem description
===================

Some OpenStack services like Ceilometer and Monasca have the collaboration part with
Apache Kafka, distributed messaging system, to publish and subscribe logs and metrics
data. Since Kafka is well-designed log-centric messaging broker, it will be expected
to appear the new Kafka related implementation in existing or future OpenStack projects.
This blueprint aims to implement kafka driver in oslo_messaging, which enable us to
reduce the wasting time to re-implement the same functionality, and since Kafka would
have multiple clients from separate projects, to use the same client to communicate
with Kafka will make the reduce of the implementation-dependent bugs and errors.

Proposed change
===============

To reduce the cost of independently implementing kafka communication functionality,
let's support for the kafka driver in oslo_messaging. Kafka driver enables us to publish
and subscribe messages similar to the other oslo_messaging drivers, but will not
support for the RPC methods since Kafka is not expected to be used as a RPC broker.
In the future, if there are some needs for Kafka RPC, it will be a new proposal.

Alternatives
------------

There are several messaging brokers currently not supported by oslo_messaging, for
example NATS, NSQ and etc. However, Kafka have already been used more than one OpenStack
projects, and also since Kafka is developed for handling high load logs, Kafka have
several features which are better for logging data. For example, Kafka queue retains the
messages for configured period of time. This means that when consumers of the queue lost
messages after subscribing, they can replay the same message. Also additional kafka brokers
and consumers are easily joined, because horizontal scaling of kafka is supported by
Zookeeper. Moreover, kafka can send the bunch of messages together, this can contribute
the performance and flexibility of messaging.

Impact on Existing APIs
-----------------------

None

Security impact
---------------

Current security support of Kafka are under implementation. Authentication of clients
and encrypting connections would be coming. More information can be found in the references.

Performance Impact
------------------

There would be no impact unless the kafka is selected for use.
The overall performance will depend on the server component which the broker
is setted up. The paper related to Kafka says that producers can publish about
50,000 messages/sec on the condition that message size is 200 byte and messages
are sent one by one. However, this number is affected by parameters such as
message size, the number of replication, batch size (kafka can send multiple
messages together), and environments. Roughly, RabbitMQ can publish about 10,000
messages/sec, it means kafka might not be the bottleneck of performance.

Configuration Impact
--------------------

None

Developer Impact
----------------

None

Testing Impact
--------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  <kshimamu>

Other contributors:
  <yudupi>

  <dedutta>

Milestones
----------

Target Milestone for completion:
  liberty

Work Items
----------

* Integration test environment for Kafka driver
  - Add the codes for integration test to OpenStack infrastructure

* Making Kafka driver for oslo_messaging
  - Provide the communication path with Kafka

* Documentation for Kafka driver
  - Change OpenStack developer documentation

Incubation
==========

None

Adoption
--------

Currently Ceilometer and Monasca are using Kafka service. Ceilomter project have
Kafka publisher as a metrics publisher, and Monasca project is using kafka as
a part of their architecture. For more detail, see the References chapter.

Library
-------

oslo_messaging

Anticipated API Stabilization
-----------------------------

None

Documentation Impact
====================

OpenStack developer documentation for oslo_messaging library will have the
description for the behaviors and how to select kafka driver plugin.

Dependencies
============

Kafka python package

* https://pypi.python.org/pypi/kafka-python

References
==========

Apache Kafka Project

* http://kafka.apache.org/

Kafka: a Distributed Messaging System for Log Processing

* http://research.microsoft.com/en-us/um/people/srikanth/netdb11/netdb11papers/netdb11-final12.pdf

Kafka Security

* https://cwiki.apache.org/confluence/display/KAFKA/Security

KAFKA 0.8 PRODUCER PERFORMANCE

* http://blog.liveramp.com/2013/04/08/kafka-0-8-producer-performance-2/

Performance of Kafka

* http://kafka.apache.org/07/performance.html

RabbitMQ Performance Benchmarks

* http://blogs.vmware.com/vfabric/2013/04/how-fast-is-a-rabbit-basic-rabbitmq-performance-benchmarks.html

Comparison of Messaging Queues

* http://www.bravenewgeek.com/dissecting-message-queues/


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
