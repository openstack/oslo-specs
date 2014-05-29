========================================
Add tpool proxy wrapper for DB-API calls
========================================

https://blueprints.launchpad.net/oslo/+spec/add-tpool-proxy-wrapper

During Icehouse release cycle in order to drop dependency on eventlet we
removed eventlet ``tpool.Proxy`` helper and the corresponding config option
(``use_tpool``) from oslo.db code. Projects were supposed to store those in
their source trees. Since then we've got a lot of push back from Nova and
Cinder teams based on their experience of adoption of oslo.db changes. To
make things easier for oslo.db users, it'd actually be better to provide
optional integration with eventlet ``tpool.Proxy`` as a separate module within
oslo.db tree.


Problem description
===================

Most OpenStack deployments nowadays use MySQL. Unfortunately, the most popular
MySQL Python DBAPI driver - ``MySQL-Python`` - has a serious problem with
eventlet green threads: being a C-extension it hangs the process on blocking
DB queries (as eventlet can't monkey patch it to force a green thread switch
on blocking reads/writes from/to a socket).

eventlet provides a work around for this problem: ``tpool.Proxy`` helper class
is meant to wrap classes/modules which methods/functions might possibly block
the execution of a green thread. The call is performed in the context of a
real OS thread, which knows how to deal with eventlet thread pool, on return
it will switch the execution context back to a green thread, so the process
doesn't hang.

Common DB code used to provide ``use_tpool`` option which enabled
``tpool.Proxy`` proxying for all database methods calls. This was used by Nova
at least.  It's worth mentioning, that in order to actually use ``use_tpool``
option one had to use a patched version of eventlet, as neither PyPI releases
nor master HEAD play nicely with ``MySQL-Python``.

During Icehouse release cycle we worked on removing extra dependencies from
common DB code. eventlet was removed as one of the dependencies we thought were
unnecessary (as oslo.db should neither enforce you to use a particular
concurrency model, nor it can make any assumptions how the target projects
process concurrent requests, whether they use eventlet green threads, real
OS threads, multiple processing, etc). But the best is the enemy of the good,
and it seems that it's actually better to provide optional integration with
eventlet ``tpool.Proxy``, so the people wouldn't need to do this in their
source trees.


Proposed change
===============

To make it possible to use oslo.db with ``MySQL-Python`` DB API driver and
eventlet ``tpool.Proxy`` call proxying we need:

1. Provide a helper that will either call ``DBAPI`` methods directly or use
   ``tpool.Proxy`` to wrap the calls depending on the value of ``use_tpool``
   config option set.
2. Make this proposed helper register ``use_tpool`` config option in group
   ``database``.
3. Add an additional entry point to oslo.db, that will expose ``use_tpool``
   config option to projects.
4. Even though we'll use eventlet ``tpool.Proxy`` class at runtime, we are not
   going to add it to oslo.db ``requirements.txt`` (we don't want eventlet to
   be an install time dependency; if you use eventlet, it will be up to you to
   ensure it's installed) and ``test-requirements.txt`` (that would prevent us
   from running unit tests on Python 3.x versions; as we don't need to test
   ``tpool.Proxy`` functionality itself, we could safely mock this class in
   tests).


Alternatives
------------

The alternative way to solve this would be:

1. Put this helper into ``openstack.common.concurrency`` module, which would
   depend on oslo.db.
2. Document, that if someone wanted to use oslo.db with eventlet
   ``tpool.Proxy`` and ``MySQL-Python`` Python DB API driver, they would need
   to use a helper provided by ``openstack.common.concurrency`` module.

The advantage of this solution is that we don't need to re-add eventlet stuff
back to oslo.db.

The disadvantage of this solution is that we add more interdependencies between
oslo.* libraries and make it harder to use oslo.db (it'd probably be not very
clear to users why they need to use another library, if they use eventlet and
MySQL together).


Impact on Existing APIs
-----------------------

None.


Security impact
---------------

None.


Performance Impact
------------------

Enabling of ``use_tpool`` improves performance of DB-bound services (APIs) a
lot, when eventlet and ``MySQL-Python`` are used. Note: you will still need
to use unreleased eventlet code.


Configuration Impact
--------------------

``use_tpool`` won't be a new config file option, we just introduce it in the
context of ``oslo.db``. Currently, projects consume it from
``openstack.common.db`` package. No changes will be needed from deployers
perspective.


Developer Impact
----------------

OpenStack projects that want to use oslo.db with eventlet ``tpool.Proxy`` call
proxying will need to switch from using of ``DBAPI`` class to the new helper.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  akurilin

Other contributors:
  rpodolyaka


Milestones
----------

Target Milestone for completion:
  Juno-1


Work Items
----------

1. Add a new module to oslo.db which will introduce ``tpool.Proxy`` helper and
   ``use_tpool`` config option.
2. Add a new entry point to oslo.db exposing ``use_tpool`` config option.


Incubation
==========

None.


Adoption
--------

None.


Library
-------

None.


Anticipated API Stabilization
-----------------------------

None.


Documentation Impact
====================

``use_tpool`` should be marked as experimental. It should be stated in docs,
that patched version of eventlet is needed to use it.


Dependencies
============

To work properly, this depends on the unreleased version of eventlet. Though,
we've been providing ``use_tpool`` option so far anyway. Rackspace uses patched
version of eventlet in production. We are going to leave it up to deployers to
decide whether to enable this or not (default was and remains ``False``).


References
==========

A PoC patch on review:

https://review.openstack.org/#/c/96467/

The related ML thread:

http://lists.openstack.org/pipermail/openstack-dev/2014-April/033120.html

The Launchpad bug for tracking usage of ``use_tpool`` in projects:

https://bugs.launchpad.net/nova/+bug/1309297

eventlet tpool docs:

http://eventlet.net/doc/threading.html#module-eventlet.tpool

The patch fixing the eventlet issue:

https://bitbucket.org/eventlet/eventlet/pull-request/29/


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
