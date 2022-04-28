=========================
local notification driver
=========================

https://blueprints.launchpad.net/oslo.messaging/+spec/unix-socket-oslo-messaging-notifications-driver

Exporting oslo notifications via a local Unix socket.

Problem description
===================

Today, if you have two daemons/agents on the same host and one wants
to consume notifications from the other there is no practical driver
that can be used which does not require non-local networking,
complex setup or misuse of multiple feature to emulate a local notification
driver.

As an operator, I would like to be able to locally consume notifications
with minimal configuration, overhead, or maintenance.

Proposed change
===============

To address this gap this spec proposes adding a minimal Unix socket driver
which will relay all notification to any subscriber to the socket.

To keep resource utilization and complexity to a minimum the Unix-socket driver
will not queue notification if there are no clients and will instead drop all
notifications

Multiple client can either be supported by using multiple instance of the
driver or multiplexing over a single socket.

As with the log driver the Unix socket driver will serialize the message to
JSON.

Alternatives
------------

An operator could abuse the notification log driver to emit notification to the
Python logging system and then use a Python log handler to redirect the log
stream for the notification topic to a Unix socket.

An operator could use AMQP with a local or remote message bus.

Impact on Existing APIs
-----------------------

None

Security impact
---------------

None. Simple filesystem users and groups will provide security for the socket.

Performance Impact
------------------

None. This is expected to have little overhead similar to the Python log
driver.

Configuration Impact
--------------------

A new config options to specify the socket URI will be provided by the driver.
This will be required if using the driver.

.. code-block:: ini

    [oslo_messaging_notifications]
    sock_path=/run/<service>/notifications.sock

Developer Impact
----------------

None

Testing Impact
--------------

The test surface is expected to be small and simple unit and functional tests
will be provided in line with the logging driver. Integration testing via a
dedicated DevStack-based job is not planned, although an existing job could
perhaps be extended to also enable it if required.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  sean-k-mooney

Milestones
----------

Target Milestone for completion: milestone 2

Work Items
----------

- Add driver
- Add tests
- Release note and docs
- Profit

Documentation Impact
====================

Documentation impact will be limited to the config options and release notes

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
