================================================
 Extend the gettext support of oslo.i18n library
================================================

https://blueprints.launchpad.net/oslo.i18n/+spec/more-gettext-support

The oslo.i18n library already supports the standard gettext function.

But the "contextual markers" and "plural form" gettext functions
are needed for translations.
See the Reference - Horizon Translation Wiki.


Problem description
===================

The standard gettext function support the most of use cases of translations.

But there are two situations needed to be addressed:
* different translations of the same English words from different contexts,
such as menu item and label;
* plural form of some languages like English,
different translations are needed for single item or plural items;


Proposed change
===============

In python gettext module, "contextual markers" and "plural form" are supported
but without lazy translation support.

The plan is to add the two features with lazy translation support
in oslo.i18n library.

oslo.i18n will provide contextual_form and plural_form as additional properties,
and abbreviated forms of the two properties as "_C" and "_P".


Alternatives
------------

Actually we can translate without using "contextual markers" or "plural form".

But in some cases, "contextual markers" can reduce ambiguities, "plural form"
can improve the translation quality.

Impact on Existing APIs
-----------------------

The new contextual_form and plural_form properties on TranslatorFactory
will be provided, and exported from the library.


Security impact
---------------

None


Performance Impact
------------------

For using the new methods, some gettext call _("str") needs to be replaced
by _C("context", "str"), or _P("singular", "plural", count).

As new methods requires additional arguments, only user cases where new methods
can improve the translation quality need to switch to use the new methods.

Most of the code can still use the standard gettext function.


Configuration Impact
--------------------

Need to change Jenkins jobs to extract translatable messages with contextual form and plural form.

Developer Impact
----------------

This spec only adds more functions to oslo.i18n, developers only need to
switch to the new functions when improving translations.

If no problem, the code can still use the standard gettext function.


Testing Impact
--------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  alexepico

Other contributors:
  anish-developer

Milestones
----------

Target Milestone for completion:

Work Items
----------

* extend class Message to support contextual_form and plural_form;
* export contextual_form and plural_form on TranslatorFactory;
* document when and how to use contextual_form or plural_form properties;
* change Jenkins jobs to extract translatable messages with contextual form and plural form;

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

New contextual_form and plural_form properties will be provided on TranslatorFactory from oslo.i18n.

Documentation Impact
====================

Update the developer documentation for oslo.i18n with examples.

Translation team needs to translate "contextual markers" and "plural form"
gettext message if used by developers.

Dependencies
============

- https://blueprints.launchpad.net/oslo/+spec/graduate-oslo-i18n

References
==========

* Horizon Translation Wiki:
  https://wiki.openstack.org/wiki/I18n/TranslatableStrings

* Some Experimental Code:
  https://review.openstack.org/134850


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
