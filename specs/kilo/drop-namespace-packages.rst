====================================
 Drop our use of namespace packages
====================================

https://blueprints.launchpad.net/oslo-incubator/+spec/drop-namespace-packages

Installing our libraries into a namespace package has caused several
types of errors. Rather than continuing to fight with them, I propose
that we phase them out.

Problem description
===================

The namespace package support in setuptools is fragile, and some of
the ways we use code regularly within OpenStack expose the issues in
ways that are hard to debug.

The main issue we have seen is with installing two separate libraries
into the same python namespace package using different installation
"modes". If one library installed with ``pip install -e`` to enable
"editable" mode, and another is installed without the ``-e`` option as
a regular library, then the import path for the package is broken and
some of the installed components are not importable. This happened a
lot when devstack installed Oslo libraries editable, and we have
changed devstack to stop doing that by default. It also happens when a
developer installs something using a system package and then installs
another library from source. We have no real way to control that
behavior, so it still crops up from time to time.

We also see trouble with virtualenvs configured to allow access to the
global site-packages directory, as nova needs for libvirt access. If
anything from the ``oslo`` namespace package is installed globally, it
will shadow the versions visible in the virtualenv. That would
normally lead to a version error if some old version is installed
globally, but in this case it can also lead to import errors because
the namespace package doesn't not properly span the two site-packages
directories.

Proposed change
===============

I propose that we move all current Oslo libraries out of the ``oslo``
namespace and create simple packages that can be imported
independently. For example, we would change::

  from oslo.foo import bar

to::

  from oslo_foo import bar

To avoid issues with distros, we should not rename the ``oslo.foo``
library to ``oslo_foo``. This may be a little confusing for
developers, so we might look at the decision again in the future, but
as a first step this is less obtrusive because it means we don't need
to change our requirements lists, repository names, and distro package
names.

To support backwards compatibility, we will provide shadow-packages
for the ``oslo`` namespace so that the old import form still works for
the Kilo releases of the libraries. That will give us time to update
all of the applications and let them cycle out of the long-term
support window before dropping the namespace packages entirely during
the M release.

Moving to regular packages will also let us move our unit tests inside
the library, so they are delivered and installed under ``oslo_foo``,
so we should do that at the same time, retaining just enough of the
test suite to ensure that the public API exposed through the namespace
package still works.

The distribution names of existing libraries won't change, and the
same pattern will be used to create new libraries to avoid
confusion. That means one would ``pip install oslo.foo`` and then
``from oslo_foo import bar``.

Alternatives
------------

1. lifeless has a patch to oslo.db that sets up the namespace package
   using pkgutils instead of setuptools:

     https://review.openstack.org/#/c/123604/3/oslo/__init__.py

   This retains the ability to use namespace packages, with the extra
   cost of shipping a real ``oslo`` library
   (https://github.com/rbtcollins/oslo) and maintaining the override
   code ourselves. We don't know what other issues we might find with
   namespace packages, though, so I'm more comfortable with just
   dropping them entirely.

2. Python 3 has better native namespace package support, so we could
   review the decision when we move to Python 3.

3. Do nothing, and continue to help developers debug problems on their
   systems when they come up. If we choose this option, we might want
   to write a script "why_is_oslo_broken.sh" to put in the incubator.

The "oslo\_" name prefix was selected to distinguish the libs from the
non-production libraries like oslotest and oslosphinx. We could
theoretially rename those as well so that all of our branded libraries
have the same naming convention. I don't know if that's worth doing or
not.

Impact on Existing APIs
-----------------------

The imports will change, but we should not need to change other
aspects of the libraries' APIs.

Security impact
---------------

None

Performance Impact
------------------

None

Configuration Impact
--------------------

None

Developer Impact
----------------

Developers need to be aware of the import changes. We have a few
options for communicating that widely:

1. Add a deprecation warning to the oslo namespace packages so
   importing them reports a warning.
2. Add a hacking rule to make importing "from oslo." illegal.
3. Rely on reviewers to catch it.

Option 1 is easy for us to do ourselves.

Option 2 has to wait until we have converted all of our own libraries,
and updated all the apps, but it would then prevent improper imports
being restored.

Option 3 is brittle, so I don't think we want to rely on it alone.

To ease the transition, we should be able to prepare a bash/sed script
to make the required edits to a project.  I don't think we'll have
more than a handful of different types of import statements, but we
can update the script as we find new patterns

Testing Impact
--------------

The unit tests will be updated in each library so that all of them run
against the new module name. Then some of the public API tests will be
duplicated to use the namespace package to ensure that we don't break
that.

The existing unit tests in applications should cover the uses of the
libraries in the applications. We will need to update any mocks in
those tests.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Doug Hellmann

Other contributors:
  None

Milestones
----------

Target Milestone for completion: K-2 (I hope early)

Work Items
----------

1. Rearrange all of our library code, including tests and
   documentation. See https://review.openstack.org/#/c/127323/ for an
   example.
2. Write helper script for liaisons (maybe a liaison can do this?).

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

N/A

Documentation Impact
====================

None

Dependencies
============

None

References
==========

* setuptools bug 250, "develop and
  `--install-single-version-externally-managed` are not compatible
  with each other for namespace packages" -
  https://bitbucket.org/pypa/setuptools/issue/250/develop-and-install-single-version

* lifeless has a patch to oslo.db that sets up the namespace package
  using pkgutils instead of setuptools:

  https://review.openstack.org/#/c/123604/3/oslo/__init__.py

  it uses a real oslo package: https://github.com/rbtcollins/oslo

* PEP-420 spec: http://legacy.python.org/dev/peps/pep-0420/

* My WIP patch for oslo.i18n to move it out of the namespace package:
  https://review.openstack.org/#/c/127323/

* Notes from the Kilo summit session:
  https://etherpad.openstack.org/p/kilo-oslo-namespace-packages

* Mailing list thread following up after the Kilo summit:
  http://lists.openstack.org/pipermail/openstack-dev/2014-November/050313.html

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

