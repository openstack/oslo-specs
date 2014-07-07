==============================
 Redis backed jobs and boards
==============================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/taskflow/+spec/redis-jobboard

To avoid having just one implementation of a jobboard in taskflow (currently
based on `zookeeper`_) it would be advantageous from a design
perspective (having more than one implementation usually ensures that the
design is correct) and from a user perspective (not everyone wants
to or can run zookeeper) to provide a job posting and consumption mechanism
that is based on at least one other *capable* system (`redis`_ is one of the
next best potential implementations, while it *does* have issues and
is *not* perfect/ideal it will likely be acceptable).

.. _redis: http://redis.io/
.. _zookeeper: http://zookeeper.apache.org/

Problem description
===================

The `job`_ (and associated `jobboard`_) mechanism that taskflow provides as a
way to submit `tasks`_ and `flows`_ to be worked on as jobs (aka the posting
and work creation process) and ensure those jobs are robustly executed in a
manner that is reliable, atomic and scalable (aka the consumption
process) provides a novel mechanism to transfer work from producers to capable
consumers (typically these are `conductors`_) in a reliable and
inherently fault-tolerant manner.

Currently the implementation that exists requires zookeeper to provide the
primitives that are used to implement the `features`_ that form the basis of
the job and jobboard API.

At a high-level this is done via the following zookeeper primitives:

* Workflow/job postings; publishing of a non-ephemeral nodes to a
  given zookeeper `directory`_ by some set of producers.
* Atomic ownership; implemented by acquisition
  of zookeeper `ephemeral nodes`_ (these nodes act as distributed locks) by
  some set of workers (those workers can be selective in what work they attempt
  to take ownership of).
* Automatic ownership release; lose of previously gained `ephemeral nodes`_
  which happens automatically when the client heartbeat is lost (zookeeper
  will also notify others, via `watches`_ that this ephemeral node has been
  destroyed, which makes it very easy for other workers to then attempt to
  acquire & finish that newly lost/abandoned work).

The issue is that there is currently only one implementation and that
implementation has the following (supposed) drawbacks:

* Requires zookeeper and the supporting infrastructure and brainpower
  to maintain and run java and zookeeper and that surrounding ecosystem. This
  makes certain people sad (``java -Xmx -Xms ...`` doesn't apparently make them
  feel so happy about life).
* Can be complicated to setup (due to previously stated expertise) and
  maintain which can be painful for new developers (those without a zookeeper
  setup) and new operators (or those that just don't want to run java).

To make it possible to gain *most* of the above features using redis we need
to flush out how to make that possible while avoiding some of the *landmines*
that are possible with the implementation of those primitives in redis (for ex,
atomic ownership & release will be more problematic in redis since it lacks the
built-in primitives and support that releases owned items when a client
disconnects or stops sending the appropriate heartbeat).

.. _directory: https://zookeeper.apache.org/doc/trunk/zookeeperOver.html#sc_dataModelNameSpace
.. _conductors: http://docs.openstack.org/developer/taskflow/conductors.html
.. _tasks: http://docs.openstack.org/developer/taskflow/atoms.html#task
.. _flows: http://docs.openstack.org/developer/taskflow/patterns.html#taskflow.flow.Flow
.. _job: http://docs.openstack.org/developer/taskflow/jobs.html#definitions
.. _jobboard: http://docs.openstack.org/developer/taskflow/jobs.html#definitions
.. _ephemeral nodes: http://zookeeper.apache.org/doc/r3.2.1/zookeeperProgrammers.html#Ephemeral+Nodes
.. _features: http://docs.openstack.org/developer/taskflow/jobs.html#features

Proposed change
===============

Add a `redis`_ backed jobboard mechanism using `tooz`_ to implement the base
primitives required (using existing or new tooz concepts/abstractions). Use
these primitives to mirror as much of the previously described
functionality that currently exists for jobs and jobboards using tooz + redis
as the backing implementation.

This will knowingly have the following problems:

* Redis does not support client heartbeats; this will be required to be done
  using timeouts and selected client keys (?) and associated job recovery that
  is done when a jobs owner dies or is lost. This is added complexity that
  zookeeper or raft come with built-in, and is a problem/debt that will be
  incurred with this solution.
* Redis lacks a multi-master strategy (this is getting better with
  `redis clustering`_ in 3.0 but that feature still does not exist as a
  recommended `production ready`_ solution). It is also an unknown how this
  clustering strategy will *really* work under `partitions and high-load`_.

  * Without this feature as production ready it will imply that the redis
    server that clients (job workers and the job posters) connect to will be
    of limited use at large scale without involving client side *static*
    partitioning (dynamic partitioning means the key-space will be split across
    many servers, which can lead to inconsistencies during network partitions
    or server loss...). Until that feature is proven out and known to be
    production ready; I would *personally* rather not recommend it.

* Redis does not support a concept of `watches`_ which the current zookeeper
  backed implementation uses to allow clients (aka workers or conductors) to
  asynchronously (without polling) become aware of new jobs appearing (and
  disappearing). This will need to be worked around by using polling or
  using the `pub/sub`_ capabilities of redis to trigger workers to react to
  new job/s appearing or disappearing.

.. _tooz: https://github.com/stackforge/tooz
.. _redis clustering: http://redis.io/topics/cluster-spec
.. _production ready: http://stackoverflow.com/a/14956106
.. _watches: http://zookeeper.apache.org/doc/trunk/zookeeperProgrammers.html#ch_zkWatches
.. _partitions and high-load: http://aphyr.com/posts/307-call-me-maybe-redis-redux
.. _pub/sub: http://redis.io/commands/pubsub

Alternatives
------------

A few alternatives are possible and from reviewing the current state of the
python world they appear to be.

* `RQ`_; this project does nearly the same thing that is described above, even
  using redis internally. It could be a potential alternative, from looking
  at the source code it has a few inherent flaws (using ``pickle`` to serialize
  the workers function to be executed). It is also not integrated into taskflow
  but it should be a possible reference or alternative that could be worked
  into taskflow (assuming the above `pickle issue`_ usage is
  fixed/removed...) and just used. We should likely consider
  this **pretty strongly** as a way to make this work (and just help
  improve the `RQ`_ library?).
* `Raft`_; provide a comparable implementation to the existing zookeeper based
  one but instead back that implementation by a a raft client and require
  individuals and operators that want to take advantage of this feature to
  setup a raft based cluster and associated quorum. This is a desirable and
  likely one of the better/best alternatives (in terms of feature parity and
  capabilities, since the primitives that exist in raft based implementations
  and the API exposed is *nearly* identical to what zookeeper provides). Sadly
  though the implementations that exist for raft seem to be not *yet* mature
  enough for this to be a realistic alternative; I **strongly** believe we can
  revisit this in the near future as those implementations mature and are more
  extensively proven out (and adopted).
* Don't change anything; doesn't seem so elegant (and it also restricts the
  API of the current design to be specific to just one system, which
  means the API can/could be *unknowingly* and *unnecessarily* fragile).

.. _pickle issue: https://github.com/nvie/rq/issues/378
.. _RQ: http://python-rq.org/
.. _raft: http://raftconsensus.github.io/

Impact on Existing APIs
-----------------------

No new API changes, this should be a API compatible new backend that can be
selected using `stevedore`_. If the existing API is to specific to the current
implementation then we will need to consider how to adjust the existing API
in a backward-compatible manner.

.. _stevedore: http://stevedore.readthedocs.org/

Security impact
---------------

Redis has limited support for authentication features as it is designed to
be ran `inside trusted environments`_. This should be taken into account when
selecting redis as a deployed implementation. The existing zookeeper one is
better off since it supports `SASL`_ (since 3.4.0) and it has concepts
of restricted `ACLs`_ natively built-in.

.. _inside trusted environments: http://redis.io/topics/security
.. _sasl: https://github.com/ekoontz/zookeeper/wiki
.. _acls: http://zookeeper.apache.org/doc/r3.1.2/zookeeperProgrammers.html#sc_ZooKeeperAccessControl

Performance Impact
------------------

None expected.

Configuration Impact
--------------------

A new set of configuration will be required when selecting the new backend. It
will likely involve at least the following:

* The redis server IP and port.
* The key prefix that should be used (used for name-spacing
  servers and clients).
* A pub/sub channel/s (used so that workers become aware of new work being
  posted).
* Likely a few others.

Developer Impact
----------------

This should make it easier for developers (and deployers) to start using the
job and jobboard functionality that taskflow offers and makes it easier for
them to test locally (using redis) and deploy to small and medium sized
environments (also using redis) and for larger environments they can use the
alternative (but feature compatible implementation using zookeeper, or later
raft when that is ready).

Implementation
==============

Assignee(s)
-----------

Primary assignee:

* ``<TBD>``

Other contributors:

* ``<TBD>``

Milestones
----------

K (or at least end of J).

Work Items
----------

* Investigate a prototype with the RQ library (and report back on failure
  or successes). If this seems like a feasible implementation consider just
  using it instead.
* If RQ is not a feasible implementation then create a implementation using
  tooz primitives (the tooz library likely requires redis additions to make
  this possible). If the tooz change becomes not feasible, then just use the
  redis python library and work on making the other solutions more
  feasible (and eventually depreciating/replacng the created implementation
  when those other solutions become feasible).
* Test like crazy.
* Provide/update `documentation`_ so that people know how to use it.

Incubation
==========

N/A

Adoption
--------

N/A

Library
-------

N/A

Anticipated API Stabilization
-----------------------------

Hopefully the existing API that already exist just works and no tweaks are
required to make the redis implementation operate correctly. If stabilization
is required I would expect it to not take more than one release cycle to
flush out/adjust.

Documentation Impact
====================

New documentation describing the feature, how to use it and the features (and
any described drawbacks, see above) that come along with using it. It is
expected that the `documentation`_ will be updated accordingly with
this new addition so that users can easily reference how to take advantage
of it (extra brownie points for adding *working* and
*understandable* `examples`_ as well).

.. _documentation: http://docs.openstack.org/developer/taskflow/
.. _examples: http://docs.openstack.org/developer/taskflow/#examples

Dependencies
============

* Redis client in requirements: already exists as the redis `python client`_ is
  already part of the global requirements repository (the requirement was added
  at least before or during the havana cycle, so has been existing there for
  quite a while).
* RQ in requirements (if it is feasible) or tooz in requirements (both are not
  currently in the requirements respository).

.. _python client: https://pypi.python.org/pypi/redis/

References
==========

If tooz works out, then we can also/later consider moving the zookeeper based
implementation also to complementary tooz primitives and remove/depreciate or
augment some or all of that code in taskflow existing implementation.

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

