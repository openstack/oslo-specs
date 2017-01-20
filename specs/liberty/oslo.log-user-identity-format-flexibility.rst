==================================================
 oslo.log -- ``user_identity`` format flexibility
==================================================

https://blueprints.launchpad.net/oslo.log/+spec/user-identity-format-flexibility

The goal of this blueprint is to make it easier to adjust the format
of the ``user_identity`` field in the log line without having to
specify the full log format string.

Problem description
===================

* We want devstack to log identity using names, but by default we want
  identity to use UUID values because they are guaranteed to be
  unique.
* We don't want devstack to override the format string for projects
  individually.
* We do want devstack to be able to change the default format without
  having to specify the whole string, for this leaves devstack with no
  info on anything added into the default formatting string.

Proposed change
===============

Since oslo.context is not using oslo.config, and is incorrectly
enforcing formatting, we want to make this change to oslo.log.

Let oslo.log control the formatting for the user_identity value in the
log output. We have to leave the value in place in oslo.context, but
we don't have to use it any more.

Add a new configuration option to specify how to format the
user_identity field. (We might find it useful to do this for other
fields in the future, too, but let's focus on one for now.)

Update oslo.log so it asks oslo.context for the values, and then
replaces the user_identity with a string it builds itself using values
it gets from oslo.context and the format string it gets from its
configuration option.

Alternatives
------------

We could require anyone wanting to customize the log format to replace
the entire format string, but that makes it a little harder to adjust
just part of it as we standardize the overall structure of the log
messages.

We could place the configuration option in oslo.context, but that
library is not using oslo.config yet and it should not have log
formatting logic embedded in it.

Impact on Existing APIs
-----------------------

None. The :class:`RequestContext` from oslo.context will still need to
provide user_identity for backwards compatibility.

Security impact
---------------

The result will be no more or less secure than before.

Performance Impact
------------------

One extra format call should not have a big performance impact.

Configuration Impact
--------------------

One new configuration option, with the default set up to result in the
same format we have now.

Developer Impact
----------------

Users of devstack will eventually be able to see user identity in a
nicer format.

Testing Impact
--------------

No significant change.

Implementation
==============

Assignee(s)
-----------

Primary assignee: doug-hellmann

Other contributors: ihrachyshka

Milestones
----------

Target Milestone for completion: liberty-3

Work Items
----------

#. add a new config option to oslo.log to control how the
   user_identity values are formatted; default it to what oslo.context
   does now
#. add a new method to oslo.context to provide identity values to go
   into that format string (or just use the whole context dict?) Dict
   is fine.
#. update oslo.log to build a new string and update the dictionary
   given to it from to_dict() always
#. update devstack to set the new configuration option in a way that
   uses names instead of, or in addition to, uuids

Incubation
==========

N/A

Documentation Impact
====================

The new configuration option needs to be documented.

Dependencies
============

- This is related to :doc:`../kilo/app-agnostic-logging-parameters`
  but only depends on it in the sense that only projects using
  oslo.log and oslo.context will be able to take advantage of the
  feature.

References
==========

- notes: https://etherpad.openstack.org/p/logging-flexibility


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

