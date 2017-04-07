=================================
 Backend Drivers for oslo.config
=================================

https://blueprints.launchpad.net/oslo.config/+spec/oslo-config-drivers

Currently, oslo.config is tightly bound to the plain text
configuration files. This spec describes changes to allow deployers to
store configuration data in other places, such as secret stores
managed by castellan, by adding a driver layer to oslo.config.

Problem description
===================

Various regulations and best practices say that passwords and other
secret values should not be stored in plain text in configuration
files. There are "secret store" services to manage values that should
be kept secure. Castellan provides an abstraction API for accessing
those services. Castellan also depends on oslo.config, which means
oslo.config cannot use castellan directly.

This spec describes a new driver API for oslo.config to allow us to
(separately) write a driver in castellan that can be used when it is
installed but will not cause errors when it is missing.

Proposed change
===============

oslo.config is updated so that multiple backends can be used and the
existing INI parser is turned into one driver.

As part of initializing the ``ConfigOpts`` instance and loading
settings, all known drivers will be interrogated to determine if they
can provide one or more "sources" of data. The driver is responsible
for defining its own configuration options and interpreting them to
define a data "source".

A new configuration option ``DEFAULT.config_sources`` is added to
define sources other than those provided by ``--config-file`` and
``--config-dir`` on the command line. The value for ``config_sources``
is a list of source identifiers used to find configuration settings
for other sources. Each source identifier corresponds to a
configuration option group, which provides the details for a single
source of configuration data.

When ``ConfigOpts`` looks for an option value, it goes through the
defined sources in the order they are provided, starting with the
command line, then any configuration files, and finally the sources
loaded from ``config_sources``. The first source that provides a
configured value for an option causes the search to end (sources are
not "merged" internally).

An occurance of ``--config-dir`` will continue to be treated as a
single source, as it is now (all of the options are merged into one
namespace) using the INI file driver.

Implementation details
----------------------

When ``ConfigOpts`` is done parsing the command line options and
loading configuration files, it will iterate over the items in
``DEFAULT.config_sources``. Each string in the list value will be
interpreted as the name of an option group that defines another
configuration source. The ``driver`` setting in each group will
specify which ``oslo.config`` driver to use to load a source from the
option group using ``open_source_from_opt_group()``.

::

  def open_source_from_opt_group(self, conf, group_name):
      """Return an open option source.

      Use group_name to find the configuration settings for the new
      source then open the source and return it.

      If a source cannot be open, raise an appropriate exception.

      :param conf: The active configuration option handler from which
                   to seek configuration values.
      :type conf: ConfigOpts
      :param group_name: The configuration option group name where the
                         options for the source are stored.
      :type group_name: str
      :return: instance of subclass of ConfigurationSource
      """

Each ``ConfigurationSource`` instance is expected to retain any
information it needs to maintain a connection. Whether the connection
is long-lived or opened each time a configuration value is needed is
up to the driver.

The ``ConfigurationSource`` is not explicitly closed. If a connection
is lost, it is the responsibility of the driver to re-open it, or emit
a hard failure exception.

Each time ``ConfigOpts`` is asked for the value of an option, it will
iterate over the drivers and sources in the order they were registered
and call ``get()`` on the source, always passing an explicit group
name and option name.

::

  def get(self, group_name, option_name, opt):
      """Return the value of the option from the group.

      :param group_name: Name of the group.
      :type group_name: str
      :param option_name: Name of the option.
      :type option_name: str
      :param opt: The option definition.
      :type opt: Opt
      :return: Option value or NoValue.
      """

The source should return the value of the option, if it is present in
the data store being accessed. The return value should either match
the type for the ``Opt``, or another type such as a string that can be
coerced into the required type. The caller will perform the type
conversion in that case.

Converting complex types such as lists and dictionaries for storage is
left up to the driver to specify, though if the values need to be
encoded it would be good if that happened either as JSON or using the
same syntax that the INI files use.

If the value is not available in the data store, the source should
return ``oslo_config.drivers.NoValue``. We cannot use ``None`` as a
sentinel indicating a missing value because it may be a valid value or
default, so we use a custom singleton instead.

The opt parameter is provided in case the driver needs to do advanced
coercion (such as mapping an integer value to a choice). It should not
be used for type coercion except in special circumstances.

The driver is not responsible for handling deprecated option
names. The caller will look for a value using the current option name
then search again using the deprecated name(s) if no source has a
value under the current name.

New error classes with more generic names need to be derived from
``ConfigFilesNotFoundError`` and ``ConfigFilesPermissionDeniedError``
to be used in similar situations by the drivers.

All other errors raised from the drivers will be trapped by
``ConfigOpts`` and logged as warnings and the driver will be treated
as though it returned ``NoValue``.

Drivers will be implemented inside the oslo.config library, and loaded
through entry points managed by stevedore_ using the namespace
``oslo.config.driver``. This will allow us, for example, to add a
driver to the castellan library without introducing a circular
dependency between castellan and oslo.config.

.. _stevedore: https://docs.openstack.org/developer/stevedore/

Caching and Mutable Option Handling
-----------------------------------

The existing "mutate configuration" behavior, which allows a service
to tell oslo.config to reload the configuration file, is extended to
work with the new configuration sources.

Values retrieved from a ``ConfigurationSource`` may be cached by the
ConfigOpts instance to avoid repeated calls to a remote service (they
should *not* be cached by the driver).  When the ``ConfigOpts`` class
is told to mutate its options, it discards any cached values it holds,
as well as any open ``ConfigurationSource`` instances. It will then
load its configuration sources again, from scratch. This avoids the
need for a cache-flushing API in the ``ConfigurationSource`` class,
keeping the drivers simple.

The existing behavior for detecting changes to options not configured
as mutable is retained, as is the existing callback system for
notifying applications that options have been reloaded.

Alternatives
------------

An earlier version of this spec focused on an etcd driver for
container use cases. That problem has been solved using a different
approach.

Other backends, such as castellan, consul, zookeeper, MySQL, and etcd,
can be implemented separately without writing additional specs, unless
implementing them will require modifying the API defined for the
drivers.

There is `another proposal <https://review.openstack.org/130047>`_
that introduces a proxy interface to configuration options. However,
it does not provide any mechanism to make it configurable.

Impact on Existing APIs
-----------------------

There are no changes to the existing public API for oslo.config.

The ``ConfigurationSource`` class and the new exceptions will be added
to the API.

The behavior when oslo.config is told to "mutate" its configuration
will change, but the call to perform the mutation is the same.

Security impact
---------------

We assume that any remote access would occur over an encrypted
connection.

Performance Impact
------------------

Because configuration options can be registered by a service at any
time during operation, it may not always be possible for a driver
initialized early in the process start up to load "all" of the
settings in one call. Therefore some configuration accesses may be
slower than when reading just from an INI file. We can use caching in
the top layer in oslo.config to mitigate this impact. Drivers are free
to implement their own optimizations internally (such as fetching all
of the keys in a namespace or all of the rows from a table), but the
ability to do so is not assumed in the driver API.

Configuration Impact
--------------------

Deployers using a secret store will need to load configuration values
into their database using a native tool. The scheme for each backend
service must be documented in order for them to be able to do this.

We may want to build a tool to read an INI file and publish it to a
remote system, but that is not part of this spec and would have to be
described separately before being implemented. Deployment tools such
as Tripleo may provide their mechanism for doing this, or contribute
to doing the work through oslo.config to be shared. It is expected
that drivers will need a ``set()`` method to support uploading
configuration settings.

Below is an example using a configuration file and hypothetical secret
store set up via the config file.

The program is started using the standard ``--config-file`` option on
the command line.

.. code-block:: console

   $ app --config-file /path/to/file.conf

and the configuration file ``file.conf`` contains::

  [DEFAULT]
  config_sources = secret

  [secret]
  driver = castellan
  mapping_file = /path/to/mapping.ini

Developer Impact
----------------

Developers will not notice any difference in their use of oslo.config.

Testing Impact
--------------

We will need unit tests for the priority resolution algorithm.

We will need unit tests for the driver(s).

We will need functional tests for the driver(s).

Implementation
==============

Assignee(s)
-----------

Primary assignee:

* Samuel Pilla (spilla)

Other contributors:

* Doug Hellmann (dhellmann)

Milestones
----------

queens-3 or rocky-2

Work Items
----------

* Define the base class for a configuration driver.
* Define the ``ConfigurationSource`` base class.
* Set up the namespace for entry points for drivers.
* Define a new driver for loading configuration from simple URLs to be
  used as a test case.
* Extend ``ConfigOpts`` to load and use the drivers, as described
  above. This will add URL handling without changing the way file
  loading works.
* Update ``ConfigOpts`` to use the ``ConfigurationSource`` search
  algorithm described above in addition to its current search
  algorithm.
* Ensure that ``ConfigOpts`` only caches non-mutable values.
* Change ``mutate_config_files()`` to discard all of the existing data
  and reload it, without performing any validation. Fix tests and
  erase dead code left by rewriting that feature.

Incubation
==========

None.

Adoption
--------

TBD

Library
-------

oslo.config

Anticipated API Stabilization
-----------------------------

TBD

Documentation Impact
====================

TBD

Dependencies
============

None

References
==========

* https://etherpad.openstack.org/p/oslo.config_etcd_backend
* https://etherpad.openstack.org/p/tripleo-etcd-transition
* https://etherpad.openstack.org/p/oslo-config-pluggable-cmdb
* A `related spec`_ by Vladimir Eremin <veremin@mirantis.com>

.. _related spec: https://review.openstack.org/#/c/243114/

.. note::

  This work is licensed under a `Creative Commons Attribution 3.0
  Unported License
  <http://creativecommons.org/licenses/by/3.0/legalcode>`_.
