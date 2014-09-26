==========================================================
Add a ConfigFilter wrapper class to enforce option scoping
==========================================================

https://blueprints.launchpad.net/oslo.config/+spec/oslo-config-cfgfilter

Add a new class designed to wrap cfg.ConfigFilter, with the following use cases
in mind:

1. Help enforce that a given module does not access options registered by
   another module, without first declaring those cross-module dependencies
   using import_opt().

2. Prevent private configuration opts from being visible to modules other than
   the one which registered it.

Problem description
===================

Cross-Module Option Dependencies
--------------------------------

When using the global cfg.CONF object, it is quite common for a module to
require the existence of configuration options registered by other modules.

For example, if module 'foo' registers the 'blaa' option and the module 'bar'
uses the 'blaa' option then 'bar' might do::

  import foo

  print(CONF.blaa)

However, it's completely non-obvious why foo is being imported (is it
unused, can we remove the import) and where the 'blaa' option comes from.

The CONF.import_opt() method allows such a dependency to be explicitly
declared::

  CONF.import_opt('blaa', 'foo')
  print(CONF.blaa)

However, import_opt() has a weakness - if 'bar' imports 'foo' using the import
builtin and doesn't use import_opt() to import 'blaa', then 'blaa' can still be
used without problems. Similarly, where multiple options are registered a
module imported via import_opt(), a lazy programmer can get away with only
declaring a dependency on a single option.

Private Configuration Options
-----------------------------

Libraries which register configuration options typically do not want users of
the library API to access those configuration options. If API users do access
private configuration options, those users will be disrupted if and when a
configuration option is renamed. In other words, one does not typically wish
for the name of the private config options to be part of the public API.

For example, users of the oslo.messaging library should not be allowed to
reference configuration options (like CONF.rpc_backend) which were registered
by the library.

Proposed change
===============

Add a ConfigFilter Class
------------------------

The ConfigFilter implementation recognizes that there are two parts to a
ConfigOpts instance - the set of option schemas registered with it and raw
config values parsed from config files and the command line.

By simply ensuring that ConfigOpts has its own set of option schemas but yet
shares the parsed values (the _namespace attribute) with the underlying
ConfigOpts, we allow ConfigFilter to act as a distinct view of the underlying
parsed values.

Cross-Module Option Dependencies
--------------------------------

The ConfigFilter class will provide a way to ensure that options are not
available unless they have been registered in the module or imported using
import_opt() e.g. with::

  CONF = ConfigFilter(cfg.CONF)
  CONF.import_opt('blaa', 'foo')
  print(CONF.blaa)

no other options other than 'blaa' are available via CONF.

Private Configuration Options
-----------------------------

The ConfigFilter class will provide a way for a library to register options
such that they are not visible via the ConfigOpts instance which the API user
supplies to the library. For example::

  from __future__ import print_function

  from oslo.config.cfg import *
  from openstack.common.cfgfilter import *

  class Widget(object):

      def __init__(self, conf):
          self.conf = conf
          self._private_conf = ConfigFilter(self.conf)
          self._private_conf.register_opt(StrOpt('foo'))

      @property
      def foo(self):
          return self._private_conf.foo

  conf = ConfigOpts()
  widget = Widget(conf)
  print(widget.foo)
  print(conf.foo)  # raises NoSuchOptError

Alternatives
------------

No other way of addressing the cross-module dependencies issue was considered.

The private configuration options issue could have been addressed by making it
somewhat sane for configuration options to be part of the public API, by
providing backwards compatibility support when configuration options are
renamed or moved. This option was rejected because it seems desirable to not
expose configuration options unconditionally through the API even if this
backwards compat was available.

Impact on Existing APIs
-----------------------

There is no direct impact to the existing APIs, but ConfigFilter uses a private
implementation detail of ConfigOpts where it references ConfigOpts._namespace
and ConfigOpts._args to link ConfigFilter's ConfigOpts instance with the raw
parsed values in the wrapped ConfigOpts instances.

Security impact
---------------

None.

Performance Impact
------------------

Minimal memory impact for each ConfigFilter instance the application, along
with minimal lookup time overhead.

Configuration Impact
--------------------

None.

Developer Impact
----------------

Developers who choose to use ConfigFilter will need to change how their
configuration options are exposed to Oslo's configuration file generator since
options will not be discoverable via cfg.CONF. Instead, developers will need to
register an oslo.config.opts entry point which returns a list of the available
configuration options.

The change impacts oslo.config developers by making ConfigOpts slightly harder
to refactor later because ConfigFilter depends on its implementation details.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  markmc@redhat.com

Milestones
----------

Target Milestone for completion:
  juno-1

Work Items
----------

The work items should be straightforward - a working ConfigFilter
implementation is waiting for review in oslo-incubator. It just needs to be
moved into oslo.config with zero changes.

Incubation
==========

The cfgfilter module does exist in oslo-incubator, but there are no users yet
so it can just be removed.

Adoption
--------

oslo.messaging will most likely be the first to adopt this.

Library
-------

oslo.config.

Anticipated API Stabilization
-----------------------------

The API should be stable now.

Documentation Impact
====================

None.

Dependencies
============

None.

References
==========

* https://blueprints.launchpad.net/oslo/+spec/cfg-filter-view
* https://review.openstack.org/95676

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
