=============
http driver
=============

This is a proposal to create a new driver implementation which communicates
RPC client and server directly over HTTP without messaging queue.

Problem description
===================

In oslo.messaging, RabbitMQ driver is widely used and validated that
the driver works very stably on most of OpenStack environment.
However, in PUB/SUB model using message queue, message queue itself
might be a single point of failure and also message queue is bit
difficult to support large scale of client and server communications.

For example, if there are more than 10,000 hypervisors which host
nova-compute and neutron-agent, each RabbitMQ node must always support
large number (ex. more than 40,000) of network connections from nova
and neutron clients. In this situation, if RabbitMQ cluster restart
happens, large number of RPC clients started to connect RabbitMQ nodes
simultaneously, this makes RabbitMQ nodes unstable.

Also due to large number of hypervisors, RabbitMQ must support huge
number of message queues to allow to communicate neutron-server and
neutron-agent, for example. All queue data must be synchronized between
all RabbitMQ nodes, so having large number of queue also makes RabbitMQ
cluster unstable.

Note, this is not a proposal to deny RabbitMQ (PUB/SUB model) backend.
The proposal should be aware both PUB/SUB model and REQ/RESP model have
different advantages described in the following section.

PUB/SUB advantage examples
--------------------------

- Simple architecture in a small cluster
- Easy ACL configuration in a secure cluster

REQ/RESP advantage examples
---------------------------

- Fault tolerant against control plane (consul) down
- Easy to scale out the cluster

As mentioned in above, the PUB/SUB model has simple and easy to use
most of the cases, but for large scale OpenStack environment, REQ/RESP
model for all RPC communications could be more proper and reliable.

This specification proposes to implement OpenAPI based REQ/RESP model
driver called ``http driver`` which enable to communicates between RPC
client to RPC server directly without a component which is single point
of failure for OpenStack internal communication.

Proposed change
===============

This is overview diagram of HTTP driver for RPC Call/Cast/Cast Fanout requests.
There are 4 main components to realize the driver.

* RPC client
* RPC server
* Endpoint datastore (ex. Consul)
* Broadcaster

.. code-block:: none

               +--------------+
       +------>|   Consul     |<------------------+
       |       +--------------+                   |
       |                                     +-------------+
       |                                +--->|  RPC server |
       |                                |    +-------------+
 +-------------+   Call/Cast RPC        |    +-------------+
 | RPC client  +---------------------------> |  RPC server |
 +-------------+                        |    +-------------+
       |                                |    +-------------+
       | Cast Fanout                    +--->|  RPC server |
       |                                |    +-------------+
       |       +--------------+         |
       +------>| Broadcaster  |---------+
               +--------------+
            Send Cast to all RPC servers


.. note:: Scope of the proposal

          - The scope of this proposal covers Call/Cast/Cast Fanout RPC cases
          - Notification is out of scope in this proposal

Main points to be improved by the architecture
----------------------------------------------
* Separate control plane from data plane
* Allow direct API call without single point of failure
* Reduce RPC communication between multiple availability zones

Responsibility of each components like followings.

RPC Client
^^^^^^^^^^
Fetch the RPC server list from the consul cluster for
an RPC target service.
Pick up appropriate RPC server for the RPC, then send a RPC request
over HTTP protocol.

RPC Server
^^^^^^^^^^
Listen and handle an in-coming rpc request over HTTP protocol

When the RPC server starts, the server registers its RPC server
information to Consul cluster as Consul's "service".
Also the PRC Server works as ``Push Style``, not poll style.

For RPC client/server communication over HTTP with RESTful API, OpenAPI
allows us to define formatted RESTful API definition easily. Once API
definition is generated, it can be launched as http server using
Web framework and WSGI server. For example, they are candidate for Web
framework and WSGI server to enable HTTP client and server.

* Web famework: `connexion <https://connexion.readthedocs.io/en/latest/>`_
* WSGI server: eventlet

Endpoint datastore
^^^^^^^^^^^^^^^^^^
Store the RPC server information.

The server information includes following items.
oslo.messaging layer information(exchange, topic and server)
RPC server information (IP address, port and etc).

In this spec, `Consul <https://developer.hashicorp.com/consul/api-docs>`_
is one example imeplementation for the endpoint datastore.

For other use-case, the service discovery feature code with backend
selectable implementation should be added for users who would like
to avoid introducing new dependency for datastore.

HTTP Broadcaster
^^^^^^^^^^^^^^^^
An amplifier for an HTTP request

HTTP protocol doesn't have broadcast mechanism though the oslo
RPC has Cast Fanout RPC.
The Broadcaster sends an in-coming RPC to all target RPC servers.

Sample RPC communication flow for Nova
--------------------------------------
.. code-block:: none

               +--------------+
       +------>|   Consul     |
       |       +--------------+
       |
       |             * Call RPC
 +----------------+  (1) select_destinations    +----------------+
 | nova-conductor +---------------------------> | nova-scheduler |
 |                +------+                      +----------------+
 +----------------+      | * Cast RPC
                         | (2) build_and_run_instance
                         |                      +----------------+
                         +--------------------->|  nova-compute  |
                                                +----------------+

In this figure, nova-conductor on left side is RPC client and each
nova-scheduler and nova-compute on right side are RPC servers.

select_destinations() Call RPC
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
During instance creation, in order to choose target nova-compute
node to launch new instance, nova-conductor make a Call RPC request
select_destinations() to nova-scheduler.
In this case, Call RPC communication works with following steps.

#. A nova-conductor fetches nova-scheduler's hostn and port
   port information from Consul, and pick one of Call RPC
   target randomly
#. A nova-conductor makes a select_destinations() Call RPC and
   wait a response.

build_and_run_instance() Cast RPC
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
During instance creation, once target nova-compute is choosen by
scheduler, nova-conductor sends instance creation request to
target nova-compute using build_and_run_instance() Cast RPC.
In this case, Cast RPC communication works with following steps.

#. A nova-conductor fetches a target nova-compute's host and
   port information from Consul
#. A nova-conductor makes a build_and_run_instance() Cast RPC and
   return immediately without waiting actual instance creation


Sample RPC server information registered in Consul
--------------------------------------------------
Nova's RPC server information
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This figure shows Nova's RPC server information registered into `nova` AZ.
Nova has nova.scheduler, nova-conductor, nova-compute and nova-consoleauth
as RPC server.

.. image:: ../../../../images/http-driver/consul-service-list.png
   :width: 850px
   :align: left

nova-condutor RPC server list
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This figure shows nova-conductor RPC server list on `nova` AZ.
Each nova-conductor has <service name>:<port number> and also
<IP address>:<port number> identifier. RPC client access to
RPC server via the <IP address>:<port number>.

.. image:: ../../../../images/http-driver/conductor-service-list.png
   :width: 850px
   :align: left

Health check status of one of nova-condutor RPC server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Consul has health check mechanism for registered HTTP endpoint.
The figure shows one of nova-conductor RPC server respond 200 OK
to Consul's periodical health check. If the endpoint is healthy,
the endpoint marked as green check.

.. image:: ../../../../images/http-driver/conductor-health-check.png
   :width: 850px
   :align: left

Multi-AZ support
^^^^^^^^^^^^^^^^
Consul has a feature to federate multiple Consul cluster into one to
support multiple datacenter case. In the figure, there are multiple
nova AZ such as `nova`, `az-1`, `az-2` and `az-3`, then each nova AZ
has one Consul cluster. These 4 Consule clusters are manged as one
cluster using Consul federation.

.. image:: ../../../../images/http-driver/consul-federation.png
   :width: 850px
   :align: left

Alternatives
============

Datastore for host/topic management
-----------------------------------

In above architecture, Consul is chosen because it supports healthcheck
mechanism and multi DC federation so that these features enable user to
monitor RPC server status easily, and scale out easily to support large
scale OpenStack.

But alternatively, managing service endpoint using Keystone service
catalog, DNS or registering data into Redis cluster similar to ZeroMQ
are another choices.

Once the endpoint datastore supports selectable mechanism, these
alternative datasotre plugin can be developped based on use-cases.

Cast Fanout support design
--------------------------

In above diagram, broadcaster process is splitted out as one another
service from RPC client. The Cast Fanout could be implemented into
RPC client, but it takes much CPU and memory if number of targets are
quite huge. Instead, by splitting out the broadcaster, the user easily
scale out number of broadcaster processes based on number targets on
OpenStack cluster.

API framework
-------------

For API schema definition, any approaches are available.
For example, there are REST, OpenAPI, json-rpc, gRPC or any http
protocol implementation are available if it allow to integrated with
eventlet which is used by oslo.service.
In above diagram, OpenAPI is chosen in order to realize HTTP protocol
client-server model.


Advanced feature
================

Multi Availability zones support
--------------------------------
* Consul provides Federation mechanism between multiple Consul clusters.
* By using the Federation, Consul cluster can be splitted per OpenStack
  Availability zones.
* Splitting Consul to multiple cluster reduces workload of Consul and makes
  the cluster stable.
* Also in basic, RPC client and server communication happen in one Availability
  zone. This reduces network communication between multiple AZ.

.. code-block:: none

 Availability Zone-A                Availability Zone-B
 +----------------+                 +----------------+
 |                |   RPC Request   |                |
 |   RPC server   |        +------->+   RPC server   |
 |       |        |        |        |       |        |
 |       |        |        |        |       |        |
 |   RPC client   +--------+        |   RPC client   |
 |       |        |                 |       |        |
 |       |        |   Federation    |       |        |
 | Consul Cluster +<--------------->+ Consul Cluster |
 |                |                 |                |
 +----------------+                 +----------------+



Impact on Existing APIs
-----------------------

None.

Security impact
---------------

* OpenAPI supports SSL based communication between client and server.
  This enables secure RPC communication same as other messaging drivers.

Performance Impact
------------------

Performance should become better because RPC client communicates to
RPC server directly over HTTP.

Configuration Impact
--------------------

New config options to configure http server are needed.
Here is sample config parameters which is defined in oslo.messaging
library user configuration file like nova.conf, neutron.conf.

.. code-block:: ini

  [oslo_messaging_http]
  port_range=20000:20100

  [consul]
  port = 8500
  host = <Consul hostname>
  token = <Consul token>
  check_timeout = 60s
  check_deregister = 30m

  [http_driver]
  http_token = <Token to access OpenAPI server>
  http_api_config_file = <OpenAPI definition>
  enable_ssl = True
  ssl_certfile = <Path for SSL Cert file>
  ssl_keyfile =  <Path for SSL Key file>
  listen_timeout = 60


Detailed design for port_range
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
For port_range, following spec could reduce complexity of this option.

#. If the port_range is not defined, unused ephemeral port is chosen randomly.
   For most of use cases, this satisfies the requirement.
#. If the port_range is defined, RPC server pick port from the specified range
   during service launch.

Here is the reason why multiple ports are required for RPC server.
For example, Nova has "conductor.workers" config parameter and Neutron-server
has "rpc_workers" config parameter. By specifying more than "1" for these configs,
multiple RPC workers are launched on single host. Therefore, from RPC client-server
communication perspective, each RPC worker must have individual destination port
number to launch it on a host.

And purpose of port_range is to support secure cloud environment which strictly
manages network communication using dest/source port at firewall, it would be better
that default behavior is random choice from unused ephemeral port.

Developer Impact
----------------

If other OpenStack component use http rpc_backend, ``oslo_messaging_http``,
``consul`` and ``http_driver`` configuration section must be defined based
on Consul and OpenAPI configuration.

Testing Impact
--------------

Basic unit test and integration test (using DevStack) will be implemented.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Mitsuhiro Tanino (mitsuhiro-tanino)
Other contributors:
  Xiang Wang

  Yushiro Furukawa (y-furukawa-2)

  Masahito Muroi (masahito-muroi)

Milestones
----------

None

Work Items
----------

- Propose driver and test codes
- Release note and docs

Documentation Impact
====================

The http driver documentation will be added to the library.
This documentation will follow the style of documentation provided by the
other drivers and should include the following topics:

* Overview of http driver architecture
* pre-requisites
* driver options overview
* Consul configuration
* HTTP broadcaster configuration


Dependencies
============

None

References
==========

None

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
