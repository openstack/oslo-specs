..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

========================
Policy Merge in Keystone
========================

`bp example <https://blueprints.launchpad.net/keystone/+spec/policy-merge>`_

Managing Policy By composing Fragments in the Keystone server.


Problem Description
===================

Policy in OpenStack is incredibly Static. Coupled with that, the
defaults are not set up to scale.  However, changing policy cluster
wide is a difficult task.

Many of the policy files have common sections, or section that vary
slightly, but use the same rule names.  This has the potential to
confuse deployers, as well as contribute to security holes.

While each of the project teams needs to be able maintain their own
inventory of policy targets, they should be able to consume a common
section from Keystone.  Composing that common section is going to be a
work in progress, and needs support from the Keystone server.

With the various APIs for associating policy files with endpoints and
services, Keystone now has a way to act as a system of record for
policy. However, the policy files themselves are still opaque blobs,
disjoint between services.

Proposed Change
===============

Add a CLI for creating a new policy file by merging a set of existing
policy files.

For an initial implementation, Keystone will assume all of the policy files
are JSON files.  They will be parsed, and the set of rules merged into a
single JSON file, which will be deserialized.

Once  YAML is supported by oslo.policy, it will be handled the same way.

A parameter will indicate how to treat conflicts between existing
rules.  This paramter can be specificied once globally, and also per
file:

 The strategies are:

*  FAIL: If two rules have the same key, the API will return an error code.
*  OVERRIDE: If two rules have the same key, the rule from the later
   file in the list will over-write the rule specified by the earlier file.
*  MAINTAIN: The first specification of a rule will be maintained,
   and conflicting definitions will be discarded.


  Once the merger is complete, a new policy file will be produced in
  JSON format.

Alternatives
------------

Merging and composing of the JSON blobs could be done off line.
However, this is merely another way of implementing the same function,
but without integrating it in with OpenStack.


Security Impact
---------------

As with most policy changes, this is designed to improve the security
story of OpenStack deployments.   By itself, this change will have no
impact. However, when coupled with the ability to distribute policy
files based on the associations, the policy will be more dynamic, and
can lead to an improvement or degradation based on the quality of the
review and distribution process.


Notifications Impact
--------------------

There is no notification impact.


Other End User Impact
---------------------

Deployers can make use of this call to create more specific policies.

One expected use case is to allow a user to override a small set of
APIs from the basic policy for a service.

OpenStack Client will also need an option to trigger the call.


Performance Impact
------------------

None, calls to this CLI should be done at deployment time or earlier.

Other Deployer Impact
---------------------

This is a work flow change, but will not materially impact the general
deployment of OpenStack until tooling takes advantage of the
Associations.  Once that happens, the overall work flow will look like
this:

* Create a common policy fragment.
* Create  the new policy fragment.
* Merge the Common fragment with the new
* Distribute the associated policy file to the new endpoint.


Developer Impact
----------------

API Developers working on policy will be able to think in terms of
common policy fragments.


Implementation
==============

Assignee(s)
-----------


Primary assignee:
ayoung Adam Young ayoung@redhat.com


Work Items
----------

* Server Should be done in a single commit.
* Client Code
* Deployment tooling.




Dependencies
============

No external dependencies. However, the coming change to let Oslo
policy render to YAML or other formats might complicate the merge process.


Documentation Impact
====================

This should have little impact to start.  Once the whole work flow is
in place, it should be documented in a "How to manage policy" guide.


References
==========

None Yet.
