========================================
New RabbitMQ Pika driver implementation
========================================

https://blueprints.launchpad.net/oslo.messaging/+spec/rabbit-pika

This specification proposes a new RabbitMQ Pika driver implementation.

Problem description
===================

Current RabbitMQ oslo.messaging driver uses Kombu client library.
But new features support and bugfixes appear in Kombu more slower then in Pika.
Now we have problems with RabbitMQ stable work in HA mode. And when we asked
RabbitQM developers for help with bugfixing they said that it is possible but
first of all, please update your environment to recommended library stack.
It is main reason of developing this driver.

Also Pika supports modern RabbitMQ features, like direct reply and heartbeats.
I guess It is preferred way to use this functionality instead developing it
ourselves.

Proposed change
===============

In this specification I propose to create fully new driver which:

#. should be developed in optimal way regarding to all Pika client
   library new features and best practices;
#. should be fully compatible with current driver interface;
#. may change internals and does not guarantee compatibility with
   Kombu driver (means you can not use old Kombu driver for some set
   of services and new Pika driver for another services)
#. support only current actual features without any deprecated features.

Features and it's design
------------------------

During oslo.messaging driver investigation I seperated a few main
supported features:

#. RPC - unreliable fast sending of the message to single remote server
   defined using target and getting reply.
   It has small timeout (a couple of seconds) therefore this
   message should be recieved by server and processed in real time
   (defined by timeout) or be skipped otherwise.
#. CAST - unrelieble sending of the message to set of remote servers
   defined by target. This message should be recieved by server in real time
   (defined by timeout) or be skipped otherwise. If somehow service
   does not listen the topic or some connectivity problem occurs
   and we can not recover it fast - this server will never get the message.
#. NOTIFY - reliable version of CAST - we can not loose the messages.
   if you send notification and send_notification method returns without any
   error - message should be stored and wait until remote server gets started
   and gets conectivity to our RabbitMQ brocker.

Eventlet compatibility
----------------------

Pika has a few connection adapters For working with different frameworks.
It does not have special adapter for eventlet. But It is possible to use
'BlockingConnection' adapter and eventlet monkey patching. It works pretty
well. Only one problem I found - it tries to use 'select.epull' API which is
not patched by current eventlet implementation. So I added code which removes
'pull' and 'epull' attributes from 'select' module if eventlet is patched.
In this case Pika uses standard select api which is patched by eventlet
correctly.

Heartbeats
----------

Pika has it's own heartbeats mechanism. 'BlockingConnection' adapter has
method 'process_data_events' which listen in loop response from RabbitMQ.
It should be executed after sending request or when consumers are registered.
This method run loop:

(code snippet from https://github.com/pika/pika/blob/master/pika/adapters/blocking_connection.py#L410)
::

 while not is_done():
     self._impl.ioloop.poll()
     self._impl.ioloop.process_timeouts()

which sends heartbeats (inside process_timeout_method) according to configured
heartbeat_timeout. So we have heartbeats working for all listeners with defined
interval. For connections used for message publishing heartbeats will be sent
only when connection is active - when you are executing publish method.


Alternatives
------------

#. Use old driver;
#. Not develop fully new driver, try to just replace client library
   and keep logic of current driver

Impact on Existing APIs
-----------------------

None.

Security impact
---------------

None

Performance Impact
------------------

Performance should become better because of more optimal implementation.


Configuration Impact
--------------------

Configuration options should be added to setup Pika client library.

The next configuration possibilities are suggested:

Connection options (represents Pika functionality):
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* 'channel_max' (default - 0) - Maximum number of channels to allow,
* 'frame_max' (default - 131072) - The maximum byte size for an AMQP frame,
* 'heartbeat_interval' (default - 0) - How often to send heartbeats,
* 'ssl' (default - False) - Enable SSL or not,
* 'ssl_options' (default - None) - SSL options if ssl is enabled,
* 'socket_timeout' (default - 0.25) - Socket timeout for Pika connections,

Connection pool options:
^^^^^^^^^^^^^^^^^^^^^^^^

* 'pool_max_size' (default - 10) - Maximum number of connections to keep
  queued,
* 'pool_max_overflow' (default - 10) - Maximum number of connections to create
  above
* 'pool_timeout' (default - 30) - Number of seconds to wait for available
  connection,
* 'pool_recycle' (default - None) - Lifetime of a connection (since creation)
  in seconds or None for no recycling. Expired connections are closed on
  acquire,
* 'pool_stale' (default - None) - Threshold at which inactive (since release)
  connections are considered stale in seconds or None for no staleness. Stale
  connections are closed on acquire

Reconnection policy options:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* 'connection_retry_attempts' (default - 3) - Reconnecting retry count in case
  of connectivity problem,
* 'connection_retry_delay' (default - 0.1) - Reconnecting retry delay in case
  of connectivity problem,
* 'rejected_message_retry_attempts' (default - 3) - Resend rejected messages
  retry count,
* 'rejected_message_retry_delay' (default - 0.1) - Resend rejected messages
  retry delay

RPC options:
^^^^^^^^^^^^

* 'rpc_queue_expiration' (default - 60) - Time to live for rpc queues without
  consumers in seconds,
* 'default_rpc_exchange' (default - "openstack_rpc") - Exchange name for sending
  RPC messages,
* 'rpc_reply_exchange' (default - "openstack_rpc_reply") - Exchange name for
  receiving RPC replies.

Notification options:
^^^^^^^^^^^^^^^^^^^^^
* 'notification_persistence' (default - False) - Persist notification messages,
* 'default_notification_exchange' (default - "openstack_notification") -
  Exchange name for for sending notifications.


Developer Impact
----------------

Devstack should be adapted to be able to setup gate test environment with
new driver.


Testing Impact
--------------

Functional tests should be adapted (without changing test logic).

Implementation
==============

Assignee(s)
-----------
dukhlov, yosh-m

Primary assignee:
    dukhlov


Milestones
----------

Target Milestone for completion: mitaka

Work Items
----------

* Design and implement rpc functionality (send and listen driver methods)
  based on Pika library functionality
* Design and implement notify functionality (send_notification and
  listen_notifications driver methods)
  based on Pika library functionality
* Adapt functional tests
* Adapt devstack to be able to setup environment with new Pika driver


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

The new driver should successfully run with adapted devstack.
Adapted oslo.messaging functional tests should successfully pass in
devstack-gate.


Documentation Impact
====================

Detailed doc strings should be written

Dependencies
============

pika library

References
==========

.. [1] https://github.com/dukhlov/oslo.messaging/blob/master/oslo_messaging/_drivers/impl_pika.py
.. [2] https://review.openstack.org/#/c/226348/

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

