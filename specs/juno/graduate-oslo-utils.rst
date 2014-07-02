=======================
 Graduating oslo.utils
=======================

https://blueprints.launchpad.net/oslo/+spec/graduate-oslo-utils

Every project has one. ``oslo.utils`` is our "grab-bag" library, made
up of little modules with few dependencies that are too small to
warrant release management on their own.

Library Name
============

oslo.utils

Contents
========

* openstack/common/excutils.py
* openstack/common/importutils.py
* openstack/common/network_utils.py -> openstack/common/netutils.py
* openstack/common/timeutils.py
* openstack/common/strutils.py
* openstack/common/units.py
* tests/unit/test_excutils.py
* tests/unit/test_importutils.py
* tests/unit/test_netutils.py
* tests/unit/test_timeutils.py
* tests/unit/test_strutils.py
* tests/unit/test_units.py

Early Adopters
==============

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  dims

Other contributors:
  doug-hellmann
  flaper87

Primary Maintainer
------------------

Primary Maintainer:
  dims

Other Contributors:
  doug-hellmann
  flaper87

Security Contact
----------------

Security Contact:
  dims

Milestones
----------

Target Milestone for completion: Juno-2

Work Items
----------

* https://blueprints.launchpad.net/oslo/+spec/graduate-oslo-i18n
* After bringing importutils.py into the library repo, clean up the
  portions that will be part of its public API so that only
  :func:`try_import` is exported. Clean up test_importutils.py to
  match.
* https://wiki.openstack.org/wiki/Oslo/CreatingANewLibrary#Checklist
* Split strutils into 2 different modules:
  1. Containing encoding/decoding functions
  - safe_encode
  - safe_decode
  2. Containing string transformation functions
  - to_slug
  - string_to_bytes
  - int_from_bool_as_string
  - bool_from_string
  - mask_password
* Mark not ported functions as deprecated in the incubator.

Adoption Notes
==============

The copy of importutils we are releasing in this library will only
have the function :func:`try_import` in its public API. Use of the
other functions for actually importing modules and classes is
deprecated, and should be replaced with stevedore. We are leaving the
current importutils.py in the incubator untouched to ease that
transition.

No API changes are anticipated for the other modules, so it should
just be a matter of updating the import statements.

Dependencies
============

*  https://blueprints.launchpad.net/oslo/+spec/graduate-oslo-i18n

References
==========

* This work obsoletes
  https://blueprints.launchpad.net/oslo/+spec/graduate-oslo-language,
  since we're incorporating excutils.py into this library instead.
* https://wiki.openstack.org/wiki/Oslo/GraduationStatus#oslo.utils
* https://etherpad.openstack.org/p/juno-oslo-release-plan

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

