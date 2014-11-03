===================================================================
 Provide application-agnostic logging parameters in format strings
===================================================================

https://blueprints.launchpad.net/oslo.log/+spec/app-agnostic-logging-parameters

We still have some nova-specific names in the default logging format
string, and we want to eliminate those to make oslo.log more generally
useful across projects.

Problem description
===================

The default ``logging_context_format_string`` and
``logging_default_format_string`` option values include
``%(instance)s``, which is not useful in all projects. We should do
something like what we did with "user_identity" and provide a generic
name, which the projects can fill in with their desired value.

Proposed change
===============

Make :class:`RequestContext` from :mod:`openstack.common.context` into
an abstract base class for other applications to use for their own
application-specific request contexts. In the new base class, define
some abstract properties with generic names like ``user_identity``,
``resource_id``, the chain of request ids, etc. that the subclass
can override.

Change the default for the logging format strings to refer to these
generic names.

Add a new method to the base class to return values useful for
logging. We cannot use the existing :meth:`to_dict` because we expect
the logging values to contain generated properties not used for things
like reconstructing the context when it passes through RPC calls.

::

   def get_logging_values(self):
       """Return a dict containing values for logging using this context.
       """
       values = self.to_dict()
       values.update({
          'user_identity': self.user_identity,
          'resource_id': self.resource_id,
          'request_chain': ' '.join(self.request_ids),
       })
       return values

Remove the other functions in the :mod:`context` module for creating
and testing contexts. The applications all have their own version of
these functions and the versions provided in :mod:`context` are not
useful when subclasses of :class:`RequestContext` are used.

Update the logging code to use :meth:`get_logging_values` instead of
:meth:`to_dict`.

Alternatives
------------

We had previously talked about removing this module entirely, but
given changes to logging to make the user identity parameters log
consistently across projects, I think making it a useful base class is
a better approach.

Impact on Existing APIs
-----------------------

Existing context classes will be updated to be subclasses of the base
class, which may allow us to save some repeated code in the
constructor.

Security impact
---------------

When we talk about logging and contexts together we typically worry
about exposing secret details. I don't think any of these proposed
changes expose any information beyond what we are exposing already.

Performance Impact
------------------

Possibly a slight impact creating :class:`RequestContext` instances in
the application. If an app sees that as a problem, they could opt to
simply copy the base class API into their local class rather than
using a subclass, but it would be up to them to keep up with API
changes at that point. I don't think this is a significant performance
issue.

Configuration Impact
--------------------

The defaults for the configuration options might change, but the
*output* should be the same and the old values will still work as well
as they did before.

Developer Impact
----------------

The idea is for the other projects to define their context as a
subclass of the :class:`RequestContext` in Oslo, implementing or
overriding private methods or properties in order to meet the API
needed by the logging module.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Doug Hellmann (doug-hellmann)

Other contributors:
  None

Milestones
----------

Target Milestone for completion: Kilo-2

Work Items
----------

1. Remove unused functions from :mod:`context`.
2. Add new :meth:`get_logging_values` to :class:`RequestContext`.
3. Add abstract properties to :class:`RequestContext`.
4. Update default format strings in :mod:`log`.
5. Update :mod:`log` to use :meth:`get_logging_values`.

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

I expect :meth:`get_logging_values` to be stable.

We may add more generated properties to :class:`RequestContext` over
time, but we will have to add those as normal properties (not
abstract) to provide backwards compatibility.

Documentation Impact
====================

The defaults for the config options will need to be updated in any
documentation generated from the option definitions.

Dependencies
============

None

References
==========

* Discussion at the juno summit:
  https://etherpad.openstack.org/p/juno-oslo-release-plan
* Mailing list thread that mentions the domain support in Oslo's
  context as a potential issue for nova:
  http://lists.openstack.org/pipermail/openstack-dev/2014-February/027634.html


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
