..
  This content is based on the "Incubation" section of
  https://wiki.openstack.org/wiki/Oslo, which will be removed when the
  information is added to the specs repository history section.

====================
 The Oslo Incubator
====================

Problem description
===================

One source of code for Oslo libraries is code in an existing project
that is identified as useful to another project. The existing
implementation may be tightly coupled to the application, and need to
be modified to make it more general. This spec describes how the
"incubator" repository can be used to evolve the module's API to
eventually make it suitable for release as a library.

Proposed Policy
===============

The process of developing a new Oslo API usually begins by taking code
which is common to some OpenStack projects and moving it into the
`oslo-incubator`_ repository. New APIs live and evolve in the
incubator until they have matured to meet the graduation criteria
described below under "API Principles".

Using the incubator helps increase *developer* performance by making
it possible to quickly change the API of a module, while postponing
adoption of that API in the consuming application until it is
convenient for the application review team.

Consider incubated code as "statically linked" to an application,
while a graduated modules are "shared libraries".

.. _oslo-incubator: http://git.openstack.org/cgit/openstack/oslo-incubator

Syncing Code from Incubator
---------------------------

APIs which are incubating can be copied into individual openstack
projects from oslo-incubator using the ``update.py`` script provided
(which may be invoked through the convenient ``update.sh``). An
``openstack-common.conf`` configuration file in the project describes
which modules to copy and where they should be copied to.

Usually the API maintainer or those making significant changes to an
API take responsibility for syncing that specific module into the
projects which use it by doing::

  $> cd ../
  $> git clone git://git.openstack.org/openstack/oslo-incubator
  $> cd oslo-incubator
  $> ./update.sh --nodeps --base nova --dest-dir ../nova --modules jsonutils,gettextutils

Alternatively, it can make sense for someone to batch sync more minor
changes into a project together. To sync all code for a specific
project, you can do::

  $> ./update.sh ../nova
  Copying the config,exception,extensions,utils,wsgi modules under the nova module in ../nova

In this latter case, the ``update.sh`` script uses the
``openstack-common.conf`` config file to determine which modules to
copy. The format of that file is::

  $> cd ../nova
  $> cat openstack-common.conf
  [DEFAULT]

  # The list of modules to copy from oslo-incubator
  modules=cfg,iniparser

  # The base module to hold the copy of openstack.common
  base=nova

For master oslo-incubator sync requests, we tend to sync whole modules
or even all the modules that a project uses (unless there are specific
obstacles to doing so). This keeps the project up to date with the
version of the modules tested together in the incubator.

Developers making major changes to incubating APIs in
``oslo-incubator`` must be prepared to update the copies in the
projects which have previously imported the code.

The tests for incubated code should not be synced into consuming
projects.

Stable Branches
---------------

For stable branches, the process is a bit different. For those
branches, we don't generally want to introduce changes that are not
related to specific issues in a project. So in case of backports, we
tend to do per-patch consideration when synchronizing from incubator.

Backporting for stable branches is a bit complicated process. When
reviewing synchronization requests for those branches, we should not
only check that the code is present in all consequent branches of the
appropriate project (f.e. for N-2, in both N and N-1), but also that
the patches being synchronized were successfully backported to
corresponding stable branches of oslo-incubator. So the usual way of
oslo-incubator bug fix is (in case of Neutron):

1. oslo-incubator (master)
2. neutron (master)
3. oslo-incubator (stable/icehouse)
4. neutron (stable/icehouse).

For N-2, it's even more complicated, introducing more elements in the
backporting chain.

Developer Impact
----------------

Projects which are using such incubating APIs must avoid ever
modifying their copies of the code. All changes should be made in
oslo-incubator itself and copied into the project.

All changes related to code synchronization from ``oslo-incubator``,
such as updating the use of APIs that have evolved, must be 'atomic'
with the sync. For example, when syncing a new version of an incubator
module that uses a library containing a newly graduated module, it may
be necessary to update the rest of the application to use that same
library, too. The Oslo team does not support versions of incubated
modules with local changes, other than the import statements modified
automatically by ``update.py``.

API Principles
--------------

APIs included in Oslo should reflect a rough consensus across the
project on the requirements and design for that use case. New
OpenStack projects should be able to use an Oslo API safe in the
knowledge that, by doing so, the project is being a good OpenStack
citizen and building upon established best practice.

To that end, we keep a number of principles in mind when designing and
evolving Oslo APIs:

1. The API should be generally useful and a "good fit" - e.g. it
   shouldn't encode any assumptions specific to the project it
   originated from, it should follow a style consistent with other
   Oslo APIs and should fit generally in a theme like error handling,
   configuration options, time and date, notifications, WSGI, etc.

2. The API should already be in use by a number of OpenStack projects

3. There should be a commitment to adopt the API in all other
   OpenStack projects (where appropriate) and there should be no known
   major blockers to that adoption

4. The API should represents the "rough consensus" across OpenStack
   projects

5. There should be no other API in OpenStack competing for this "rough
   consensus"

6. It should be possible for the API to evolve while continuing to
   maintain backwards compatibility with older versions for a
   reasonable period - e.g. compatibility with an API deprecated in
   release N may only be removed in release N+2

Graduation
----------

Code in the incubator is expected to move out to its own repository to
be packaged as a standalone library or project.  When that process
starts, the ``MAINTAINERS`` file should be updated so the status of
the module(s) is "Graduating". After this all changes should be
proposed first to the new library repository, and then back-ported to
the incubator if necessary. While the module is in the Graduating
state, all bug fixes and features will need to be back-ported to the
incubator and maintained in both repositories.

After the first release of the new library, the module(s) should be
removed from the master branch of the incubator. During this phase,
only critical bug fixes will be allowed to be back-ported to the prior
stable branches. New features and minor bugs should be fixed in the
released library only, and effort should be spent focusing on having
downstream projects consume the library.

Testing Impact
--------------

Tests for incubated code should be managed in the test suite in the
``oslo-incubator`` repository. Tests should be organized in a way to
make them easy to graduate along with the production code when the
library is graduating.

The tests for incubated code should not be synced into consuming
projects.

Specialist Maintainers
----------------------

While incubating, all APIs should have at least one specialist API
maintainer. The responsibility of these maintainers and the list of
maintainers for each incubating API is documented in the
``MAINTAINERS`` file in ``oslo-incubator``.

The maintainer's +1 vote on code related to their specialty is
considered as a +2 for approval purposes.

Adoption
--------

We assume the application from which the incubated code is copied will
use the incubated version as part of the evolution process. One other
application should be identified for integration as well, to provide
more input into whether the API is sufficiently generalized. The
number of applications using the incubated module should be minimized
until the library graduates.

Library
-------

Each new incubated module should have a full life-cycle plan worked
out before incubation begins. See the default spec template in
``oslo-specs`` for details.

Anticipated API Stabilization
-----------------------------

Incubation shouldn't be seen as a long term option for any API -- it
is merely a stepping stone to inclusion into a published Oslo library.

Alternatives
============

Direct-to-Library
-----------------

Not all Oslo modules need to be incubated. Ideas for new libraries or
library components may lead to creating a library "from scratch". This
approach is suitable when the purpose of the module is understood up
front, and there is no existing code coupled to the rest of an
application's code base.

Examples of Oslo libraries that used this approach successfully
include cliff, stevedore, and taskflow.

Adoption
--------

Existing libraries, possibly created outside of the OpenStack project,
can be "adopted" by the Oslo team, who then takes over maintenance
duties.

Examples of adopted Oslo libraries include tooz and PyCADF.

Incubating in Place
-------------------

Not all application modules are tightly coupled to the other parts of
the application in which they live. In these cases, it may be faster
to evolve the API in place in the application's repository, and
graduate directly from there to a new library.

oslo.versionedobjects is an example of an Oslo library that incubated
in place (in the nova source repository).

References
==========

* File bugs for incubating APIs in the `oslo-incubator project`_ in
  launchpad.

* Instructions for the graduation process evolve over time, so we keep
  them in the wiki. See `Oslo/CreatingANewLibrary`_

* We track the graduation status of incubated code in the wiki in
  `Oslo/GraduationStatus`_.

* Mailing list discussions of handling feature requests for code being
  graduated:

  * http://lists.openstack.org/pipermail/openstack-dev/2013-November/020742.html
  * http://lists.openstack.org/pipermail/openstack-dev/2013-December/020771.html

* Mailing list discussion of deprecation process for graduating code:
  http://lists.openstack.org/pipermail/openstack-dev/2014-March/029936.html

* Mailing list discussion of the change to deleting code instead of
  marking it obsolete:
  http://lists.openstack.org/pipermail/openstack-dev/2014-August/044360.html

.. _Oslo/CreatingANewLibrary: https://wiki.openstack.org/wiki/Oslo/CreatingANewLibrary

.. _oslo-incubator project: https://launchpad.net/oslo-incubator

.. _Oslo/GraduationStatus: https://wiki.openstack.org/wiki/Oslo/GraduationStatus

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
