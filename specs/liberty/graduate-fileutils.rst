..
  This template should be in ReSTructured text.  For help with syntax,
  see http://sphinx-doc.org/rest.html

  To test out your formatting, build the docs using tox, or see:
  http://rst.ninjs.org

  The filename in the git repository should match the launchpad URL,
  for example a URL of
  https://blueprints.launchpad.net/oslo?searchtext=awesome-thing should be
  named awesome-thing.rst.

  Wrap text at 79 columns.

  Do not delete any of the sections in this template.  If you have
  nothing to say for a whole section, just write: None

  If you would like to provide a diagram with your spec, ascii diagrams are
  required.  http://asciiflow.com/ is a very nice tool to assist with making
  ascii diagrams.  The reason for this is that the tool used to review specs is
  based purely on plain text.  Plain text will allow review to proceed without
  having to look at additional files which can not be viewed in gerrit.  It
  will also allow inline feedback on the diagram itself.

======================
 Graduating fileutils
======================

blueprint: https://blueprints.launchpad.net/oslo-incubator/+spec/graduate-oslo-io

summary: move the fileutils code (and associated tests) into oslo.utils

Library Name
============

oslo.utils and oslo.policy

Contents
========

* openstack/common/fileutils.py
* tests/unit/test_fileutils.py

Early Adopters
==============

* keystone

Public API
==========

fileutils.py has only 7 functions and 1 global. Their usage, and
graduation plan will be broken down below.

1. ensure_tree()

  * used by nova/cinder/ironic
  * to be added to oslo.utils

2. delete_if_exists()

  * used extensively in nova and cinder and a bit in neutron
  * to be added to oslo.utils

3. remove_path_on_error()

  * used by nova/cinder/ironic
  * to be added to oslo.utils

4. write_to_tempfile()

  * used sparingly in keystone and ceilometer (tests only)
  * consider deprecation

5. file_open

  * used extensively in cinder
  * can be replaced with just an open() call
  * consider deprecation

6. read_cached_file()

  * used only by nova's policy engine, and by oslo.policy
  * can push both of these into oslo.policy and when/if nova switches to
    oslo.policy, they will no longer require these functions.

7. delete_cached_file()

  * same as above.

8. DEFAULT_MODE

  * not being referred to, can be marked as private.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Steve Martinelli (stevemar)

Primary Maintainer
------------------

Primary Maintainer:
  Steve Martinelli (stevemar)

Security Contact
----------------

Security Contact:
  Doug Hellmann (doug-hellmann)

Milestones
----------

Liberty-1

Work Items
----------

* https://wiki.openstack.org/wiki/Oslo/CreatingANewLibrary#Checklist

Adoption Notes
==============

Projects currently importing::

  from openstack.common import fileutils

would have to switch to importing::

  from oslo_utils import fileutils

if using::

  fileutils.file_open()

switch to::

  open()

if using::

  fileutils.read_cached_file()

switch to::

  oslo_policy

Dependencies
============

None

References
==========

* https://etherpad.openstack.org/p/kilo-oslo-library-proposals
* WIP patch https://review.openstack.org/#/c/154975/


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

