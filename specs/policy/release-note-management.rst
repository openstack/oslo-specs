========================
 Managing Release Notes
========================

This spec documents the policy for where and how to manage release
notes for Oslo libraries.

Problem Description
===================

Oslo libraries have several potential audiences:

* OpenStack service developers
* OpenStack deployers
* other developers

The type of information those audiences want for release notes can be
quite different. This policy describes how we manage release notes to
ensure we are communicating appropriately with each audience.

Proposed Policy
===============

Release notes for developers, whether part of the OpenStack community
or not, are handled in the developer documentation published for the
libraries. This ensures that all developer-focused information is in
one place.

The packaging library pbr includes a facility for automatically
generating a ChangeLog file based on the git history for the project
being packaged. That file is reStructuredText, and should be included
directly in the developer documentation compiled by Sphinx into HTML
and published under http://docs.openstack.org/developer/ by adding a
static ``history.rst`` file that uses the ``include`` directive to
load the generated file.

Additional information for developers can be added directly to the
developer documentation. Docstrings in code should be annotated with
version information for new features or parameters using the
``versionadded`` directive and for deprecations using the ``warning``
directive.

Release notes for deployers should be managed through reno_ and
published under http://docs.openstack.org/releasenotes/. Each library
with configuration options or other deployer-facing interfaces should
set up reno to publish release notes. Not all Oslo libraries will need
to do that.

.. _reno: http://docs.openstack.org/developer/reno/

The deployer-facing release notes should be written with them in mind,
and only describe features or changes from the perspective of someone
who is not also reading the source code for the library. For example,
it is not necessary to document changes to a library unless they are
visible to the deployer. Changes to configuration options or file
formats should have reno notes. Changes to internal APIs do not need
them. New features and bug fixes should be documented with reno
release notes. For example, changes such as better timeout handling or
reconnection management for messaging or database services should have
reno release notes.

Alternatives & History
======================

In the past we focused on communicating with developers using Oslo
libraries. This is no longer sufficient, since we now manage
configuration options and other features that are visible to deployers
of software built using Oslo libraries.

We could add a section to the developer documentation, but this will
make it more difficult to build a single set of release notes for all
of OpenStack, or at the very least link directly to release notes in a
location common to all projects.

Implementation
==============

Author(s)
---------

Primary author: doug-hellmann

Milestones
----------

This policy applies starting with the Mitaka cycle, where we added
reno to oslo.log and oslo.config.

Work Items
----------

Add reno build instructions and CI jobs to libraries, as needed.

References
==========

* https://etherpad.openstack.org/p/reno-rollout

* http://lists.openstack.org/pipermail/openstack-dev/2015-November/078301.html

Revision History
================

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Mitaka
     - Introduced

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

