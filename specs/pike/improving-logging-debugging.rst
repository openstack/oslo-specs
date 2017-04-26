=======================================
 Improving Logging to Aid in Debugging
=======================================

Operators have been asking for mnemonic identifiers for log messages
since the start of the Folsom cycle in 2012. This proposal tries to
provide the features of those identifiers, without having to update
every log message and string being passed through the logging modules.

Problem description
===================

Many commercial (closed-source) enterprise applications, and even some
open source projects, include unique identifiers for every user and
log message. The IDs are used as reference points in documentation and
bug reports, either instead of or in addition to the text of the log
message. Message IDs also mean that online searches can be language
independent, to some degree, although translating the results of a
search may still require someone to be able to read English if there
are no results in their primary language.

As an open source project with a widely distributed contributor base
and multi-service architecture, adding message IDs to OpenStack
presents some unique challenges not faced in other environments.  A
central repository of unique IDs will be difficult to maintain.
Adding IDs to every log message in anticipation of documentation to be
written later will produce a lot of patches with little value,
triggering reviews, test jobs, and rebases of other patches.
Requiring IDs for each log call, or for only some log levels, will
require incompatible changes to our logging library APIs.  This
proposal tries to address all of those issues in a way that will allow
us to deliver the benefit of those message IDs without the expense of
introducing unique IDs to all logging calls.

The benefits of unique IDs for log messages have been given as

1. A unique ID for an error can act as a mnemonic, when discussing the
   error with another operator or when a user reports an error through
   support channels.

2. A unique ID for a message helps locate that message in the source
   for the program, making it easier to troubleshoot and debug by
   being able to jump directly to the source code.

Proposed change
===============

Although unique message IDs are useful, maintaining the list would
grow tedious. The new rules reviewers would need to learn in order to
manage a segmented ID value correctly would lead to frustration and
nit picking on reviews. Adding the IDs in the first place would take
manual work, and keeping them correctly organized over time would
increase our maintenance burden. The two primary features leading to
the request for message IDs are both available in other forms with
minimal source code changes, so this proposal describes how to achieve
the goals in the easiest way possible.

Message Locations
-----------------

The location of a message (filename and line number) can be exposed
today in any version of OpenStack by adding the relevant fields to the
logging format configuration option. No source code changes are needed
at all. There are 3 different ways to expose the location, depending
on how much detail is desired.

1. The form in use today is the ``%(name)s`` field, which introduces
   the "logger name" into the log line. The standard practice in
   OpenStack is to use the Python module name, accessible via the
   ``__name__`` variable, to get a logger object for each
   file. Therefore in most cases, the logger name and module name will
   match. For example, in nova/api/auth.py the line::

       LOG = logging.getLogger(__name__)

    causes the logger to be called ``nova.api.auth``.

2. The ``%(filename)s`` field inserts the last part of the full file
   name into the log line. For example, nova/api/auth.py produces
   ``auth.py``.  OpenStack contains quite a few modules with the same
   base file name, so this version is not likely to be very useful for
   debugging.

3. The ``%(pathname)s`` field inserts the full name of the file into
   the log line. For example nova/api/auth.py produces something like
   ``/usr/local/lib/python2.7/site-packages/nova/api/auth.py`` (the
   actual value depends on how the software is packaged and
   installed).  These paths can be quite long, but for a site where
   that level of detail is desired it is available.

The file name is only one part of the necessary information for
finding a log message.  The other is the line number. The
``%(lineno)s`` field will insert the line number of the location of
the logging call that introduces a line to the log. For example, the
line::

    LOG.debug("Neither X_USER_ID nor X_USER found in request")

appears on line 102 of nova/api/auth.py, so ``%(lineno)s`` would
insert ``102`` into the log line.

As stated above, the ``%(name)s`` field already appears in the default
format string set by oslo.log. The ``%(lineno)s`` field can be added
there easily.  This information can be added to the oslo.log
documentation to make it easier for users to find. Although this may
lead to operators running with non-default configurations, it is less
likely to break the logging pipelines in existing deployments. Over
time, as we see how useful the line numbers are, we can revisit this
approach.

Error Identifiers
-----------------

Most errors in Python programs are associated with an instance of a
class derived from Exception. These classes have message text,
frequently with the ability to insert dynamic values (such as the name
of a specific thing that has a problem). Python's logging library
recognizes exception instances, and when a log message is emitted
while there is an active exception the exception can be included in
the output, producing a traceback.

Exceptions are logged by calling the exception() method of the logger,
or by passing exception information to another method such as error()
or warning(). In all cases, the logging formatter is responsible for
taking the arguments given and producing the appropriate log output
line.

Given the example logging call::

    LOG.exception('the exception log msg')

Today when an exception is logged, the output produced looks like:

::

    2017-04-24 15:15:54.823 1108 ERROR oslo.tester:24 [-] the exception log msg
    2017-04-24 15:15:54.823 1108 ERROR oslo.tester Traceback (most recent call last):
    2017-04-24 15:15:54.823 1108 ERROR oslo.tester   File "./tester.py", line 21, in <module>
    2017-04-24 15:15:54.823 1108 ERROR oslo.tester     raise RuntimeError('the error text')
    2017-04-24 15:15:54.823 1108 ERROR oslo.tester RuntimeError: the error text
    2017-04-24 15:15:54.823 1108 ERROR oslo.tester

Note that the exception name (``RuntimeError``) and error text appear
several lines removed from the first error line, which contains the
string passed to the exception() method.

The log formatter used by oslo.log can be modified to insert the
summary of the exception into the first log line, along with the local
message. The results would look like:

::

    2017-04-24 15:15:54.823 1108 ERROR oslo.tester:24 [-] the exception log msg: RuntimeError: the error text
    2017-04-24 15:15:54.823 1108 ERROR oslo.tester Traceback (most recent call last):
    2017-04-24 15:15:54.823 1108 ERROR oslo.tester   File "./tester.py", line 21, in <module>
    2017-04-24 15:15:54.823 1108 ERROR oslo.tester     raise RuntimeError('the error text')
    2017-04-24 15:15:54.823 1108 ERROR oslo.tester RuntimeError: the error text
    2017-04-24 15:15:54.823 1108 ERROR oslo.tester

We can actually do this no matter the log level, so that if a log
message is emitted in the context of handling an exception, that error
is included in the output even if the level for the log message is
INFO or DEBUG.

See https://review.openstack.org/#/c/459424/ for an example
change. The other log formatters provided by oslo.log will also need
to be updated.

This change works with any Python library, not just OpenStack modules,
so errors produced by upstream dependencies are treated the same way.

We can simultaneously allow operators to add the error summary to
their default format, so if they want to place it earlier in the line
they can. If the default error summary value is "``-``", the field
will be present, making log line parsing easier. For example, the
``logging_context_format_string`` value can be set to

::

  %(asctime)s.%(msecs)03d %(process)d %(levelname)s %(name)s:%(lineno)s [%(request_id)s %(user_identity)s] [%(error_summary)s] %(instance)s%(message)s

to produce a line like the following (when there is an error)

::

    2017-04-24 15:15:54.823 1108 INFO oslo.tester:24 [-] [RuntimeError: the error text] a regular log message goes here

or like the following (when there is not an error)

::

    2017-04-24 15:15:54.823 1108 INFO oslo.tester:24 [-] [-] a regular log message goes here

see https://review.openstack.org/461506 for an example implementation
of this additional flexibility.

Alternatives
------------

1. The first public specification related to this topic was posted in glance-specs
   under the title "Glance Error Codes": https://review.openstack.org/#/c/127482

   The Glance spec was eventually moved to the cross-project specs repo with
   the title "OpenStack wide Error Codes for Log Messages":
   https://review.openstack.org/#/c/172552

2. We could, once and for all, declare that this is not a feature we are going
   to add to OpenStack.

3. We could adopt the "situation ID" proposal in the cross-project
   spec proposed as https://review.openstack.org/460110, or one of the
   variations described in the alternatives section of that document.

4. We could add the directives to the default logging format string to
   add the line numbers automatically. This would likely break the log
   management pipelines in existing deployments, since the line format
   would change.

References
----------

* `Python logging module documentation about log record attributes
  <https://docs.python.org/2/library/logging.html#logrecord-attributes>`__
* `Lessons learned from working on large scale, cross-project
  initiatives in OpenStack
  <https://doughellmann.com/blog/2017/04/20/lessons-learned-from-working-on-large-scale-cross-project-initiatives-in-openstack/>`__
* `Boston Forum session to discuss logging proposals <https://www.openstack.org/summit/boston-2017/summit-schedule/events/18778/enhancing-log-message-headers-for-rt-debug-and-traceability>`__
* `Boston Forum Logging Working Group Work session
  <https://www.openstack.org/summit/boston-2017/summit-schedule/events/18507/logging-working-group-working-session>`__

Implementation
==============

Assignee(s)
-----------

Primary assignee:

oslo.log work: dhellmann

documenting exceptions in more detail: TBD

Work Items
----------

* Add documentation about how to include line numbers in the log
  messages.
* Make the oslo.log context formatter add exception summary when
  logging an exception (https://review.openstack.org/#/c/459424/)
* Make the other oslo.log formatters add the exception summary, where
  appropriate. (JSON, journald, etc.)
* Make the other oslo.log formatters and handlers include the line
  number, where appropriate. (JSON, journald, etc.)

Dependencies
============

None

History
=======

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Pike
     - Introduced

.. note::

  This work is licensed under a Creative Commons Attribution 3.0 Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
