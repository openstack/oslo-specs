=================================================
 Migrate Default Policy Format from JSON to YAML
=================================================

A combination of factors has resulted in problems with deprecating policies.
We need to make some changes in order to allow policy deprecation without
causing pain to OpenStack deployers.

Problem description
===================

There is an intersection of a few separate but related things that are causing
pain when deprecating policies:

* Packagers like to generate a sample policy for users to reference as they
  configure a service.
* oslo.policy still defaults the filename of the policy file to policy.json
  for backward compatibility reasons. This encourages packages to generate
  a JSON sample policy file, which is not what we want.
* Generating a sample policy file in JSON results in all the policy-in-code
  rules being overridden because it is not possible to comment out the default
  rules in JSON.

Because of the above, when a policy rule is deprecated in a service, users who
have a JSON sample policy file will have the new rule applied immediately on
upgrade. This does not give them a chance to deal with the change, as intended
by the deprecation mechanism in oslo.policy (which would ordinarily apply an
OR operation on the old rule and the new rule to ensure environments relying
on the old rule will continue to work).

Proposed change
===============

We want to officially deprecate JSON file format support and switch the
oslo.policy default to YAML.

In order to do this, we will need careful coordination with consumers of
oslo.policy. It is dangerous to change the default value for ``policy_file``
without making every effort to communicate the change to deployers. If a
deployer misses this change, it is possible that their custom policy may fail
to be applied, creating significant security problems.

The proposal made here is for each project to add an upgrade check that will
look for a JSON-formatted policy file and fail if one is found. Once a project
has this check in place, they can use
`set_defaults <https://opendev.org/openstack/oslo.policy/src/branch/master/oslo_policy/opts.py#L121>`_
to change the default value for ``policy_file`` to ``policy.yaml``. A release
note about the change should be added to each project as well.

To facilitate this migration, we should write a tool to migrate an existing
policy to YAML. The tool would make the format change, and it should also
comment out any rules that match the default from policy-in-code. Only rules
that have actually been customized by the deployer should be present in the
resulting file. We may be able to use the
`oslopolicy-policy-upgrade <https://opendev.org/openstack/oslo.policy/src/branch/master/oslo_policy/generator.py#L389>`_
tool to do this.

In parallel we can officially deprecate JSON format support in oslo.policy.
If we detect that a JSON file is in use for policy we should log a warning.
Support for JSON in CLI tools will also need to be deprecated.

We may also want to make existence of a JSON file a hard error on the
oslo.policy side. We could provide a flag that services can set once they have
completed their migration to YAML. If that flag is set and we find a
policy.json file that would be a fatal error and stop the service from even
starting. That would prevent us from silently opening security holes in a
deployment.

A related change that is not strictly necessary for changing the default file
format, but would further improve the deprecation process, is to add a runtime
check for redundant rules in a policy file. This would provide the same
functionality as
`oslopolicy-list-redundant <https://docs.openstack.org/oslo.policy/latest/cli/index.html#oslopolicy-list-redundant>`_.

Alternatives
------------

Leave things as they are and try to communicate better that deployers should
be using YAML. This was essentially the original plan around policy-in-code
and it has obviously not been effective.

Impact on Existing APIs
-----------------------

Support for policy files in JSON format will be deprecated.

Security impact
---------------

Policy has a significant security impact so we need to be very careful with
how we make this change. It will require coordination with Oslo consumers
to ensure we make the change in the safest way possible.

Performance Impact
------------------

None in the short term. When JSON support is removed we will be able to stop
checking for JSON formatted files which may slightly improve performance when
reading policy files.

Configuration Impact
--------------------

The default value for the ``policy_file`` option in oslo.policy will change
from ``policy.json`` to ``policy.yaml``.

Developer Impact
----------------

Each project will need an upgrade check to warn users who still have a JSON
policy file present.

Each project will need to override the ``policy_file`` default once they have
added an upgrade check.

Testing Impact
--------------

We will want to come up with a test matrix covering all the possible cases we
may encounter. For example, deployers may have:

* policy.json
* policy.yaml
* both policy.json and policy.yaml
* a JSON file at a custom path
* a YAML file at a custom path

We need to make sure to test all of those to ensure we do the right thing.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  gmann

Other contributors:
  ???

Milestones
----------

Target Milestone for completion:

Work Items
----------

* Coordinate with other projects to add upgrade checks and change the default
  for ``policy_file``.
* Provide a tool to convert existing policy files to YAML, preferrably with
  functionality to comment out any rules from the original file that match the
  default from policy-in-code.
* Once all projects have upgrade checks in place, change the default for
  ``policy_file`` in oslo.policy so all future projects will have the correct
  default.
* Deprecate JSON support in oslo.policy.
* Deprecate JSON output in policy CLI tools.

Documentation Impact
====================

Release notes to warn deployers about this will be important. Per-project
documentation advising against JSON may also be helpful. Note that the
oslo.policy docs already recommend using YAML over JSON.

Dependencies
============

We will need all projects to have upgrade checks in place in order to safely
change this default.

References
==========

`Oslo Victoria Virtual PTG Etherpad <https://etherpad.opendev.org/p/oslo-victoria-topics>`_

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

