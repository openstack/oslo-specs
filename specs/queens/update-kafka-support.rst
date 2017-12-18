====================================================
 Kafka Driver Revisions for Messaging Notifications
====================================================

https://blueprints.launchpad.net/oslo.messaging/+spec/update-kafka-support

This specification proposes changes to the existing kafka driver
that allows notification message transport over the Apache Kafka
distributed streaming platform [1]_. The blueprint for the original
driver implementation can be found here [2]_ and the spec for the
implementation can be found here [3]_. The goal of the changes
described by this specification is to transition the driver from
'experimental' to 'supported' status in order to encourage driver
adoption. The driver will (continue to) only support notification
messaging as the use of the kafka server is non-optimal for RPC
messaging patterns. Thus, this kafka driver is intended for deployment
in hybrid messaging configurations where RPC messaging will be
provided by a separate messaging backend.

Problem description
===================

The original kafka driver was introduced during the mitaka release
cycle. Adoption of the driver has been limited due to a number of
factors such as its 'experimental' designation and its intended use
for notification messaging only. Meanwhile, the kafka server has experienced
widespread adoption and is frequently included in application
architectures to provide accurate analytics in cloud monitoring
systems. This success and the progression of configuration frameworks
to easily enable hybrid messaging deployments in OpenStack is a
catalyst to revise this driver and provide active maintenance and
support going forward.

Kafka hybrid oslo.messaging deployment::

     +------------+          +----------+
     | RPC Caller |          | Notifier |
     +-----+------+          +----+-----+
           |                      |
           |                      |
           v                      v
  +-------------------+  +-------------------+
  |       RPC         |  |    Notification   |
  | Messaging Backend |  | Messaging Backend |
  |   (amqp:// or     |  |    (kafka://)     |
  |    rabbit://)     |  |                   |
  +--------+----------+  +--------+----------+
           |                      |
           |                      |
           v                      v
     +------------+        +------+-------+
     |    RPC     |        | Notification |
     |   Server   |        |    Server    |
     +------------+        +--------------+


Proposed change
===============

The revision to the kafka driver is not a major rework. A number of
issues need to be resolved in order to support Notifications over a
kafka server messaging backend:

* release updates
* virtual host (vhost) emulation
* encryption and authentication
* driver aspects
* documentation
* functional and integration testing

Release Updates
---------------

The driver should be updated to support the latest kakfa server
software release. As of this writing, the latest versions are:

* scala version - 2.12
* kafka version - 1.0.0
* kafka-python version - 1.35

Virtual Hosts (vhost) Emulation
-------------------------------

Currently, only the rabbitmq messaging backend supports vhosts
contained in the transport url [4]_. Since the kafka server
architecture does not natively support vhosts, the kafka driver
revision will emulate vhost support by adding the virtual host name to
the topic created on the kafka server. This will effectively
create a private topic per virtual host that is configured for use.

Related to this change the devstack kafka plugin will
need to be updated so that the kafka backend does not fail.

Encryption and Authentication
-----------------------------

The Apache Kafka allows clients to connect over SSL. By default, SSL
is disabled and the kafka driver will be updated to enable it via
configuration. This release will support server authentication and
client authentication will be planned for a future release and will
be dependent upon client library capabilties. The configuration for
SSL will be the same for both producer and consumer:

In section [oslo_messaging_kafka]:

* ssl - attempt to connect via ssl
* ssl_ca_file - file containing the trusted CA's digital certificate

SASL may be used with PLAINTEXT or SSL as the transport layer when
there is a username and password present in the transport_url.  The
SASL configuration support is currently for PLAIN authentication
only. The following configuration options will be provided by the driver:

In section [oslo_messaging_kafka]:

* sasl_mechanisms - space separated list of acceptable SASL mechanisms

Driver Aspects
--------------

The revision to the kafka driver will include updates to a number of
driver functional aspects to incorporate new features and to enhance
driver support-ability:

* config options - update the driver configuration options to include
  new security options as well as remove deprecated options removed
  from the oslo messaging library [5]_.
* logging - add additional info, warning, debug messages to the driver
  to help operational and debugging tasks when deploying the driver
* check python client - check for installed library dependencies
* connection management - review and identify any simplification that
  would benefit driver operation and support
* ack/requeue message - investigate support of manual message commit
  in order to support message requeue following notify message dispatch

Alternatives
------------

Presently, there are alternative oslo messaging drivers that can be used
for different messaging backends. With hybrid messaging support, there
is the flexibility to optimally align the messaging backend with the
RPC or Notification communication patterns provided by the oslo
messaging library. The objective to support and maintain the kafka
driver should enhance the overall value of oslo messaging by providing
users messaging backend alternatives that best suit their operational
objectives and needs.

The alternative is to deprecate this driver and support a single
messaging backend for notifications (e.g. rabbit broker).

Impact on Existing APIs
-----------------------

The existing API should not require any changes. The changes to the
kafka driver will preserve compatibility with existing experimental
kafka deployments and will not affect other oslo.messaging drivers.

Security impact
---------------

With the additional support of authentication and encryption, there will
be an expansion of the security model provided by the driver through
its use of the python client library and its interactions with the
kafka server for message exchange.

Performance Impact
------------------

Any performance impact should be limited to the users of the kafka
driver for messaging notifications. Users of other drivers such as
rabbitmq and amqp 1.0 will not be affected. Any performance changes
realized in the kafka driver update may be due to:

* changes to the underlying kafka protocol in the new server version

Configuration Impact
--------------------

New configuration items for authentication and security will be added
as detailed above. The default value for these options will be
determined as the driver is updated and revised.

Developer Impact
----------------

To be considered as supported, any new features added to
oslo.messaging that must be implemented via driver modification should
be implemented in the kafka driver as well. In the circumstance when a
new feature requires behaviors/capabilities that cannot be provided by
kafka, clients attempting to use the feature will cause a
NotImplementedError excpetion to be raised. Additionally, the absence
of supported functionality must be documented and included in the
release notes.

Testing Impact
--------------

The kafka server will be used as the messaging backend for
notifications in testing. An alternative backend such as rabbit or
amqp 1.0 should be used as the messaging backend for RPC.

The kafka driver tests should be expanded as necessary for the new
features and capabilities in the update and the driver must pass all tests.

The driver must pass the following gate checks with deployed in a
hybrid messaging configuration (e.g. when kafka is configured as the
notification backend):

* oslo.messaging-tox-py27-func-kafka
* oslo.messaging-tox-py35-func-kafka
* oslo.messaging-src-dsvm-full
* oslo.messaging-telemetry-dsvm-integration
* oslo.messaging-tempest-neutron-dsvm-src

The zookeeper, kafka, jdk and client will need to be avabilable in the
CI environment in order to fully test this driver.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  ansmith@redhat.com  (ansmith on IRC)

Other contributors:
  kgiusti@gmail.com  (kgiusti on IRC)

Milestones
----------

Target Milestone for completion: queens

Work Items
----------

* Update environment for latest software release updates and dependencies
* Implement virtual hosts support
* Implement SSL and SASL integration
* Implement new configuration items
* Update documentation
* Functional test integration
* Update devstack plugin
* Upstream CI integration
* Send announcement to openstack-dev and openstack-operators following
  release

Incubation
==========

None.

Adoption
--------

The kafka driver is expected to be adopted in hybrid messaging deployments
as the notification messaging backend. Adoption is likely in environments
that already have kafka servers broadly deployed (e.g. operational
benefit) or where the characteristics of the kafka server best suit
the information analytics requirements.

Library
-------

oslo.messaging

Anticipated API Stabilization
-----------------------------

None

Documentation Impact
====================

The kafka driver documentation will be added to the libary. This
documentation will follow the style of documentation provided by the
other drivers and should include the following topics:

* theory of operation (overview) of the Apache Kafka messaging backend
* pre-requisites
* driver options overview
* kafka server operations
* devstack support
* platforms and software

Dependencies
============

The driver revision will require no additional dependencies.

References
==========

.. [1] https://kafka.apache.org/
.. [2] https://blueprints.launchpad.net/oslo.messaging/+spec/adding-kafka-support
.. [3] https://review.openstack.org/#/c/189003/6/specs/liberty/adding-kafka-support.rst
.. [4] https://bugs.launchpad.net/oslo.messaging/+bug/1706987
.. [5] https://etherpad.openstack.org/p/oslo-queens-tasks

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

