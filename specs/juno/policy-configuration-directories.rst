========================================
Support Policy configuration directories
========================================

https://blueprints.launchpad.net/oslo-incubator/+spec/policy-configuration-directories

This propose to add a way to override the default policy rules.

Problem description
===================

There some complain about policy configuration is hard to use. So think of
there isn't a way to override default policy rule. The only way to modify
default policy rule is to edit the policy.conf. This isn't convenient for
deployer.

Proposed change
===============

Proposed to support for policy configuration directories. The policy rules
that loaded from policy configuration directories will override the default
policy rules from 'policy_file'.

Add new configuration option:

cfg.ListOpt('policy_configuration_directories', default=['policy.d'],
            help=_('The directories of policy configuration files'))

'policy_configuration_directories' accept a list of directories. Those
directories will be iterated by order. The files in those directories will be
loaded by alphabet order, and the rules will be overrided by that order. The
sub-directories will be ignore.

If the directory in the policy_configuration_directories isn't existed, there
will be error raised when loading policy.

Alternatives
------------

None

Impact on Existing APIs
-----------------------

None

Security impact
---------------

The policy rules will be loaded from specified directories. If those
directories have appropriate permissions, there won't have any security issue.

The permissions suggest only the admin can read and write the policy
configurations directories and files. And openstack program can read those
directories and files is enough.

Performance Impact
------------------

This change need iterated a list of directories, that will slow down the
init/reload of policy rules.

Configuration Impact
--------------------

This change introduce new configuration option:
policy_definition_path = [list of directories]

The option is convenient for deployer change where to store the policy config
files. The default value is 'policy.d'. The location searching will be same with
option 'policy_file'.

Developer Impact
----------------

When developer add this feature into app, developer need to add UpgradeImpact
flags and upgrade docs to notice deployer to create 'policy.d' directory in
his development, otherwise there will be error raised by 'policy.d' can't be
found.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Alex Xu (xuhj@linux.vnet.ibm.com)

Milestones
----------

Target Milestone for completion: Juno-3

Work Items
----------

This change only need one single patch.
This will be implemented in
oslo-incubator/openstack/common/policy.py:Enforcer

Enforcer.load_rules will scan the policy configuration directories, and load
them to override the rules by order.

Incubation
==========

None

Adoption
--------

Nova will use this to improvement the configuration of policy rules. But this
feature can be used by most of openstack project that support policy rules.

Library
-------

None

Anticipated API Stabilization
-----------------------------

None

Documentation Impact
====================

The new option should be documented at configuration documents.
http://docs.openstack.org/icehouse/config-reference/content

And we should describe how to write policies to explain how multiple policy
files are combined to build up the full set of rules.

Dependencies
============

None

References
==========

https://etherpad.openstack.org/p/juno-nova-devops

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

