..

=============================
Policy sample file generation
=============================

https://blueprints.launchpad.net/oslo?searchtext=policy-sample-generation

It is useful to deployers to have a sample configuration file outlining all
available options, and it is a burden on projects to try to keep that sample
file up to date. It would be preferable to generate that file from policies
registered in the project in the same way that it's done for configuration
options.


Problem description
===================

Projects which provide a sample policy file need to manually keep that up to
date with what's being checked in the code. In practice it can often be out of
date. If all used policies are already registered in code that sample file
should just be generated.


Proposed change
===============

The proposal is to add a few helpers to oslo.policy. These are intended to help
deployers maintain and trim their policy files.

1. An oslo-policy-sample-generator along the same lines as the
   oslo-config-generator that exists in oslo.config. A console script
   'oslo-policy-sample-generator' will be added to oslo.policy. This script
   will look at the namespace(s) in an oslo.policy.policies entry point and
   from there load in a list of oslo_policy.policy.RuleDefault objects. The
   sample file will be generated from this list. RuleDefault objects may
   include a description string which will be included as a comment. Output
   will be in the yaml format since it can include comments.
2. A method for generating a policy file that contains the effective configured
   policy. This will merge rules defined in a policy file with registered
   default rules and output a full policy file with the result. By referencing
   this file a deployer can know exactly how a rule is set.
3. A method for retrieving a list of policies loaded from a policy file which
   match the default registered rules. These are policies that are not
   necessary to be in a policy file so this output will help deployers trim
   their file overrides.
4. A method for generating a yaml version of a policy file. This will read in
   the current policy file(s) and output a yaml version of those rules. This
   can be used to convert from a json format poliy file to yaml format. It must
   be noted that rules are not sorted so the output may not be directly
   diffable against the output of #1 or #2 above.

Files to change:

* olso_policy/generator.py (new file)
* setup.cfg (register an entry point)

Alternatives
------------

Policy sample files could continue to be maintained manually.

Impact on Existing APIs
-----------------------

A new "oslo-policy-sample-generator" console script would be registered in
setup.cfg.  This doesn't affect existing APIs, it is purely additive.

Security impact
---------------

None

Performance Impact
------------------

None. This is done outside of a service running and serving requests.

Configuration Impact
--------------------

Sample policy.yaml files can be generated. This does not affect any current
configuration, it is a tool to help those who would like to configure their
policies.

Developer Impact
----------------

Projects wishing to take advantage of this will need to register all policy
checks in order to be included in the sample file. Developers should add this
registration for existing policy checks, and register new policy checks when
they are added.

Testing Impact
--------------

There is no direct testing impact here. However this does enable other projects
to have a test job which ensure that the sample file can be generated. Details
on how this might be accomplished will be documented as part of this change.

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

* Add an oslo_policy/generator.py modeled after the one on oslo.config.
* Add policy sample generation.
* Add generation of effective policy.
* Add method for determining default rule definitions in a policy file.
* Add generation of yaml policy file from current policy file(s).
* Add an entry_point to oslo.policy setup.cfg to create a console script.
* Document how a consuming project might configure themselves to use the file
  generation ability, or setup a tox target to be used for testing.


Incubation
==========

N/A

Adoption
--------

Nova would like to use this

Library
-------

N/A

Anticipated API Stabilization
-----------------------------

N/A

Documentation Impact
====================

The ability to generate policy files will be documented in developer facing
documentation. Any deployer facing changes will be the responsibility of
consuming projects to document as they switch over to using policy
registration.

Dependencies
============

'policy-in-code' spec.

References
==========

None

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

