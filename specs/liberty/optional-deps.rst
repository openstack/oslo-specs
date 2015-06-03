=======================
 Optional Dependencies
=======================

Projects wish to capture their optional dependencies - things they need only
when specific configuration options are enabled. We need to make sure the
plumbing works for this to allow them to do that.

Problem description
===================

Python tooling supports 'extras' but pbr hasn't exposed it, and our tooling is
unaware of it.

Proposed change
===============

Add extras to oslo.db exporting the various driver options it uses, and update
keystone to consume those during CI. Deal with any issues, and then open the
floodgates.

Alternatives
------------

None

Impact on Existing APIs
-----------------------

Folk introspecting requirements.txt will not see the optional dependencies
within a project (but they wouldn't before either). Dependencies using extras
can already be used (e.g. requests[security]) so this isn't new in that
dimension.

Security impact
---------------

None.

Performance Impact
------------------

None.

Configuration Impact
--------------------

None.

Developer Impact
----------------

Developers need to know a little bit more about how Python packaging
works, but not much.

Testing Impact
--------------

None.

Implementation
==============

Assignee(s)
-----------

Who is leading the writing of the code? Or is this a blueprint where you're
throwing it out there to see who picks it up?

If more than one person is working on the implementation, please designate the
primary author and contact.

Primary assignee:
  <launchpad-id or None>

Other contributors:
  <launchpad-id or None>

Milestones
----------

Target Milestone for completion:

Work Items
----------

* Raise the cap on pbr to <2.0 everywhere in master, or perhaps uncapped.
* Decide whether to centralise the driver choices (e.g. postgresql) into the
  oslo library directly using it, or to keep them in the applications, or to
  export the choice from the application but centralise the implementation.
  Concretely, is it 'pip install nova oslo.db[mysql]' or 'pip install
  nova[mysql]', and should the latter case be defined as 'mysql: PyMySQL' or
  'mysql: oslo.db[mysql]'.
* Ensure everyone knows to use latest virtualenv packages (the requirements
  management spec will be driving that).
* Teach update.py to update extras in setup.cfg.
* Document the convention of things for test being in the 'test' extra (used
  via pip install -e .[test]).
* Add extras to oslo.db.
* Add use of those to keystone for CI.
* Announce the readiness and encourage people to do this.

Incubation
==========

N/A.

Documentation Impact
====================

We need to update some pbr docs, but thats about it AFAIK.

Dependencies
============

None known.

References
==========

* summit session https://etherpad.openstack.org/p/YVR-oslo-optional-dependencies
* oslo.db patch https://review.openstack.org/#/c/184328/


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

