=================================================================
 Support notification Transports per oslo messaging notifications
=================================================================

https://blueprints.launchpad.net/oslo.messaging/+spec/support-transports-per-oslo-notifications

Large clouds where the cloud is being maintained with multiple regions,
operators usually configure global components(for ex: Designate, Ceilometer)
in the DR(Disaster Recovery) fashion. The core services like Nova and
Neutron are then configured to send oslo.messaging notifications to both
the region based components(for ex: Searchlight) and at the same time to
global components. Currently oslo.messaging only allows to send all the
notifications to just one underlying messaging transport(for ex:
one rabbitmq cluster which has deployed region based components).
This spec proposes to add feature into oslo.messaging which enables operators
to define different transport_url for each notification so that they can be
sent to the different messaging transport(for ex: rabbitmq clusters)

Problem description
===================

``oslo.messaging`` allows to specify the drivers and notifications transports
in each components config files like below For example, in nova.

.. code-block:: ini

  [oslo_messaging_notifications]
  driver = messaging
  topics = notifications,notifications_designate
  transport_url = rabbit://username:password@rabbit001.com:5672


With above configuration the ``notifications`` and ``notifications_designate``
related notifications are sent to the defined ``transport_url`` to
``rabbit001.com``. If the designate service is deployed onto different
region/cluster which is using different rabbitmq cluster, currently there is no
way to send only the ``notifications_designate`` to say ``rabbit002.com`` which
is designate service rabbitmq cluster.

Operators should be allowed to send the notifications into different underlying
messaging transport based on the ``transport_url per notification``.


Proposed change
===============

The spec proposes to follow the same implementation of ``enabled_backends``
done Cinder [1]_ and Glance [2]_ components.

Define dynamic new config group for each notification
-----------------------------------------------------

For example:

.. code-block:: ini

  [oslo_messaging_notifications]
  driver = messaging
  topics = notifications,notifications_designate,any_other_notification
  transport_url = rabbit://username:password@rabbit001.com:5672

  [oslo_messaging_topic_notifications]
  transport_url = rabbit://username:password@rabbit001.com:5672

  [oslo_messaging_topic_notifications_designate]
  transport_url = rabbit://username:password@rabbit002.com:5672

As described in the above config section, ``[oslo_messaging_notifications]``
section contains the list of ``topics`` being used for notifications.
Each of the notification is then dynamically grouped later and has its own
``transport_url``. The format of the topic based section will be
``oslo_messaging_topic_<topic-name>`` to avoid collisions between topic
names and possibly other config section names.

By default if the transport_url is not defined for any of the notification
it will fall back to the main sections transport_url
``[oslo_messaging_notifications]`` and if it is defined over there as well then
it will finally fallback to the transport_url defined in the
``[oslo_messaging_rabbit]``.
In the above example ``notifications`` topic uses ``rabbit001.com`` rabbitmq
cluster. ``notifications_designate`` uses ``rabbit002.com`` rabbitmq cluster
and ``any_other_notification`` used ``rabbit001.com`` rabbitmq cluster.

The notifications will inherit all the other config option values like
``driver`` etc.

This change is backward compatible so even if operator do not specify each
notifications transport_urls they will fall back to the main sections.

This change does not require any changes to oslo.config since everything is
already supported.

Also this will not require the clients like Nova, Neutron to change their
config files if they don't want to send notifications to different clusters.


Alternatives
------------

This use case can be implemented with below new feature:

#. Add ``MultiOptGroup`` support in oslo.conf same as ``MultiOpt``.
#. Make use of  ``MultiOptGroup`` in oslo.messaging and in the clients like
   Nova and Neutron

For example:

.. code-block:: ini

  [oslo_messaging_notifications]
  driver = messaging
  topics = notifications
  transport_url = rabbit://username:password@rabbit001.com:5672

  [oslo_messaging_notifications]
  driver = messaging
  topics = notifications_designate
  transport_url = rabbit://username:password@rabbit002.com:5672

  [oslo_messaging_notifications]
  driver = messaging
  topics = any_other_notification
  transport_url = rabbit://username:password@rabbit001.com:5672

This solution requires to add a new feature in oslo.config which will allow to
define the option group multiple times as shown above which can be used in
oslo.messaging to define the transport_urls per notification.
This feature might be useful in other use-cases as well where it is required
to define the group multiple times.

One more alternative could be to use RabbitMQ Shovel plugin (in case if you are
using rabbitmq as a messaging backend) to move messages from one cluster to
other cluster. You can define separate shovel policy for each ``notification``
with different ``dest-uri`` to send them to different rabbitmq clusters.
One disadvantage of using shovel approach is RabbitMQ shovel plugin actually
creates a non-existent queue on the RabbitMQ node as a durable queues because
thats the behaviour of Shovel plugin and if the OpenStack service is not using
durable queues the service will fail to send the messages to rabbitmq and gives
below error:
Error: Queue.declare: (406) PRECONDITION_FAILED

Impact on Existing APIs
-----------------------

No impact.

Security impact
---------------

No impact.

Performance Impact
------------------

No impact.

Configuration Impact
--------------------

Each notification will have its own group which can be defined like above.

Developer Impact
----------------

No impact.

Testing Impact
--------------

Additional unit tests will be required to cover the added functionality.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Dinesh_Bhor (bhordinesh07@gmail.com)

Other contributors:
  volunteers?

Milestones
----------

..TODO(Dinesh_Bhor): figure this out

Work Items
----------

* Implement the new dynamic ``notifications`` OptGroup generation.
* Integrate it in `get_notifications_transport` and ``Notifier`` class.
* Update documentation.
* Update the sample configuration generator to include the variable names.
* Update the documentation generator to include the variable names.


Incubation
==========

N/A

Documentation Impact
====================

The documentation will need to be updated to indicate that notification option
can be overridden with its own dedicated group.

Dependencies
============

N/A

References
==========

.. [1] https://github.com/openstack/glance/blob/0bb0fca24c23d8e8000ce7a3cabc695aec52f334/doc/source/admin/multistores.rst
.. [2] https://github.com/openstack/cinder/blob/ea04cda682168b642ae2fa823338c4dd26e5c86c/doc/source/admin/blockstorage-multi-backend.rst
