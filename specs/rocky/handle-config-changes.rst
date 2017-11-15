..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===========================================
Configuration change handling over releases
===========================================

Problem description:
====================

When users perform upgrade their OpenStack system to new release, normally
they are required to update configuration files for adapting changes from old
release to new release. Basically, at that time they must read release notes
or change logs or even track source code changes for doing this.

But unfortunately, there could be some misunderstanding, lack of information
in release notes that cause users confuse. There should be some helper in
oslo.config for automatically adopt new changes and help users manage their
configuration files easily.

Scenario:

Below is the proposed workflow that users can perform on old system to generate
new configuration for preparing upgrading to new release::

                                +--------------+
    Old configuration  +-------->              |
     (N-1 release)              |     Oslo     |
                                |    Config    +-------> New configuration
          Namespaces   +-------->   Migrator   |            (N release)
                                |              |
                                +--------------+

                          Running on new environment


Proposed change:
================

We had a method to generate data structure of machine readable sample config for
any projects, so we could base on this method to get a ConfigOpts instance
(CONF object) with full list of options from not only main project but also
other projects which are listed in namespaces.

Base on the CONF object then we can get the information of options about
whether ``deprecated_name`` and ``deprecated_group`` or not. If yes, then it
is possible to implement a function to update from old configuration to new
configuration, so we call this case is "Mapping 1:1 without changing value.
In fact, not only this case but also other cases including:

* **Case 1**: Mapping 1:1 without changing value.
* **Case 2**: Mapping 1:1 with changing value.
* **Case 3**: Mapping N:1. It means one option can replace a group of options.
* **Case 4**: Mapping M*N:1. Meaning that one option can replace a super
  group of options.
* **Case 5**: Dynamic section.
* **Case 6**: Dynamic option.

By using ``deprecated_name`` and ``deprecated_group``, we are able to solve
**Case 1**.  The examples of **Case 1** are as follows:

1. Change the key of option:

.. code-block:: ini

  [keystone_authtoken]
  auth_uri = http://192.168.122.250:5000
  -->
  [keystone_authtoken]
  www_authenticate_uri = http://192.168.122.250:5000

2. Change section of option:

.. code-block:: ini

  [DEFAULT]
  api_paste_config = api-paste.ini
  -->
  [wsgi]
  api_paste_config = api-paste.ini

3. Change section and key of option:

.. code-block:: ini

  [DEFAULT]
  notification_driver = messaging
  -->
  [oslo_messaging_notifications]
  driver = messaging

In order to solve **Case 2** then it is necessary to adding a parameter to Opt
class. It is called "convert_on_upgrade". It will be a function that is to map
from old value to new value.

For example:

.. code-block:: python

    cfg.StrOpt('choices_opt',
                choices=('a_new', 'b_new', 'c_new'),
                convert_on_upgrade=choice_opt_converter,
                help = 'a choice opt')


    def choice_opt_converter(opt, value):
        return {
            'a': 'a_new',
            'b': 'b_new',
            'c': 'c_new',
        }.get(value)


Problems:
=========

With this proposal, we have just solved only 2 basic cases (case 1 and case 2).
For the more complicated cases, we have not yet to resolve them. Here are
remaining cases that need to be achieved for this feature.

Case 3: Mapping N options to 1 option:
--------------------------------------

For example:

``identify_uri`` can replace 3 options: ``auth_host``, ``auth_port``
and ``auth_protocol``.


.. code-block:: ini

  [keystone_authtoken]
  auth_protocol = http
  auth_host = controller
  auth_port = 35357
  -->
  [keystone_authtoken]
  identity_uri = http://controller:35357


Case 4: Mapping M*N options to 1 option:
----------------------------------------

Currently, ``transport_url`` is a big example for this case. With M is the
number of options in a driver for message queue, N is the number of drivers
(N>1).

For example:

If RabbitMQ is used as backend for message queue then ``transport_url`` can
replace four options such as ``rabbit_host``, ``rabbit_port``,
``rabbit_userid`` and ``rabbit_password`` (M=4) by using a template like this:
``rabbit://rabbit_userid:rabbit_password@rabbit_host:rabbit_port``.

If Kafka is backend for message queue then ``transport_url`` can replace
two options including ``kafka_default_host`` and ``kafka_default_port``
(M=2) by using  a template like this:
``kafka://kafka_default_host:kafka_default_port``.

.. code-block:: ini

  [DEFAULT]
  rpc_backend = rabbit
  #rpc_backend = kafka

  [oslo_messaging_rabbit]
  rabbit_host = controller
  rabbit_userid = openstack
  rabbit_password = RABBIT_PASS
  rabbit_port = 5672

  [oslo_messaging_kafka]
  #kafka_default_host = controller
  #kafka_default_port = 9092
  -->

  [DEFAULT]
  transport_url = rabbit://openstack:RABBIT_PASS@controller:5672
  #transport_url = kafka//openstack:9092


Case 5: Dynamic section
-----------------------

One important thing that there is a dynamic section. For example, Cinder has
a option named ``enabled_backends`` [1]_, if this option is declared like
``enabled_backends = lvm``, then there will be a new section ``[lvm]`` declared
in ``cinder.conf`` like below.

.. code-block:: ini

  [DEFAULT]
  enabled_backends = lvm

  [lvm]
  # ...
  volume_driver = cinder.volume.drivers.lvm.LVMVolumeDriver
  volume_group = cinder-volumes
  iscsi_protocol = iscsi
  iscsi_helper = tgtadm


but if ``enabled_backends = ceph`` then new section ``[ceph]`` shoud be
declared.


.. code-block:: ini

  [DEFAULT]
  enabled_backends=ceph

  [ceph]
  # ...
  volume_driver=cinder.volume.drivers.rbd.RBDDriver
  rbd_pool=volumes
  rbd_ceph_conf=/etc/ceph/ceph.conf
  rbd_store_chunk_size = 4
  rados_connect_timeout = -1
  rbd_secret_uuid=457eb676-33da-42ec-9a8c-9293d545c337


Both sections ``[lvm]`` and ``[ceph]`` are not registered in codebase, the
options in these sections are actually registered in ``[backend_defaults]``
section and are belonging to cinder namespace.

So how can we understand all values in dynamic section? This can be done via
dynamic groups or driver groups [2]_ but we don't have any projects using
them, so each project should migrate to use those things instead of their
special ways to read dynamic sections.


Case 6: Dynamic option
----------------------

The options like ``user_domain_id``, ``project_name`` in ``[keystone_authtoken]``
are registered dynamically when start service based on which ``auth_type``
(password, token...) the service using [3]_. They don't belong to any
namespace. How can we understand these options?


.. code-block:: ini

  [keystone_authtoken]
  ...
  auth_uri = http://controller:5000
  auth_url = http://controller:5000
  memcached_servers = controller:11211
  auth_type = password
  project_domain_id = default
  user_domain_id = default
  project_name = service
  username = cinder
  password = cinder



Work Items:
===========

* Implement one attribute: mapping_value.

* Implement a new function to render new configuration files based on codebase
  and old configuration files.


Documentation Impact:
=====================

Need to have two documentations:

* Having a docs to guide projects to update source-code if they want to have
  this feature.

* Having a docs for Operators about step by step to use this feature.

Implementation:
===============

Assignee(s)
-----------

Primary assignee:

* Phuong Hung Nguyen <phuongnh@vn.fujitsu.com>

* Duc Nguyen Van <ducnv@vn.fujitsu.com>

References:
===========

.. [1] https://github.com/openstack/cinder/blob/66b3a52794f9c2aa6652b28c0a8e67792e2f993b/cinder/common/config.py#L160

.. [2] https://docs.openstack.org/oslo.config/latest/reference/cfg.html#dynamic-groups

.. [3] http://eavesdrop.openstack.org/irclogs/%23openstack-keystone/%23openstack-keystone.2018-08-28.log.html#t2018-08-28T12:06:55