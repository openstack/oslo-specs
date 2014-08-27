=============================================================================
Run database tests within long-lived schemas and transactionalized containers
=============================================================================

https://blueprints.launchpad.net/oslo/+spec/long-lived-transactionalized-db-fixtures

Problem description
===================

OpenStack applications currently do not include a standard technique of
testing database-enabled code against any number of potential database
backends.  The techniques that are available themselves have issues
that keep them from being practical in a general sense.

* It is common that the test suite of a particular OpenStack component
  is ultimately hardcoded to run on the SQLite backend.   SQLite is chosen
  both for it's simplicity and great speed of schema setup, but is not
  the actual database used in OpenStack environments.  The system by which
  this connectivity is established is often buried and spread across
  multiple files, with no option to alter what database is used.

* There is no solution to the case of the component that wishes to run hundreds
  of tests against a common schema, without requiring that the schema
  in question is built and torn down for every test.  This makes it
  infeasible for the test suite to be run against non-SQLite backends on
  a regular basis, as the cost of this setup and teardown is too time
  consuming.  A typical approach to
  this problem is to run tests inside of transactions which are rolled
  back at the end of the test, thereby allowing the schema to
  remain present.  However, experiments with simplistic, single-database
  versions of this approach have failed due to the use of parallel testing,
  as well as being able to allow tests themselves to retain rudimental
  "commit/rollback" functionality without impacting the isolation of the
  fixture.

* While there is a system by which an application can run a suite of tests
  against other backends, known as the "Opportunistic" test suite, currently
  the "opportunistic" suite will fix those tests against a single, alternate
  backend, such as MySQL or Postgresql.    While a "stub" suite can be added
  for each desired backend so that the same tests run on each, this approach
  does not accommodate attempting to run the suite against new backends
  not anticipated by the application, and also places the responsibility
  on the developer to ensure that all tests which apply to variable backends
  include that these "stubs" are present in multitude.

* The connection URL for "opportunistic" tests is also a fixed URL, with a
  hardcoded username/password and the requirement that the database is on
  localhost.   If such a URL is connectable, it is used.  This hardcoding
  and "opportunistic" style makes it inconvenient to control how tests run;
  for example, a workstation that has both MySQL and Postgresql servers running
  with the hardcoded username/password available cannot control a test run to
  only test against one or the other, or neither, of these databases; the suite
  will always run applicable tests against both based on their presence.  It
  is also not possible for the developer to point the test suite at a
  server running on a host other than "localhost".   The scheme used by
  this system is also hardcoded to the notion of a user/password/hostname
  based configuration; it can't work for databases that connect using a
  data source name or other symbolic name.

* The system by which "opportunistic" tests create and drop databases does
  not offer adequate extensibility for new backends.


Proposed change
===============

The proposed changes will in all cases ensure that total compatibility is
retained for all current test setup techniques.  The opportunistic system
will continue to work as it does now, but offer environmental options to
alter its behavior.

The key component will be the oslo/db/sqlchemy/provision.py
module, as well as the oslo/db/sqlalchemy/test_base.py module.
This provision module currently contains logic which handles the creation
and dropping of anonymously named databases within the Postgresql and
MySQL backends.   When combined with the OpportunisticFixture, it
creates/drops an anonymously named database per test setup/teardown.
test_base includes the base test classes and fixtures which make
use of provision.py for connectivity.

These modules will be enhanced to include several new constructs,
described in the following sections.

Backend
-------

This is an extensible "backend" system, based on a base class known as
the Backend and used by the provision module.  Backend will
encapsulate the tasks needed in order to run tests against a particular
backend, including:

* the ability to detect if a given database is available, either
  "opportunistically" or through environmental settings

* the ability to create, drop, and detect the presence of "anonymously"
  named databases

* the ability to produce a connection URL that will directly access this
  database upon connect

* the ability to drop individual all schema objects within
  a database of this type.

Logic for these features can vary across backends.  For SQLite, which may be
using in-memory databases or file-based databases, the URL scheme
is SQLite-specific and needs to be generated from an anonymous schema
name in a special way.  For a Postgresql database, the backend will benefit
by including the feature of disconnecting all users from a target database
before dropping it, or being able to handle Postgresql's ENUM
type that must be dropped explicitly when erasing the objects within
a database.

Opportunistic URLs
-------------------

The Backend system can report on whether or not a database of a particular
backend type (e.g. MySQL, SQlite, Postgresql, etc) is available based on
the "opportunistic" URL system.  This system defaults to searching for
a database given a fixed connectivity profile.   Suppose the system
includes a Backend implementation for each of: SQlite, Postgresql, and
MySQL.  Each of these backend implementations reports on a candidate
"opportunistic" URL; a URL such as
"postgresql://openstack_citest:openstack_citest@localhost" that can be tested
for connectivity.   Without any configuration, the system will attempt
to make available "opportunstic" URLs for each BackendImpl that is implemented.
In this way, the system works pretty much as it does today.

However,  to make it configurable at runtime, we will enhance the role
of the OS_TEST_DBAPI_ADMIN_CONNECTION environment variable.  The
current system allows this variable to specify a single "override" URL
that is linked to the SQLite tests, but not the "opportunistic" ones.
In the new system, it will allow a list of URLs, separated by a
semicolon.  For example, a value that allows tests to run against a specific
SQLite database as well as a Postgresql database::

  export OS_TEST_DBAPI_ADMIN_CONNECTION=\
         /path/to/sqlite.db;\
         postgresql+psycopg2://scott:tiger@localhost/openstack

When an explcit OS_TEST_DBAPI_ADMIN_CONNECTION is present, those URLs
determine the complete list of BackendImpls that will  report
themselves as available, and overrides the usually fixed
"opportunistic" URLs.  With this function, the list of database
backends as well as their full connectivity information can be
determined at runtime.


Provisioning
------------

The provision module will call upon Backend in order to produce a
"provisioning" system that works at three levels: database, schema,
and transaction.   The management of these three levels of resource will
be maintained over the span of any number of tests.

A "database" will typically be maintained on a per-backend basis over
the span of all tests run within a single Python process.   By ensuring
that an anonymous database is created per process for a given backend,
the test suite can be safely run in parallel with no danger of concurrent
tests colliding with each other.  The current approach is that this database
is created and dropped per-test; allowing the same database to persist across
all tests in a run will reduce load and complexity.

A "schema" consists of a set of tables and other schema constructs that
are created within a database.  The vast majority of OpenStack applications
run their tests within a single schema corresponding to their models.
Most of these tests only need to exercise data manipulation within these
schemas; a second class of test, the "migration" test, is less common and
requires that it actually create and drop components of these schemas.

To support tests that exercise data manipulation within a fixed schema,
the provisioning system will call upon an app-specific "create schema" hook
when a newly created database is about to be used, within the scope of a
so-called "schema scope".  This schema will then remain in place as long
as additional tests which also specify the same scope continue to be
invoked.  A "schema scope" is a string symbolic name
that any number of tests can refer to, to state that they all run within
the same schema.  For example, if four different test suites in Nova all
stated that their "SCHEMA_SCOPE" is "nova-cells", and these suites all referred
to a "create schema" function that generated the nova model, the
"create schema" function would be invoked just once, and then all four test
suites would be run fully against the target database.   The cleanup of data
changes made by these tests is achieved using transaction rollbacks, rather
than by dropping the whole database.

To support tests that are testing schema migrations and wish to create and
drop their own schema elements, those tests specify a "SCHEMA_SCOPE" of None;
the provisioning system will provide to these tests an empty database, and
upon release of the provision, a DROP will be performed for any schema objects
that still remain.

A "transaction" is an optional unit that is built up and torn down on a
per-test basis.   This feature is used when the test base specifies that
it wishes to have "transactional" support, which is implied when a non-None
"SCHEMA_SCOPE" is specified.  This feature makes use of SQLAlchemy's
Engine and Connection system in order to produce a mock "transaction"
environment transparently provided to the test.  Within this environment,
any calls to "commit" the transaction don't actually commit for real.
Tests are given the ability to emit rollbacks that work by also wrapping
the environment within a SAVEPOINT.  This is based on a technique that
is commonly used with SQLAlchemy and is presented in various forms within
the documentation as well as in talks; in this case, the technique will be
enhanced to work not just at the ORM level but at the Core level as well,
so that even applications that use the Core directly can participate in
the transactionalized environment.

The SQLite backend has long had issues with SAVEPOINT, however in support
of this feature, the backend is repaired in oslo.db using recent
hooks; see https://review.openstack.org/#/c/113152/ for the review.

Fixture Integration
-------------------

The provisioning system will be integrated into the test suite by taking
advantage of the `testresources <https://pypi.python.org/pypi/testresources>`_
library, which provides a system of
allocating resources that may last across the span of multiple tests.
``testresources`` works by maintaining the state of various resources
within a dependency tree, that is tracked as many tests proceed.   Only
when a given resource reports itself as "dirty" is it torn down
for the next test, and the final teardown only occurs once that resource
is no longer needed.

Tests that use testresources by default will function normally, however
the resources that they require will be fully created and dropped on a
per-test basis, unless additional steps are taken which are specific
to the testtools package.  The tests therefore
will remain compatible with any style of test runner, however the optimization
or resources require the use of the testr or testtools runner, or with
some extra work, the standard Python unittest runner.

In order to optimise resources among multiple tests, the tests must
be assembled into the ``OptimisingTestSuite`` object provided by
testresources.  Integration of ``OptimisingTestSuite`` typically
requires that the unittest-supported
``load_tests()`` directive be stated either within an individual test module,
or at the package level (e.g. ``__init__.py``), which will replace the usual
system of test discovery with one which assembles the tests into a master
``OptimisingTestSuite``.    It is assumed that we will be able to provide
a single oslo.db directive that can be dropped into the top-level
``__init__.py`` file of a test suite as a whole in order to provide this
effect.

In order to integrate with ``testresources``, the concepts of "database",
"schema", and "transaction" will be implemented as individual test resource
object types.

Scenarios
---------

Scenarios refers to the use of a tool like  `testscenarios
<https://pypi.python.org/pypi/testscenarios/>`_, so that individual
tests can be run multiple times against different backends.  The
existing Opportunistic fixture system will be enhanced such that the
"DRIVER" attribute, which refers right now to a single type of
database backend, can refer to a set of types.  Each test will then be
run against those drivers that are deemed to be available by the
Backend system.

Usage within Actual Tests
-------------------------

Real world tests take advantage of the system by using
``oslo.db.sqlalchemy.DbTestCase``.   This test case superclass acts much
like it always has, providing ``self.session`` and ``self.engine`` members to
use for database connectivity.   However, the class can now mark via
class-level annotations which databases it is appropriate towards, and what
schema.  For example, Nova can suggest a test suite against the Nova schema
and to run against SQLite, Postgresql, and MySQL as follows::

  class SomeNovatest(DbTestCase):

      SCHEMA_SCOPE = "nova-cells"
      DRIVER = ('sqlite', 'postgresql', 'mysql')

      def generate_schema(self, engine):
          """Generate schema objects to be used within a test."""

          nova.create_all_tables(engine)

      def test_something(self):
          # do an actual test

The above class specifies how schemas are to be generated within the
``generate_schema()`` method, which is called upon by the provisioning system
to produce a schema corresponding to the "nova-cells" schema scope.
As many test suites may use the same ``generate_schema()`` method, it is
probably best to link ``generate_schema()`` with ``SCHEMA_SCOPE="nova-cells"``
on a common mixin.

In order to integrate with testresources, the above set of directives will
be used to compute the full set of test resource manager objects to
be delivered via the ``.resources`` hook; this is an attribute that's bound
to the ``DbTestCase`` class itself which testresources looks for in order
to determine what kinds of resource objects are needed for the specific test.
The implementation uses a Python descriptor for ``.resources`` so that its
value is dynamically determined on a per-test basis.


Alternatives
------------

The decision to use testresources is made against two other variants
that don't use it.  All three variants are discussed here.

* The testresources library provides a means of spanning resources across
  tests that integrates with the mechanics of the standard Python
  unittest.TestSuite object, as well as the load_tests() hook which is used
  to estalibish TestSuite objects into a single OptimisingTestSuite.
  These mechanics are not fully or at all available in other commonly used
  test runners, including nose and py.test.

  Advantages to testresources include that it is the standard system that
  goes along with the other use of testtools, and provides a sophisticated
  system of organizing tests to make the best use of resources declared by
  each.   It's test manager API sets up a clear system of declaration and
  dependency between the various types of resource proposed in the
  provisioning system.

  Disadvantages are that the optimising behavior is only available
  with a testtools-style run, or with a unittest-style run if additional
  steps are taken to integrate OptimisingTestSuite, as unittest itself
  does not appear to honor a package-level load_tests() hook.

  Still to be resolved are some remaining issues with the load_tests() hook
  as implemented in the top-level ``__init__.py`` file when the "start"
  directory is that directory itself; it seems that the ``load_tests()``
  hook is skipped in this case, and may require that oslo.db's own tests
  are reorganized such that all tests can be loaded from named packages.
  However note that this issue is not a blocker; the ``load_tests()`` hook
  works fine as placed within specific test modules or within ``__init__.py``
  files that are loaded as packages, which is the case for the vast majority
  of openstack tests suites.

* Maintain awareness of test suite start/end per process using the Testr
  "instance provision" hooks.   These hooks allow a set of fixed database
  names to be generated before tests run, to provide this name to the
  provisioning system within each subprocess, and finally after all
  test suites are finished, to emit a DROP for each database name on all
  available backends.   The system can create databases lazily and only
  drop those which actually got created.

  The configuration looks like this::

    instance_provision=${PYTHON:-python} -m oslo.db.sqlalchemy.provision echo $INSTANCE_COUNT
    instance_execute=OSLO_SCHEMA_TOKEN=$INSTANCE_ID $COMMAND
    instance_dispose=${PYTHON:-python} -m oslo.db.sqlalchemy.provision drop --conditional $INSTANCE_IDS

  The "instance provision" hook does not actually create any databases; only
  string names of databases that will be used if a database of a particular
  backend is requested during the test run.  The "instance dispose" hook
  then delivers these names to the "drop" command, which will drop the
  named database on all possible backends if it is shown to exist; else the
  name is skipped.

  This system runs mostly as efficiently as the testresources system,
  and still degrades gracefully when using other test runners.

  The advantage to this system is that it is independent of the mechanics
  of unittest, and has only very simplistic hooks within testr which can
  easily be made to work with other test runners as well.  It also does not
  require any package- or module-level load_tests() hooks and does not involve
  any changes to the ordering of tests.

  Disadvantages include that it is more of a "homegrown" approach that
  reinvents a lot of what testresources already does.   It may be more
  advantageous to look into enhancing testresources itself to be more
  easily integrated with other kinds of test runners.

* Maintain awareness of test suite start/end process by ensuring that the
  suite always runs within a special shell script that essentially runs
  the same commands and environmental settings as the testr hook.

  This system is similar to that of using testr hooks, and both systems
  can coexist.

  The disadvantages include not just those of the testr approach but also
  that shell scripts are complicated and ad-hoc, so in that sense there's
  even more code being reinvented here.


Impact on Existing APIs
-----------------------

Test suites which wish to take advantage of this system will need to base
themselves on the new mechanics of DbTestCase, and to rework any existing
systems they have of setting up connections or schemas to work within
the new system.   They will also need some kind of module- or package-level
load_tests() directive in order to load up the OptimisingTestSuite system.

Security impact
---------------

none

Performance Impact
------------------

A key deliverable of this blueprint is to significantly improve performance
for test suites that wish to run many tests against a common schema on
heterogeneous database backends.

Configuration Impact
--------------------

The configuration of the test runner may be impacted based on integration
approach.   The changes should be deliverable to gate runs without any
direct changes to gates.

Developer Impact
----------------

Developers should be aware of the DbTestCase base fixture, its
implications, and will want to use it for tests that work against
the database in a serious way.

Testing Impact
--------------

The individual components of the system will have their own tests
within oslo.db, to ensure database setup/teardown as well as to ensure
that the transactional container works as expected.

Implementation
==============

Assignee(s)
-----------

Mike Bayer has already prototyped everything except scenario support,
based on the use of testresources.

Robert Collins is also contributing towards issues observed in ensuring
that testtools loads up all Python packages as packages, so that the
load_tests() hook runs in all cases.

Milestones
----------

N/A

Work Items
----------

* Build out provisioning system and backend system.   This is already
  complete including the integration with testresources.

* build out the test scenarios integration - still a TODO

* implement the means by which load_tests() will be integrated, this is
  complete.

* documentation


Incubation
==========

N/A

Adoption
--------

Nova, Neutron and Keystone might be good starts.

Library
-------

oslo.db

Anticipated API Stabilization
-----------------------------

unknown

Documentation Impact
====================

Docstrings regarding DbTestCase.

Dependencies
============

Testresources and testscenarios.

References
==========

Original bug: https://bugs.launchpad.net/oslo/+bug/1339206

Current prototypes: https://review.openstack.org/#/q/status:open+project:openstack/oslo.db+branch:master+topic:bug/1339206,n,z


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

