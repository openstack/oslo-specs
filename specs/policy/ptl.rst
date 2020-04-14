===========
 PTL Guide
===========

There are some Oslo-specific aspects to being the Oslo PTL. This document is
a place to capture those for future reference.

Problem Description
===================

Each PTL learns things about the position during the time in which they serve
it. However, historically they've kept private notes that had to be passed
along from PTL to PTL, which is not ideal. First, if the handoff doesn't happen
for any reason, the new PTL will have to start over from scratch. Second, it
makes these notes hidden from public view, which is not useful for potential
future PTL candidates.

Proposed Policy
===============

This should be a living document that is updated by PTLs as they discover
new best practices and tips for leading the Oslo project.

A new or future PTL should first read the `Project Team Guide PTL Document`_.
It contains a wealth of useful information that a PTL should know. Pay
particular attention to the parts about delegating.

Releases
--------
In general, the PTL or release liaison should `propose releases`_ for all Oslo
libraries that need one weekly. Generally this is done early in the week, and
releasing on Friday is avoided when possible to avoid anyone having to work
the weekend to fix a breakage. If a critical fix needs to be released
immediately, it does not have to wait for the regular weekly release cycle.
The intent of the weekly cycle is to ensure changes get released in a timely
fashion, not to prevent anything from being released.

Exceptions to the weekly release schedule can be made at the discretion of the
PTL. Releasing immediately before a holiday when most of the team will not be
around is not ideal. It is also a good idea to wait to release master after a
new stable branch has been cut until the release associated with the stable
branch has shipped. This allows backports of things like dependency bumps in
case bugs are found during final testing of an OpenStack release. In that case,
a minor version bump would be needed and if master has already been released
then that minor version will already be taken.

.. note:: In general, minor version changes are not allowed on stable branches,
          but exceptions can be made if the situation warrants it. See
          the `stable branch guide`_ for more details.

When making releases, there are some useful commands to know. First, to find
all the changes in all the Oslo libraries since they were last released, use
the following commands in the openstack/releases repo::

   ./tools/list_unreleased_changes.sh master $(.tox/venv/bin/list-deliverables --team oslo -r)
   ./tools/list_unreleased_changes.sh master $(.tox/venv/bin/list-deliverables --team oslo -r --series independent)

.. note:: These commands assume that the ``venv`` tox environment has been
          created. That can be done with the command ``tox -e venv --notest``

.. note:: Oslo contains both libraries that are tied to the OpenStack release
          as well as some that are independent of it. That's why two commands
          are needed to cover all of them.

To do the same for a stable branch, use the following (replace the branch names
as appropriate)::

   ./tools/list_unreleased_changes.sh stable/train $(.tox/venv/bin/list-deliverables --team oslo -r --series train)

Meetings
--------
The Oslo team typically meets weekly. The specific day and time can be found
on the `eavesdrop page`_. The PTL normally chairs the meeting, but other
contributors can also do so if desired or needed. The `meeting agenda`_
can be found on the wiki page. Chairing the meeting involves going through
the topics in the agenda - some weeks this takes 15 minutes or less, others
it takes the full hour or more.

Ping List
---------
The Oslo team uses a courtesy ping list in the `meeting agenda template`_ so
regular meeting attendees can be reminded of the start of the meeting.
Attendees can add or remove their names as desired and the person running
the weekly meeting should copy the ping list into IRC so everyone on the list
gets a notification.

Weekly Wayward Review
---------------------

This meeting topic requires a bit more explanation. The idea is to find an old
review and move it along in some way. This means at the end of the meeting,
the review should either be approved, -1'd, or have someone assigned to follow
up after the meeting.

bnemec uses `reviewstats`_ to find the oldest open reviews in Oslo.

Beginning of Cycle Activities
-----------------------------

* The ping list should be cleared each cycle to avoid pinging people who no
  longer work on Oslo. A new ping list can be created in parallel to the old
  one to allow contributors who want to stay on the list to sign up before the
  list is cleared. These parallel lists should both exist for a couple of weeks
  to give everyone a chance to update the new one.

* When a new release name is announced, it needs to be added to the oslo.log
  versionutils module. See this `versionutils review`_ for an example.

* At the start of each cycle, the Oslo `feature freeze`_ date should be added
  to the release calendar. See this `feature freeze date review`_ for an
  example of doing that. A detailed explanation of why Oslo has its own
  feature freeze can be found in the `feature freeze`_ policy.

* Check the `oslo-coresec`_ group and make sure all members are active Oslo
  cores so private security bugs are not being sent out to people who don't
  need to see them. If necessary, add current core team members to ensure
  that there are enough people on the coresec team to handle any security bugs
  that come in.

  For more details on managing the coresec team, see the
  `vulnerability management team's requirements`_.

End of Cycle Activities
-----------------------

* Make sure all libraries get released before non-client library freeze, even
  if they don't have changes that would normally prompt a release (such as
  doc or test changes). This may be handled automatically by the release team
  now, but it's still good to do it explicitly. It is important for all changes
  to be released before stable branches are cut because branches are based on
  the last released commit, not what was on master at the time. If there are
  unreleased doc or test changes they may be lost on the stable branch and need
  to be backported.

  When doing the final release of a library for the cycle, also request to
  create the appropriate stable branch. For an example of doing so, see
  `this branch creation request`_. In the future this can all be done in one
  review, but it's a change in the previous process so there are no example
  reviews for that yet.

  When doing a final release, you can easily include the branch creation
  with it by adding ``--stable-branch`` to the new_release.sh call. For
  example::

    ./tools/new_release.sh ussuri oslo.config feature --stable-branch

* Manually request a stable branch for the devstack-plugin repos. Because these
  are not released, they are not automatically branched. For details on how to
  do this, see this `branch request`_ change.

PTL Handoff Activities
----------------------

Hopefully most of these activities are automated, but one thing that needs to
be done manually is to make the new PTL an administrator on the
`oslo-coresec`_ group in Launchpad.


.. _`Project Team Guide PTL Document`: https://docs.openstack.org/project-team-guide/ptl.html
.. _`propose releases`: https://releases.openstack.org/reference/using.html#requesting-a-release
.. _`stable branch guide`: https://docs.openstack.org/project-team-guide/stable-branches.html#appropriate-fixes
.. _`eavesdrop page`: http://eavesdrop.openstack.org/#Oslo_Team_Meeting
.. _`meeting agenda`: https://wiki.openstack.org/wiki/Meetings/Oslo#Agenda_for_Next_Meeting
.. _`meeting agenda template`: https://wiki.openstack.org/wiki/Meetings/Oslo#Agenda_Template
.. _`reviewstats`: https://opendev.org/openstack/reviewstats
.. _`versionutils review`: https://opendev.org/openstack/oslo.log/commit/adef9b6ecbecedad9836e96a092c32cc8a17eb97
.. _`feature freeze`: http://specs.openstack.org/openstack/oslo-specs/specs/policy/feature-freeze.html
.. _`feature freeze date review`: https://github.com/openstack/releases/commit/58585a1fa0084fb8aca8146c848d338ccc7766ba#diff-6590df7965d3a63150e201d8881d33f9
.. _`vulnerability management team's requirements`: https://governance.openstack.org/tc/reference/tags/vulnerability_managed.html#requirements
.. _`this branch creation request`: https://review.opendev.org/#/c/718760/
.. _`branch request`: https://review.openstack.org/#/c/650118/
.. _`oslo-coresec`: https://launchpad.net/~oslo-coresec

Alternatives & History
======================

As discussed in the problem description, we could continue to have the Oslo
PTL maintain a private set of notes that is passed individually to the next
PTL. This is not preferred for the reasons mentioned there.

Implementation
==============

Author(s)
---------

Primary author:
  bnemec

Other contributors:
  Future PTLs

Milestones
----------

N/A

Work Items
----------

Writing the policy itself is the main work item. Updating it as the community
evolves will be an ongoing process.

References
==========

`Ussuri community goal <https://governance.openstack.org/tc/goals/selected/ussuri/project-ptl-and-contrib-docs.html>`_

Revision History
================

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Ussuri
     - Introduced

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

