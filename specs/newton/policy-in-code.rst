..

==============
Policy in code
==============


https://blueprints.launchpad.net/oslo?searchtext=policy-in-code

For a while now there has been a desire to embed sane policy defaults in code
and allow for a policy file to override them. This would allow deployers to
only configure policies that they specifically want to override which could
reduce the size and complexity of those files. It would also allow for
generating a sample policy file which includes an exhaustive list of all
policies.


Problem description
===================

There are two issues being addressed here:

Given a deployed policy file it is not trivial to determine how much it differs
from the defaults that a project expects. This is due to there not being an
authoritative place to find all policies and their defaults. Some projects
provide sample files but they're not always exhaustive. And it's not easy to
diff a production policy file against the sample file after extensive
modification.

Given an authenticated request context it is not possible to determine which
policies will pass. This is because policy checks are ad hoc throughout the
code with no central registry of all possible checks. And a policy file may not
have all policies listed as some may be left to fallback to the default rule.


Proposed change
===============

The proposal is that any policy that should be checked in the code can be
registered with the Enforcer class, similar to how configuration
registration is done. A new method for policy enforcement will be added which
errors if the policy being checked has not previosly been registered. Current
methods of policy loading from a file and policy checking will not be affected.

Registration will require two pieces of data:

1. The rule name, e.g. "compute:get" or "os_compute_api:servers:index"
2. The rule, e.g. "rule:admin_or_owner" or "role:admin"

Registration will optionally take a third piece of data:

3. A description string. This can help guide admins with information on each
   policy.

The rule name is needed for later lookups. The rule is necessary in order to
set the defaults and generate a sample file. The description can be added as a
comment to policy sample files.

Registration will be done by passing a PolicyOpt class to
Enforcer.register_rule or a list of PolicyOpt's to Enforcer.register_rules.

As an example, based on how Nova might use this::

    -- nova/policy/create.py

    from oslo_policy import policy
    from nova import policy as nova_policy

    server_policies = [
        policy.PolicyOpt(rulename='os_compute_api:servers:create',
                         rule='rule:admin_or_owner',
                         description='Checked on POST /servers'),
        policy.PolicyOpt(rulename='os_compute_api:servers:create:forced_host',
                         rule='rule:admin_or_owner',
                         description='Controls whether the forced_host '
                         'scheduler hint is allowed.'),
        policy.PolicyOpt(rulename='os_compute_api:servers:create:attach_volume',
                         rule='rule:admin_or_owner',
                         description='Checks if a volume can be attached '
                         'during instance create.'),
        policy.PolicyOpt(rulename='os_compute_api:servers:create:attach_network',
                         rule='rule:admin_or_owner',
                         description='Checks if a network can be attached '
                         'during instance create.'),
    ]

    policy_engine = nova_policy.get_policy()
    # registration will error if a duplicate policy is defined
    policy_engine.register_rules(server_policies)


    -- nova/api/openstack/compute/servers.py

    from nova import policy

    policy_engine = policy.get_policy()

    def create(self, context):
        ...
        policy_engine.authorize('os_compute_api:servers:create', target, creds)
        try:
            # This would error because the policy is not registered
            policy_engine.authorize(
                'os_compute_api:servers:create_not_registered', target, creds)
        except:
            pass
        if volume_to_attach:
            policy_engine.authorize(
                'os_compute_api:servers:create:attach_volume', target, creds)


The proposed change to oslo.policy is that the Enforcer class will gain two new
methods: "register_rule" and "register_rules".  These methods will process and
store the registered policies.  The "load_rules" method will be modified to
merge rules loaded from policy files in with the registered defaults. Rules
loaded from files will overwrite registered defaults.

An "authorize" method will be updated so that attempting to check against a
rule that doesn't exist will be an error. In other words the default rule loses
its special status and is not a fallback for rules that are not defined. It
will still remain as a reference for other rules to use.

A PolicyOpt class will be added which defines a policy to be registered. It
will initially hold rulenames, rules, and descriptions.

Files to change:

* oslo_policy/policy.py

Alternatives
------------

Rather than modifying the Enforcer class in oslo_policy/policy.py a new Policy
class could be added which handles registration and contains a new "authorize"
method. The Policy class would mostly handle registration and storage of
policies and would proxy to Enforcer for loading policy from files and handling
the actual enforcement. Over time it may make sense to pull the loading of
policy from files out of the Enforcer class and into Policy.

Impact on Existing APIs
-----------------------

A new "register" method will be added to the Enforcer class.

Security impact
---------------

There is no security impact from this change. The way that policies are
enforced does not change, just where they're loaded from.

Performance Impact
------------------

Registration of policies from code will have a slight peformance at the time of
registration, but this should be no different than registering configuration
options

Configuration Impact
--------------------

There is no direct configuration impact from this change. This change will
allow projects who have registered policies to not need a policy file in order
to use those defaults. This will allow deployers to trim down, or remove, their
policy files if they are running close to the defaults.

Developer Impact
----------------

It will not be required, but it will be encouraged, that projects switch to
registering policy rules before using them. So developers will need to get in
the habit of adding that registration before use, similar to adding a new
configuration option.

Testing Impact
--------------

Unit testing should be sufficient here. This adds a new capability that can be
used by other projects but it is not directly dependent on anything.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  alaski

Other contributors:
  None

Milestones
----------

Target Milestone for completion:
  newton-1

Work Items
----------

* Add a PolicyOpt class to oslo_policy/policy.py
* Add a "register_rule" method to Enforcer for registration of rules
* Add a "register_rules" method to Enforcer for registration of rules
* Update Enforcer.load_rules() to merge registered rules with file loaded rules
* Add an "authorize" method to Enforcer which functions like "enforce" but 
  errors if the policy being checked has not been registered.

Incubation
==========

N/A

Adoption
--------

Nova would like to use this functionality.

Library
-------

N/A

Anticipated API Stabilization
-----------------------------

N/A

Documentation Impact
====================

The ability to register policy rules will be documented in developer facing
documentation. Any deployer facing changes will be the responsibility of
consuming projects to document as they switch over to using policy
registration.

Dependencies
============

None

References
==========

Nova spec for this capability: https://review.openstack.org/#/c/290155/


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

