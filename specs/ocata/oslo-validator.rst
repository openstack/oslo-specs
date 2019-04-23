==========================
 Configuration Validator
==========================

https://blueprints.launchpad.net/oslo.config/+spec/oslo-validator

Support the ability to validate oslo.config options at a basic level
against an operator configuration file, as-well-as potentially validation
of options on service start(example usage).

Problem description
===================

It is extremely easy to have invalid conf files for any project:

* Invalid Sections
* Invalid Option Name
* Deprecated Options
* Misspellings
* Usage of Advanced Options (warnings)
* Lack of Configured Required Options
* Usage of Choices Outside of Scope
* Usage of Default Values in Configuration File

Configuration validation, in its basic form, can help alleviate these basic
issues by providing a way to validate options and configured values both
manually, via cli, and on service start(example usage).  Operators have been
asking for this functionality for some time now, as the deviation from version
to version, with regard to options, can be substantial.

Use Cases
---------

As an operator, being able to validate the configuration prior to deployment
is invaluable, providing a clear path for both CI/CD utilization and manual
checks.

As a developer, being able to provide an option to operators for basic
validation against project configuration files.  This can be by way of shell
script traversing each namespace, as Neutron utilizes, or it could be by way of
an additional argument specific for config validation, i.e. `ironic-api
--validate-config`.  Implementation is customizable per project.


Proposed change
===============

The new validator module would offer two avenues for consumption: cli
command and the ability to import the validator for use during service
start(example usage).  Oslo config validator would be a basic check on
common configuration mistakes and in no way offers an opinion on a correct
configuration or a desired configuration.

For cli usage, a new entry point will be added to oslo.config,
`oslo-config-validator`.  Similar to `oslo-config-generator`, operators will
be able to pass an argument, `--namespace`, to indicate what application
namespace their configuration file will validate against.  Or, optionally an
operator/developer can pass `--validator-config-file`, which would contain the
application namespaces. In addition, `--config-file` will be a required
argument to indicate the location of their configuration file. Ideally, each
project would implement a shell script tool to traverse the namespaces used
by the project for validation.  For example, here is the usage in Neutron:
neutron/blob/master/tools/generate_config_file_samples.sh

For module import, developers will be able to utilize `validator.validate`
and pass a required collection of configured options to check against the
registered namespaces and options in `oslo.config`.  This could be
performed on service start(example usage), after configuration files are
ingested, and output to the configured log file.  It could be also used
in each project as an additional argument, i.e. `ironic-api --validate-config`,
where the configuration is then validated as a separate operation, if a shell
script is not developed above.  Both options would be available, how each
project implements config validation is out of the scope of this spec.

One use case for `validator.validate` would be to fail on service start, where
`validate` returns `valid_configuration(bool)`, `invalid_configuration_items(dict)`.
The return values can help determine if the service is capable of starting by
examining `invalid_configuration_items['errors'] (bool)` if `valid_configuration`
is `false`.  This would allow developers to have control over warnings being
suppressed by having `invalid_configuration_items['errors'] (bool)` and
`invalid_configuration_items['warnings'] (bool)` separate with their own
respective iterable list of items considered in error::

    invalid_configuration_items['config_errors'] = [
        {'config_item': 'namespace', 'item_name': 'DEFULT',
         'message': 'Namespace DEFULT does not exist.'},
        {'config_item': 'option', 'item_name': 'auth_uri',
         'message': 'Option auth_uri has no value assigned.'},
    ]

And for configuration warnings::

    invalid_configuration_items['config_warnings'] = [
        {'config_item': 'option', 'item_name': 'auth_strategy',
         'message': 'Option is configured with the default value, not required.'},
        {'config_item': 'option', 'item_name': 'some_advanced_option',
         'message': 'Option some_advanced_option is an advanced option and may'
                    'effect performance.'},
    ]

These are just examples of data structures potentially being returned and
may change when configuration validator is implemented.  In any case, a list of
errors/warnings will be returned for easy output to console or logs.

Configuration validator would report on the following discrepancies:

* Option not in namespace (error)
* Option has no value (error)
* Option has no value and is required (error)
* Option value is not in range (error)
* Option value is default, not required in config (warning)
* Option is deprecated (warning)
* Option is advanced (warning)
* Option type validation, i.e. '2' vs 2 (error)
* Invalid configuration section (error)
* Missing configuration section, i.e. [DEFAULT] (warning)

Files to add:

* oslo.config/oslo_config/validator.py
* oslo.config/doc/source/validator.rst

Files to modify:

* oslo.config/setup.cfg

Alternatives
------------

None.

Impact on Existing APIs
-----------------------

None.

Security impact
---------------

None.

Performance Impact
------------------

This could be an additional check on service start(example usage), which could
have an impact on the time it would take to become fully operational.  At its
most basic form, manual checks via cli would not have a performance impact.

Configuration Impact
--------------------

None.

Developer Impact
----------------

None.

Testing Impact
--------------

Additional unit tests would be required to cover raised warnings and
errors provided by validator.

Implementation
==============

Assignee(s)
-----------
Primary assignee:
  ski

Milestones
----------

Target Milestone for completion:
  ocata-1

Work Items
----------

* Create new module `validator.py`.
* Create new entrypoint `oslo-config-validator`.
* Create new docs file `validator.rst`

Incubation
==========

None.

Adoption
--------

It is likely that this module will be used throughout OpenStack as it satisfies
operator need surrounding the complexity of configuration files.

Library
-------

oslo.config

Anticipated API Stabilization
-----------------------------

None.

Documentation Impact
====================

Will need to develop additional documentation in `validator.rst` to detail how
validator can be consumed both at the cli level and as a module.

Dependencies
============

This additional module will not require any dependencies.

References
==========

oslo.config: https://docs.openstack.org/oslo.config/latest/

neutron: https://docs.openstack.org/neutron/latest/

ironic: https://docs.openstack.org/ironic/latest/

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
