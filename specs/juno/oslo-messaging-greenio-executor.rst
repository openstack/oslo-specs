===============================
oslo.messaging greenio executor
===============================

https://blueprints.launchpad.net/oslo.messaging/+spec/greenio-executor

Add a new oslo.messaging executor which adds a new capability to the
eventlet executor - the ability to dispatch requests to asyncio
coroutines running on greenio's greenlet based asyncio event loop.

Problem description
===================

We're attempting to take baby-steps towards moving completely from
eventlet to asyncio/trollius.

Any OpenStack service code is run in response to various I/O events like
REST API requests, RPC calls, notifications received, periodic timers,
etc. We eventually want the asyncio event loop to be what schedules
code to run in response to these events. Right now, it is eventlet doing
that.

Now, because we're using eventlet, the code that is run in response to
these events looks like synchronous code that makes a bunch of
synchronous calls. For example, the code might do some_sync_op() and
that will cause a context switch to a different greenthread (within the
same native thread) where we might handle another I/O event (like a REST
API request) while we're waiting for some_sync_op() to return::

  def foo(self):
      result = some_sync_op()  # this may yield to another greenlet
      return do_stuff(result)

Eventlet's infamous monkey patching is what make this magic happen.

When we switch to asyncio's event loop, all of this code needs to be
ported to asyncio's explicitly asynchronous approach. We might do::

  @asyncio.coroutine
  def foo(self):
      result = yield from some_async_op(...)
      return do_stuff(result)

or::

  @asyncio.coroutine
  def foo(self):
      fut = Future()
      some_async_op(callback=fut.set_result)
      ...
      result = yield from fut
      return do_stuff(result)

Porting from eventlet's implicit async approach to asyncio's explicit
async API will be seriously time consuming and we need to be able to do
it piece-by-piece.

The problem this spec addresses is how to allow a single oslo.messaging
RPC endpoint method to be ported to asyncio's explicit async approach.

Proposed change
===============

The plan is:

#. Stick with eventlet; everything gets monkey patched as normal.
#. We register the greenio event loop with asyncio - this means that
   e.g. when you schedule an asyncio coroutine, greenio runs it in a
   greenlet using eventlet's event loop.
#. oslo.messaging will need a new variant of eventlet executor which
   knows how to dispatch an asyncio coroutine. It's important that even
   with a coroutine endpoint method, we send the reply from a
   greenthread so that the dispatch greenthread doesn't get blocked if
   the incoming.reply() call causes a greenlet context switch.
#. When all of ceilometer has been ported over to asyncio coroutines,
   we can stop monkey patching, stop using greenio and switch to the
   asyncio event loop
#. When we make this change, we'll want a completely native asyncio
   oslo.messaging executor. Unless the oslo.messaging drivers support
   asyncio themselves, that executor will probably need a separate
   native thread to poll for messages and send replies.

This spec specifically proposes the addition of a 'greenio' executor
which would do something roughly like this::

    while True:
        incoming = self.listener.poll()
        method = dispatcher.get_endpoint_method(incoming)
        if asyncio.iscoroutinefunc(method):
            fut = asyncio.Task(method())
            fut.add_done_callback(lambda fut: incoming.reply(fut.result()))
        else:
            self._greenpool.spawn_n(method)

If the endpoint method is just a normal python function, we dispatch
it in a new greenthread just like the current eventlet executor does.

If the endpoint method is an asyncio coroutine, we schedule that through
the greenio event loop which means the coroutine runs in a greenlet.
When the coroutine completes, a callback is invoked in another greenlet
to send the reply back to the client.

Alternatives
------------

The alternative is to add an asyncio executor which can only schedule asyncio
coroutines to the asyncio eventloop. This would mean all code in a service
would need to be ported and eventlet replaced with asyncio in one atomic
change. That would be bonkers.

Impact on Existing APIs
-----------------------

Two changes to the public oslo.messaging API:

#. The get_rpc_server() and get_notification_listener() will now accept
   executor='greenio'.
#. RPC server or notification listener endpoint methods can now be asyncio
   coroutines (i.e. methods annotated with @async.coroutine that use
   constructs like 'yield from' or asyncio.Task()).

Security impact
---------------

None.

Performance Impact
------------------

In theory, there could be differences in the performance of endpoint methods
ported to be asyncio coroutines but we have no idea yet.

Configuration Impact
--------------------

None.

Developer Impact
----------------

Developers will need to understand the difference between implicitly async
code relying on eventlet's monkey patching versus explicitly async code using
asyncio constructs. This will be a far-ranging change for OpenStack, but this
blueprint is only about one small feature in oslo.messaging which will enable
this work to begin.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  victor-stinner

Other contributors:
  markmc
  flaper87

Milestones
----------

Target Milestone for completion:
  juno-3

Work Items
----------

#. greenio needs to be added to openstack/requirements. See `Review Criteria`_
   for the requirements repo. In particular, the availability of greenio in
   distros and greenio's commitment to API stability are worth considering.
#. Add a greenio executor.
#. Include examples of asyncio coroutine endpoint methods in the docs.
#. Include greenio based unit tests which dispatch both types of endpoint
   methods with both RPC servers and notification listeners. Basing these tests
   the rabbit and/or fake drivers probably makes sense.

.. _Review Criteria: https://wiki.openstack.org/wiki/Requirements#Review_Criteria

Incubation
==========

Adoption
--------

Ceilometer is likely to be the first service to use this executor.

Library
-------

oslo.messaging.

Anticipated API Stabilization
-----------------------------

The API should be stable from introduction.

Documentation Impact
====================

oslo.messaging developer docs needs some small additions.

Dependencies
============

- This introduces a dependency on trollius and greenio.

References
==========


Victor's excellent docs on asyncio and trollius:

  https://docs.python.org/3/library/asyncio.html
  http://trollius.readthedocs.org/

Victor's proposed asyncio executor:

  https://review.openstack.org/70948

The case for adopting asyncio in OpenStack:

  https://wiki.openstack.org/wiki/Oslo/blueprints/asyncio

Victor's current status on trollius in OpenStack:

  http://haypo-notes.readthedocs.org/openstack.html#trollius-in-openstack

A blog post on the subject from Victor:

  http://techs.enovance.com/6562/asyncio-openstack-python3

Summary of the discussion at the Paris Juno Sprint which lead to this design:

  http://lists.openstack.org/pipermail/openstack-dev/2014-July/039291.html

A previous email I wrote about an asyncio executor:

 http://lists.openstack.org/pipermail/openstack-dev/2013-June/009934.html

The mock-up of an asyncio executor Mark wrote (and never tested):

  https://github.com/markmc/oslo-incubator/blob/8509b8b/openstack/common/messaging/_executors/impl_tulip.py

Mark's blog post on async I/O and Python:

  http://blogs.gnome.org/markmc/2013/06/04/async-io-and-python/

greenio - greelets support for asyncio:

  https://github.com/1st1/greenio/

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

