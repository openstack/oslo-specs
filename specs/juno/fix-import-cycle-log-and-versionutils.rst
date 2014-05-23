===================================================
 Fix the Import Cycle Between log and versionutils
===================================================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/oslo/+spec/fix-import-cycle-log-and-versionutils

Break the import cycle so we can release oslo.log.

Problem description
===================

There is a circular dependency between versionutils and the logging
code, which are slated to be released in separate libraries. We need
to break the cycle to allow oslo.log to graduate this cycle.

Proposed change
===============

Move the :meth:`ContextAdapter.deprecated` method to a function in
versionutils with the other deprecation-related code. That means
moving the ``fatal_deprecations`` configuration option, and updating
all callers.

The proposed function signature is:

::

   # versionutils.py

   def deprecation_warning(msg, *args, **kwds):
       """Call this function when a deprecated feature is used.

        If the system is configured for fatal deprecations then the message
        is logged at the 'critical' level and :class:`DeprecatedConfig` will
        be raised.

        Otherwise, the message will be logged (once) at the 'warn' level.

        :raises: :class:`DeprecatedConfig` if the system is configured for
                 fatal deprecations.

        """

To maintain the current logging behavior, :func:`deprecation_warning`
will look up the stack one level to get the module name, ask for the
logger with that name, and then use it to emit the message (instead of
having a single logger with the name of the versionutils module).

Move ``fatal_deprecations`` out of the default option group to the
``deprecation`` group, with appropriate deprecation settings to honor
the old name if it is found.

Update :func:`versionutils.deprecated` to call
:func:`deprecation_warning` instead of ``LOG.deprecated()``.

Alternatives
------------

1. Change the implementation of the deprecated() decorator in
   versionutils to not call LOG.deprecated(). That might mean
   duplicating the logic from LOG.deprecated().

2. Move most of the body of LOG.deprecated() to versionutils but
   keep the method. This limits the number of changes we have to make
   in the callers, but means that oslo.log depends on
   oslo.versionutils. We can eliminate the circular dependency by
   having the function in versionutils use python's standard logger
   instead of oslo.log.  This seems to be in keeping with the API
   changes for oslo.log above.

Both alternative solutions fix the cycle, but require that we keep
LOG.deprecated() and our special ContextAdapter. We are trying to
remove that class in another blueprint related to graduating oslo.log.

Impact on Existing APIs
-----------------------

Callers of LOG.deprecated() will need to be updated to use
:func:`versionutils.deprecation_warning` instead.

For backwards compatibility and slow adopters, we will keep
ContextAdapter.deprecated() in the log setup code in the incubator but
it will be removed from ``oslo.log`` when that module graduates.

Security impact
---------------

None

Performance Impact
------------------

None

Configuration Impact
--------------------

Move ``fatal_deprecations`` out of the default option group to the
``versionutils`` group.

Developer Impact
----------------

The API for reporting deprecated code and features will be moving to a
new place, so we will need to publicize the change. The apps can be
updated when syncing changes to the logging and versionutils code from
the incubator.

Most callers use the :func:`deprecated` decorator instead anyway.

Calls to update:

::

   oslo-incubator/tests/unit/test_deprecated.py
   38:    def test_deprecated(self):
   39:        LOG.deprecated('test')
   54:        LOG.deprecated('only once!')
   55:        LOG.deprecated('only once!')
   56:        LOG.deprecated('only once!')
   65:        LOG.deprecated(msg1)
   66:        LOG.deprecated(msg2)
   67:        LOG.deprecated(msg1)
   68:        LOG.deprecated(msg1)
   69:        LOG.deprecated(msg2)
   70:        LOG.deprecated(msg2)
   83:        LOG.deprecated('only once! %s', 'arg1')
   84:        LOG.deprecated('only once! %s', 'arg1')
   85:        LOG.deprecated('only once! %s', 'arg2')
   86:        LOG.deprecated('only once! %s', 'arg2')
   108:        LOG.deprecated(msg_fmt_1, msg_fmt_1_arg_1)
   109:        LOG.deprecated(msg_fmt_1, msg_fmt_1_arg_2)  # logged: args different
   110:        LOG.deprecated(msg_fmt_1, msg_fmt_1_arg_1)  # no log: same msg+args
   112:        LOG.deprecated(msg_fmt_2, msg_fmt_2_arg_1)
   113:        LOG.deprecated(msg_fmt_2, *msg_fmt_2_arg_2)  # logged: args different
   114:        LOG.deprecated(msg_fmt_2, *msg_fmt_2_arg_3)  # logged: args different
   115:        LOG.deprecated(msg_fmt_2, *msg_fmt_2_arg_3)  # no log: same msg+args
   116:        LOG.deprecated(msg_fmt_2, *msg_fmt_2_arg_2)  # no log: same msg+args

   cinder/cinder/api/contrib/services.py
   91:            LOG.deprecated(_("Query by service parameter is deprecated. "

   cinder/cinder/quota.py
   106:                LOG.deprecated(_("Default quota for resource: %(res)s is set "

   cinder/cinder/scheduler/manager.py
   66:            LOG.deprecated(_('ChanceScheduler and SimpleScheduler have been '

   neutron/neutron/plugins/vmware/nsx_cluster.py
   49:            LOG.deprecated(_("Attribute '%s' has been deprecated or moved "

   neutron/neutron/agent/common/config.py
   104:        LOG.deprecated(_('DEFAULT.root_helper is deprecated! Please move '

   glance/glance/store/__init__.py
   200:                LOG.deprecated(_("%s not found in `known_store`. "


Searching for uses:

::

   $ ack --ignore-dir=.tox --ignore-dir=build --ignore-dir=.venv \
   --ignore-dir=.update-venv --ignore-dir=openstack 'deprecated\('

   python-keystoneclient/keystoneclient/tests/test_discovery.py
   673:    def test_allow_deprecated(self):

   python-keystoneclient/keystoneclient/tests/test_http.py
   136:    def test_client_deprecated(self):

   keystone/keystone/catalog/backends/templated.py
   128:@versionutils.deprecated(

   keystone/keystone/contrib/stats/core.py
   130:    @versionutils.deprecated(

   keystone/keystone/contrib/access/core.py
   35:    @versionutils.deprecated(

   keystone/keystone/middleware/s3_token.py
   50:    @versionutils.deprecated(

   keystone/keystone/middleware/core.py
   148:    @versionutils.deprecated(

   keystone/keystone/auth/plugins/external.py
   102:    @versionutils.deprecated(
   113:    @versionutils.deprecated(
   130:    @versionutils.deprecated(
   151:    @versionutils.deprecated(

   keystone/keystone/token/core.py
   263:    @versionutils.deprecated(versionutils.deprecated.ICEHOUSE, remove_in=+1)

   keystone/keystone/common/controller.py
   33:def v2_deprecated(f):
   42:        v2_deprecated = versionutils.deprecated(

   keystone/keystone/common/kvs/legacy.py
   49:    @versionutils.deprecated(versionutils.deprecated.ICEHOUSE,

   keystone/vendor/python-keystoneclient-master/keystoneclient/tests/test_http.py
   136:    def test_client_deprecated(self):

   oslo-incubator/tests/unit/test_versionutils.py
   24:    def assert_deprecated(self, mock_log, **expected_details):
   35:        @versionutils.deprecated(as_of=versionutils.deprecated.ICEHOUSE)
   48:            @versionutils.deprecated(as_of=versionutils.deprecated.ICEHOUSE)
   59:        @versionutils.deprecated(as_of=versionutils.deprecated.ICEHOUSE,
   66:        self.assert_deprecated(mock_log,
   75:        @versionutils.deprecated(as_of=versionutils.deprecated.GRIZZLY,
   82:        self.assert_deprecated(mock_log,
   91:        @versionutils.deprecated(as_of=versionutils.deprecated.GRIZZLY)
   97:        self.assert_deprecated(mock_log,
   105:        @versionutils.deprecated(as_of=versionutils.deprecated.GRIZZLY,
   113:        self.assert_deprecated(mock_log,
   122:        @versionutils.deprecated(as_of=versionutils.deprecated.GRIZZLY,
   129:        self.assert_deprecated(mock_log,
   137:        @versionutils.deprecated(as_of=versionutils.deprecated.GRIZZLY,
   144:        self.assert_deprecated(mock_log,

   oslo-incubator/tests/unit/test_log.py
   600:    def test_logfile_deprecated(self):
   610:    def test_logdir_deprecated(self):

   oslo-incubator/tests/unit/test_deprecated.py
   38:    def test_deprecated(self):
   39:        LOG.deprecated('test')
   54:        LOG.deprecated('only once!')
   55:        LOG.deprecated('only once!')
   56:        LOG.deprecated('only once!')
   65:        LOG.deprecated(msg1)
   66:        LOG.deprecated(msg2)
   67:        LOG.deprecated(msg1)
   68:        LOG.deprecated(msg1)
   69:        LOG.deprecated(msg2)
   70:        LOG.deprecated(msg2)
   83:        LOG.deprecated('only once! %s', 'arg1')
   84:        LOG.deprecated('only once! %s', 'arg1')
   85:        LOG.deprecated('only once! %s', 'arg2')
   86:        LOG.deprecated('only once! %s', 'arg2')
   108:        LOG.deprecated(msg_fmt_1, msg_fmt_1_arg_1)
   109:        LOG.deprecated(msg_fmt_1, msg_fmt_1_arg_2)  # logged: args different
   110:        LOG.deprecated(msg_fmt_1, msg_fmt_1_arg_1)  # no log: same msg+args
   112:        LOG.deprecated(msg_fmt_2, msg_fmt_2_arg_1)
   113:        LOG.deprecated(msg_fmt_2, *msg_fmt_2_arg_2)  # logged: args different
   114:        LOG.deprecated(msg_fmt_2, *msg_fmt_2_arg_3)  # logged: args different
   115:        LOG.deprecated(msg_fmt_2, *msg_fmt_2_arg_3)  # no log: same msg+args
   116:        LOG.deprecated(msg_fmt_2, *msg_fmt_2_arg_2)  # no log: same msg+args

   cinder/cinder/api/contrib/services.py
   91:            LOG.deprecated(_("Query by service parameter is deprecated. "

   cinder/cinder/quota.py
   106:                LOG.deprecated(_("Default quota for resource: %(res)s is set "

   cinder/cinder/scheduler/manager.py
   66:            LOG.deprecated(_('ChanceScheduler and SimpleScheduler have been '

   oslo.config/tests/test_cfg.py
   654:    def test_conf_file_str_value_override_use_deprecated(self):
   1086:    def test_conf_file_dict_values_override_deprecated(self):
   1106:    def test_conf_file_dict_deprecated(self):
   1232:    def test_conf_file_multistr_values_append_deprecated(self):
   1271:    def test_conf_file_multistr_deprecated(self):

   neutron/neutron/plugins/vmware/nsx_cluster.py
   49:            LOG.deprecated(_("Attribute '%s' has been deprecated or moved "

   neutron/neutron/agent/common/config.py
   104:        LOG.deprecated(_('DEFAULT.root_helper is deprecated! Please move '

   heat/heat/tests/test_neutron_loadbalancer.py
   429:    def test_create_deprecated(self):

   heat/heat/tests/test_neutron_vpnservice.py
   201:    def test_create_deprecated(self):

   heat/heat/tests/test_parser.py
   759:    def test_stack_resolve_runtime_data_deprecated(self):

   heat/heat/tests/test_engine_service.py
   1950:    def test_list_resource_types_deprecated(self):

   heat/heat/tests/test_neutron.py
   914:    def test_subnet_deprecated(self):
   1387:    def test_router_interface_deprecated(self):
   1801:    def test_floating_ip_deprecated(self):

   heat/heat/tests/test_neutron_network_gateway.py
   233:    def test_network_gateway_create_deprecated(self):

   os-refresh-config/os_refresh_config/tests/test_os_refresh_config.py
   27:    def test_default_base_dir_deprecated(self):

   glance/glance/store/__init__.py
   200:                LOG.deprecated(_("%s not found in `known_store`. "

   os-apply-config/os_apply_config/tests/test_apply_config.py
   293:    def test_default_templates_dir_deprecated(self):
   298:    def test_default_templates_dir_old_deprecated(self):


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Doug Hellmann (doug-hellmann)

Other contributors:
  None

Milestones
----------

Target Milestone for completion: Juno-1

Work Items
----------

1. Move :meth:`ContextAdapter.deprecated` to
   :func:`deprecation_warning` and update the implementation.
2. Move location of ``fatal_deprecations`` option definition and the
   group where it is registered.
3. Update Cinder.
4. Update Neutron.
5. Update Glance.

Incubation
==========

N/A

Adoption
--------

N/A

Library
-------

N/A

Anticipated API Stabilization
-----------------------------

This new API should be stable enough that oslo.versionutils can graduate.

Documentation Impact
====================

The configuration option is moving to a new group, so the sample
config files and config tables generated in the documentation will
need to be updated.

Dependencies
============

None

References
==========

* Discussion at Juno summit: https://etherpad.openstack.org/p/juno-oslo-release-plan


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

