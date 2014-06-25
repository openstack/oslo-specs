=====================
oslo-config-generator
=====================

https://blueprints.launchpad.net/oslo/+spec/oslo-config-generator

Add a command line utility for generating sample config files to
oslo.config which will replace the generator utility in
oslo-incubator.

Problem description
===================

The need for such a utility is well understood:

* A sample config file containing the list of all available config
  options, the associated help text, type and commented out default
  value makes it much easier for operators to discover and understand
  config options.

* It needs to be possible for operators to run the tool themselves
  rather than attempting to maintain these auto-generated files in
  git.

The issues with the current tool include:

* Loading modules and expecting them to register their options with
  cfg.CONF is slow, weird, and error prone.

* This reliance on cfg.CONF perpetuates the use of a global object.

* The generator doesn't have information about which groups an option
  belongs to so it resorts to guessing - this probably has resulted in
  people avoiding adding a 'debug' option in multiple groups, for
  example.

* It's impossible to to handle "split configs" - i.e. some config
  options only make sense in glance-api.conf and others only make
  sense in glance-registry.conf - because the generator has no
  information on to decide which service an option is used by.

* We already have a pattern of explicitly registering config options
  under the oslo.config.opts entry point namespace, but it's not
  used outside oslo.messaging right now.

Proposed change
===============

We will add a sample config file generator utility called
oslo-config-generator to the oslo.config package.

This new utility will take a dramatically different approach to
discovery from the current generator in oslo-incubator, whereby we
move away from magic towards much more explicit control over the
options the generator sees.

To generate a sample config file for oslo.messaging you would run::

  $> oslo-config-generator --namespace oslo.messaging > oslo.messaging.conf

This generated sample lists all of the available options, along with their help
string, type, deprecated aliases and defaults.

The --namespace option specifies an entry point name registered under the
'oslo.config.opts' entry point namespace. For example, in oslo.messaging's
setup.cfg we have::

  [entry_points]
  oslo.config.opts =
      oslo.messaging = oslo.messaging.opts:list_opts

The callable referenced by the entry point should take no arguments and return
a list of (group_name, [opt_1, opt_2]) tuples. For example::

  opts = [
      cfg.StrOpt('foo'),
      cfg.StrOpt('bar'),
  ]

  cfg.CONF.register_opts(opts, group='blaa')

  def list_opts():
      return [('blaa', opts)]

You might choose to return a copy of the options so that the return value can't
be modified for nefarious purposes::

  def list_opts():
      return [('blaa', copy.deepcopy(opts))]

A single codebase might have multiple programs, each of which use a subset of
the total set of options registered by the codebase. In that case, you can
register multiple entry points::

  [entry_points]
  oslo.config.opts =
      nova.common = nova.config:list_common_opts
      nova.api = nova.config:list_api_opts
      nova.compute = nova.config:list_compute_opts

and generate a config file specific to each program::

  $> oslo-config-generator --namespace oslo.messaging \
                           --namespace nova.common \
                           --namespace nova.api > nova-api.conf
  $> oslo-config-generator --namespace oslo.messaging \
                           --namespace nova.common \
                           --namespace nova.compute > nova-compute.conf

To make this more convenient, you can use config files to describe your config
files::

  $> cat > config-generator/api.conf <<EOF
  [DEFAULT]
  output_file = etc/nova/nova-api.conf
  namespace = oslo.messaging
  namespace = nova.common
  namespace = nova.api
  EOF
  $> cat > config-generator/compute.conf <<EOF
  [DEFAULT]
  output_file = etc/nova/nova-compute.conf
  namespace = oslo.messaging
  namespace = nova.compute
  namespace = nova.compute
  EOF
  $> oslo-config-generator --config-file config-generator/api.conf
  $> oslo-config-generator --config-file config-generator/compute.conf

The default runtime values of configuration options are not always the most
suitable values to include in sample config files - for example, rather than
including the IP address or hostname of the machine where the config file
was generated, you might want to include something like '10.0.0.1'. To
facilitate this, options can be supplied with a 'sample_default' attribute::

  cfg.StrOpt('base_dir'
             default=os.getcwd(),
             sample_default='/usr/lib/myapp')

Alternatives
------------

The alternative would be to stick with the current generator's
automagic option discovery approach and attempt to work around its
deficiencies. This has been the path we've been on for quite some
time, but has been a constant source of frustration.

Impact on Existing APIs
-----------------------

The generator is primarily intended to be used via the
oslo-config-generator command line interface, but it is also available
via a public generate(conf) API. There is also a
register_cli_opts(conf) API so that callers to generate() can set
config options beforehand.

Security impact
---------------

There is no security impact.

Performance Impact
------------------

The generator completes more quickly because it has to load less
modules in order to discover options.

Configuration Impact
--------------------

No configuration impact.

Developer Impact
----------------

The explicit approach of advertising configuration options means that
developers will need to manually maintain a list of the config options
available in their code so it can be returned by the callable
registered as a oslo.config.opts entry point.

This shouldn't be a huge burden because it typically is a list which
references existing lists of options.

However, some sort of automated assistance to help catch cases where
the list needs updating would be hugely helpful. How exactly that will
work remains to be seen.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  markmc

Other contributors:
  None

Milestones
----------

juno-2

Work Items
----------

* Add oslo-config-generator to oslo.config.
* Advertise the keystone auth_token options under oslo.config.opts.
* Demonstrate how services like Nova, Ceilometer, Glance or Heat can
  adopt this new utility.
* Remove the old generator from oslo-incubator.
* Set up infra jobs to publish sample config files somewhere like
  docs.openstack.org.
* Consider adding something like 'python setup.py sample_config'.

Incubation
==========

The new utility replaces the one in oslo-incubator.

Adoption
--------

All applications are expected to adopt it.

Library
-------

oslo.config.

Note this means that oslo.config gains a dependency on stevedore.

Anticipated API Stabilization
-----------------------------

The API is pretty minimal and is expected to be stable from the time
it is merged.

Documentation Impact
====================

The operators guide would benefit from instructions on how to use the utility.

Dependencies
============

None.

References
==========

* https://blueprints.launchpad.net/oslo/+spec/oslo-config-generator
* https://bugs.launchpad.net/oslo/+bug/1300546
* http://lists.openstack.org/pipermail/openstack-dev/2014-June/thread.html#37954

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

