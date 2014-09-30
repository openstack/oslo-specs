================================
Make EngineFacade into a Facade
================================

https://blueprints.launchpad.net/oslo.db/+spec/make-enginefacade-a-facade

Problem description
===================

The oslo.db.sqlalchemy.session.EngineFacade class serves as the gateway
to the SQLAlchemy Engine and Session objects within many OpenStack projects,
including Ceilometer, Glance, Heat, Ironic, Keystone, Neutron, Nova, and
Sahara.  However, the object is severely under-functional; while it provides
a function call that ultimately calls ``create_engine()`` and
``sessionmaker()``, consuming projects receive no other utility from this
object, and in order to solve closely related problems that all of them
share, each invent their own systems, all of which are different,
verbose, and error prone, with various performance, stability,
and scalability issues.

Registry Functionality
----------------------

In the first case, EngineFacade as used by projects needs to act as a
thread-safe registry, a feature which it does not provide and for
which each consuming project has had to invent directly.   These
inventions are verbose and inconsistent.

For example, in Keystone, the EngineFacade is created thusly in
keystone/common/sql/core.py::

    _engine_facade = None

    def _get_engine_facade():
        global _engine_facade

        if not _engine_facade:
            _engine_facade = db_session.EngineFacade.from_config(CONF)

        return _engine_facade

In Ironic we have this; Sahara contains something similar::

    _FACADE = None

    def _create_facade_lazily():
        global _FACADE
        if _FACADE is None:
            _FACADE = db_session.EngineFacade(
                CONF.database.connection,
                **dict(CONF.database.iteritems())
            )
        return _FACADE

However in Nova, we get a similar pattern but with one very critical twist::

    _ENGINE_FACADE = None
    _LOCK = threading.Lock()

    def _create_facade_lazily():
        global _LOCK, _ENGINE_FACADE
        if _ENGINE_FACADE is None:
            with _LOCK:
                if _ENGINE_FACADE is None:
                    _ENGINE_FACADE = db_session.EngineFacade.from_config(CONF)
        return _ENGINE_FACADE

Each library invents their own system of establishing EngineFacade as a
singleton, and providing CONF into it; none of which are alike.
Nova happened to discover that this singleton pattern isn't threadsafe,
and added a mutex, however the lack of this critical improvement remains a
bug in all the other systems.

Transactional Resource Functionality
-------------------------------------

Adding a fully functional creational pattern is an easy win,
but the problem goes beyond that.  EngineFacade ends its work at ``get_engine()``
or ``get_session()``; the former returns a SQLAlchemy Engine object, which
itself is only a factory for connections, and the latter returns a
SQLAlchemy Session object, ready for use but otherwise unassociated with
any specific connection or transactional context.

The definition of "facade" is a layer that conceals the use of fine-
grained APIs behind a layer that is coarse-grained and tailored to the
use case at hand.   By this definition, the EngineFacade currently is
only a factory, and not a facade.

The harm caused by this lack of guidance on EngineFacade's part is widespread.
While the failure to provide an adequate creational pattern leads
each Openstack project to invent its own workaround,
the failure to provide any guidance on connectivity or transactional
scope gives rise to a much more significant pattern of poor implementations
on the part of all Openstack projects.   Each project observed illustrates
mis-use of engines, sessions and transactions to a greater or lesser degree,
more often than not having direct consequences for performance, stability,
and maintainability.

The general theme among all projects is that while they are all
presented as web services, there is no structure in place which
establishes connectivity and transactional scope for a service method
as a whole.  Individual methods include explicit boilerplate which
establishes some kind of connectivity, either within a transaction or
not.  The format of this boilerplate alone is not only inconsistent
between projects, it's inconsistent within a single project and even
in a single module, sometimes intentionally and sometimes not.
Equally if not more seriously, individual API methods very frequently
proceed across a span of multiple connections and non-connected
transactions within the scope of a single operation, and in some cases
the multiple transactions are even nested. The use of multiple
connections and transactions is in the first place a major performance
impediment, and in the second place dilutes the usefulness of
transactional logic in the first place as an API method is not
actually atomic.   When transactions are actually nested, the risk surface
for deadlocks increases significantly.

Transactional Scoping Examples
-------------------------------

This section will detail some specific examples of the issues just described,
for those who are curious.

We first show Neutron's system, which is the most
organized and probably has the fewest issues of this nature.
Neutron has a system where all database operations proceed
where a neutron.context.Context object is passed; the Context object serves
as home base to a SQLAlchemy Session that was ultimately retrieved
from EngineFacade.   A method excerpt looks like this::

    def add_resource_association(self, context, service_type, provider_name,
                                 resource_id):

        # ...

        with context.session.begin(subtransactions=True):
            assoc = ProviderResourceAssociation(provider_name=provider_name,
                                                resource_id=resource_id)
            context.session.add(assoc)

We see that while the Context object at least allows that all operations
are given access to the same Session, the method still has to state
that it wishes to begin a transaction, and that it needs to support the
fact that the Session may already be within a transaction.   Neutron's system
is a little verbose, and suffers from the issue that individual methods called
in series may invoke their work within distinct transactions on new
connections each time,  but at least ensures that just one Session is in
play for a given API method from start to finish; this prevents the issue
of inadvertent multiple transaction nesting, as the Session's ``begin()``
method will disallow a nested call from opening a new connection.

Next we look at Keystone.  Keystone has some database-related helper functions
but they don't serve any functional purpose other than some naming abstraction.
Keystone has a lot of short "lookup" methods, so many of them
look like this::

    @sql.handle_conflicts(conflict_type='trust')
    def list_trusts(self):
        session = sql.get_session()
        trusts = session.query(TrustModel).filter_by(deleted_at=None)
        return [trust_ref.to_dict() for trust_ref in trusts]

Above, the ``sql.get_session()`` call is just another call to
EngineFacade.get_session(), and that's where the connectivity is set up.
The ``sql.handle_conflicts()`` call doesn't have any role in establishing
this session.

The above call uses the SQLAlchemy Session in "autocommit" mode; in
this mode, SQLAlchemy essentially creates connection/transaction
context on a per-query basis, and discards it when the query is complete;
using the Python Database API (DBAPI), there is no cross-platform option to
prevent a transaction from ultimately being present; hence "autocommit"
doesn't mean, "no transaction".

In all but the most minimal cases, using the Session in "autocommit"
mode is not a good approach to take, and is discouraged in SQLAlchemy's
own documentation (see
http://docs.sqlalchemy.org/en/rel_0_9/orm/session.html#autocommit-mode),
as it means a series of queries will each proceed upon a brand new connection
and transaction per query, wasting database resources with expensive rollbacks
and even creating a new database connection per query under slight
load, where the connection pool is in overflow mode.  oslo.db
itself also emits a "pessimistic ping" on each connection, where a
"SELECT 1" is emitted in order to ensure the connection is alive, so emitting
three queries in "autocommit" mode means you're actually emitting *six*
queries.

It's true that for a method like the above where exactly one SELECT is
emitted and definitely nothing else, there is a little less Python
overhead in that the Session does not build up an internal state
object for the transaction, but this is only a tiny optimization; if
optimization at that scale is needed, there are other ways to make the
above system vastly more performant (e.g. use baked queries, column-
based queries, or Core queries).

While both Keystone and Neutron have the issue of implicit use of
"autocommit" mode, Nova has more significant issues, both because
it is more complex at the database level and is also more performance
critical regarding persistence.

Within Nova, the connectivity system is more or less equivalent to
that of Keystone; many explicit calls to get_session() and heavy use of
the session in "autocommit" mode, most commonly through the model_query()
function.   But more critical is that the complexity of Nova's API without a
foolproof system of maintaining transaction scope leads to
a widespread use of multiple transactions per API call, in some cases
concurrently, which has definite stability and performance implications.

A typical Nova method looks like::

    @require_admin_context
    def cell_update(context, cell_name, values):
        session = get_session()
        with session.begin():
            cell_query = _cell_get_by_name_query(context, cell_name,
                                                 session=session)
            if not cell_query.update(values):
                raise exception.CellNotFound(cell_name=cell_name)
            cell = cell_query.first()
        return cell

In the above call, the ``get_session()`` call returns a brand new session
upon which a transaction is begun; the method then calls into
``_cell_get_by_name_query``, passing in the Session in an effort to
ensure this sub-method uses the same transaction.   The intent here is
good, that the ``cell_update()`` method knows it should share its
transactional context with a sub-method.

However, this is a burdensome and verbose coding pattern which is
inconsistently applied.   In those areas where it fails to be applied,
the end result is that a single operation invokes several new
connections and transactions, sometimes within a nested set of calls;
this is wasteful and slow and is a key risk factor for deadlocks.
Examples of non-nested, multiple connection/session use within a
single call are easy to find.   Truly nested transactions are less
frequent; one is nova/db/api.py -> floating_ip_bulk_destroy. In this
method, we see::

    @require_context
    def floating_ip_bulk_destroy(context, ips):
        session = get_session()
        with session.begin():
            project_id_to_quota_count = collections.defaultdict(int)
            for ip_block in _ip_range_splitter(ips):
                query = model_query(context, models.FloatingIp).\
                    filter(models.FloatingIp.address.in_(ip_block)).\
                    filter_by(auto_assigned=False)
                rows = query.all()
                for row in rows:
                    project_id_to_quota_count[row['project_id']] -= 1
                model_query(context, models.FloatingIp).\
                    filter(models.FloatingIp.address.in_(ip_block)).\
                    soft_delete(synchronize_session='fetch')
            for project_id, count in project_id_to_quota_count.iteritems():
                try:
                    reservations = quota.QUOTAS.reserve(context,
                                                        project_id=project_id,
                                                        floating_ips=count)
                    quota.QUOTAS.commit(context,
                                        reservations,
                                        project_id=project_id)
                except Exception:
                    with excutils.save_and_reraise_exception():
                        LOG.exception(_("Failed to update usages bulk "
                                        "deallocating floating IP"))


The entire method is within ``session.begin()``.  But within that, we
first see a two calls to ``model_query()``, each of which forget to pass the
session along, so ``model_query()`` makes it's own session and transaction
for each.   But more seriously, ``get_session()`` is called many times again, without
any way of passing a session through, down below when ``quota.QUOTAS.commit``
is called within a loop.  The interface for this starts outside of the
database API, in nova/quota.py, where no ``session`` argument is available::

    def commit(self, context, reservations, project_id=None, user_id=None):
        """Commit reservations."""
        if project_id is None:
            project_id = context.project_id
        # If user_id is None, then we use the user_id in context
        if user_id is None:
            user_id = context.user_id

        db.reservation_commit(context, reservations, project_id=project_id,
                              user_id=user_id)

``db.reservation_commit`` is back in nova/db/api.py, where we
see a whole new call to ``get_session()``, ``begin()``, calling a second
time through the ``@_retry_on_deadlock`` decorator which also would best
know how to manage its scope at the topmost-level::

    @require_context
    @_retry_on_deadlock
    def reservation_commit(context, reservations, project_id=None, user_id=None):
        session = get_session()
        with session.begin():
            _project_usages, user_usages = _get_project_user_quota_usages(
                    context, session, project_id, user_id)
            reservation_query = _quota_reservations_query(session, context,
                                                          reservations)
            for reservation in reservation_query.all():
                usage = user_usages[reservation.resource]
                if reservation.delta >= 0:
                    usage.reserved -= reservation.delta
                usage.in_use += reservation.delta
            reservation_query.soft_delete(synchronize_session=False)

In the above example, we first see that the "ad-hoc-session" system and
"more than one way to do it" approach of ``model_query()`` leads
to coding errors that are silently masked, but in the case of
``reservation_commit()``, the architecture itself disallows this coding
error to even be corrected.

Examples of non-nested multiple sessions and transactions in one API call can
be found by using an assertion within the test suite.    The two main
areas this occurs in the current code are:

* instance_create() calls get_session(),
  then ec2_instance_create() -> models.save() -> get_session()

* aggregate_create() calls get_session(),
  then aggregate_get() -> model_query() -> get_session()

The above examples can be fixed manually, but rather than adding
more boilerplate, decorators, and imperative arguments to solve the problem
as individual cases are identified, the solution should instead be to replace
all imperative database code involving transaction scope with a purely
declarative facade that handles connectivity, transaction scoping and
related features like method retrying in a consistent and context-aware
fashion across all projects.


Proposed change
===============

The change is to replace the use of get_session(), get_engine(), and
special context managers with a new set of decorators and
context managers, which themselves are invoked from a
simple import that replaces the usual EngineFacade logic.

The import will essentially allow a single symbol that handles the work
of ``EngineFacade`` and ``CONF`` behind the scenes::

    from oslo.db import enginefacade as sql

This symbol will provide two key decorators, ``reader()`` and
``writer()``, as well as context managers which
mirror their behavior, ``using_reader()`` and ``using_writer()``.
The decorators deliver a SQLAlchemy Session object to
the existing ``context`` argument of API methods::

    @sql.reader
    def some_api_method(context):
        # work with context.session

    @sql.writer
    def some_other_api_method(context):
        # work with context.session

Whereas the context managers receive this ``context`` argument locally::

    def some_api_method(context):
        with sql.using_reader(context) as session:
            # work with session

    def some_other_api_method(context):
        with sql.using_writer(context) as session:
            # work with session


Transaction Scope
-----------------

These decorators and context managers will acquire a new Session using
methods similar to that of the current ``get_session()`` function if
one is not already scoped, or if one is already scoped, will return
that existing Session.   The Session will then unconditionally be
within a transaction using ``begin()``, or we may better yet switch to
the default mode of ``Session`` which is that of "autocommit=False".
The state of this transaction will be to remain open until the method
ends, either by raising an exception (unconditional rollback) or by
completing (either a commit() or a close(), depending on reader/writer
semantics).

The goal is that any level of nested calls can all call upon
``reader()`` or ``writer()`` and participate in an already ongoing
transaction.  Only the outermost call within the scope actually ends
the transaction except in the case of an exception; the ``writer()``
method will  emit a ``commit()`` and the ``reader()`` method will
``close()`` the session, ensuring that the underlying connection is
rolled back in a lightweight way.

Context and Thread Locals
-------------------------

The proposal at the moment expects a "context" object, which can be
any Python object, to be present in order to provide some object that
bridges all elements of a call stack together.   Most APIs with the notable
exception of Keystone appear to already include a context argument.

To support a pattern that does not include a "context" argument, the only
alternative is to use thread locals.  In discussions with the community,
the use of thread locals has the two concerns of: 1. it requires early patching
at the eventlet level and 2. thread locals are seen as "action at a distance",
more "implicit" than "explicit".

The proposal as stated here can be made to work with thread locals using
this recipe::

    # at the top of the api module
    GLOBAL_CONTEXT = threading.local()


    def some_api_method():
        with sql.using_writer(GLOBAL_CONTEXT) as session:
            # work with session

Whether or not we build in the above pattern, or we get Keystone to use
an explicit context object, is not yet decided.  See "Alternatives" for
a listing of various options.

Reader vs. Writer
-----------------

At the outset, ``reader()`` vs. ``writer()`` only intend to allow a block
of functionality to mark itself as only requiring read-only access, or
involving write access.   At the very least, it can indicate if the outermost
block need to be concerned about committing a transaction.   Beyond that,
this declaration can be used to determine if a particular method or block
is suitable for "retry on deadlock", and also allows systems that attempt
to split logic between "reader" and "writer" database links to know upfront
which blocks should be routed where.

While a fully specified description for open-ended support of multiple
databases is out of scope for this spec, as part of the
implementation here we will necessarily implement at least what is already
present.  The existing EngineFacade features a "slave_engine" attribute
as well as a "use_slave" flag on ``get_session()`` and ``get_engine()``;
at least the Nova project and possibly others currently make use of this
flag.  So we will carry over an equivalent level of functionality into
``reader()`` and ``writer()`` to start.

Beyond maintaining existing functionality, more comprehensive and
potentially elaborate systems of multiple database support will be
made easier to specify and implement subsequent to the rollout
of this specification.  This is because consuming projects will greatly reduce
their verbosity down to a simple declarative level, leaving oslo.db
free to expand upon the underlying machinery without incurring additional
across-the-board changes in projects (hence one of the main reasons "facades"
are used).

The behavior for nesting of readers and writers is as follows:

1. A ``reader()`` block that ultimately calls upon methods that then invoke
   ``writer()`` should raise an exception; it means this ``reader()`` is not
   really a ``reader()`` at all.

2. A ``writer()`` block that ultimately
   calls upon methods that invoke ``reader()`` should pass successfully;
   those ``reader()`` blocks will in fact be made to act as a ``writer()``
   if they are called within the context of a ``writer()`` block.

Core Connection Methods
-----------------------

For those methods that use Core only, corresponding methods
``reader_connection()`` and ``writer_connection()`` are supplied,
which instead of returning a ``sqlalchemy.orm.Session``, return a
``sqlalchemy.engine.Connection``::

    @sql.writer_connection
    def some_core_api_method(context):
        context.connection.execute(<statement>)

    def some_core_api_method(context):
        with sql.using_writer_connection(context) as conn:
            conn.execute(<statement>)

``reader_connection()`` and ``writer_connection()`` will integrate with
``reader()`` and ``writer()``, such that the outermost context will establish
the ``sqlalchemy.engine.Connection`` that is to be used for the full
context, whether or not it is associated with a ``Session``.  This means
the following:

1. If a ``reader_connection()`` or ``writer_connection()`` manager is invoked
   first, a ``sqlalchemy.engine.Connection``
   is associated with the context, and not a ``Session``.

2. If a ``reader()`` or ``writer()`` manager is invoked first, a ``Session``
   is associated with the context, which will contain within it a
   ``sqlalchemy.engine.Connection``.

3. If a ``reader_connection()`` or ``writer_connection()`` manager is invoked
   and there is already a ``Session`` present, the ``Session.connection()``
   method of that ``Session`` is used to get at the ``Connection``.

4. If a ``reader()`` or ``writer()`` manager is invoked and there is already
   a ``Connection`` present, the new ``Session`` is created, and it is
   bound directly to this existing ``Connection``.

Integration with Configuration / Startup
-----------------------------------------

The ``reader()``, ``writer()`` and other methods will be calling upon
functional equivalents of the current ``get_session()`` and
``get_engine()`` methods within oslo.db, as well as handling the logic
that currently consists of invoking an ``EngineFacade`` and combining
it with ``CONF``.  That is, the consuming application does not refer
to ``EngineFacade`` or ``CONF`` at all; the interaction with ``CONF``
is performed similarly as it is now within oslo.db only, and is done
under a mutex so that it is thread safe, in the way that Nova performs
this task.

For applications that currently have special logic to add keys to ``CONF``
or ``EngineFacade``, additional API methods will be provided.  For example,
Sahara wants to ensure the ``sqlite_fk`` flag is set to ``True``.  The
pattern will look like::

    from oslo.db import enginefacade as sql

    sql.configure(sqlite_fk=True)

    def some_api_method():
        with sql.reader() as session:
            # work with session

Retry on Deadlock / Other failures
-----------------------------------

Oslo.db provides the ``@wrap_db_retry()`` decorator, which allows an API
method to replay itself on failure.  Per
https://review.openstack.org/#/c/109549/, we will be adding specificity
to this decorator, which allows it to explicitly indicate that a method
should be retried when a deadlock condition occurs.   We can look into
integrating this feature into the ``reader()`` and ``writer()`` decorators
as well.


Alternatives
------------

A key decision here is that of the decorator vs. the context manager,
as well as the use of thread locals.

Example forms:

1. Decorator, using context::

        @sql.reader
        def some_api_method(context):
            # work with context.session

        @sql.writer
        def some_other_api_method(context):
            # work with context.session


2. Decorator, using thread local; here, the ``session`` argument is injected
   into the argument list of the API method within the scope of the decorator,
   it is *not* present in the outer call to the API method::

        @sql.reader
        def some_api_method(session):
            # work with session

        @sql.writer
        def some_other_api_method(session):
            # work with session

3. Context manager, using context::

        def some_api_method(context):
            with sql.using_reader(context) as session:
                # work with session

        def some_other_api_method(context):
            with sql.using_writer(context) as session:
                # work with session

4. Context manager, using implicit thread local::

        def some_api_method():
            with sql.using_reader() as session:
                # work with session

        def some_other_api_method():
            with sql.using_writer() as session:
                # work with session

5. Context manager, using explicit thread local::

        def some_api_method():
            with sql.using_reader(GLOBAL_CONTEXT) as session:
                # work with session

        def some_other_api_method():
            with sql.using_writer(GLOBAL_CONTEXT) as session:
                # work with session

The author favors approach #1.   It should be noted that *all* the above
approaches can be supported at the same time, if projects cannot agree
on an approach.

Advantages to using a decorator only with an explicit context are:

1. The need for thread locals or any issues with eventlet is removed.

2. The "Retry on deadlock" and other "retry" features could be
   integrated into the ``reader()`` / ``writer()`` decorators, such that
   all API methods automatically gain this feature.   As it stands,
   applications need to constantly push out new changes each time an
   unavoidable deadlock situation is detected in the wild, adding their
   ``@_retry_on_deadlock()`` decorators to ever more API methods.

3. The decorator reduces nesting depth compared to context managers, and
   is ultimately less verbose, save for the need to have a "context"
   argument.

4. Decorators eliminate the possibility of this already-present
   antipattern::

    def some_api_method():
        with sql.writer() as session:
            # do something with session

        # transaction completes here

        for element in stuff:
            # new transaction per element
            some_other_api_method_with_db(element)

Above, we are inadvertently performing any number of distinct
transactions, first with the ``sql.writer()``, then with each call to
some_other_api_method_with_db().  This antipattern can already be seen
in methods like Nova's ``instance_create()`` method, paraphrased
below::

    @require_context
    def instance_create(context, values):

        # ...  about halfway through

        session = get_session()

        # session / connection / transaction #1
        with session.begin():
            # does some things with instnace_ref

        # session / connection / transaction #2
        ec2_instance_create(context, instance_ref['uuid'])

        # session / connection / transaction #3
        _instance_extra_create(context, {'instance_uuid': instance_ref['uuid']})

        return instance_ref

Because the context manager allows unnecessary choices about when a
transaction can begin and end within a method, we open ourselves up to make
the wrong choice, as is already occurring in current code.  Using a decorator,
this antipattern is impossible::

    @sql.writer()
    def some_api_method(context):
        # do something with context.session

        for element in stuff:
            # uses same session / transaction guaranteed
            some_other_api_method_with_db(context, element)

        # transaction completes here

One advantage to using an implicit "thread local" context is that it is impossible
to inadvertently switch contexts in the middle of a call-chain, which would
again lead to the nested-transaction issue.

An advantage of using context managers with implicit threadlocals is that
it would be easier for Keystone to migrate to this system.


Impact on Existing APIs
-----------------------

Existing projects would need to integrate into some form of the
patterns given.


Security impact
---------------

none

Performance Impact
------------------

Performance will be dramatically improved as the current use of many
redundant and disconnected sessions and transactions will be joined together.


Configuration Impact
--------------------

none.


Developer Impact
----------------

new patterns for developers to be aware of.

Testing Impact
--------------

As most test suites currently make the simple decision of working with
SQLite and allowing API methods to make use of their usual get_session() /
get_engine() logic without any change or injection, little to no changes
should be needed at first.   Within oslo.db, the "opportunistic" fixtures
as well as the DbTestCase system will be made to integrate with the
new context manager/decorator system.



Implementation
==============

Assignee(s)
-----------

Mike Bayer

Milestones
----------

Target Milestone for completion:

Work Items
----------


Incubation
==========

Adoption
--------

Library
-------

Anticipated API Stabilization
-----------------------------


Documentation Impact
====================

Dependencies
============


References
==========


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

