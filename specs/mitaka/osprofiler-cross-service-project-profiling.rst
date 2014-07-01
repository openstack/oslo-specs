=============================================
 OSprofiler cross service & project profiling
=============================================

https://blueprints.launchpad.net/oslo/+spec/osprofiler-cross-service-project-profiling


Mission Statement
=================

The OSprofiler is a distributed trace toolkit library. It provides pythonic
helpers to do trace generation to avoid repeated code to trace WSGI, RPC, DB,
and other important places... It also provides an interfaces for various
collection backends and helpers to parse data in and out of it.


Problem Description
===================

* Background:

  OpenStack consists of multiple projects. Each project, in turn, is composed
  of multiple services. To process some request, e.g. to boot a virtual
  machine, OpenStack uses multiple services from different projects. In the
  case something works too slowly, it's extremely complicated to understand
  what exactly goes wrong and to locate the bottleneck.

  To resolve this issue, we introduce a tiny but powerful library,
  **OSprofiler**, that could be used by all OpenStack projects and their
  python clients. To be able to generate a single trace per request, that goes
  through all involved services, and builds a tree of calls (see an
  `example <http://boris-42.github.io/ngk.html>`_).


* For more details about how exactly OSprofiler works take a look at
  `readme <https://github.com/openstack/osprofiler/blob/master/README.rst>`_


Proposed Change
===============

OSprofiler is already used by Cinder, Heat, Glance and it is going
to be used by most of other projects like:

- Nova https://review.openstack.org/#/c/254703/
- OpenStack Client https://review.openstack.org/#/c/255861/


Since currently OSprofiler is not under OpenStack umbrella in governance
https://github.com/openstack/governance/blob/master/reference/projects.yaml
we are proposing the Oslo program should be home for OSprofiler.

Further just like other oslo projects, we should have a core team just for
OSprofiler as well.


Implementation
--------------

* **How OSprofiler works** *

  * OSprofiler is very tiny library that allows you to create nested
    traced. Basically it just keeps in memory stack (list) of elements.

    Each element has 3 trace id:

      base_id     - all points of the same trace have same base_id, which helps
                    us to fetch all points related to some trace

      parent_id  - parent's point id

      current_id - current point's id

    And it has 2 methods start() and stop(), start() is pushing new elements
    and calling driver's notify method with payload, stop() is removing latest
    element from stack and calling one more notify()

    This allows us to build tree of calls with durations and payload info:
    Like `here <http://boris-42.github.io/ngk.html>`_.

    For more details please
    `read the docs <https://github.com/openstack/osprofiler>`_.


* **What is going to be used as a OSprofiler driver (trace collector)** *

   * OSprofiler is going to have multi drivers support. Which means
     that basically any centralized system can be used to collect data.
     Or even we can write trace information just to files.

   * As a first driver we are going to use oslo.messaging & Ceilometer

   * In future OSprofiler team is going to add drivers for:
     MongoDB, InfluxDB, ElasticSearch


* **OSprofiler integration points:** *

  * Changes in projects configuration:

    Add config group "profiler" and 3 config options inside (in all projects):

    enabled = False     # Fully disable OSprofiler by default

    trace_db = False    # Whatever trace DB requests or not. It is disabled
                        # by default, because there are too many DB  requests
                        # and tracing them is useful only for deep debugging.

    hmacs = SECRET_KEY  # HMAC keys that are used to sign HTTP headers
                        # that activate OSprofiler, this is used to
                        # block regular users to trigger OSProfiler.
                        # They must be the same for all projects.

    connection = None   # Connection string that specify which
                        # OSProfiler driver to use and credentials
                        # for specified backend. Like
                        # mongo://user:password@ip:port/schema

  * Keep single trace between 2 projects:

    Add OSprofiler middleware to all pipelines in all paste.ini of all projects

    This middleware is initializing OSProfiler if there is special HTTP
    header signed with proper HMAC key.

  * Keep single trace between 2 services of single project:

    If RPC caller has initialized profiler it should add special payload
    to all RPC messages that contains trace information.
    Callee process should initialize OSProfiler if it found such message.

  * Changes required in python clients

    There are 2 changes required in each python client:

    - If profiler is enabled add profiler trace header, this will be used
      when project A is calling project B API via python client.

    - CLI argument --profile <HMAC> - that will initialize OSprofiler


* **What points should be tracked by default?**

   I think that for all projects we should include by default 5 kinds of points:

   * All HTTP calls - helps to get information about: what HTTP requests were
     done, duration of calls (latency of service), information about projects
     involved in request.

   * All RPC calls - helps to understand duration of parts of request related
     to different services in one project. This information is essential to
     understand which service produce the bottleneck.

   * All DB API calls - in some cases slow DB query can produce bottleneck. So
     it's quite useful to track how much time request spend in DB layer.

   * All driver layer calls - in case of nova, cinder and others we have vendor
     drivers. (e.g. nova.virt.driver)

   * All DB API layer calls (e.g. nova.db.api)

   * All raw SQL requests (turned off by default, because it produce a lot of
     traffic)

    * Any other import for specific project methods/classes/code pieces


* ** Points that should be tracked in future as well:**

   * All external commands.
     For example, oslo.concurrency processutils.execute() calls.
     Because the work done by external commands is a key part of many backend
     API implementations and takes non-trivial time.

   * Worker threads spawned / run.
     Some API calls will result in single-use background threads being spawned
     to process some work asynchronously from the rest of the work.
     I think it is important to be able to capture this work in traces,
     by recording a trace when a thread start is requested, and then having
     a trace in the start+end of the thread main method.



Alternatives
------------

* Why not cProfile and other python tracer/debugger?

  **The scope of this library is quite different:**

  * It should create single trace that goes cross all services/projects

  * It is more interesting to be able to collect data about specific points
    in code instead of all methods

  * CProfiler like functionality can be integrated in future in OSprofiler

  * This library should be easy integratable with OpenStack. This means that:

    * It shouldn't require too many changes in code bases of integrating
      projects.

    * It should be simple to turn it off fully

    * It should be possible to keep it turned on in lazy mode in production
      (e.g. users that knows HMAC key can trace their requests).

* What about Zipkin and other existing distributed tracing solutions?

  OSprofiler is small library that is used to provide no vendor lock-in
  tracing solution for OpenStack.

  OSprofiler doesn't intend to implement whole Zipkin like stack. It's just
  tiny library that is used integrate OpenStack with different collectors
  and provide native OpenStack tracer/profiler that is not hard coded on any
  tracing service (e.g. Zipkin).


Impact On Existing APIs
-----------------------

* All API methods of all projects will accept 2 new headers:
  X-Trace-Info and X-Trace-HMAC that will actually trigger profiler.

* All python clients will accept --profile key, that will actually put proper
   X-Trace-Info and X-Trace-HMAC headers to HTTP request, and print trace id.

* There is no need in any changes in any existing oslo libs at the moment.
  If we decide to integrate OSprofiler to some of oslo libs we will do the
  standard process of specs/pr/reviews in that specific lib.


Security Impact
---------------

OSprofiler is using HMAC to sign trace headers. Only the people who know the
secret key used for HMAC are able to trigger profiler.
As HMAC is quite secure there won't be issues with security.

Even in worse case, when attacker knows secret key, he will be able to trigger
profiler, that will make his request a bit slower, but won't affect other
users.


Performance Impact
------------------

* If it is turned off there is negligible performance overhead.
  Just couple of "if None" checks

* If it is turned on, there are two different cases:

  * No trace headers in request => No performance impact

  * There is trace header:

    * Trace id is signed with wrong HMAC overhead on checking that trace id
      is signed by proper HMAC key.

    * Trace id is signed with proper HMAC, overhead will depend on amount of
      trace points and Notification API performance. For requests like
      booting VM, creating Volumes it can be measurable, for simple requests
      like showing details about resource it will be insignificant.

* Trace every N request configuration (not done yet)

  In such configuration every N request will have OSprofiler overhead that
  depends on many things: Amount of traced points (depends on API method),
  OSprofiler backend, and other factors..


Configuration Impact
--------------------

We are adding to all projects new CONF group options:

[profiler]
#If False fully disable profiling feature.
#enabled = False

# If False doesn't trace SQL requests.
#trace_db = True

# HMAC keys that are used to sign headers.
# Because OpenStack contains many projects we are not able to update all HMAC
# keys at the same point of time. To provide ability of no downtime rolling
# updates of HMAC keys (security reasons) we need ability to specify many HMACs
# The process of update OLDKey -> NEWKey will look like:
# 1) Initial system configuration:
#    ALL Services have OLDKey, users use OLDKey
# 2) in the middle 1:
#    All Services have OLDKey, part of them have both OLDKey and NEWKey, users
#    use OLDKey
# 3) in the middle 2:
#    All Services have OLDKey and NEWKey, users use NEWKey
# 4) in the middle 3:
#    Part of service have both keys and some of services have only NEWKey,
#    users use NEWKey
# 5) end system configuration:
#     All services have only NewKey
#hmacs = SECRET_KEY1, SECRET_KEY2

# Profiler driver collector connection string.
connection = None

By default OSprofiler is turned off. However it can be keep on in production,
because it doesn't add any overhead until it is triggered and profiler can be
trigged only by person who knows HMAC key.


Developer Impact
----------------

Developers will be able to profile OpenStack and fix different issues related
to performance and scale.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  boris-42
  dinabelova
  harlowja
  zhiyan

Milestones
----------

Mitaka-3

Work Items
----------

* Remove from paste.ini OSprofiler configuration:
  https://github.com/openstack/osprofiler/blob/master/doc/specs/in-progress/make_paste_ini_config_optional.rst

* Multi backend support:
  https://github.com/openstack/osprofiler/blob/master/doc/specs/in-progress/multi_backend_support.rst

* Move all projects to new multi backend model

* Integrate OSprofiler in all OpenStack projects

* Better integration testing:
  https://github.com/openstack/osprofiler/blob/master/doc/specs/in-progress/integration_testing.rst

* Better DevStack integration:
  https://github.com/openstack/osprofiler/blob/master/doc/specs/in-progress/better_devstack_integration.rst

* Integrate Rally & OSprofiler


Incubation
==========

Adoption
--------

All projects and python clients should add quite small amount of code to
make it possible to do the cross project/service tracing.

Library
-------

Code of OSprofiler library can be find here:
https://github.com/openstack/osprofiler/


Anticipated API Stabilization
-----------------------------

None.


Documentation Impact
====================

We should document in one place how to configure and use OSprofiler.


Dependencies
============

- OSprofiler can be runtime dependency to python clients
- OSprofiler should be in requirements of projects that are will use OSprofiler


References
==========

* OSprofiler lib: https://github.com/stackforge/osprofiler

* OSprofiler specs: https://github.com/openstack/osprofiler/tree/master/doc/specs


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
