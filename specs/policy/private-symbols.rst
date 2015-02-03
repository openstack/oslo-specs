==============================================
 Public vs. Private Symbols in Oslo Libraries
==============================================

The Oslo team differentiates between "public" and "private" parts of
Oslo libraries using "``_``" as a prefix in private names. Code using
private symbols is going to break as we move things around in the
libraries, so it should be changed to avoid those symbols.

Problem Description
===================

The Oslo team strives to create stable APIs for all Oslo libraries. We
try to follow good practices for defining those APIs, by making them
as small as possible at first and by extending them in
backwards-compatible ways, slowly over time.

One challenge we have in doing this is with protecting implementation
details from consuming projects. Languages like C++ and Java have
language-level constructs for hiding data and methods inside classes
and modules. Python is a more open language, and has no parallel to
those data-hiding facilities. Instead, Python developers have adopted
conventions of designating private parts of libraries by naming
symbols that are "private" with a single underscore as the prefix for
the name and by explicitly documenting the supported public interface
of a library. The Oslo team is following these conventions throughout
the Oslo code base.

The work we started during the Kilo cycle to `move out of the "oslo"
namespace package`_ exposed places in several projects where symbols
we have marked as private are being imported and used
directly. Usually this happens in tests, but not always. This was the
source of problems in a couple of applications as we released new
versions of the libraries where those private symbols either no longer
exist or have moved to a new location.

Proposed Policy
===============

As a result of the repeated issues with recent releases, we have built
some tools to let us run the tests for projects with pre-release
versions of the libraries, which we are using to minimize issues for
now.  At the same time, we do expect to be able to change the
implementation details of libraries fairly freely -- that's why we go
to such lengths to designate the public API, just as with the REST
APIs of the applications.

We expect consuming projects to honor the private designations of
symbols and to avoid using them directly or mocking them in
tests. Where it is impossible or inconvenient to mock the public API
of the library, we have provided (and will continue to add) fixtures
for configuring libraries to be used in application unit tests. We
also have `documentation for the public APIs of all Oslo libraries`_
to try to make clear what portion of the API is considered stable and
supported.

There are a couple of easy guidelines for determining what part of a
library is private:

1. If the name of the module, class, function, variable, attribute, or
   other symbol starts with "``_``" it is private and should not be
   used.

2. If the symbol is not documented, it may be private and should
   probably not be used. There may be symbols we've missed in the
   documentation, so please ask in #openstack-oslo or on the
   mailing list if you aren't sure.

Alternatives & History
======================

Automatically Run the Tests in the Gate
---------------------------------------

Running the unit tests for consuming projects before every release is
*very* expensive. A single pre-release of oslo.i18n currently requires
running test jobs against 37 repositories. We run the py27 and pep8
jobs for each of those projects, so we actually run 74 jobs. We cannot
do that on the CI infrastructure without consuming enough VMs to
`negatively impact the ability to land patches elsewhere`_, so we
are using other resources and doing the testing by hand.

Manually Run the Tests Before Releases
--------------------------------------

Running the tests by hand before releases will delay important patches
and bug fixes from being released quickly. It also requires individual
library maintainers to have access to enough resources to run all of
the unit tests.

Implementation
==============

Author(s)
---------

Primary author: Doug Hellmann

Other contributors: None

Milestones
----------

We will be running these tests for the remaining namespace package
releases, to try to minimize further breaks. However, we do not plan
to continue doing this level of testing by hand after the namespace
package changes are completed (currently scheduled for the Kilo-2
milestone) because we do not anticipate having the same level of code
churn.

Work Items
----------

N/A

References
==========

* https://blueprints.launchpad.net/oslo-incubator/+spec/drop-namespace-packages
* https://etherpad.openstack.org/p/juno-infra-library-testing
* http://docs.openstack.org/developer/openstack-projects

.. _move out of the "oslo" namespace package: https://blueprints.launchpad.net/oslo-incubator/+spec/drop-namespace-packages
.. _negatively impact the ability to land patches elsewhere: https://etherpad.openstack.org/p/juno-infra-library-testing
.. _documentation for the public APIs of all Oslo libraries: http://docs.openstack.org/developer/openstack-projects


Revision History
================

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Icehouse
     - Introduced
   * - Kilo
     - Formalized during the move out of the ``oslo`` namespace package.


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

