===========================
 oslo.log: Quiet Libraries
===========================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/oslo?searchtext=quiet-libraries

Problem description
===================

As we add more dependencies, we find more cases where we need to
customize the logging output for those libraries. Rather than forcing
applications to manage their own list of customizations, and rather
than having a single large list of customizations in oslo.log, we
should change the way we configure the logger tree so that libraries
are quiet by default.

Proposed change
===============

We currently attach a logging handler to the root logging node and
configure it to emit output to whatever source the user has specified
(a file, syslog, etc.) using a default log level. We then use the
``default_log_levels`` option to specify different default settings
for other libraries, usually to quiet them so that output is only
produced at warning or higher levels. This configuration takes
advantage of the fact that Python's logging module configures the
loggers in a tree structure, where messages move up the tree until
they find a node that handles them.

That gives us a logger structure like:

* <root> - INFO

  * myapp (messages propagate up to <root>)
  * amqp - WARN
  * amqplib - WARN
  * boto - WARN
  * qpid - WARN
  * sqlalchemy - WARN
  * suds - INFO
  * oslo

    * messaging - INFO

  * iso8601 - WARN
  * requests

    * packages

      * urllib3

        * connectionpool - WARN

  * urllib3

    * util

      * retry - WARN

  * keystonemiddleware - WARN
  * routes

    * middleware - WARN

  * stevedore - WARN

One drawback to this approach is that new versions of libraries affect
the log content and the settings to control them need to be updated
fairly frequently. This problem will increase as we start to support
more drivers with additional third-party dependencies.

To solve the problem, we configure the loggers so that the root
node always only emits data at WARN or higher, and then configure a
logger named for the base package of the application to emit messages
at the level requested by the logging configuration flags
(``--debug``, ``--verbose``, etc.).

The ``default_log_levels`` option will still be supported, but any
libraries with custom output levels managed through
``default_log_levels`` can be ignored unless their output level is
different than WARN. This is a minor optimization in the configuration
setup, though, so we don't need to implement it.

The result would look more like:

* <root> - WARN

  * myapp - INFO (has a local handler)
  * suds - INFO
  * oslo - INFO

The other loggers still exist, but they wouldn't need custom
configuration. They could still be given levels based on the
configuration options, in case that turns out to be useful.

Moving all of the Oslo library loggers under the ``oslo`` part of the
logger tree will require a little custom logic in
:func:`oslo_log.log.getLogger` to replace ``"oslo_library"`` with
``"oslo.library"``.

Alternatives
------------

Don't Place Oslo Libraries Under a Common Node
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We could keep the Oslo libraries logging under their own
library-specific names ``oslo_config``, ``oslo_concurrency``,
etc. However, this makes it more difficult to configure them to all
log at a consistent level. Because the Oslo library code is a growing
part of the overall OpenStack code base, and errors frequently require
information about the libraries' behavior to debug, having them all
under a single common node makes it easy to adjust the log output.

Leave Things Alone
~~~~~~~~~~~~~~~~~~

We do have ``default_log_levels`` and the ability to configure logging
through a file instead of just configuration flags, so deployers could
set this up themselves. However, the default behavior of oslo.log is
supposed to represent a useful configuration for *most* deployers, so
making the change there is better than asking each deployer to figure
it out for themselves.

Set Root Logger Level to ERROR
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rather than using WARN as the default level for the root logger, we
could use ERROR or even CRITICAL. This would further reduce the extra
output, but WARN seems like it should be good enough for most
libraries that we are using now. We can evaluate changing the level
after the main part of the work is done, since it will be a simple
change to experiment with at that point.

Add Configuration Option for Root Logger Level
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rather than hard-coding the level of the root logger, we could use a
configuration option to let the deployer control it. We can evaluate
this alternative after the main part of the work is done, since it
will be a simple change to experiment with at that point.

Impact on Existing APIs
-----------------------

No API changes.

We already have the application name as the ``product_name`` argument
to :func:`oslo_log.log.setup`, so we can use it to set up the
application's primary log handler.

Security impact
---------------

None

Performance Impact
------------------

None

Configuration Impact
--------------------

All of the existing configuration options will continue to produce the
same results.

We can eventually change the default value of ``default_log_levels``,
although that's not necessary at first.

Developer Impact
----------------

None

Testing Impact
--------------

We will want to verify that the log output doesn't increase
significantly when we change the default behavior for the Oslo
libraries.

Implementation
==============

Assignee(s)
-----------

Primary assignee: Doug Hellmann

Other contributors: None

Milestones
----------

Target Milestone for completion: Liberty-2

Work Items
----------

#. Modify the setup code to create separate root and application
   loggers with their own handlers.
#. Modify :func:`getLogger` to handle the ``"oslo_"`` to ``"oslo."``
   conversion.

Incubation
==========

N/A

Adoption
--------

N/A

Library
-------

N/A

Anticipated API Stabilization
-----------------------------

N/A

Documentation Impact
====================

The proposed change affects the default log levels, but all of the
configuration options will work in the same way so no documentation
changes should be needed.

Dependencies
============

None

References
==========

* Python's logging module: https://docs.python.org/2/library/logging.html
* Brant Knudson's patch to make the default logger list expandable
  through :func:`set_defaults`: https://review.openstack.org/#/c/164503

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

