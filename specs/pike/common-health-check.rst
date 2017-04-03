==================================
 Common health-check API end-point
==================================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/oslo?searchtext=common-health-check

After deploying all your API's, how do you know they're properly configured?

Problem description
===================

When putting loadbalancers infront of api's, there's no common way to probe if
the service has access to all the dependencies it's configured for. What does a
200 OK mean when you're polling http://internal.service.api/ ? Is the database
accessed, or rabbit_mq?

Proposed change
===============

It would be beneficial for loadbalancers (or humans) to determine whether a
service can actually respond to requests to given to it. If it has all the
necessary connections for its current configuration.

Introducing http://internal.service.api/status (or health-check, or whatever)

Some endpoint where loadbalancers can run a check, and the api will check its
internals. Is it set up to use a transport_url, and is it available?
Does it have a connection to the database? Are all its tables present?
Is it configured to access swift, sheepdog or ceph? Everything in order there?

If yes, return 200 OK

If no, return 5xx and some json object with errors.
{
  rabbit_mq: "can't connect to host: 10.13.37.10"
  database: "missing table 'super_cereal'"
}


Alternatives
------------

CloudPulse, yet another service that can check if your other services are up
and running.

Impact on Existing APIs
-----------------------

All API's will have to implement this new end-point, and do some form of
internal checks and report back.

Security impact
---------------

Unknown.

Performance Impact
------------------

If polled to often, depending on the thoroughness of the check, it might tax
the api somewhat. 

Configuration Impact
--------------------

Unknown.

Developer Impact
----------------

Unknown.

Testing Impact
--------------

Unknown.

Implementation
==============

Assignee(s)
-----------

This is a blueprint I'm just throwing it out there to see if someone thinks is
a good enough idea to pick up.

Milestones
----------

N/A.

Work Items
----------

Work items or tasks -- break the feature up into the things that need to be
done to implement it. Those parts might end up being done by different people,
but we're mostly trying to understand the timeline for implementation.

For graduation blueprints, start with
https://wiki.openstack.org/wiki/Oslo/CreatingANewLibrary#Checklist and
add any additional steps necessary at the appropriate place in the
sequence. If no extra work is needed, referencing the checklist
without reproducing it is sufficient.

Incubation
==========

Unknown.

Adoption
--------

Unknown.

Library
-------

Unknown.

Anticipated API Stabilization
-----------------------------

One or two cycles.

Documentation Impact
====================

Some information as to what the endpoint checks, and/or what the error
messages would mean.

Dependencies
============

Possibly taking the ideas of this spec a bit further.
http://specs.openstack.org/openstack/oslo-specs/specs/ocata/oslo-validator.html

References
==========

N/A.

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

