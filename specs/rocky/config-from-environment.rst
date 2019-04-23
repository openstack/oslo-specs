
==============================
 Config Opts From Environment
==============================

https://blueprints.launchpad.net/oslo.config/+spec/config-from-environment

It is common and convenient in service management, especially container
orchestration, to manage configuration settings using environment variables set
by the controlling environment. This allows the service being managed to avoid
extraneous files and other artifacts, allowing service immutability and thus
straightforward elasticity. This specification proposes using the new
`drivers`_ functionality provided by ``oslo.config`` to automatically support
overriding or setting configuration from environment variables with standard
and predictable names.

Problem description
===================

A common way to pass instance specific settings to a container is to use
shell environment variables. For example, in docker::

    docker run -t -p 127.0.0.1:8081:80 \
      -e "DB_SYNC=True" \
      -e "AUTH_STRATEGY=noauth2" \
      myservice

or in a (fragment of a) Kubernetes deployment::

    spec:
      containers:
        - name: myservice
          image: myservice
          env:
            - name: DB_SYNC
              value: "True"
            - name: AUTH_STRATEGY
              value: noauth2
          ports:
          - containerPort: 80

In OpenStack these settings are usually managed by config files read by
``oslo.config`` into instances of ``ConfigOpts`` classes. At this time there is
no unified way to use environment variables for these settings, meaning that in
many cases if a deployer would like to run an OpenStack service in a container,
they must provide a configuration file for that container, or provide some way
for the service to gather configuration at run time.

The `drivers`_ functionality being developed for ``oslo.config`` provides one
model for that run time configuration, but does not specifically address
the case of using simple environment variables.


Proposed change
===============

The spec proposes using the drivers model to create a ``ConfigurationSource``
for ``oslo.config`` that looks to the running environment for variables that
match expected names for registered configuration settings. The source will be
available by default, ideally coming second in the stack, after individual
command line overrides, but before any files or other sources. If this proves
impossible because of inter-dependencies in the file and command line handling,
first in the stack is the second-best option.

The ``ConfigurationSource`` will translate config option names to candidate
variable names. If those variables are set in the local environment (a member
of ``os.environ`` in Python) the values will be returned. If they are not set,
further processing of other sources will proceed.

There are two main challenges with this proposal. Resolving them in a
satisfactory fashion is why this spec is being written. They are:

#. Determining a satisfactory scheme for translating configuration option names
   to environment variable names in a way that is both predictable for humans
   and highly unlikely to collide with variable names that might otherwise be
   used. A strawman proposal is as follows:

   #. Prefix each variable with ``OS_``
   #. Followed by the group: ``DEFAULT``
   #. Separated from the name by a double-under ``__`` (to allow unders in the
      group)
   #. Followed by the name, resulting in something like:
      ``OS_PLACEMENT_DATABASE__CONNECTION``

   This will result in quite long names in some cases, but that's likely going
   to be the case with any solution that satisfies both requirements. Note that
   this format can be transformed in both directions: from option group and
   name to environment variable name and vice versa.

#. Individual options in a ``ConfigOpts`` have types. Environment variables, on
   the other hand, are strings. We either need to establish a way of coercing
   string-based representations of non-string types to the desired type
   (`keystonemiddleware`_ has some code that does some of this) or we perhaps
   initially only support ``StrOpt``.

Here is a contrived example that describes two options which have similar names
that demonstrates the importance of group handling. Configuration items as
follows::

    [placement]
    database_connection = foo

    [placement_database]
    connection = bar

would result in two environment variables ``OS_PLACEMENT__DATABASE_CONNECTION``
and ``OS_PLACEMENT_DATABASE__CONNECTION``.

Alternatives
------------

This is not something that has to be done in ``oslo.config``. Individual
services could manage their own environment checking, but that's not really
in keeping with the oslo principles nor the consistency goals of OpenStack.

In some circumstances an ``Opt`` could set a default that reads from the
environment using ``default=os.environ.get('SOMETHING')`` but this has a
critical disadvantage: The environment variable is only used if the option is
not already set in the configuration. Ideally the environment variable should
override configuration.

Another way to do this would be to add another parameter to ``Opt`` named
``envvar``. If set, the value would be used to override the automatically
generated environment variable name (as described above). This is considered
undesirable as it made lead to published inconsistencies in variable naming.


Impact on Existing APIs
-----------------------

See above.

Security impact
---------------

There's a slim chance that service behavior could change if pre-existing
environment variables are present that happen to match the naming scheme
described here.

Performance Impact
------------------

No significant performance impact is expected. Querying the environment is
quick and the querying is done as needed, not for all possible configuration
values.

Configuration Impact
--------------------

No new options will be added when registering options. Support for environment
variable-based overrides will be automatic.

Developer Impact
----------------

Developers will have an additional customization option available.

Testing Impact
--------------

Additional unit tests will be required to cover the added functionality.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  cdent

Other contributors:
  volunteers?

Milestones
----------

..TODO(cdent): figure this out

Work Items
----------

* Implement the new ``ConfigurationSource`` driver.
* Integrate it as a default driver.
* Update documentation.
* Update the sample configuration generator to include the variable names.
* Update the documentation generator to include the variable names.


Incubation
==========

N/A

Documentation Impact
====================

The documentation will need to be updated to indicate that each option can be
overridden with an environment variable and to describe how the name of the
variable will be generated.

Dependencies
============

This implementation is dependent on the emerging `drivers`_ functionality in
``oslo.config``.

References
==========

* Backend Drivers for oslo.config:
  `<http://specs.openstack.org/openstack/oslo-specs/specs/queens/oslo-config-drivers.html>`_
* Keystone Middleware option type coercing:
  `<https://opendev.org/openstack/keystonemiddleware/src/branch/stable/rocky/keystonemiddleware/_common/config.py>`_

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

.. _drivers: http://specs.openstack.org/openstack/oslo-specs/specs/queens/oslo-config-drivers.html
.. _keystonemiddleware: https://opendev.org/openstack/keystonemiddleware/src/branch/stable/rocky/keystonemiddleware/_common/config.py
