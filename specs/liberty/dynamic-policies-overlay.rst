..

==========================
 Dynamic Policies Overlay
==========================

https://blueprints.launchpad.net/oslo?searchtext=dynamic-policies-overlay

`Dynamic Policies <https://wiki.openstack.org/wiki/DynamicPolicies>`_ aims to
improve access control in OpenStack by improving the mechanisms in which
policies are defined and delivered to service endpoints.

One step of dynamic delivery of policies is to overlay the existing service
endpoint's local policy file with the custom rules defined in
``Keystone server``. This overlay task is delegated to ``oslo.policy``.

Problem description
===================

Alice the Cloud Deployer
------------------------

Alice is the kind of person who loves new features and eagerly awaits for new
OpenStack features like ``Dynamic Policies`` to enable them in her cloud.

With that feature, she expects to be able to define her custom policy rules in
``Keystone server`` and have those applied to service endpoints transparently.

Behind the scenes, ``Keystone Middleware`` will fetch the ``Dynamic Policy``,
which contains the custom policy rules, for the service it is serving and ask
``oslo.policy`` to overlay the ``Stock Policy``, which is the existing local
policy file.

Proposed change
===============

Based on the ``Dynamic Policy`` and on the existing ``policy_file`` and
``policy_dirs`` options, add to ``oslo.policy`` the capability to overlay
rules in the ``Stock Policy``.

When there is a rule clashing, the rule from ``Dynamic Policy`` always
overrides the rule in ``Stock Policy``. It means that any customization made
directly in the ``Stock Policy`` will be lost if there is an entry for it in
the ``Dynamic Policy``.

Alternatives
------------

Make ``Keystone Middleware`` itself do the overlay logic, however it seems to
not be a task for it at all, since ``oslo.policy`` is the one which does handle
policy files and owns the config options defining where such file is placed.

Impact on Existing APIs
-----------------------

None

Security impact
---------------

This change touches policy rules, which are sensitive data since they define
access control to service APIs in OpenStack.

Performance Impact
------------------

None

Configuration Impact
--------------------

None

Developer Impact
----------------

None

Testing Impact
--------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Samuel de Medeiros Queiroz - samueldmq

Other contributors:
  Adam Young - ayoung
  Morgan Fainberg - mdrnstm

Milestones
----------

Target Milestone for completion: Liberty-2

Work Items
----------

* Create a new function that receives as input the ``Dynamic Policy`` as a
  Python dict and write them to the ``Stock Policy``, i.e the existing local
  policy file, using override strategy when a clashing occurs.

Incubation
==========

Adoption
--------

Any service using the ``Dynamic Policies`` mechanism for access controll will
be using the proposed change through ``Keystone Middleware``, which means that
adoption is transparent to services.

Library
-------

The proposed change will affect the ``oslo.policy`` library.

Anticipated API Stabilization
-----------------------------

None

Documentation Impact
====================

None besides the regular Python code level documentation.

Dependencies
============

A list of related specs defining the dynamic delivery of policies can be found
under the topic `dynamic-policies-delivery <https://review.openstack.org/#/q/topic:bp/dynamic-policies-delivery,n,z>`_.

References
==========

None


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

