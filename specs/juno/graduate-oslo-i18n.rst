======================
 Graduating oslo.i18n
======================

https://blueprints.launchpad.net/oslo.i18n/+spec/graduate-oslo-i18n

oslo.i18n includes modules related to internationalization and
localization. The initial version focuses on translation utilities
built on top of the ``gettext`` module.

Library Name
============

This library includes some code that may eventually be useful outside
of OpenStack, but it does assert some policies and behaviors that are
specific to OpenStack, so it was placed in the ``oslo`` namespace
package as ``oslo.i18n``.

Contents
========

The code for this library was exported from the incubator before we
started using specs documents. See
https://opendev.org/openstack/oslo.i18n

* openstack/common/gettextutils.py
* tests/unit/test_gettextutils.py

Early Adopters
==============

* Keystone

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Doug Hellmann (doug-hellmann)

Other contributors:
  None

Primary Maintainer
------------------

Each graduated library needs a primary maintainer. That may be the
same person who started the code, the person who graduated it, or it
may be someone who is taking over maintenance duties.

If more than one person *who is not already on the oslo-core team*
intends to participate as a core reviewer for the new library, list
them under "Other Contributors".

Primary Maintainer:
  Mark McLoughlin (markmc)

Other Contributors:
  Doug Hellmann (doug-hellmann)

Security Contact
----------------

Each graduated library needs a contact for the OpenStack Vulnerability
Management team. It may be the same as the primary maintainer, an
existing Oslo team member who helps with security issues, or it may be
someone else on the development team for the new library.

Talk with the Oslo and Vulnerability management teams about who the
person is, and make sure they agree to their participation before
proceeding.

Security Contact:
  Doug Hellmann (doug-hellmann)

Milestones
----------

Target Milestone for completion:
  Juno-1

Work Items
----------

1. https://wiki.openstack.org/wiki/Oslo/CreatingANewLibrary
2. Before the library was exported the API was changed so that
   USE_LAZY is only evaluated once at startup. That won't work for
   libraries that are using their own translations, though, since they
   may be initialized through imports that happen before the
   application has an opportunity to establish whether it wants lazy
   translation enabled. We need to correct that, probably by updating
   _make_translation_func() to work with USE_LAZY at runtime again.
3. Since each consuming app and library will have their own copy of
   the marker functions, we can remove the global marker functions
   from gettextutils.

Adoption Notes
==============

The translation marker functions are essentially global variables that
are partial functions that have their translation domain argument
baked in. In the past, there was one global translation marker
function (``_()``), which was created one time using the application's
name. This was accomplished by having the string ``oslo`` replaced
with the application name when gettextutils.py was copied out of the
incubator into the application's source tree. We won't be copying
gettextutils.py into the application any more, and we will have
libraries creating their own translation marker functions, so we need
a way have multiple marker functions defined with *different*
translation domains.

The simplest approach to achieve that is to create a small
"integration module" in each consuming app or library that
instantiates the functions, and then have the app or library use that
module instead of using oslo.i18n directly. This is documented in the
usage.rst page for the library:
http://docs.openstack.org/developer/oslo.i18n/usage.html

In addition to the marker functions, some apps are using the
:class:`Message` class from :mod:`gettextutils`. That class is meant
to be a private implementation detail of lazy translation, and is not
exposed in the public API of ``oslo.i18n``. To convert a Message to a
translated string, use :func:`translate`. To instantiate a new
Message, use :func:`enable_lazy` to turn lazy translation on and then
use a property of a :class:`TranslatorFactory` (e.g.,
``TranslatorFactory().primary``) to get a translation function, which
will return a Message object.

Dependencies
============

* https://blueprints.launchpad.net/oslo/+spec/log-messages-translation-domain-rollout
  is related but is not blocked on this blueprint.

References
==========

* Discussion at the Icehouse summit: https://etherpad.openstack.org/p/icehouse-oslo-status
* Discussion at the Juno summit: https://etherpad.openstack.org/p/juno-oslo-release-plan
* https://wiki.openstack.org/wiki/Oslo/Dependencies
* https://wiki.openstack.org/wiki/Oslo/GraduationStatus


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

