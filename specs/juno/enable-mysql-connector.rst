=========================================
 Enable MySQL Connector driver (phase 1)
=========================================

https://blueprints.launchpad.net/oslo/+spec/enable-mysql-connector

Switch from MySQLdb to MySQL Connector [#pypi]_ which provides multiple
benefits, including resilience of code and potential performance advantages.

Note: this phase includes adding optional support to run Devstack against MySQL
Connector and is not meant to change the default recommended database driver
for running against MySQL. Choice of default driver will be revisited the next
cycle.

Problem description
===================

The current MySQL client library we use (MySQLdb) plays badly with eventlet and
may result in db deadlocks (see [#dead_locks]_). It also blocks execution of
other green threads while we're deep in the library code (see [#one_thread]_).
To avoid those issues, we need to be able to switch to a pure python library
with better eventlet support. MySQL Connector [#official_page]_ is an official
MySQL Python client library and has the needed qualities.

Proposed change
===============

Oslo.db already supports using other MySQL drivers [#dialects]_. Oslo.db uses
SQLAlchemy which supports switching client libraries by modifying the SQL
connection URI that we pass to a service as a configuration option.

We can specify the driver to use when connecting to MySQL as follows:

connection = mysql+mysqlconnector://...

So most work is around oslo.db, devstack, and documentation. (For details, see
'Work Items' section below.)

Alternatives
------------

Some database lock timeouts can be mitigated by refactoring code
[#hack_around_notifications]_. We may also introduce special mechanisms that
would reduce the chances for the current thread to yield under transaction that
are one of the main causes of db deadlocks. It is not realistic to expect that
we're able to nail down and fix all occurances of possible yields under
transactions.

We could also switch to some other library that is also supported by SQLAlchemy
[#dialects]_.  Though those other libraries do not provide clear benefits in
comparison to MySQL Connector, while the latter is the official driver for the
MySQL project.

We could also introduce a per-kernel-thread (or global) Python/eventlet lock
around any calls into MySQLdb that may block. Not a particularly attractive
option, because the impact on parallel operations is expected to be enormous.

Finally, we could just drop eventlet from all our projects, though this option
is not realistic.

Impact on Existing APIs
-----------------------

None.

Security impact
---------------

None.

Performance Impact
------------------

Though MySQL Connector is a pure Python library, while MySQLdb is largely
written in C, and we could expect that the new module is a bit slower than the
current one, performance may actually be improved.  This is because the new
module is eventlet aware, meaning threads will be able to switch while waiting
for I/O from a database server.

This expectation is proved by the following measurements [#measurements]_.

A simple performance test for Neutron was run locally on devstack to check
impact of the change. Four scenarios were checked:

* create 200 ports in serial
* create 200 ports in parallel using 'futures' module with 10 thread workers
* create 2000 networks in serial
* create 2000 networks in parallel using 'futures' module with 10 thread workers

Each scenario was run three times.

For serial scenarios, the average result is pretty the same:

* mysqldb (ports): 59.43 sec
* mysql connector (ports): 62.81 sec
* mysqldb (networks): 211.94 sec
* mysql connector (networks): 206.80 sec

For parallel scenarios, there is a very significant benefit:

* mysqldb (ports): 58.37 sec
* mysql connector (ports): 35.32 sec
* mysqldb (networks): 215.81 sec
* mysql connector (networks): 88.66 sec

More detailed benchmarking and scalability testing will be done in the second
phase which belongs to Kilo cycle. Details on what constitutes a proper
benchmark for global switch are to be decided during that cycle.

Configuration Impact
--------------------

From configuration point of view, this is just a matter of changing connection
string for each service. Old values should continue to work, so migration to
the new library can be delayed or done iteratively. Also, we don't enforce or
even recommend operators to switch their database driver of choice, so unless
they explicitly opt-in, there is no change for them whatsoever.

Developer Impact
----------------

More strict rules will be applied for migration code to facilitate using
multiple database drivers from the same code (like not passing multiple SQL
statements in single call to engine.execute()).

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  ihar-hrachyshka

Secondary assignee:
  gus (Angus Lees)

Milestones
----------

Juno-3

Work Items
----------

The following items should be handled before claiming the switch to MySQL
Connector to be completed:

* oslo.db requires a few small changes for testing and feature parity with
  non-default MySQL drivers (development tracked by Angus Lees).
* update devstack to enable optional support for running it against MySQL
  Connector.
* create a separate gate check to run tempest against the new driver.

Incubation
==========

None.

Documentation Impact
====================

We won't recommend users to switch database module in Juno. We may still be
interested in notifying them that there is now an option to run their
deployments against the new driver, which has its own benefits though.

Dependencies
============

MySQL Connector must be posted to PyPI to be able to introduce it as part of
global requirements list.

MySQL Connector is published under the terms of the same license as for MySQLdb
(GPLv2), so there should be no legal issues with using that. Also, MySQL
Connector provides FOSS exception for a vast number of open source licenses
[#exceptions]_, so it can be considered as more liberal than MySQLdb.

References
==========

.. [#pypi] https://pypi.python.org/pypi/mysql-connector-python
.. [#dead_locks] https://wiki.openstack.org/wiki/OpenStack_and_SQLAlchemy#MySQLdb_.2B_eventlet_.3D_sad
.. [#one_thread] http://docs.openstack.org/developer/nova/devref/threading.html
.. [#official_page] http://www.mysql.com/products/connector/
.. [#dialects] http://docs.sqlalchemy.org/en/rel_0_9/dialects/
.. [#hack_around_notifications] https://review.openstack.org/100934/
.. [#measurements] http://www.diamondtin.com/2014/sqlalchemy-gevent-mysql-python-drivers-comparison/
.. [#exceptions] http://www.mysql.com/about/legal/licensing/foss-exception/

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

