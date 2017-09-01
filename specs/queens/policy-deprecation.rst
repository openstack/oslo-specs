==================
Policy Deprecation
==================

https://blueprints.launchpad.net/oslo?searchtext=policy-deprecation

Several OpenStack projects have moved their policies into code and treat them
like configuration. This has numerous benefits for both developers and
operators. Moving policy into code and documenting it is targeted as a
community-wide `goal
<https://governance.openstack.org/tc/goals/queens/policy-in-code.html>`_ for
the Queens release.

Problem description
===================

Policy management in OpenStack has always been a source of operator and
developer pain. It's hard for operators to know what policies were changed or
added across releases without manually diffing policy files. Developers are
unable to programmatically communicate changes to policy files for their users.

Now that projects will be moving policies into code, we have the opportunity to
use oslo.policy to advertise deprecations and future removal of policies. This
gives developers a programmatic way to make much needed changes to policy and
communicate those changes to operators in a way they already know how to
consume. This is consistent with how we deprecate other things in OpenStack,
like configuration options.

Use Cases
---------

The following list describes the cases that need to be covered by the
deprecation functionality in oslo.policy:

* Changing the semantics of a policy in a backwards incompatible way
* Renaming a policy
* Removal of a policy in a backwards incompatible way but with a transition
  plan

These can be explained further in actual use cases and examples:

1. As a developer, I need to be able to change the default role or rule for a
   policy using oslo.policy

2. As a developer, I need to be able to rename a policy using oslo.policy

3. As an operator, I need to know if a policy's default role or rule is
   changing so I can either copy-paste the old policy into my policy file or
   create the role required by the new default

4. As an operator, I need to know if a policy that I'm overriding is going to
   be renamed or removed so that APIs in my deployment aren't accidentally
   unprotected or exposed in an insecure way

Example 1
^^^^^^^^^

The policy, ``"foo:create_bar": "role:fizz"``, needs to change its policy value
to ``"role:bang"``. An operator can do one of two things when upgrading. The
first option is to copy-paste the original policy into the policy file and
override the new default for ``foo:create_bar``. The second option is for the
operator to create role ``bang`` in their deployment so that the new default is
useable after the upgrade. The same process can be applied to ``rule``
evaluations in-place of ``role``.

Example 2
^^^^^^^^^

The policy, ``"foo:post_bar": "role:fizz"``, should be replaced with
``"foo:create_bar": "role:fizz"`` to be consistent with other policies used by
the service. So long as the role or rule check remains consistent there should
be no operator impact to operators using the default. The newer version of the
service will start using ``create_bar`` for policy enforcement, phasing out the
usage of ``post_bar``.

If an operator is overriding the policy for ``post_bar``, a message should be
logged saying that ``post_bar`` is no longer going to be an enforcible policy
and that ``create_bar`` should be used instead. This will give operators a
chance to fix their policy before ``post_bar`` goes away completely. This
ensures that operators don't accidentally expose ``create_bar`` if they are
using a custom policy to protect it.

Example 3
^^^^^^^^^

The policy, ``"foo:bar": "role:bazz"``, should be broken into:

* ``"foo:get_bar": "role:bazz"``
* ``"foo:list_bars": "role:bazz"``
* ``"foo:create_bar": "role:bazz"``
* ``"foo:update_bar": "role:bazz"``
* ``"foo:delete_bar": "role:bazz"``

This gives developers or operators the ability to associate different roles to
different operations of ``bar`` instances, instead of all operations on ``bar``
requiring the ``bazz`` role.

Proposed change
===============

The oslo.policy library exposes a ``DocumentedRuleDefault`` object that
policies are registered as. We can extend this object to support an optional
``deprecated`` attribute, or set of attributes that communicate information
about the deprecation. This won't require projects to change their current
policy definitions or implementations. The following are the attributes that
would be useful to expose to projects so they can improve policy:

* ``deprecated_for_removal``: This is a boolean values that denotes if the
  policy is deprecated or not
* ``deprecated_reason``: This is a string containing justification for the
  removal or deprecation of the policy
* ``deprecated_since``: The release in which the policy was officially
  deprecated

These additional attributes should be very similar, if not the same as the
deprecated functionality of oslo.config. This change will likely be limited to
the oslo.policy library, specifically the ``DocumentedRuleDefault`` object.

Policies that are flagged for deprecation will emit log warnings similar to
using a deprecated configuration option. Likewise, deprecated policies will be
marked as such in generated sample policy files.

Alternatives
------------

Developers can continue to rely on release notes and mailing lists to
communicate policy changes to operators. This is considered suboptimal since it
is prone to human error, lacks consistency across projects, and isn't
programmable. As a result, policies are rarely changed from their original
definitions, which is very problematic since policies never evolve with the
project.

This is really the only alternative we have today, but since it doesn't really
help improve policy it could be argued as not an alternative at all.

Impact on Existing APIs
-----------------------

The API for ``DocumentedRuleDefault`` or ``RuleDefault`` will be improved to
support communicating deprecated policies.

Security impact
---------------

Projects consuming this change can use it to improve security by offering more
secure default rules.

Performance Impact
------------------

None.

Configuration Impact
--------------------

No new configuration options should be required to consume or leverage this
functionality. This should be available for projects to use once they have a
version of oslo.policy that supports deprecated information in
``DocumentedRuleDefault``.

Developer Impact
----------------

Developers will not be impacted unless they are looking to improve or modify
policies for their project. If that is the case, they can use the new
functionality to describe the reason for the deprecation, when it will be
removed, and what is replacing it.

Testing Impact
--------------

We need to ensure that deprecated policies emit some sort of warning when they
are invoked. This can likely be done in oslo.policy's tests, but it can also be
done in project consuming the tests as well. One thing to discuss might be
adding a criteria that requires a unit test for deprecating a policy.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Lance Bragstad <lbragstad@gmail.com> lbragstad

Other contributors:
  None

Milestones
----------

Target Milestone for completion: queens-1

Making this available early in the Queens release will allow projects to
deprecate policies before Queens is released.

Work Items
----------

* Implement deprecated functionality in ``RuleDefault`` or
  ``DocumentedRuleDefault`` objects

Documentation Impact
====================

It is likely that many projects will use this functionality to deprecate and
improve their existing policies. The usage of these deprecated flags should be
well documented.

Dependencies
============

None.

References
==========

None.


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

