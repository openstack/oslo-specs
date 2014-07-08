======================
 Rootwrap daemon mode
======================

https://blueprints.launchpad.net/oslo/+spec/rootwrap-daemon-mode

As it was pointed out several times on ML [#neu_ml]_ [#nova_ml]_ different
services (most notably Neutron and Nova) suffer from performance penalty of
having to run new instance of rootwrap executable for each call that needs root
privileges. [#nova_ml]_ ended basically with "Who's up to the task?" question.

Problem description
===================

The structure of this overhead has been analyzed in [#neu_ml]_. It's clear that
the main issue here is rootwrap startup time that consists of  Python
interpreter startup and rootwrap config parsing.

Proposed change
===============

I propose creating a new mode of operation for rootwrap - daemon mode. In this
mode rootwrap would start, read config file and wait for commands to be run
with root priviledges. Each service's process will have its own rootwrap daemon
process.

Daemon starting
---------------

Daemon will be started using a separate binary (like neutron-rootwrap-daemon
for Neutron) pointing to ``oslo.rootwrap.cmd:daemon`` endpoint (instead of
``:main``). The binary will receive the same options (config file) as the
normal one except the command to be run in priviledged mode. For example::

  rootwrap-daemon /etc/myservice/rootwrap.conf

The startup process is the same as in normal mode up to the point when the
command is about to be run. In daemon mode a separate method is called instead
that starts RPC [#rpc]_ server and falls into infinite loop serving requests.

Daemon API
----------

Upon startup daemon will push to its stdout:

* path to UNIX domain socket (encoded in UTF-8);
* newline character ``\n``;
* 32-byte auth key.

These credentials can be used to connect a
``multiprocessing.BaseManager``-based client. Because ``pickle`` and
``xmlrpclib`` are unsafe, it uses its own JSON serialization (see `Under the
hood`_ section). The only exposed object is ``rootwrap`` with one method:
``run_one_command(userargs, env=None, stdin=None)``. Arguments are:

* ``userargs`` - list of command line arguments that are to be used to run the
  command;
* ``env`` - dict of environment variables to be set for it (by default it's an
  empty dict, so all environment variables are stripped);
* ``stdin`` - string to be passed to standard input of child process.

The method returns 3-tuple containing:

* return code of child process;
* string containing everything captured from its stdout stream;
* string containing everything captured from its stderr stream.

Here is a sketch of basic usage for rootwrap daemon::

  >>> from subprocess import *
  >>> from multiprocessing.managers import BaseManager
  >>> process = Popen(["rootwrap-daemon", "rootwrap.conf"], stdout=PIPE)
  >>> address = process.stdout.readline()[:-1].decode('utf-8')
  >>> authkey = process.stdout.read(32)
  >>> class MyManager(BaseManager): pass
  ...
  >>> MyManager.register("rootwrap")
  >>> from oslo.rootwrap import client  # to set up 'jsonrpc' serializer only
  >>> manager = MyManager(address, authkey, serializer='jsonrpc')
  >>> manager.connect()
  >>> proxy = manager.rootwrap()
  >>> proxy.run_one_command(["cat"], stdin="Hello, world!")
  [0, u'Hello, world!', u'']
  >>> process.kill()

Note that this requires ``rootwrap-daemon`` pointing to
``oslo.rootwrap.cmd:daemon`` to be available in ``PATH``.

The ``run_one_command`` call returns a list here because of JSON serialization
but it doesn't change Python API usage.

Client API
----------

To simplify daemon usage a ``oslo.rootwrap.client`` module is provided
containing one class ``Client`` that wraps all necessary steps to work with
rootwrap daemon.

Its constructor expects one argument - a list that can be passed to ``Popen``
to create rootwrap daemon process. For Neutron it'll be
``["sudo", "neutron-rootwrap-daemon", "/etc/neutron/rootwrap.conf"]``
for example.

The class provides one method ``execute`` with the same profile as
``run_one_command`` method shown above.

The class lazily creates an instance of the daemon, connects to it and passes
arguments. Note that some reconnection and respawning mechanism will be in
place so that if daemon process dies or hangs, ``Client`` will detect this on
the next call and will simply restart it.

This laziness will allow user to kill all rootwrap daemon processes to reload
config file, for example.

Under the hood
--------------

The biggest expected security risk in this proposal is the way that client
talks to daemon so I'll discuss the underlying protocol in details.

#. Credentials passing

   The credentials required to connect to daemon are passed to stdout stream
   that is expected to be bound through a pipe directly to calling process.
   They are exposed only to the kernel and calling process here.

#. Authentication

   ``multiprocessing`` involves digest authentication for every new connection
   made to the server. The key is never passed over the socket, so we could
   even use TCP socket here (no way). The key is generated using
   ``os.urandom(32)`` call.

#. Connection (non-)pooling

   Managers use threadlocal connections so there's no need to create a pool of
   them. Although it might sound wasteful to create new connection for every
   thread, creating a connection over UNIX socket is almost nothing compared to
   spawning a new process time-wise.

#. On-wire protocol

   By default ``multiprocessing`` uses ``pickle`` to serialize RPC [#rpc]_
   requests and responses but it's very unsafe as it allows to call any method
   on the receiving side (see warning in [#pickle]_). The only other option is
   to use ``xmlrpclib`` as a serializer but it's unsafe as it's prone to
   resource exhaustion attacks [#xml_unsafe]_. That's why JSON serialization
   support is implemented. It's very simple (~50 SLOC) and is safe because JSON
   serialization is widely regarded as being safe.

   This serialization is plugged in using undocumented features of
   ``multiprocessing.managers`` module:

   * ``listener_client`` - dictionary of available serialization options with
     strings as keys and pairs (listener, client) as values;
   * ``serializer`` - argument of ``BaseManager.__init__`` constructor,
     contains a key in ``listener_client`` dictionary.

   The author of ``multiprocessing`` module assured that this mechanism is not
   going to go away any time soon [#ser_bug]_.

   .. note::
     Although it's risky to rely on undocumented feature,
     it's mitigated by the assurance of the stdlib module author.

Alternatives
------------

There are a number of alternative approaches to optimize number of rootwrap
calls to mitigate the overhead (see [#neu_eth]_). There were a number of
suggestions in original thread in mailing list [#neu_ml]_ and in corresponding
etherpad [#neu_eth]_:

* Scrap rootwrap, switch to sudo.

  We'll lose current fine-grained control over what can be run as root.

* Use other interpretator for rootwrap.

  Doesn't fix the interpretator startup cost.

* Rewrite rootwrap in other language.

  This includes suggestions to rewrite entirely or partially in C or some
  Python dialect that would be translateable to C.

  As OpenStack community is focused on Python development, bringing some other
  language to the field would require more developers that would be familiar
  with it.

* Filter commands on the calling process side and use sudo.

  This would provide the same security as the first option.

* Consolidate calls that use rootwrap into scripts

  We could create scripts that would require only one rootwrap call to do all
  necessary work for one request, for example. But these scripts will either
  become very complex (say rewriting parts of Neutron agents in shell) or there
  will be too many of them. Either way defeats the purpose of sudo and rootwrap
  - to minimize amount and complexity of code running with root priviledges.

* Per-host daemon process

  This would require some D-Bus or MQ set up and secured. It doesn't look
  feasible to set up such secure daemons. Supporting them across projects
  seems even less feasible since every project uses its own rootwrap
  configuration and such configurations might be host-dependent.

Impact on Existing APIs
-----------------------

Operations in standalone mode are not affected in any way, so all existing
usages will work as before.

Security impact
---------------

This change require another binary to be added to sudoers for the projects
that would use daemon mode.

Daemon itself will listen UNIX domain socket but every connection is passed
through digest authentication.

JSON is used as a transport to avoid known vulnerabilities in other types of
serialization mechanisms.

Performance Impact
------------------

There is a benchmark results in commit message in [#rw_cr]_. They show that
although initial daemon startup time is slightly bigger than with usual
rootwrap call, on average daemon shows over 10x better performance.

Configuration Impact
--------------------

None in oslo.rootwrap itself. Projects using it might require a separate option
for new behavior.

Developer Impact
----------------

None

Implementation
==============

The feature implementation is in progress at [#rw_cr]_. Example usage for
Neutron is at [#neu_cr]_.

Assignee(s)
-----------

Primary assignee:
  yorik-sar (Yuriy Taraday, YorikSar @ freenode)

Milestones
----------

Target Milestone for completion:
  Juno-2

Work Items
----------

This blueprint suggests rather small addition to rootwrap.

Further integration into different projects should be covered separately.

Documentation Impact
====================

Both mechanisms involved in daemon work and its API should be covered in docs.

Dependencies
============

None

References
==========

.. [#neu_ml] Original mailing list thread:
   http://lists.openstack.org/pipermail/openstack-dev/2014-March/029017.html

.. [#nova_ml] Earlier mailing list thread
   http://lists.openstack.org/pipermail/openstack-dev/2013-July/012539.html

.. [#rpc] Nowhere in this document "RPC" refer to that MQ-based RPC messaging
   that ``oslo.messaging`` does

.. [#pickle] https://docs.python.org/2.7/library/pickle.html

.. [#ser_bug] http://bugs.python.org/issue21078

.. [#neu_eth] https://etherpad.openstack.org/p/neutron-agent-exec-performance

.. [#rw_cr] https://review.openstack.org/81798

.. [#neu_cr] https://review.openstack.org/84667

.. [#xml_unsafe] https://docs.python.org/2/library/xml.html#xml-vulnerabilities

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

