===============================
 Mutable logging configuration
===============================

https://blueprints.launchpad.net/oslo-log/+spec/mutable-logging

There is a strong desire from operators to be able to reconfigure logging
without a service restart. For example, to selectively enable DEBUG logging in
response to observed issues. Mutable config patches have enabled options to be
mutated at runtime, now we need to do the same for logging config.

Problem description
===================

Mutable logging
---------------

Previous work on oslo.config and oslo.log has allowed the 'debug' flag to be
mutable at runtime. However, oslo.log also accepts a 'log_config_append'
option. If this is provided, most of the options are ignored and a logging
config file is read. In this case, mutating the 'debug' flag is insufficient
to change the log level.

This flag also provides minimal control over logging. It should be possible to
change the log level of individual loggers at runtime. To support this, full
mutation of the logging config should be supported.

Proposed change
===============

Mark 'log_config_append' as mutable. When the hook is called, call
logging.fileConfig if the value of log_config_append changed or the timestamp
of the file it points to changed.

Alternatives
------------

The primary usecase for a logging config file is to output log records as JSON
suitable for Logstash. If oslo.log provided a simple way to configure this
then full logging configurations would be less common. Other suggestions are
for 'syslog', 'fluentd' and 'color' logging.

There are three reasons to proceed with the proposed change. Firstly, making
one change does not preclude the other. We can "make the simple easy and the
complex possible". Secondly, the plurality of "simple" configurations implies
that another could be needed at any moment. Until this can be provided, users
would have to do without or use a full logging config.

Lastly, although configuring an additional handler is the most common reason
to use a full logging config, it is also common to reconfigure some log
levels. If we expose options which can turn on Logstash and/or Fluentd and/or
syslog handlers, plus set arbitrary logger levels - have we not reinvented the
logging config system? And with a plethora of switches and options rather than
a well-defined DSL. This feels like a retrograde step.

Impact on Existing APIs
-----------------------

None.

Security impact
---------------

None.

Performance Impact
------------------

None.

Configuration Impact
--------------------

None.

Developer Impact
----------------

None.

Testing Impact
--------------

Although the oslo.log change is simple, the 'logging' module is doing a lot
for us. Unit tests will demonstrate the behaviour in cases such as when a
handler initially configured is no longer mentioned when the config is
reloaded.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  alexisl

Other contributors:
  None

Work Items
----------

* Mark 'log_config_append' as mutable.
* Call logging.fileConfig from the hook.

Documentation Impact
====================

None.

Dependencies
============

This work relates to the mutate_config_files work in oslo.config, which has
already merged.

https://review.openstack.org/#/c/254821/ adds a mutate hook to oslo.log. This
spec will extend the hook by making log-config-append mutable.

References
==========

* Some testing of fileConfig:
  https://gist.github.com/lxsli/3ef859d641da7bcc9bd6

The 'logging' module was creating a Lock before eventlet could monkey-patch
it. Eventlet now patches that lock so this is no longer a problem. Gevent
already has code to do this.

* Locking issue originally diagnosed by Alexander Makarov:
  https://review.openstack.org/#/c/154838
* Demonstration of the locking issue:
  https://gist.github.com/lxsli/9d2458834e13ad0f5e25
* Eventlet fix: https://github.com/eventlet/eventlet/pull/309


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
