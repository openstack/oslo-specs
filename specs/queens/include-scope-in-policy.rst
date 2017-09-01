===================
Add Scope to Policy
===================

https://blueprints.launchpad.net/oslo?searchtext=add-scope-to-policy

This specification details the benefits and outlines the work required to
extend oslo.policy to include a scope attribute.


Problem description
===================

There are several initiatives underway to make consuming and understanding role
based access control (RBAC) easier for developers and deployers.

The first is a community-wide `goal
<https://governance.openstack.org/tc/goals/queens/policy-in-code.html>`_ to
register all policies into code and treat them like we we treat configuration.
This has numerous benefits for deployers and eases maintenance, especially
upgrades.

The second is the ability to introduce a scope that fits naturally with
system-level policies or operations. The main idea here is that today
OpenStack's Identity service allows users to get authorization on the domain
and project levels.  This makes a lot of sense when dealing with APIs that act
on resources owned by projects or domains. When dealing with operations above
project scope (e.g. modifying endpoints or listing hypervisors), it gets
harder to repurpose project or even domain scope for these actions. This
usually leads to end-user and deployer confusion. In addition to confusion, it
makes it really hard for operators to properly isolate project operations from
system operations (see `bug 968696 <https://bugs.launchpad.net/keystone/+bug/968696>`_).
As a result, there is work to introduce elevated scopes in OpenStack that make
the solution to the problem a little easier to understand and implement. For
more information on the actual approach, please see the related Identity
specifications:

* `A roadmap for improving security through policy <https://review.openstack.org/#/c/462733/>`_
* `Specification for system-level scope <https://review.openstack.org/#/c/464763/>`_

If the above approaches are accepted, documenting the scope of each operation
in a project will be required. We can leverage the oslo.policy library to do
this since the community already leans on the library to document and register
default policies in code.

Use Cases
---------

As an operator, I need to understand at which level an operation is applied.

As a developer, I want to enforce the scope for a specific operation through
code.

Proposed change
===============

The oslo.policy library currently has a ``DocumentedRuleDefault`` object that
is used to register policy in code and document it. We can extend this object
to support an additional attribute that denotes the scope of the operation.
Consider the following two examples::

    from oslo_policy import policy

    ...

    policy.DocumentedRuleDefault(
        name=SERVERS % 'create',
        check_str=RULE_ADMIN_OR_OWNER,
        description='Create a server.',
        operations=[
            {'method': 'POST',
             'path': '/servers'}
        ]
    )

    ...


    policy.DocumentedRuleDefault(
        name=base.IDENTITY % 'create_user',
        check_str=base.RULE_ADMIN_REQUIRED,
        description='Create a user.',
        operations=[
            {'method': 'POST',
             'path': '/v3/users'}
        ]
    )

Both rules are descriptive in what they do, but they don't include the scope at
which they are intended to operate. Instances must belong to a project and user
can exist globally or within a specific domain. The following representations
are better because they are easier to understand and they help enforce
necessary scope during policy enforcement::

    from oslo_policy import policy

    ...

    policy.DocumentedRuleDefault(
        name=SERVERS % 'create',
        scope_type=['project'],
        check_str=RULE_ADMIN_OR_OWNER,
        description='Create a server.',
        operations=[
            {'method': 'POST',
             'path': '/servers'}
        ]
    )

    ...


    policy.DocumentedRuleDefault(
        name=base.IDENTITY % 'create_user',
        scope_type=['system', 'project'],
        check_str=base.RULE_ADMIN_REQUIRED,
        description='Create a user.',
        operations=[
            {'method': 'POST',
             'path': '/v3/users'}
        ]
    )

The ``scope_type`` attribute of policy can then be generated in sample policy
files with the existing ``description`` making it even more helpful for
deployers that need to understand policy. It can also be available during the
policy enforcement of an operation at runtime. This makes it easier for
oslo.policy enforcement to ensure the operation being performed matches the
scope of the authorization context of the token. For example, comparing the
``scope_type`` of the policy operation against the role on the token's scope
should help solve `admin-ness issues <https://bugs.launchpad.net/keystone/+bug/968696>`_
across OpenStack.

Alternatives
------------

We can document the scope of operations outside of the project, but doing it
in-code with policy registration makes the approach less error-prone.

Impact on Existing APIs
-----------------------

This will make the ``DocumentedRuleDefault`` object more useful in documenting
and evaluating policy. The changes described here are additive only and should
not impact existing functionality of the object.

Security impact
---------------

Directly, there are no security implications of this. Down the road, after
projects start using the attribute to evaluate policy, security will improve.
See the previously linked `Identity specification
<https://review.openstack.org/#/c/462733/>`_ for details.

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

We should test that scope is actually advertised and set on policies. We should
also loop-in the `Patrole team <https://docs.openstack.org/patrole/latest/>`_
to see how this can improve testing of RBAC across OpenStack.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Lance Bragstad <lbragstad@gmail.com> lbragstad

Milestones
----------

Target Milestone for completion: queens-1

Making this available early in the Queens release will allow projects to supply
scope documentation through automated docs.

Work Items
----------

* Extend the ``DocumentedRuleDefault`` object to support a ``scope`` attribute

Documentation Impact
====================

This functionality will need extensive documentation and usage guides
describing how it improves policy documentation and evaluation.

Dependencies
============

Projects must move policy into code and document it before associating scope to
specific policies. Keystone will also need to provide a way for users to get
system-scoped tokens. After that, projects can start enforcing policy scope by
comparing it to the token scope, but most of that will be handled automatically
by oslo.policy's ``Enforcer`` object.

References
==========

None.


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

