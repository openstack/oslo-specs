..
  This template should be in ReSTructured text.  For help with syntax,
  see http://sphinx-doc.org/rest.html

  To test out your formatting, build the docs using tox, or see:
  http://rst.ninjs.org

  The filename in the git repository should match the launchpad URL,
  for example a URL of
  https://blueprints.launchpad.net/oslo?searchtext=awesome-thing should be
  named awesome-thing.rst.

  For specs targeted at a single project, please prefix the first line
  of your commit message with the name of the project.  For example,
  if you're submitting a new feature for oslo.config, your git commit
  message should start something like: "config: My new feature".

  Wrap text at 79 columns.

  Do not delete any of the sections in this template.  If you have
  nothing to say for a whole section, just write: None

  If you would like to provide a diagram with your spec, ascii diagrams are
  required.  http://asciiflow.com/ is a very nice tool to assist with making
  ascii diagrams.  The reason for this is that the tool used to review specs is
  based purely on plain text.  Plain text will allow review to proceed without
  having to look at additional files which can not be viewed in gerrit.  It
  will also allow inline feedback on the diagram itself.

==============================
Notification Dispatcher Filter
==============================

https://blueprints.launchpad.net/oslo?searchtext=notification-dispatcher-filter

Oslo.messaging lacks the ability to filter out notifications it sends to
endpoints. This spec proposes to enable filtering process before messages are
dispatched to endpoints.

Problem description
===================

Currently, oslo.messaging blindly dispatches notifications to all registered
endpoints. It is after the endpoints receive the messages are we able to filter
and decide whether the endpoint should process the notifications. This decision
can be made earlier before it dispatches messages to the endpoints to avoid
the overhead of sending messages to endpoints which will ignore them.

For example, in Ceilometer, multiple endpoints are connected to the
notification listener. Each endpoint may only process a subset of the
notifications that are picked up. It is at the endpoint level where we
currently filter whether to continue processing the notification but this
filtering can easily be done before it's even dispatched to the endpoint.


Proposed change
===============

The proposed solution is to add a NotificationFilter to the dispatcher. When
oslo.messaging dispatches messages to the endpoints, it will first pass through
the filter and check if the messages fits the criteria defined in filter.
Messages can be filtered using regex against all first level attributes of a
message: context, publisher_id, event_type, metadata, and payload. As context,
metadata, and payload are dictionary values, multiple contraints can be
defined for them.

An example filter is as follows:

.. code-block:: python

  filter =  NotificationFilter(
      publisher_id='^compute.*',
      context={'tenant_id': '^5f643cfc-664b-4c69-8000-ce2ed7b08216$',
               'roles': 'private'},
      event_type='^compute\.instance\..*',
      metadata={'timestamp': 'Aug'}.
      payload={'state': '^active$'})

Alternatives
------------

We continue to filter at the endpoint level.

Impact on Existing APIs
-----------------------

None.

Security impact
---------------

None.

Performance Impact
------------------

None, but it does offer potential to reduce load dispatched.

Configuration Impact
--------------------

None.

Developer Impact
----------------

Developers nowi have ability to add a filter when they defined Endpoints.

.. code-block:: python

  class NotificationEndpoint(object):
      filter = NotificationFilter(publisher_id='^compute.*')


Testing Impact
--------------

Unit tests are sufficient as the functionality is limited to dispatcher.
Indirectly, when implemented in Ceilometer, this will be tested via tempest.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  sileht 

Other contributors:
  gordc

Milestones
----------

Target Milestone for completion: kilo-1

Work Items
----------

- Add filter to dispatcher with unit tests
- change filters in Ceilometer to use new filters.

Incubation
==========

None.

Adoption
--------

Ceilometer but it seems like common functionality that other listeners
would use.

Library
-------

oslo.messaging.

Anticipated API Stabilization
-----------------------------

None.

Documentation Impact
====================

None.

Dependencies
============

None.

References
==========

code review: http://review.openstack.org/#/c/77886/


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

