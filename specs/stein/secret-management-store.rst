============================
Protecting Plaintext Secrets
============================

bp protecting plaintext password https://blueprints.launchpad.net/oslo.config/+spec/protect-plaintext-passwords

Problem description
===================

Current OpenStack services require plaintext passwords and credentials for
various access, e.g. database, keystoneauth, etc.

Even with proper file permissions set on these files, often time during
troubleshooting sessions, these configuration files are sent via emails
without the passwords properly redacted.

Also, the ability to change passwords across multiple nodes are
heavily relying on the deployment tools of choice (ansible, fuel, etc.)

Proposed change
===============

First of all, in order to properly secure the secrets in those configuration
files, we should implement an oslo.config driver as described in the oslo spec
http://specs.openstack.org/openstack/oslo-specs/specs/queens/oslo-config-drivers.html

Phase 0:

Using HTTP and HTTPS urls as a reference to secrets:

As a basic but useful solution, we proposed using an external URL pointing to
an HTTP or HTTPS url to access those secrets.

Note: This Phase 0 was merged on oslo.config in the Rocky release.


Phase 1:

Currently, on OpenStack, we have a Generic Key Manager interface called
Castellan, which means that Castellan works on the principle of providing an
abstracted key manager based on your configuration. In this manner, several
different management services can be supported through a single interface.
To integrate Castellan with oslo.config will have a Castellan implementation
to oslo.config driver defined before.

After that, we will be able to use a Castellan reference for those secrets
and store it using a proper key store backend. Currently, Castellan supports
Barbican and also Hashicorp Vault as backends options. For this scenario,
we will be looking for using Vault as a chosen solution, since we can point
to an external Vault server with no internal dependencies to other OpenStack
services, also for authentication and validation methods, since Barbican needs
Keystone tokens as authentication method also we need to store the Barbican
and Keystone secrets present in their configuration files.

Phase 2:

Finally, we should use some deployment tool like Ansible to create those
secrets and store them properly on Vault following the Castellan interface and
inject those secrets in the configuration files. So, later, we will be able to
restore it properly in the configuration files, with any necessary manual
steps.

Consuming projects
==================

Any OpenStack service which have some secrets in their configuration files,
such as Glance, Nova, Keystone, Mistral and so on.

Alternatives
------------
* Encrypt the configuration files:

Which requires decryption keys and makes difficult to update configurations

* Configuration Management DB (CMDB):

Need to secure database connection credentials

* Other types of providers can be included as a key store solution since those
  providers implements the Castellan interface, such as Vault or a KMIP device

Security impact
---------------

This change wants to make OpenStack services passwords and credentials
management more secure, removing the plaintext passwords in the OpenStack
services configuration files by using a secure and encrypted alternative
following the Castellan interface for secrets management.


Configuration Impact
--------------------

For the first phase of this work, the operator can update their configuration
files to point to the password reference and no more using plaintext
passwords. Although, after the second phase with the Puppet and/or Ansible
that change will be made automatically by those tools.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  raildo

Other contributors:
  dhellmann
  moguimar
  spilla

Milestones
----------

We are targetting the Phase 0 for Rocky-3 and Phase 1 and Phase 2 for Stein.

Work Items
----------

* Implement oslo.config driver for URI
* Implement oslo.config driver for Castellan
* Documentation


Documentation Impact
====================

We should document how to update the OpenStack Services
configuration file to use the proper password references
instead of the plaintext passwords.


References
==========

Oslo PTG discussion: https://etherpad.openstack.org/p/oslo-ptg-queens
Meetings logs: https://etherpad.openstack.org/p/oslo-config-plaintext-secrets
Phase 0 on Rocky Release: https://docs.openstack.org/oslo.config/latest/reference/drivers.html

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

