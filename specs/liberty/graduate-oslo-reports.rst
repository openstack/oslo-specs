====================
 Graduating Reports
====================

https://blueprints.launchpad.net/oslo-incubator/+spec/graduate-oslo-reports

The `reports` module currently provides a convenient way to assemble
"Guru Meditation Reports" about the current state a of a given OpenStack
process.  The basic report includes thread (both normal and green) state
and stack traces, as well as configuration and version information.  The
reports are customizable and may be extended with additional sections on
a per-process or per-project basis.  A mechanism is also included to set
up the reports to dump to stdout (or a file) on SIGUSR1, and may be
serialized as text (default), as well as XML and JSON.


Library Name
============

The library will be called "oslo.reports".  The current name in the the
incubator is "openstack.common.report", but pluralizing the name seems more
natural.

Contents
========

openstack/common/report/report.py
openstack/common/report/utils.py
openstack/common/report/guru_meditation_report.py
openstack/common/report/__init__.py
openstack/common/report/views/__init__.py
openstack/common/report/views/text/__init__.py
openstack/common/report/views/text/generic.py
openstack/common/report/views/text/threading.py
openstack/common/report/views/text/header.py
openstack/common/report/views/xml/__init__.py
openstack/common/report/views/xml/generic.py
openstack/common/report/views/jinja_view.py
openstack/common/report/views/json/__init__.py
openstack/common/report/views/json/generic.py
openstack/common/report/generators/conf.py
openstack/common/report/generators/__init__.py
openstack/common/report/generators/version.py
openstack/common/report/generators/threading.py
openstack/common/report/models/base.py
openstack/common/report/models/conf.py
openstack/common/report/models/__init__.py
openstack/common/report/models/version.py
openstack/common/report/models/with_default_views.py
openstack/common/report/models/threading.py

tests/unit/reports/test_base_report.py
tests/unit/reports/test_guru_meditation_report.py
tests/unit/reports/test_openstack_generators.py
tests/unit/reports/test_views.py

Early Adopters
==============

None

Public API
==========

The `reports` module contains several public submodules:

`reports.guru_meditation_report`
  Contains the code revolving around setting up the signal handler and
  registering persistent custom sections

`reports.report`
  Contains the basic classes for the reports themselves, including a class
  for the whole report, a class for each section, and a subclass specifically
  for reports serialized as text

`reports.generators`
  Contains the submodules containing generator code: `conf`, `threading`,
  `version` (not that there is no `base` module here since generators are
  just callables)

`reports.models`
  Contains the submodules containing the base model classes (`base` and
  `with_default_views`) as well as the implementation model classes
  (`threading`, `version`, and `conf`)

`report.views`
  Contains the submodule containing the basic Jinja-based view (`jinja_view`),
  as well as the JSON, XML, and text views (`json`, `xml`, and `text`,
  respectively).  Note that each of the serialization-formatting submodules
  contains a `generic` submodule containing generic classes, and the
  `text` submodule additionally contains the `header` submodule
  (as well as the `threading` submodule, which may be made private).

The following submodules do not necessarily need to be public:

`reports.utils`
  Contains a utility class for attaching attributes to strings, as well as
  a function for finding all objects of a particular class using the garbage
  collector functionality.  Neither of these need to be exposed as public,
  and the object-finding function can be moved into the file of the generator
  which uses it (`StringWithAttrs` is used by both `reports.views.xml.generic`
  and `reports.views.json.generic`), so it needs to stay in its own file.

`reports.views.text.threading`
  This contains several views specific to certain models (which already have
  them set as the default text view), so it does not need to be public.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
    sross-7

Other contributors:
    None

Primary Maintainer
------------------

Primary Maintainer:
    sross-7

Other Contributors:
    None

Security Contact
----------------

Security Contact:
    sross-7

Milestones
----------

Target Milestone for completion: Uknown

Work Items
----------

The graduation checklist should be completed.

Additionally, there are a few places where `reports` currently uses
`str` and should be using `six.text_type` instead.  These should be
fixed before graduation is complete.

Adoption Notes
==============

None

Dependencies
============

- oslo.utils
- oslo.serialization

References
==========

None


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

