===========================
Privilege Separation Daemon
===========================

It is difficult to sufficiently describe security policy at the
granularity of command lines.  Consequently numerous rootwrap entries
effectively grant full root access to anyone permitted to run
rootwrap.

This spec proposes a replacement (dubbed "privsep") that is both more
expressive and more limited in what it grants.

Problem Description
===================

OpenStack's privilege mechanism has evolved over time from simple
sudoers file to rootwrap.  Recent "rootwrap-daemon" work has greatly
increased the performance by avoiding the need to re-exec python.
Throughout this history, the basic API idiom has remained executing
command lines (almost always) as root.

The rootwrap security policy revolves around whitelisting particular
command lines via the configuration of various "filters".  Configuring
these correctly are hard, because the filters have limited
expressiveness, command line tools typically weren't expected to be
the privilege boundary, and the "context" of the original operation
has already been lost at this level.

For example, as shipped ``nova/rootwrap.d/compute.filters`` contains:
::

   chown: CommandFilter, chown, root

This allows the invoking user to run chown with any arguments, as
root - effectively granting root access to the caller (consider
``chown $user /etc/shadow``).  The *actual* requirement is that nova
needs to set the owner on various files produced by VMs to it's own
UID, but this is not something that can be expressed through current
rootwrap filters.

Repeatedly going through sudo for each invocation (or similar for
rootwrap-daemon) limits the ability to use more restricted privilege
mechanisms like Linux capabilities or SELinux, since the calls to sudo
effectively reset to "full privileges" mid-way through the call stack.

Generating command lines and parsing textual output from tools is slow
and susceptible to inconsistencies across tool versions, since
typically this output was not designed as a programmatic API.  In
Neutron in particular, the command lines are often repeated
invocations of trivial ip(8) commands and the overhead is significant
compared to what should be cheap AF_NETLINK exchanges.

Why have a privilege mechanism at all?
--------------------------------------

Otherwise known as "Why don't we just run agents as root?"

Running with the least privileges possible is a common defensive
security design.  The assumption is that it *might* be possible to
remotely exploit your service via the publicly exposed network
protocols so you want to run the bulk of your code with reduced/no
privilege and only gain special privileges when absolutely required.
If an attacker gains control of the unprivileged code then they
achieve no interesting access, and still have to attempt a second
exploit against the unprivileged->privileged boundary before gaining
useful powers.


Proposed Policy
===============

This spec proposes a new privilege mechanism that is based around
python function calls rather than command lines.  The intention is to
allow slightly more code into the privileged portion - enough that we
now have sufficient "context" to make better security decisions.  For
example move from "run chown" to "take ownership of VM output file".

Design priorities, in rough order of importance:

#. Security
   * Avoid root as much as possible
   * Security interface should be easy to audit
#. Easy to use by developers
   * Just add a new function with a decorator
#. Performance
   * Allows library use rather than parsing output of command line tools

In a similar way to ``rootwrap-daemon``, privsep runs two processes -
one with and one without privileges.  The privileged process is as
minimal as possible, and is written to assume it is possibly under
attack by the unprivileged process.

To limit the impact of a potential exploit, this spec proposes the
privileged process support the use of *Linux capabilities* to allow
the process to drop broad root (uid=0) superpowers but keep a limited
subset.  See capabilities(7) manpage for an overview.  As an example,
the neutron agent might be configured to use privsep as a non-root
user but with CAP_NET_ADMIN - this allows just about all kernel
network options to be changed, but a compromised process could not
read ``/etc/shadow`` or load an arbitrary kernel module.

A design limitation from using capabilities is that the privileged
process is limited to *only those* capabilities.  Eg: most of Neutron
just requires CAP_NET_ADMIN and CAP_SYS_ADMIN (for network
namespaces), but there are some operations that require additional
permissions.  Extrapolating this to absurdity, eventually the
privileged process accumulates *all* required capabilities and
effectively becomes all-powerful root again.  To combat this, privsep
allows a particularly diverse service to instantiate multiple privsep
daemons, each with their own set of permissions and privileged code.

Unlike ``rootwrap-daemon``, this spec proposes that the privileged
process *share fate* with the main (unprivileged) process.
Specifically: the privileged process should exit when the unprivileged
process has exited, and once started no attempt should be made to
restart the privileged process if it exits.  If the privileged process
exits for some reason, it is due to a bug and may be currently under
attack - restarting the process gives the attacker another
opportunity.  If the privileged process exits, the unprivileged
process will be unable to perform many functions, and will need to be
restarted by the admin - this is essentially similar to an uncaught
exception destroying a critical worker thread and leaving an
inconsistent state.

Privileged run-time environment
-------------------------------

After setup, there are two distinct processes joined with a
communication channel: The original process with no special
privileges, and a privileged process running as root and/or with extra
Linux capabilities.

Project-provided python code running in the privileged process is run
with:

* A trusted ``oslo.config`` environment.
* A trusted python module search path.
* uid/gid set to the configured values (default: root).
* Linux capabilities are restricted to the configured set (default:
  project-provided).
* ``stdin`` and ``stdout`` are closed and reopened to ``/dev/null``.
* ``oslo.log`` is configured to log to ``stderr``.  The unprivileged
  code is expected to proxy this to the correct final location.
* A communication channel is open to the unprivileged caller.

The trusted python module path and ``oslo.config`` environment are
assumed and must be provided by whatever granted the initial elevated
privileges and executed the python interpreter (eg: ``systemd``
environment, ``sudoers`` configuration, etc).  Based on the
configuration found, the privileged startup code will configure the
rest and abort if any step fails.

Communication with privileged process
-------------------------------------

The communication channel must be secure.  In particular, python
"pickle" and many other serialisation libraries are unsuitable because
they contain convenience features that can allow unexpected code to be
executed during deserialisation.  For its simplicity, this spec
proposes using ``json`` and limiting function argument/return values
to the basic JSON datatypes (32-bit integer, 32-bit floats, unicode
string, boolean, array, dictionary), with the addition of a bytestring
type.  In the return direction (privileged to unprivileged), there
will also be support for catching and re-raising most exception
objects (assumes the class can be found on the unprivileged side and
the common ``.args`` convention).

The underlying communication channel must not be exposed remotely -
Unix sockets or pipes are obvious choices.

Note the communication channel is only between the privileged and
unprivileged portions of privsep.  Specific serialisation and
communication choices are implementation details and can be changed
over time without compatibility concerns.

The current prototype offers several alternatives that all produce the
same end result: Two processes connected over a local communication
channel.

The 2nd option (sudo/rootwrap) is used by default if no specific
"start" method has been invoked by the first call to a privsep client
stub function.  We may want to revisit these choices as the
recommended OpenStack secure deployment story evolves.

1. Basic ``socketpair()`` and ``fork()``

   This just creates a pair of anonymous connected Unix sockets, and
   then forks the new privileged process.  The assumption is that the
   original process was started with at least the required privileges
   (perhaps from something like systemd), and this "start" function is
   invoked early in the process startup - prior to the regular
   unprivileged process dropping all privileges.

   This is designed to mirror the "normal" way that Unix daemons work,
   and does not use sudo at any point.  It requires an additional call
   inserted in main() and changes to the initial process environment,
   so poses the most difficult migration.

2. Use ``sudo`` or ``rootwrap`` and a Unix socket

   This is intended for use with ``sudo``, ``rootwrap``, or
   ``rootwrap-daemon``.  This is complicated by the fact that ``sudo``
   closes all open file descriptors except stdin/stdout/stderr, and
   ``rootwrap-daemon`` doesn't allow long-lived commands, nor
   streaming data over stdin/stdout.

   This approach opens a new Unix socket on the unprivileged side, and
   executes a helper command via ``rootwrap`` (or ``sudo``) with the
   path to the Unix socket as an argument.  The helper command (now
   running with root privileges) connects back to this socket then
   forks and exits, allowing ``rootwrap-daemon`` (if used) to see a
   timely process exit.  The unprivileged process accepts the first
   connection to its listening socket[#unpriv_socket], and continues.

   Note that (unlike ``rootwrap-daemon``) the connection is made from
   the privileged side to the unprivileged side.  At no point is the
   privileged process exposing an access point where other processes
   can attempt to connect to it.  Simply accepting the first
   connection to the unprivileged socket is safe because the
   filesystem permissions only allow the same uid, or root - and a
   process running as the same uid is already entrusted to start its own
   privileged daemon via ``sudo``/``rootwrap``, so this would grant no
   additional privilege.

   This approach is the default since it requires no change to
   existing OpenStack deployments (other than an updated rootwrap
   filter).

Regardless of the approach used to create the communication channel,
the privileged process continues acting on requests until the
communication channel is closed.  At this point, the privileged
process exits.  Since it is a local IPC channel, there should be no
"legitimate" reason for the channel to drop and no attempt is made by
either side to recreate the connection.

Developer's Point of View
-------------------------

From the python developer's point of view, the goal is to be as simple
as adding a regular python function.  This spec proposes the following
API (using Neutron as an example and final function names subject to
change):
::

  # In (eg) neutron_privileged/foo.py
  import os
  from neutron_privileged import privsep

  @privsep.entrypoint
  def example_task_that_requires_privileges():
      return os.getuid()

To use this function, unprivileged code just needs to call it.
::

  from neutron_privileged import foo

  def bar():
      uid = foo.example_task_that_requires_privileges()
      print "privsep is running as %s" % uid

The magic is in ``neutron_privileged/__init__.py``.  This file needs to
invoke some ``oslo.privsep`` code at import time to create the
decorator used on privileged entrypoints:
::

   # In neutron_privileged/__init__.py (once per project)
   from oslo_privsep import capabilities as c
   from oslo_privsep import priv_context

   CFG_SECTION = 'privsep'  # important with multiple privsep daemons
   DEFAULT_CAPS = [c.CAP_SYS_ADMIN, c.CAP_NET_ADMIN]  # eg
   privsep = priv_context.PrivContext(
       __name__, cfg_section=CFG_SECTION,
       default_capabilities=DEFAULT_CAPS,
   )

The decorator internally wraps each function like this (pseudo-code):
::

   # Resulting pseudo code, after decorator is applied
   def example_function(*args, **kwargs):
       if in_unprivileged_mode:
           privsep_channel.send((CALL, 'example_function', args, kwargs))
           result = privsep_channel.read()
           if result.raised_exception():
               raise result.exc_class(result.exc_args)
           return result.value
       else:
           # privileged_mode
           return _real_example_function(*args, **kwargs)

The unprivileged "client stub" function will serialise any arguments,
communicate with the privsep process, and deserialise the return
value.  Note (by choice) only basic "json-ish" python types are
accepted in args or return values - no user-defined objects.  If the
privileged code raises an exception, it will be caught and re-raised
on the unprivileged side (using the ``.args`` property).

As described earlier, the privileged daemon will be started when the
first stub is called unless the daemon has already been started.  Once
started, the same channel is reused and the privileged daemon persists
until the channel is closed (presumably when the main process exits).

Functions that are not marked with the privsep decorator are not
available across the privsep channel.  The imported module is
otherwise available as normal so module-level constants, etc are
available as expected.  Note that the unprivileged process is a
separate process, so modifying an imported global will have no effect
on the privileged code.

The decorator can be set to "privileged mode" even within the
unprivileged process, in which case it will pass calls through to the
real wrapped function.  The function will run without any special
privileges and presumably fail.  This is rarely expected to be useful
outside unittests with mocked environments.

Importing ``foo.bar.baz`` involves loading (and hence trusting)
``foo/__init__.py`` and ``foo/bar/__init__.py``.  Consequently, this
spec recommends projects create a new top-level python package within
their regular git repository to hold modules intended to be used via
privsep (eg: create ``neutron.git/neutron_privileged/...`` as in the
examples above), although this is not technically required.

Debugging
.........

Moving to function-based primitives necessarily leads to more complex
python code on the privileged side than with ``rootwrap``, and thus
being able to easily debug this python code is critical.  The
prototype code includes sufficient changes to the neutron testsuite to
correctly fail tests and capture any stacktraces triggered from
privileged code, and display them as expected in unittest output.
Incorporating similar changes will be an important part of projects
migrating to privsep.

Interactive debugging (via pdb_) of the privileged process, and in
particular use of ``pdb.set_trace()`` within privileged code requires
pdb to have a suitable channel available for interaction.  Since stdin
and stdout are closed in the privileged process, a helper function
will be provided to start pdb on a new Unix socket.  A debugging
side-channel is unsafe in a production deployment for obvious reasons,
and will require the developer to patch in an appropriate call before
using pdb.

.. _pdb: https://docs.python.org/3/library/pdb.html

Code coverage
.............

``coverage.py`` has support for collecting coverage statistics across
sub-processes[#coverage_subproc].  To do this, the privileged process
will need to call ``coverage.process_startup()`` as early as possible
(eg: from ``main()``), which enables coverage features if the
``COVERAGE_PROCESS_START`` environment variable is set.  If the
privileged process was invoked through sudo, then the sudo policy must
be explicitly configured to allow this environment variable to be
propagated.

The specific tox environment details to enable this will be worked out
in later changes.  It looks possible with a little work and needs
explicit support from the initial execution environment, so will not
affect the security of a regular deployment.

.. [#coverage_subproc] See `Measuring subprocess`_
.. _Measuring subprocess: http://nedbatchelder.com/code/coverage/subprocess.html

Profiling
.........

Python ``profile`` and ``cProfile`` modules are intended for
collecting statistics on specific function calls, and have no support
for collecting statistics across process boundaries.  Profiling within
*either* the unprivileged or privileged processes will work as
expected, but attempting to profile *across* the privilege boundary
will collect statistics for the local side of the communication
channel only.

Because each process can be profiled, it is *possible* to build a
unified profile in future.  Doing so is considered out of scope of
this spec, however.


Operator's Point of View
------------------------

Configuration files will require an additional section:
::

   [privsep]
   user = novapriv
   group = novapriv
   capabilities = CAP_SYS_ADMIN, CAP_NET_ADMIN

This is the uid, gid and capabilities that the privileged process
should run with.  By default, the privileged process continues to run
with whatever uid/gid the process was originally started with
(probably root).  The default value for ``capabilities`` is provided
by the instantiating project code, and may need to be overridden to
suit the particular config options/modules in use.

A diverse service like nova may use more than one separate privileged
daemon, and each will have their own named config section with
different default capabilities.

In the most paranoid setup, each privileged process should run as a
dedicated non-root user, separate from the unprivileged user (and
separate to any other privsep processes).  Neither privileged nor
unprivileged user should be able to write to the service configuration
files nor anywhere in the python load path.

Alternatives & History
======================

The evolution of rootwrap is simple:

* "We need to run a few commands as root" -> start using sudo
* "too many commands and sudoers is becoming unwieldy" -> introduce rootwrap
* "rootwrap is expensive to reinvoke every time" -> rootwrap-daemon

Run the entire python process with required privileges
------------------------------------------------------

Provided the unprivileged<->privileged boundary contains any hole that
effectively grants root to the caller, then there is little benefit to
having the separation and we may as well enjoy the code
simplicity/performance benefits of just running everything in a
unified process.

A variation of this is to drop "effective" privileges in a way that
can be regained in-process while performing privileged operations (eg:
`seteuid(2)`).  This protects against "accidental" abuse of privileges,
but won't grant additional security against a malicious attacker with
control over the process.

I think there's a lot to be said for this point of view.  However,
given the popularity and importance of OpenStack VMs as a security
target, I think we need to continue to strive for better in this area.
This spec is an attempt to make an effective security boundary and
grant a true additional layer of defence, while being almost as easy
to work with as an in-process function call.

Use ``multiprocessing`` library
-------------------------------

The python ``multiprocessing`` library already has client processes
talking to worker processes over an IPC channel.  We could reuse that
as the core communication mechanism (and indeed rootwrap-daemon uses
multiprocessing just like this).

This is reasonable, and perhaps something we may yet choose to do.  I
chose not to use multiprocessing initially because it was written to
be a convenient single-user worker pool and not a privilege separation
boundary.  As can be seen in rootwrap-daemon, serialisation and
several "magic proxy" choices need to be worked around to provide
security, and I felt such workarounds resulted in fragile and
difficult to audit code right at the place you want neither.

Thankfully, we only require a narrow set of features and rewriting the
core communication code from scratch is straight forward.  The result
is significantly less ambiguous code at the security entry point.

Leave stdin/stdout untouched
----------------------------

In particular, this would allow ``pdb.set_trace()`` to "just work"
without any further action (assuming it is only invoked from a single
thread).  Although there is no specific concern, having stdin
available leaves an additional potential attack vector into the
privileged context.  Since pdb already has reasonable support for
using a different channel for interaction, the choice to close these
file descriptors (and reopen on /dev/null) seemed an acceptable
security/convenience tradeoff.

Implementation
==============

Author(s)
---------

Primary author:
  gus

Other contributors:
  None

Milestones
----------

#. Move existing prototype code into oslo.privsep
#. Introduce privsep alternatives of large bodies of rootwrap code
#. Update documentation mentioning rootwrap config/filters
#. Phase out alternative rootwrap code

Work Items
----------

A working prototype already exists in
https://review.openstack.org/#/c/155631/, although the proposed API
has evolved with this spec.

Most of the remaining work involves moving the core mechanism to a new
oslo.privsep project, and rebasing the prototype Neutron change onto
that common core.  From the Neutron experience, the largest piece of
migrating a new project to this mechanism will be integrating into the
unittest mocked environment and will vary by project.

In the current prototype implementation, the communication channel can
only have one outstanding operation at a time and the privileged
process is single-threaded.  These limitations will be addressed as
the code is moved into oslo by adding unique message IDs and using a
small thread worker pool on the privileged side.

Once the bulk of the code exists in oslo.privsep we should encourage
wide review by the OpenStack Security Group and others.

Migration
---------

This mechanism may live alongside ``rootwrap`` without interference.
The expected migration process is to create alternative privsep
versions of routines that require privileges and migrate callers
across to the new implementation.  Remaining "hard" cases that require
unusual permissions or true uid=0 may continue to use sudo/rootwrap
indefinitely, and this spec makes no suggestion that we should migrate
away from rootwrap entirely.

References
==========

* Prototype Neutron implementation:
  https://review.openstack.org/#/c/155631/

* rootwrap-daemon spec:
  http://specs.openstack.org/openstack/neutron-specs/specs/kilo/rootwrap-daemon-mode.html

* A somewhat similar mechanism in ssh, from which the name "privsep"
  is borrowed: http://www.citi.umich.edu/u/provos/ssh/privsep.html

Revision History
================

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * -
     - Introduced

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
