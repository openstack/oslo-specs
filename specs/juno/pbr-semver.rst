..

=============================
 Teaching PBR about semver
=============================

https://blueprints.launchpad.net/oslo/+spec/pbr-semver

OpenStack uses semver but pbr doesn't actually understand it today.
Teaching it to understand semver will allow less thought and more automation
by developers, as well as better and clearer version numbers for folk doing
continual deployment (CD) of OpenStack.

Problem description
===================

With postversioning (the default) given a tag of 1.3.2 pbr generates per-commit
versions of 1.3.2.N.g$sha. pip currently considers such versions invalid, but if
pip learns about build tags - the g$sha, then the version would be considered a
release, but often the intent of an untagged commit is to be a developer
version for local installs / testing. So this is not `PEP-440`_ compliant.
Conflicting with this is the desire of CD deployers and CD packagers to have
monotonic versions that can be used to install packages on e.g. Debian systems,
but subsequent tags can collide with these versions as well.

PEP-440 versions do not map entirely well to version_info - a core python
concept but some users of pbr export version_info tuples in their module, and
offering that would enable them to use pbr.

Lastly, semver provides deterministic rules for picking the next version number
which at the moment is a developer task. Developers can easily get this wrong
because they're having to think 'what version next' vs categorising the changes
in the version.

In summary:

* The versions pbr generates are not always pip compatible (PEP440).

* The versions pbr generates for non-tagged commits are marked as releases
  rather than dev versions. This means that if pushed into a mirror pip
  will default to installing them rather than the latest release.

* There is no tooling support to reconcile the needs of devs (give me a version
  to install) and CD'ers (give me a unique version # for this commit in trunk
  that sorts correctly with all other trunk versions).

* There is no tooling support for picking new (postversioned) version numbers.

Proposed change
===============

Proposed details
----------------

* Change from tagging versions like 1.2.3a4 (which some projects are using) to
  tagging them as 1.2.3.0a4 instead, and update the semver docs to specify the
  leading 0 accordingly. This gets us both PEP440 compatibility (which permits
  either 1.2.3a4 or 1.2.3.0a4 but not 1.2.3.a4) and conceptual compatibility
  with semver where the MAJOR.MINOR.PATCH format is strongly expected to be just
  numbers, which the 3a4 construct breaks. We need to continue accepting the
  current format tags since they already exist on our branches - but we can
  emit deprecation warnings.

* Add pseudo-headers to commits that indicate feature / api-break / deprecation
  / bugfix changes. The default will be to assume bugfix. If a commit fails to
  mention the important changes this can be fixed up with a commit with just
  the metadata header and some trivial change. If a commit incorrectly claimed
  a significant change, we will live with the result - CD users can create
  packages for any commit that has landed in a branch. For instance to mark a
  new feature that introduces api incompatibility::

    sem-ver: feature, api-break

* For untagged builds, generate devN versions - e.g.  x.y.z.dev4+gHASH, where
  x.y.z are derived by applying the semver rules with the metadata about the
  most recent change of each type. For pre-versioned builds, we will also
  generate devN builds but will not apply semver rules. The +gHASH is driven
  by PEP-440, and will be slightly syntax incompatible with upstream semver,
  but we think this is the right tradeoff. Semantically it is compatible.

* Provide a new command (``tag-release``) to do the git tagging for developers.
  It will accept parameters allowing manual control, but will enforce semver is
  being followed (e.g. if there is a newer tag than the version being tagged in
  the history of the branch, that's an error). Alpha, beta and rc tagging can be
  automated too.

* Provide a python API for getting version_info style version data. e.g.::

      import pbr.version
      ...
      version_info = pbr.version.Version('MYPACKAGENAME').version_info()


* Provide a new command (``deb-version``) to output Debian package version
  compatible version strings. This primarily involves translating PEP-440
  precedence rules into Debian ~ and . component separators.

* Provide a new command (``rpm-version``) to output RPM version metadata for
  incorporation in RPM versions using the ENVRA_ format. As RPM lacks a
  'before' operator (~) the primary method for translation is to treat
  pre-release and dev builds as release builds of next lowest version to drive
  the sort order above all actual releases of the version below. We assume that
  no version will ever have more than 9998 patch/minor releases.  E.g.
  1.2.0.dev5 is rendered as 1.1.9999.dev5. 1.0.0.dev5 would be rendered as
  0.0.9999.dev5 and finally 0.0.0.dev5 would also be rendered as 0.0.0.dev5 to
  avoid negative version numbers.

* Provide a new command (``next-version``) to output the next calculated semver
  version. E.g. if the last release was 1.2.3 but backwards incompatibility has
  happened, this command would output 2.0.0. The expected use of this command
  is to aid developers choose the next version to tag.

* sdist and the new Debian and RPM version string commands will accept a
  ``--no-rc`` parameter which will tell them to only ever emit versions that
  are a) normal versions or b) devN builds. This resolves the sorting ambiguity
  in semver where devN is lower than *any* pre-release build, but version
  numbers may not have both a pre-release version *and* a devN version
  component. CD deployers can then include --no-rc in their scripts and have a
  consistent timeline (as long as they're pulling from a monotonically
  advancing branch) while regular users and packagers will want to select
  regular builds only.

  There is one caveat here which is that new point releases of old versions
  must not be merged into the history of trunk, or the devN versions will be
  reset at that point.

New configuration flags
^^^^^^^^^^^^^^^^^^^^^^^

We are adding a new command line option.

1. ``--no-rc`` passed on the command line to commands that output versions.
   When passed this causes version calculation from git tags to never output
   alpha/beta/rc versions - it will always work towards normal versions (that
   is X.Y.Z versions). This provides a stable comparable timeline for versions
   within one branch, so long as the 'most recent release' never resets without
   also moving up to the next semver mandated version. For instance, working
   with master, if semver dictates that the next version will be 1.2, and the
   current version is 1.1.2 adding a new tag of 1.1.3 reachable from master
   will reset the devN versions for all commits subsequent to 1.1.3 and thus
   invalidate this timeline. Adding a tag of 1.2 is however fine, because the
   next calculated version will be (at lowest) 1.2.1, and the devN versions
   for any remaining unreleased commits will have a higher precedence than the
   prior 1.2.0 devN versions before the 1.2 tag was added.


New post-version rules
^^^^^^^^^^^^^^^^^^^^^^

There are four incrementable components in a version: major, minor, patch and
pre-release. The following is a description of how pbr will implement the
assignment rules described by semver.rst for post-versioned numbers. For
pre-versioned numbers, the user specifies the target version to use and we
cannot automatically increment versions. A future spec may consider doing
semver with pre-versioned version numbers in pbr, but since they are often
not semver versions, and because their definition is 'the user has chosen',
it is out of scope for now.

1. If there are one or more tags for a commit then the highest such tag is
    considered to be the 'last tag' for these rules.

2. If the last tag is a pre-release tag, then the --no-rc option is consulted.
   If set, pre-release tags are not considered when looking for the last
   tag.

3. The highest eligible tag reachable from the commit is considered to be the
   'last tag'. If there is more than one tag with equal distance (e.g. an rc
   and a final tag on a single commit) then the highest tag is still used. If
   there is no tag reachable at all, ``0.0.0`` is implied as the last tag.
   Tags are eligible if they are PEP-440 version strings, reachable from the
   commit in the git history, and not excluded by the --no-rc option.

4. If the distance to the last tag is zero, that tag supplies the version and
   the process stops.

5. Otherwise, a patch level version is required and the version shall be a
   devN version.

6. We then ask git for all the commits leading back to the last tag.

7. In each commit we look for a sem-ver: pseudo header, and if found
   parse it (split on ',' whitespace strip and build a set). Unknown
   symbols are not an error (so that folk can't wedge pbr), but we will
   warn on them, and may want to make a linter for the gate.
   Known symbols: ``feature``, ``api-break``, ``deprecation``, ``bugfix``.
   A missing sem-ver line is equivalent to ``sem-ver: bugfix``.

8. If we found a ``deprecation`` or ``feature`` then we do a minor version
   increment.

9. I we found a ``api-break`` then we do a major version increment.

10. If the last tag has a major component of 0 then major and minor increments
    are right-shifted. That is a major increment becomes a minor increment and
    a minor increment becomes a patch level increment.

Using these rules a few examples may aid in clarity::

    # no tags, one commit, no sem-ver:
    last_tag = 0.0.0
    tag_distance = 1
    version = 0.0.1.dev1+gHASH
    Debian version = 0.0.1~dev1+gHASH
    RPM version = 0.0.0.dev1+gHASH

    # tag of 0.0.1 on a commit - tag sets version.
    last_tag = 0.0.1
    tag_distance = 0
    version = 0.0.1
    Debian version = 0.0.1
    RPM version = 0.0.1

    # tag of 0.0.1.0a4 on a commit, 5 commits since the start
    # tag sets X.Y.Z of next version, and a devN version is emitted.
    no_rc = True
    last_tag = 0.0.0
    tag_distance = 5 # distance to origin
    version = 0.0.1.dev5+gHASH
    Debian version = 0.0.1~dev5+gHASH
    RPM version = 0.0.0.dev5+gHASH

    # tag of 0.12.2, 2 commits ago with a sem-ver: deprecation line present
    # in one of them.
    # However since this is a 0.x.y version, we right shift the increment.
    last_tag = 0.12.2
    version = 0.12.3.dev2+gHASH
    Debian version = 0.12.3~dev2+gHASH
    RPM version = 0.12.2.dev2+gHASH

    # tag of 1.12.2, 2 commits ago with a sem-ver: deprecation line present
    # in one of them.
    pbr_deprecation = 1.12
    version = 1.13.0.dev2+gHASH
    Debian version = 0.13.0~dev2+gHASH
    RPM version = 0.12.9999.dev2+gHASH

Alternatives
------------

We could do nothing, but right now folk are reinventing stuff in adhoc fashions
and there is no ability to reuse their solutions in a systematic fashion.

We could put deprecated etc. markers in setup.cfg (see previous iterations of
this spec in gerrit). This was felt to be too tedious to maintain.

Impact on Existing APIs
-----------------------

No public APIs change (since pbr has approximately no public APIs at all).

New public APIs will be added that we have to support.

Security impact
---------------

None.

Performance Impact
------------------

The needed calculations are trivial, so non-trivially slower. Reading the git
history between releases is done for changelog generation already, so it will
be in cache, and pulling out lines from that is trivial.

Configuration Impact
--------------------

None.

Developer Impact
----------------

Developers can largely ignore this - it will just result in PEP-440 compatible
versions *unless* the project has chosen to start using the new features.
If a project wants to opt into the new features they can do so: export
version_info tuples in their projects, record when they make breaking changes
and have pbr enforce appropriate version changes for them. These options are
all opt-in with one exception: the change of generated numbers to be PEP-440
compatible which includes the change to issue devN for untagged versions.

Developer Workflow
^^^^^^^^^^^^^^^^^^

This forms the beginnings of a manual for using semver in PBR.

* Tagging releases: run setup.py next-version from the git commit you want to
  become the release. This outputs the next version according to semver rules.
  Make a git tag as normal using either that version, or any higher version you
  desire.

* Making API compatible bugfixes to code: Commit and push to gerrit as normal.

* Making changes that add new features: Push to gerrit as usual, but include
  ``sem-ver: feature`` in the commit.

* Making changes that deprecate things: Push to gerrit as usual, but include
  ``sem-ver: deprecation`` in the commit.

* Making changes that break compatibility - either removing deprecated code or
  removing not-yet deprecated code, or adding mandatory things users of the
  code must do that they did not have to previously: Push to gerrit as usual,
  but include ``sem-ver: api-break`` in the commit.

* Making daily/per commit builds of master for inclusion in package
  repositories: Use ``setup.py --no-rc`` to get package version numbers that
  form a consistent timeline (so alpha/beta/rc are not reflected in the
  version). The ``setup.py debian-version --no-rc`` and ``setup.py rpm-version
  --no-rc`` commands will give you appropriate version numbers for use on
  their respective platforms.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Robert Collins (lifeless)

Other contributors:
  Joshua Harlow (harlowja)
  Anyone I can rope in.

Milestones
----------

Target Milestone for completion:
  Juno-2

Work Items
----------

* Cleanup internal logic in PBR to separate out the setuptools interactions and
  the version modelling.

* Add devN-incrementing feature.

* Add history-grepping feature for incrementing major and minor versions.

* Add tagging feature.

* Add debian-version feature.

* Add rpm-version feature.

* Add version_info feature.

Incubation
==========

None

Adoption
--------

ALL OF THEM.

Library
-------

pbr

Anticipated API Stabilization
-----------------------------

None. It shall be perfect.

Documentation Impact
====================

The pbr manual (in the pbr tree) needs fleshing out to cover this behaviour.

Dependencies
============

None

References
==========

* https://etherpad.openstack.org/p/pbr-postversion-semver

* https://www.mail-archive.com/openstack-dev@lists.openstack.org/msg19450.html

* http://legacy.python.org/dev/peps/pep-0440/

.. _ENVRA: http://zenit.senecac.on.ca/wiki/index.php/ENVRA

.. _PEP-440: http://legacy.python.org/dev/peps/pep-0440/

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

