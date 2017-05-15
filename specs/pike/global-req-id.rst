====================
 Global Request IDs
====================

https://blueprints.launchpad.net/oslo?searchtext=global-req-id

Building a complex resource, like a boot instance, requires not only
touching a number of Nova processes, but also other services such as
Neutron, Glance, and possibly Cinder. When we make those service jumps
we currently generate a new request-id, which makes tracing those
flows quite manual.

Problem description
===================

When a user creates a resource, such as a server, they are given a
request-id back. This is generated very early in the paste pipeline of
most services. It is eventually embedded into the ``context``, which
is then used implicitly for logging all activities related to the
request. This works well for tracing requests inside of a single
service as it passes through its workers, but breaks down when an
operation spans multiple services. A common example of this is a
server build, which requires Nova to call out multiple times to
Neutron and Glance (and possibly other services) to create a server on
the network.

It is extremely common for clouds to have an ELK (Elastic Search,
Logstash, Kibana) infrastructure that is consuming their logs. The
only way to query these flows is if there is a common identifier
across all relevant messages. A global request-id immediately makes
existing deployed tooling better for managing OpenStack.

Proposed change
===============

The high level solution is as follows (details on specific points
later):

- accept an inbound X-OpenStack-Request-ID header on requests. Require
  that it looks like a uuid to prevent injection issues. Set this to
  the value of ``global_request_id``
- Keep the auto generated existing request_id
- update oslo.log to default also log ``global_request_id`` when it is
  in a context logging mode.


Paste pipelines
---------------

The processing of incoming requests happens piecemeal through the set
of paste pipelines. These are mostly common between projects, but
there are enough local variation to highlight what this looks like for
the base IaaS services, which will be the initial targets of this spec.

Neutron [#f1]_
~~~~~~~~~~~~~~

.. code-block:: ini

   [composite:neutronapi_v2_0]
   use = call:neutron.auth:pipeline_factory
   noauth = cors http_proxy_to_wsgi request_id catch_errors extensions neutronapiapp_v2_0
   keystone = cors http_proxy_to_wsgi request_id catch_errors authtoken keystonecontext extensions neutronapiapp_v2_0
   #                                  ^                                 ^
   # request_id generated here -------+                                 |
   # context built here ------------------------------------------------+

Glance [#f2]_
~~~~~~~~~~~~~

.. code-block:: ini

   # Use this pipeline for keystone auth
   [pipeline:glance-api-keystone]
   pipeline = cors healthcheck http_proxy_to_wsgi versionnegotiation osprofiler authtoken context  rootapp
   #                                                                                      ^
   # request_id & context built here -----------------------------------------------------+

Cinder [#f3]_
~~~~~~~~~~~~~

.. code-block:: ini

   [composite:openstack_volume_api_v3]
   use = call:cinder.api.middleware.auth:pipeline_factory
   noauth = cors http_proxy_to_wsgi request_id faultwrap sizelimit osprofiler noauth apiv3
   keystone = cors http_proxy_to_wsgi request_id faultwrap sizelimit osprofiler authtoken keystonecontext apiv3
   #                                  ^                                                   ^
   # request_id generated here -------+                                                   |
   # context built here ------------------------------------------------------------------+

Nova [#f4]_
~~~~~~~~~~~

.. code-block:: ini

   [composite:openstack_compute_api_v21]
   use = call:nova.api.auth:pipeline_factory_v21
   noauth2 = cors http_proxy_to_wsgi compute_req_id faultwrap sizelimit osprofiler noauth2 osapi_compute_app_v21
   keystone = cors http_proxy_to_wsgi compute_req_id faultwrap sizelimit osprofiler authtoken keystonecontext osapi_compute_app_v21
   #                                  ^                                                       ^
   # request_id generated here -------+                                                       |
   # context built here ----------------------------------------------------------------------+


oslo.middleware.request_id
--------------------------

In nearly all services the request_id generation happens very early,
well before any local logic. The middleware sets an
X-OpenStack-Request-ID response header, as well as variables in the
environment that are later consumed by oslo.context.

We would accept an inbound X-OpenStack-Request-ID, and validate that
it looked like ``req-$UUID`` before accepting it as the
``global_request_id``.

The returned X-OpenStack-Request-ID would be the existing
``request_id``. This is like the parent process getting the child
process id on a fork() call.

oslo.context from_environ
-------------------------

Fortunately for us most projects now use the oslo.context
``from_environ`` constructor. This means that we can add content to
the context, or adjust the context, without needing to change every
project. For instance in Glance the context constructor looks like
[#f5]_:

.. code-block:: python

   kwargs = {
      'owner_is_tenant': CONF.owner_is_tenant,
      'service_catalog': service_catalog,
      'policy_enforcer': self.policy_enforcer,
      'request_id': request_id,
   }

   ctxt = glance.context.RequestContext.from_environ(req.environ,
                                                     **kwargs)

As all logging happens *after* the context is built. All required
parts of the context will be there before logging starts.

oslo.log
--------

oslo.log defaults should include ``global_request_id`` during context
logging. This is something which can be done late, as users can always
override there context logging string format.

projects and clients
--------------------

With the infrastructure above implemented it will be a small change to
python clients to save and emit the ``global_request_id`` when
created. For instance, Nova calling Neutron, during the get_client
call ``context.request_id`` would be stored in the client. [#f6]_:

.. code-block:: python


    def _get_available_networks(self, context, project_id,
                                net_ids=None, neutron=None,
                                auto_allocate=False):
        """Return a network list available for the tenant.
        The list contains networks owned by the tenant and public networks.
        If net_ids specified, it searches networks with requested IDs only.
        """
        if not neutron:
            neutron = get_client(context)

        if net_ids:
            # If user has specified to attach instance only to specific
            # networks then only add these to **search_opts. This search will
            # also include 'shared' networks.
            search_opts = {'id': net_ids}
            nets = neutron.list_networks(**search_opts).get('networks', [])
        else:
            # (1) Retrieve non-public network list owned by the tenant.
            search_opts = {'tenant_id': project_id, 'shared': False}
            if auto_allocate:
                # The auto-allocated-topology extension may create complex
                # network topologies and it does so in a non-transactional
                # fashion. Therefore API users may be exposed to resources that
                # are transient or partially built. A client should use
                # resources that are meant to be ready and this can be done by
                # checking their admin_state_up flag.
                search_opts['admin_state_up'] = True
            nets = neutron.list_networks(**search_opts).get('networks', [])
            # (2) Retrieve public network list.
            search_opts = {'shared': True}
            nets += neutron.list_networks(**search_opts).get('networks', [])

        _ensure_requested_network_ordering(
            lambda x: x['id'],
            nets,
            net_ids)

        return nets

.. note::

   There are some usage patterns where a client is built and kept for
   long running operations. In these cases we'd want to change the
   model to assume that clients are ephemeral, and should be discarded
   at the end of their flows.

   This will also help tracking non user initiated tasks such as
   periodic jobs that touch other services for information refresh.


Alternatives
------------

Log in the Caller
~~~~~~~~~~~~~~~~~

There was a previous OpenStack cross project spec to completely handle
this in the caller - https://review.openstack.org/#/c/156508/. That
was merged over 2 years ago, but has yet to gain traction.

It had a number of disadvantages. It turns out the client code is far
less standardized here, so fixing every client was substantial
work.

It also requires some standard convention for writing these things out
to logs on the caller side that is consistent between all services.

It also **does not** allow people to use Elastic Search to trace their
logs (which all large sites have running). A custom piece of analysis
tooling would need to be built.

Verify trust in callers
~~~~~~~~~~~~~~~~~~~~~~~

A long time ago, in a galaxy far far away, in a summit room I was not
in, I was told there was a concern about clients flooding this
field. There has been no documented attack that seems feasable here if
we strictly validate the inbound data.

There is a way we could use Service roles to validate trust here, but
without a compelling case for why that is needed, we should do the
simpler thing.

For reference Glance already accepts a user provided request-id of 64
characters or less. This has existed there for a long time, with no
reports as to yet for abuse. We could consider dropping the last
constraint and not doing role validation.


Swift multipart transaction id
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Swift has a related approach where their transaction id, which is a
multipart id that includes a piece generated by the server on inbound
request, a timestamp piece, a fixed server piece (for tracking
multiple clusters), and a user provided piece. Swift is not currently
using any of the above oslo infrastructure, and targets syslog as
their primary logging mechanism.

While there are interesting bits in this approach, it's a less
straight forward chunk of work to transition to, given the oslo
components. Also, oslo.log has many structured log back ends (like
json stream, fluentd, and systemd journal) where we really would want
the global and local as separate fields so there is no heuristic
parsing required.

Impact on Existing APIs
-----------------------

oslo.middleware request_id contract will change so that it accepts an
inbound header, and sets a second env variable. Both are backwards
compatible.

oslo.context will accept a new local_request_id. This requires
plumbing local_request_id into all calls that take request_id. This
looks fully backwards compatible.

oslo.log will need to be adjusted to support logging both
request_ids. It should probably be enabled to do that by default,
though log_context string is a user configured variable, so they can
set whatever site local format works for them. An upgrade release note
would be appropriate when this happens.

Security impact
---------------

There previously was a concern about trusting request ids from the
user. It is an inbound piece of user data, so care should be taken.

* Ensure it is not allowed to be so big as to create a DOS vector
  (size validation)
* Ensure that it is not a possible code injection vector (strict
  validation)

These items can be handled with strict validation of the content that
it looks like a valid uuid.


Performance Impact
------------------

Minimal. This is a few extra lines of instruction in existing through
paths. No expensive activity is done in this new code.

Configuration Impact
--------------------

The only configuration impact will be on the oslo.log context string.

Developer Impact
----------------

Developers will now have much easier tracing of build requests in
their devstack environments!

Testing Impact
--------------

Unit tests provided with various oslo components.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  sdague

Other contributors:
  None

.. note::

   Could definitely use help to get this through the gauntlet, there
   are lots of little patches here to get right.

Milestones
----------

Target Milestone for completion: TBD

Work Items
----------

TBD

Documentation Impact
====================

TBD - but presumably some updates to operators guide on tracing across
services.

Dependencies
============

None

References
==========

.. [#f1] https://github.com/openstack/neutron/blob/5691f29e8fd1212bb22b1a48d32dbbddf7e0587d/etc/api-paste.ini#L6-L9
.. [#f2] https://github.com/openstack/glance/blob/5caf1c739e190338e87be8bcd880cb88b0920299/etc/glance-api-paste.ini#L13-L15
.. [#f3] https://github.com/openstack/cinder/blob/81ece6a9f2ac9b4ff3efe304bab847006f8b0aef/etc/cinder/api-paste.ini#L24-L28
.. [#f4] https://github.com/openstack/nova/blob/c2c6960e374351b3ce1b43a564b57e14b54c4877/etc/nova/api-paste.ini#L29-L32
.. [#f5]
   https://github.com/openstack/glance/blob/70d51c7c5c09b070588041a65905eba789ae871b/glance/api/middleware/context.py#L179-L187
.. [#f6] https://github.com/openstack/nova/blob/c2c6960e374351b3ce1b43a564b57e14b54c4877/nova/network/neutronv2/api.py#L317-L354


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
