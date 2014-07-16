..
  This template should be in ReSTructured text.  For help with syntax,
  see http://sphinx-doc.org/rest.html

  To test out your formatting, build the docs using tox, or see:
  http://rst.ninjs.org

  The filename in the git repository should match the launchpad URL,
  for example a URL of
  https://blueprints.launchpad.net/oslo/+spec/awesome-thing should be
  named awesome-thing.rst.

  Please wrap text at 79 columns.

  Please do not delete any of the sections in this
  template.  If you have nothing to say for a whole section, just write: None

  If you would like to provide a diagram with your spec, ascii diagrams are
  required.  http://asciiflow.com/ is a very nice tool to assist with making
  ascii diagrams.  The reason for this is that the tool used to review specs is
  based purely on plain text.  Plain text will allow review to proceed without
  having to look at additional files which can not be viewed in gerrit.  It
  will also allow inline feedback on the diagram itself.

=======================================
Oslo Cache Updated to use dogpile.cache
=======================================

`proposed bp oslo-cache-using-dogpile
<https://blueprints.launchpad.net/oslo/+spec/oslo-cache-using-dogpile>`_

Currently the various OpenStack projects implement caching (memoization,
key-value-store, etc) in a number of various ways. All of the mechanisms for
caching should be unified under a single Oslo library ``oslo.cache``.

Problem description
===================

With the many implementations (and varying degree of flexibility) OpenStack
projects should standardize on a single library for caching (memoization,
key-value-store, etc) within the code base. Currently, Keystone has used
`dogpile.cache <http://dogpilecache.readthedocs.org/en/latest/>`_ very
successfully. With the flexible backend implementation, ``dogpile.cache`` is
a natural fit to replace the many different implementations of caching.

The new ``oslo.cache`` library would replace the following:

* Keystone Caching Layer

* Keystone Key-Value-Store Implementation

* Oslo MemoryCache Module

* Caching within the Keystone Middleware

* Marconi use of oslo.cache (incubator) module

* (potentially) Swift Ring Memcache


This new module would also open the door for other projects to more easily
adopt memoization or other forms of caching.

The ``oslo.cache`` module is mostly targeted to be an OpenStack friendly
wrapper for ``dogpile.cache``. This will provide a consistent way to cache and
memoize data within the OpenStack ecosystem.


Proposed change
===============

The current ``oslo-incubator``
`oslo openstack.common.cache module
<https://git.openstack.org/cgit/openstack/oslo-incubator/openstack/common/
cache>`_
would be replaced with an implementation that leverages ``dogpile.cache``
library instead of a custom-built system.

This new implementation will provide a mechanism to handle key-value-store
(e.g. traditional Memcached) and memoization to begin with.

The Base backends that will be supported are:

* Memcached

  * BMemcached

  * Standard Memcached

  * Pylibmc

* In-Memory (Python dict-based)

* Redis

* MongoDB - There is a MongoDB backend that was developed for Keystone, a
  similar (based upon the code in Keystone) implementation will be submitted
  as an enhancement to the ``dogpile.cache`` library if it is not already
  supported at the time of implementation. If the backend is not accepted
  by the ``dogpile.cache`` library, it will be maintained in the
  to-be-determined method of maintaining OpenStack specific backend modules.


The ``oslo.cache`` module is intended to provide 3 distinct features above
and beyond raw use of ``dogpile.cache``:

* OpenStack style configuration of ``dogpile.cache``. It is not expected that
  ``dogpile.cache`` would accept patches that include ``oslo.config`` as the
  basis. Use of ``oslo.config`` would not be appropriate in the case of
  a more general-purpose library such as ``dogpile.cache``.

* Updates to ``dogpile.cache``. Any updates that are needed to support the
  OpenStack specific configuration will be submitted to the upstream library.
  This may include enhancements to the decorators for memoization and the
  key-value-store interfaces. These potential enhancements will be submitted
  with the plan to use them as they become available (oslo.cache may have a
  little extra conditional code added until the new features are released and
  OpenStack accepts the minimum ``dogpile.cache`` version increase to the
  global requirements), but it should not block development or use of the
  ``oslo.cache`` module.

* Backend maintenance. If the MongoDB backend is not accepted by the
  ``dogpile.cache`` library a clear path for maintaining OpenStack specific
  backends will be documented and laid out (either within ``oslo.cache`` module
  or an associated module).


Each project that implements either it's own version of caching using
``dogpile.cache`` or other implementations of caching will be converted to use
the new ``oslo.cache`` module.


Alternatives
------------

This could be left to each project to implement their own caching or develop
an OpenStack specific set of modules. Neither of these options are optimal as
it requires specific knowledge of the various (or OpenStack specific) caching
system to implement a custom backend. With ``dogpile.cache`` it is possible to
implement a very simple backend and configure it for use with all OpenStack
services that make use of the ``oslo.cache`` module.

Impact on Existing APIs
-----------------------

Current APIs should remain unchanged (both in Oslo and in other projects) until
caching is implemented. Caching implementation may impact the APIs in some
regard (e.g. memoization requires proper invalidation of data).

The current ``oslo.cache`` module will remain available but be marked as
deprecated. The new ``oslo.cache`` implementation will be provided side-by-side
for a period of time to allow time for any current consumers of ``oslo.cache``
to change-over to the ``dogpile.cache`` based implementation.

``oslo.cache`` will provide a fairly simple constructor to access/instantiate
the CacheRegion object(s) based upon the configuration built with
``oslo.cache``. There will also be an option to extract the configuration
dictionary that can be directly passed to ``dogpile.cache`` if a developer
chooses to do so.

Security impact
---------------

No direct security implications. Use of the new caching module requires all
cached data to be properly invalidated (on change, etc). Stale data could
cause security related impact (and thus should be closely reviewed).

Performance Impact
------------------

Ideally the performance impact of using caching should be only positive,
however maintenance of the cache coherency can have overhead when caching
is implemented.

It is likely ``dogpile.cache`` will have a better performance profile than
the current ``MemoryCache`` module.

Configuration Impact
--------------------

New options for caching will be added. To leverage caching the configuration
for a service using ``oslo.cache`` will need to have the values set.

By default caching will be disabled (can be overrided by a project) to ensure
that memory leaking / improper caching / negative performance impact waiting on
non-existent external services will not impact an OpenStack project.

Developer Impact
----------------

Developers will need to become familiar with ``dogpile.cache`` and how to
implement usage of memoization and/or key-value-store regions.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Morgan Fainberg <mdrnstm>

Other contributors:
  Michael Bayer
  Flavio Percoco

Milestones
----------

Target Milestone for completion:
  Kilo-2

Work Items
----------

* Convert ``oslo.cache`` module over to use ``dogpile.cache``

* Provide a clean / easy way to configure the cache region (in-memory
  cache object that provides access to the key-value-store and memoization
  decorators)

* Ensure design allows for future expansion into cryptographic signing and/or
  encryption of data stored within the key-value-store backend.


Incubation
==========

Lifecycle will be incubation, and adoption in projects that leverage either
``dogpile.cache`` directly (Keystone) or the oslo.MemoryCache module. Once
the interfaces are stable (and clearly documented) it is expected this module
can quickly move to graduation.

Adoption
--------

Keystone will be the primary (first target) to adopt the new module (replacing
the custom ``dogpile.cache`` implementation.

The oslo.MemoryCache module will be updated to leverage the new ``oslo.cache``
module.

The direct use of the oslo.MemoryCache module will be deprecated in favor of
directly using ``oslo.cache``.


Library
-------

The Library will graduate into a top-level ``oslo.cache`` library.

Anticipated API Stabilization
-----------------------------

I expect that this library should be able to stabilize within a single
development cycle. Adoption via incubator for Kilo and L, release as a library
in either K or L.

Documentation Impact
====================

* Documentation on configuring the cache region will be required.

* Developer documentation on implementing key-value-store and memoization
  within an OpenStack project will be needed.

Dependencies
============

All dependencies should already be in the global requirements. No external
blueprints should be needed.

References
==========


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

