======================================
Add ChainingRegExpFilter into rootwrap
======================================

https://blueprints.launchpad.net/oslo-incubator/+spec/chaining-regexp-filter

Add new filter which accepts utilities prefixed to other commands, such as
'nice' and 'ionice'. This will increase maintenability of config files.

Problem description
===================

Currently we don't have a good way to define filters to allow prefix utilities.
For example, cinder is using 3 RegExpFilter rules to allow 'ionice' + 'dd'
command which cover various 'dd' options. But this is fragile to changes of
'dd' usage (actually these rules are broken now by a bugfix patch for 'dd':
https://bugs.launchpad.net/cinder/+bug/1318748 ).

Proposed change
===============

By adding ChainingRegExpFilter, which is configured by the format below, we
can easily add a new filter that accepts prefix utilities.

    filter_name: ChainingRegExpFilter, <command>, <user>,
                 <RegExp list for the arguments>

This filter regards the length of the regular expressions list as the number of
arguments to be checked, and remaining parts are checked by other filters.
That is, the command specified to the argument of prefix utility must be
allowed to execute directly.

For example, 'ionice'+'dd' can be accepted by single rule below
safely (that is, accepted only when the following command is acceptable by
other filters).

    ionice: ChainingRegExpFilter, ionice, root, ionice, -c[0-3]( -n[0-7])?

'dd' must also be allowed to execute directly (without 'ionice').
Note that cinder currently allows 'dd' for root using CommandFilter as default.

Alternatives
------------

We could implement a specialized filter class for each prefix command like
IpNetnsExecFilter each time it is needed.
That might be easier to reuse the same rule among projects, although it may
require a lot of classes.
ChainingRegExpFilter is more generic, so it is still useful at least until the
utility is found sharable.

Impact on Existing APIs
-----------------------

None.

Security impact
---------------

Rules for prefix utilities must be written carefully not to allow unchecked
commands executed. For example, it can be dangerous to allowing any string
('.*') for the argument that could be interpreted as command to be executed.

Performance Impact
------------------

None.

Configuration Impact
--------------------

New filter 'ChainingRegExpFilter' will be available.

Developer Impact
----------------

None.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  tsekiyama

Milestones
----------

Target Milestone for completion:
  Juno-1

Work Items
----------

1. Implement ChainingRegExpFilter
   -> https://review.openstack.org/#/c/97336/

Incubation
==========

None.

Adoption
--------

None.

Library
-------

None.

Anticipated API Stabilization
-----------------------------

None.

Documentation Impact
====================

Usage of ChainingRegExpFilter should be added to the document.

Dependencies
============

- This feature provides a good way for Cinder to fix 'ionice' command rules

- A cinder patch to implement I/O rate limit requires to execute 'cgexec'
  prefix utility with rootwrap ( https://review.openstack.org/#/c/92894/ )

References
==========

None.

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

