=================================
Proposed new library oslo.metrics
=================================

This is a proposal to create a new library to collect metrics of oslo libraries.

Proposed library mission
=========================

The mission of oslo.metrics is exposing internal metrics infomation of oslo
libraries. OpenStack processes create a connection to other middleware using
oslo library, e.g. oslo.messaging to connect another OpenStack process and
oslo.db to connect DB. The oslo.messaging creates its own RPC protocol over the
connection to RabbitMQ, which is a default messaging middleware in OpenStack
project. The usage of RabbitMQ can be monitored by RabbitMQ management tool,
but the usage of oslo.messaging's RPC can't be monitored. Enabling OpenStack
admin and operator to monitor usage of oslo libraries is the goal of
oslo.metrics.

The oslo.metrics supports metrics of the oslo.messaging's RPC as first goal.
The metrics infomation of the RPC doesn't appear anywhere. For example, when
a user calls the Create New Instance API to Nova, there is no infomation about
how many RPC calls are made, which RPC targets are used, and etc. And for another
case, if operator adds 10 compute nodes to their OpenStack cluster, how may RPC
will be increased, and etc.

Consuming projects
==================

There are two type of cosumers. One is the OpenStack services, which use
oslo.messaging as its internal communication. Another is Monitoring systems,
which consume the metcis exposed by the oslo.metrics.

Alternatives library
====================

If oslo.messaging exposes its metrics, the notification feature of
oslo.messaging can be a one of alternatives. However, the notification is
also implemented over the RabbitMQ. It makes cross reference in the metrics
so it's not good idea to do.

The rpc_monitor is also another alternatives. This library focuses on
collecting oslo.messaging metrics, and exposes its metrics to Prometheus.
The rpc_monitor has not been developed long time. And the oslo.metrics will
support multi type of monioring system as an official library. So it's difficult
to use the rpc_monitor itself. However, the goal of rpc_monitor is similar to
the oslo.metrics's first goal. When implementing the oslo.metrics the Prometheus
support, it's better to consult the rpc_monitor's implementation.

Proposed adoption model/plan
============================

The basic architecture is the oslo.metrics works as metrics data serializer
for outside system.
The existing oslo libraries send original metrics information through
a unix socket, then the oslo.metrics gathers the metrics information
and exposes the data.

The oslo.metrics listens to unix sockets to recieve metrics data from
each of the OpenStack processes. The reason oslo.metrics uses the socket
is to collect messaging metrics information from multiple processes which
runs on the same node. One metrics process represents one node or one
OpenStack project.

The consumer of oslo.metrics, e.g. oslo.messaging, needs to send its metrics
information to the unix socket. The olso.messaging sends its metric data to
the socket as well as the actual RPC request to another oslo.messaging server.
The metrics data sending feature is configured by a new flag in oslo.messaging
library.

If we have a control server, then both Neutron-Server and Nova-API running
in the controller would share their metrics to one unix socket which can
get data from other Openstack processes as well. The Unix Socket running
in one Node would handle all openstack processes of that node

The oslo.messaging sends the RPC information one by one to oslo.metrics
with oslo.metrics's format. All information sent by oslo.messaging are
put together into one metrics data in oslo.metrics. Then oslo.metrics
exposes the one data to any monitoring system.

The monitoring system is really depending on operator. So oslo.metrics
exposes the data by common format. For example, Prometheus takes PULL
approach to get a metrics. To support Prometheus, oslo.metrics exposes
the metrics data over HTTP.

The data oslo.messaging sends to the oslo.metrics includes:

* topic
* namespace
* version
* server
* fanout
* timeout
* type of call: call or cast
* timestamp of the call

Hostname are added by oslo.metrics side.

.. code-block:: none

 +--------------+        +--------------+     +-------------+
 |              |        |              |     | any         |
 |oslo.messaging+--------> oslo.metrics <-----> monitoring  |
 |              |        |              |     | system      |
 +--------------+        +--------------+     +-------------+
                unix socket

Security Concerns
=================

The metrics information exposed by the oslo.metrics may have the sensitive
information, which should be isolated from normal user. The oslo.metrics is
an admin tool and it's expected to work inside of isolated internal network.
The isolated network usually has another security protection from normal user's
access. Because of that security protection this sensitive information is not
exposed to a normal user or end user of cloud.

Reviewer activity
=================

For the changes in oslo.messaging, the support from oslo.messaging core is needed.
For the oslo.metrics, the member of Large Scale SIG could review the patches.

Perfomance Impact
=================

The oslo.metrics requests oslo.messaing to send another information. This may
cause a perfomance impact to the RPC request. After implementing first spec,
this library should be tested how much the additional informaion sending cause
perfomance impact.

Implementation
==============

Author(s)
---------

Primary authors:
  Masahito Muroi (masahito-muroi)
Other contributors:
  <launchpad-id or None>

Work Items
----------

* Create a new library named oslo.metrics
  * The implementation includes unit tests and functional tests as well as its codes
* Change oslo.messaging to support metrics sending
* Investigation of perfomance impact of oslo.messaging RPC

References
==========

* Discussion in Large-Scale SIG:  https://etherpad.openstack.org/p/large-scale-sig-cluster-scaling
* Mirantis rpc_monitor: https://github.com/Mirantis/rpc_monitor

Revision History
================

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Ussuri
     - Introduced

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

