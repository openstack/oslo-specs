..
  This policy was originally described in
  https://wiki.openstack.org/wiki/Oslo/CreatingANewLibrary#Choosing_a_Name,
  which will be modified to refer to the published version of the spec
  after it is approved.

========================
 Naming an Oslo Library
========================

Choosing a good name for a new Oslo library is important because the
name can be used to signal how we intend the library to be used. This
page describes the guidelines we use when choosing a new name.

Problem Description
===================

Library names need to convey the purpose of the library, as well as
the intended audience.

Proposed Policy
===============

The `Project Creator's Guide`_ includes guidelines for finding unique
names with valid character sets and other technical criteria. This
policy extends those guidelines to cover some criteria that are unique
to Oslo.

There are currently three naming schemes used for Oslo libraries.

Production Runtime Dependencies Meant for OpenStack
---------------------------------------------------

Libraries used for production runtime dependencies of OpenStack
projects should follow the naming pattern ``oslo.something`` for the
library and dist, but use ``oslo_something`` for the top level package
name. Avoid using the ``oslo.`` namespace package
(:doc:`../kilo/drop-namespace-packages`).

Examples of production runtime dependencies include ``oslo.config``
and ``oslo.messaging``.

Non-production Dependencies Meant for OpenStack
-----------------------------------------------

Libraries used for non-production or non-runtime dependencies of
OpenStack projects should follow the naming convention
``oslosomething`` (leaving out the ``.`` between "oslo" and
"something") for the library, dist, and top level package.

Examples of non-production dependencies include ``oslosphinx`` and
``oslotest``.

.. note::

   If you are planning to use a name like this, please discuss it with
   the Oslo team first - we aren't sure we like this name scheme and
   may suggest an alternative.

Everything Else
---------------

Libraries that may be generally useful outside of OpenStack, no matter
how they are used within OpenStack, should be given a descriptive and
unique name, without the "oslo" prefix in any form.

Other examples of Oslo names include ``pbr`` and ``taskflow``.

Alternatives
============

Always Use a Generic Name
-------------------------

One alternative is to use all generic names, without the "oslo"
prefix. The main drawback of this approach is that it lacks the
ability to signal our intended audience for the library. Some of the
libraries we build are not useful to an audience working outside of
OpenStack.  That could be because it is unencumbered with dependencies
on OpenStack-specific libraries such as ``oslo.config``, uses patterns
not used elsewhere, or is simply unlikely to be of interest to anyone
else.  Using the "oslo" prefix gives us a way to indicate to the rest
of the Python community that the library is meant primarily for use in
OpenStack.

Non-production Libs to Use "oslo." Prefix
-----------------------------------------

As mentioned above, the Oslo team is not entirely happy with names
like ``oslotest`` and ``oslosphinx``. The decision to use the prefix
without the dot separator comes from the fact that those libraries
were not installed into the old "oslo" namespace package. The library
names were selected to be consistent with the package name used in
import statements, and we've kept those names rather than going
through the trouble of renaming a library like oslotest, on which much
of OpenStack relies.

Implementation
==============

Author(s)
---------

Primary author: doug-hellmann

Milestones
----------

Effective from the Icehouse release.

Work Items
----------

N/A

References
==========

* `Guidelines from the Project Creator's Guide
  <http://docs.openstack.org/infra/manual/creators.html#choosing-a-good-name-for-your-project>`__

.. _Project Creator's Guide: http://docs.openstack.org/infra/manual/creators.html#choosing-a-good-name-for-your-project


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
