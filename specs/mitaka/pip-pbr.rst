==================================
 PBR enhancements to support pip
==================================

pip, the Python package installation tool is looking for something very much
like pbr. pbr itself will benefit from the generalisations pip is looking for.

Problem description
===================

There are a few places where pbr today doesn't meet pips needs.

1. pbr requires pbr be easy_installable or pre-installed for both from-git and
   from-tarball installations. This is sufficiently fragile that pip wishes to
   avoid it from from-tarball situations. pbr has had that requested of it
   already by OpenStack users.

2. pbr has no way to turn off requirements.txt reflection. This is already
   planned as part of converging on upstream practices.

3. Needs to be able to generate dynamic entry points based on the Python
   environment being installed into. e.g. foo, foo2, foo2.7, when installing
   into Python 2.7, whether globally or a venv.

Proposed change
===============

embed pbr in sdists
-------------------

Via an opt-in option we can embed pbr in the root directory of the sdist. When
run from an sdist, the local directory is first in the Python path and this
will cause the embedded copy of pbr to be found and loaded. The embedding
process will copy a statically defined subset of the pbr source code (and we
may wish to refactor things a little to make this more manageable). pbr's
non-test code is 128K today uncompressed, 30K compressed - which is tolerable.
Embedding all of pbr permits tests, doc builds and so on to all work from an
sdist.

opt-out of requirements.txt reflection
--------------------------------------

We'll add an option, ``skip_requirements_files`` to disable requirements file
reflection. When set requirements will be managed via ``setup.cfg`` or
``setup.py`` exclusively. This is in line with our eventual deprecation of
those files.

entry point merging
-------------------

Rather than introducing a template language that wouldn't be supported by
wheels, we'll allow setup() to pass in entry points and merge them. That will
prevent this being an attractive-nuisance within OpenStack while still
permitting pip to perform its current workarounds for the lack of entry point
templating in the wider set of tooling.

Alternatives
------------

1. Say 'no, thats not pbr' to pip. Unnecessary. Growing the ecosystem is part
   of OpenStack's mission.

Implementation
==============

Assignee(s)
-----------

Primary assignee/contact:
  Robert Collins - lifeless


Work Items
----------

1. Embedding pbr in sdists.
2. Opting out of requirements reflection.

Dependencies
============

None

History
=======

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Mitaka
     - Introduced

.. note::

  This work is licensed under a Creative Commons Attribution 3.0 Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
