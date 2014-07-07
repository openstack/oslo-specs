=================================================================
Use a Filter API with SQLAlchemy Engine Events for Error Wrapping
=================================================================

https://blueprints.launchpad.net/oslo/+spec/use-events-for-error-wrapping

The system that oslo.db provides for transformation of SQLAlchemy execution-
time errors, including DBAPI and related errors, should be improved
to be simpler, more portable, more forwards-compatible, more extensible,
and more testable.

Problem description
===================

oslo.db presents a system by which common exceptions raised within SQLAlchemy
are intercepted and usually converted to an oslo-specific exception
within ``oslo.db.exception``.  The mechanism by which this occurs involves
placing a wrapper function around key ORM ``Session`` methods such that when
they are invoked and raise an exception, the exception is caught by
a handler function which makes some immediate decisions about the exception,
then potentially hands it off to a series of "exception match" functions.
The oslo.db test suite contains a variety of tests for this system,
with separate test suites for different kinds of exceptions.

Key issues in the current implementation of this system include:

* In order to place the error interceptor where statements are executed,
  oslo.db presents a ``Session`` subclass which then lists out key methods
  that invoke database queries, and wraps them with a wrapper called
  ``@_wrap_db_error``.  This approach misses many ORM-level
  methods, such as all of those on top of the ``Query`` object itself
  (see https://review.openstack.org/#/c/92002/ for one such issue),
  the lazy loading emitted by mapped attributes that are unloaded or
  expired, as well as the entire Core level system, which is exposed
  even at the ORM level in the case of ``Session.execute()``
  in the form of the result object, which also can throw database-level
  exceptions on row access.    The system in its current form cannot be
  expanded to cover every possible access without great difficulty,
  particularly with regards to ORM-instrumented attributes.
  Even if this system could be expanded to cover every
  possible method, it isn't forwards compatible with new systems that might
  also invoke statement execution from different start points.

* The error interceptor itself provides an imperative
  (read: lots of conditionals) system of intercepting exceptions and
  routing them to different decision paths.  Some exceptions, such as
  ``UnicodeEncodeError`` to ``DBInvalidUnicodeParameter``, are handled directly
  inside of ``@_wrap_db_error``.  Others, such as those of deadlocks
  and duplicate rows, are handed off to other functions, which
  themselves contain a fair degree of imperative logic, particularly
  the case of the "duplicate row" handler.  Adding support for new
  exception scenarios necessitates adding new conditionals to these
  systems, destabilizing the logic for all of them as they are all
  interrelated.

* The system of unit testing the exception filters is inconsistent and
  incomplete.  The ``_wrap_db_error()`` function itself has only 14
  out of 27 code lines total covered by tests; about half of the potential
  error scenarios aren't fully tested.  Additionally, the tests, such as
  ``TestDBDeadlocked``, test the error filter function
  ``_raise_if_deadlock_error()``, but don't test it in context of the full
  ``_wrap_db_error()`` function.  If a different filter function
  such as ``_raise_if_db_connection_lost()`` is inadvertently catching
  this error, that scenario is not being tested.  It's not easy to add tests
  for new error scenarios as the testing system takes different approaches
  for different exceptions.


Proposed change
===============

oslo.db will take advantage of a SQLAlchemy ``Connection``-level hook
that is called for all DBAPI-generated exceptions that SQLAlchemy itself
intercepts within the statement execution and result-fetching phases.
While such a hook, ``dbapi_error()``, has been supported
within SQLAlchemy since 0.7, it will be superseded by a new hook,
``handle_error()``, which is fleshed out to ensure that it is invoked for all
possible errors that SQLAlchemy itself handles, not just DBAPI-level
exceptions, as well as such that it supports conversion
of the given exception into a new one.

The mechanism for the ``handle_error()`` hook, which will be released in
SQLAlchemy 0.9.7, will be available for all prior versions of SQLAlchemy
listed in requirements.txt by back-porting the event into oslo.db directly,
using a custom ``Connection`` subclass, which SQLAlchemy supports
replacement of via the ``Engine`` that serves as its factory.
This aspect of the change is similar to the current approach that subclasses
``Session``, and technically can satisfy the feature going forward on its own;
however, allowing SQLAlchemy to provide this event natively from 0.9.7 forward
means that oslo.db's compatibility layer only needs to target already-released
versions of SQLAlchemy, with no risk that the ``Connection`` subclass approach
changes in future versions, as it won't be used for future versions.

Within the ``handle_error()`` listener, the logic for ``_wrap_db_error()``
will be unrolled into a declarative system, where functions can be declared
that present a filter for a specific database / exception / regular expression
combination.   These filters will be interpreted by a generic system
that ensures the correct filter is called for a given exception input.  The
existing rules, in particular the regular expressions and the notes regarding
them, can be maintained and ported to the new system without being changed,
so the existing work that's been done on this system based on real
database observation is maintained.

An example of such a filter looks like::

  @filters("mysql", sqla_exc.OperationalError, r"^.*\(1213, 'Deadlock.*")
  @filters("postgresql", sqla_exc.OperationalError, r"^.*deadlock detected.*")
  def _deadlock_error(operational_error, match, engine_name, is_disconnect):
      raise exception.DBDeadlock(operational_error)

In the above approach, support for new database backends and newly intercepted
exceptions can be added with no impact on existing rules.

On the testing side, a similar framework will allow construction of
exception filter tests using a consistent system that runs from
SQLAlchemy's point of statement execution up through the filtering routine
to the end result.   The key to this system will be to mock the
``Dialect.do_execute()`` method of the current engine's dialect, such that
a specific exception, including a mock DBAPI-level exception, can be raised.
All exception scenarios will be easy to inject here, and the system of filters
and actions can be covered 100%.


Alternatives
------------

The errors could be handled at more of a framework level.   If all
oslo.db applications used the database code within some common
wrapper, such as a univerally used "transaction" wrapper, consistent
exception handling could occur at that level as well.   We aren't
doing this because current database approaches are not at this level
of consistency, and it also places a restriction on all code that will
have the effect of unexpected and unhandled exceptions being raised if
this restriction isn't obeyed in all cases.

For routing of exceptions, an even-more data-driven system could be used,
such as a rules engine that expresses exception filtering and handling using
names.   We aren't doing this because it would be too heavy-handed; as it
stands, we have a data-driven approach at the exception filtering level,
which moves into programmatic at the point at which we handle what to
do with the now-intercepted exception.  This seems like a good way to leverage
Python's abilities to treat functions as data structures.

Impact on Existing APIs
-----------------------

The change should not have impact outside of oslo.db except to the extent
that other systems are making explicit use of ``_wrap_db_error()``.  This
function is underscored as private so should not be the case, however
if it is, we can provide ``_wrap_db_error()`` that is a do-nothing method,
as the new filtering system takes place well beneath that layer.

Security impact
---------------

None.

Performance Impact
------------------

The ``handle_error()`` event and the filtering system use a negligible
additional amount of comparison and iteration compared to that of the
current system.  Both systems are only invoked after an exception
has been raised, which is already a non-performant branch within Python,
so any slight difference in performance has essentially no impact in any case.


Configuration Impact
--------------------

None.

Developer Impact
----------------

The oslo.db.exceptions system would now be in effect for all SQL operations.
Existing systems that aren't covered by the existing system would now
invoke the new behavior.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  zzzeek

Other contributors:
  None

Milestones
----------

The initial prototype implementation is complete and will be put up as a
Gerrit accompanying this blueprint.

Work Items
----------

1. Implement the ``handle_error()`` event and tests within SQLAlchemy and
   prepare for 0.9.7 release.

2. Implement the ``handle_error()`` compatibility layer within oslo.db,
   porting selected elements of both the logic and tests from the
   SQLAlchemy change.  This will take place in a new sub-package
   ``oslo.db.sqlalchemy.compat``, which will be where various SQLAlchemy
   backwards-compatibility systems of this nature will start to go.

3. Ensure the oslo.db layer works on 0.7, 0.8, and 0.9 series of SQLAlchemy.

4. Rework ``_wrap_db_error()`` and sub-functions into the declarative filter
   system, install the filter within the
   ``oslo.db.sqlalchemy.session.create_engine()`` factory.

5. Locate all test suites within tests/ that are testing various parts of
   the exception integration system and convert them to use the new system.

Incubation
==========

None.

Adoption
--------

None.

Library
-------

oslo.db

Anticipated API Stabilization
-----------------------------

None.

Documentation Impact
====================

If there is documentation in oslo.db regarding exception handling, the fact
that this handling is installed into the ``Engine`` at a core level should
be mentioned.

Dependencies
============

- This change is dependent on the integration of SQLAlchemy 0.7, 0.8,
  0.9 versions into the tox.ini suite, which has been merged.

References
==========

This feature was discussed in the SQLAlchemy and OpenStack wiki page
at https://wiki.openstack.org/wiki/OpenStack_and_SQLAlchemy#Exception_Rewriting.


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

