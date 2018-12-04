=============================
 Proposals for new libraries
=============================

Quite often Oslo (as a group and project) is requested to create (or adopt)
new libraries for various purposes (some relevant, some not) and it would be
good to (as a group) have a stance on new libraries and the process they need
to go through to either become a new library in Oslo (that the Oslo group will
*own* and maintain going forward) or to become a new library that is
independently maintained on pypi (or some hybrid of both of these approaches).

Problem Description
===================

Assume developer *Bob* wants to make a new library for project(s) in
OpenStack to consume.

Bob at that point has a few options when building out this library:

#. Keep the library independent from the Oslo project. Create library in
   some repository site and produce a functional and useful artifact from
   that library (typically a pypi release) and integrate it into the various
   OpenStack projects once that artifact is created.

   Some **advantages** of this are:

   * Bob can work, release, iterate at his own pace.
   * Wider python community adoption can start **immediately**.

   Some **disadvantages** of this are:

   * Hard to define/find purpose for a library when it is not initially
     integrated into any project (typically to create a good library it
     helps to have an active user of that library for feedback).
   * Gamble in that adoption (in the larger python community or in
     general) may not occur.
   * No direct ability to take advantage of expertise (reviews, experience...)
     developed in the wider Oslo group (aka the creator is on
     his/her own).

#. Create library in some repository site and produce a functional and useful
   artifact from that library (typically a pypi release) and integrate it
   into the various OpenStack projects (either by oneself or with others
   to help) and then propose that the library be moved into the Oslo group's
   ownership for some reasons like it's not maintained by owner but it is
   used across OpenStack projects.

   Some **advantages** of this are (including prior option's advantages):

   * Continued maintenance (and reviews) of created library are now shared
     among the oslo reviewers (and group).

   Some **disadvantages** of this are (including prior options disadvantages):

   * Continued maintenance (and reviews) of created library are now shared
     among the oslo reviewers (and group). The creator may lose of control.
     must follow Oslo's policies.

   There are also a few misconceptions about this approach that should also
   be cleared up (these conceptions may have been previously warranted but
   due to changes in the community they no longer should be deemed so):

   * Adoption in oslo does **not** guarantee success of a library (it will
     still be a large amount of convincing and hard and dirty work to
     be successful).
   * The big tent makes it easier for a library to integrate into the
     OpenStack ecosystems processes without having to join Oslo to also
     benefit from that same ecosystems processes.

   Example **oslo** libraries that followed this workflow:

   * automaton
   * futurist

#. Create library immediately having the Oslo group or subgroup (and by
   default use the OpenStack ecosystem) help in its creation and produce a
   functional and useful artifact from that library (typically a pypi
   release) and integrate it into the various openstack projects.

   Some **advantages** of this are (including prior options advantages):

   * The expertise (years of experience, smart people) the Oslo group has
     can help guide the libraries success.
   * Continued maintenance (and reviews) of created library are now shared
     among the Oslo reviewers (and group). The creator may lose of control,
     since the project is now under Oslo's purview they can approve specs
     and changes that creator might not agree with.

   Some **disadvantages** of this are (including prior options disadvantages):

   * Continued maintenance (and reviews) of created library are now shared
     among the Oslo reviewers (and group).
   * Same misconceptions as stated in previous item.

   Example **oslo** libraries that followed this workflow:

   * tooz
   * debtcollector
   * oslo.privsep

#. Create library inside of a project, prove it is useful to its host
   project (without becoming so specific to that host project that it is not
   useful to anyone else) *then* extract that library to some repository site
   and produce a useful artifact. Following this further maintenance at that
   point will be via that repository site.

   Some **advantages** of this are:

   * Usefulness/purpose of the library will be more well-known due to
     integration with a host project.

   Some **disadvantages** of this are:

   * Usefulness/purpose can be *too* specific to host project (and
     further extraction/refactoring work will be needed to generalize).

   Example **oslo** libraries that followed this workflow:

   * taskflow
   * oslo.versionedobjects

#. Create source code in a host project, at a point where another host
   project would benefit from that same code then extract source code into
   a common incubator. At that point iterate over versions in that incubator
   and periodically sync incubator version into host consuming projects.
   At some point when deemed *stable* extract the incubators version into
   a library and then produce a functional and useful artifact from that
   library (typically a pypi release). Following this further maintenance at
   that point will be via the new library repository site (and typically
   versioning will be followed).

   Some **advantages** of this are:

   * Usefulness/purpose of the library will be more well-known due to
     integration with a *set* of host projects.

   Some **disadvantages** of this are:

   * Typically a larger number of iterations required to extract a
     isolated artifact.
   * Multiple rounds of non-versioned syncing and potential
     API collisions/conflicts (due to incubator copy/paste routine) and
     change iteration.
   * No ability for wider python community adoption from the get go.
   * Harder to cleanup and track.
   * Implementations will likely diverge and the amount of person time
     required to keep in sync.

   Example **oslo** libraries that followed this workflow:

   * oslo.config
   * oslo.cache
   * oslo.concurrency
   * oslo.db
   * oslo.log
   * oslo.messaging
   * oslo.policy
   * oslo.serialization
   * ...


Bob will also have to pick which repository site he will use. For sake
of this document we will assume the majority will choose to use the OpenStack
ecosystems gerrit review system and git based hosting system (but Bob if
he desires can use something like github and pull requests if
he so chooses, as long as Bob takes into consideration that doing this
will be make it harder to get contributions from folks in the OpenStack
community).

Proposed Policy
===============

In order to help Bob (or other author) make a *smart* selection from the
options listed above in the problem statement we as a group (who has
made these decisions many times previously) would like to
help new libraries (and their authors) become successful by having
new library proposals go through a sort of *litmus test* that we as a group
believe will help library creators figure out which of the above listed
options will be better suited for them (and be better suited for their own
library's future success).

To aid in this process we as a group believe that when Bob (or other author)
starts to figure out which of the options he (or she) will take it would
be best for that developer to fill out the template new-library-template.rst
and post it for review on the openstack-discuss mailing list with the [oslo] tag
in the subject. And then let the mailing list figure out which of the above
options will best work for the authors and the community as a whole). This
same information should also be proposed to the oslo-specs repository itself
(if/when the mailing list agrees that it should be a new oslo library).

In order to make the new oslo library healthy and continuous development,
new core contributors for that adopted library are needed, it needs at least
two individuals from the community committed to triaging and fixing bugs, and
responding to test failures in a timely manner.

Alternatives & History
======================

The other options are more along the line of what the Oslo group has
already done which is to have a sort of impromptu and tribal knowledge
around the area of new libraries and the options available to developers
wanting (and/or willing) to make new libraries. This policy will aim to
solidify that knowledge into a document that can be easily referenced and
agreed upon.

Implementation
==============

Author(s)
---------

Primary author: harlowja

Other contributors: gcb

Milestones
----------

Pike

Work Items
----------

#. Draft policy
#. Get feedback on policy
#. Repeat
#. Approve policy

References
==========

* https://etherpad.openstack.org/p/newton-oslo-maybe-new-libraries

Revision History
================

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Pike
     - Introduced

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
