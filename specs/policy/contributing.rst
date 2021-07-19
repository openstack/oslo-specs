============================
So You Want to Contribute...
============================

For general information on contributing to OpenStack, please check out the
`contributor guide <https://docs.openstack.org/contributors/>`_ to get started.
It covers all the basics that are common to all OpenStack projects: the accounts
you need, the basics of interacting with our Gerrit review system, how we
communicate as a community, etc.

Below will cover the more project specific information you need to get started
with Oslo, which includes all of the projects listed on
`the Oslo wiki <https://wiki.openstack.org/wiki/Oslo#Libraries>`_.

Communication
~~~~~~~~~~~~~
IRC: #openstack-oslo on OFTC

Mailing list: Messages tagged with [oslo] on
`openstack-discuss <http://lists.openstack.org/cgi-bin/mailman/listinfo/openstack-discuss>`_

Meeting: Weekly. Full details on
`eavesdrop <http://eavesdrop.openstack.org/#Oslo_Team_Meeting>`_

Contacting the Core Team
~~~~~~~~~~~~~~~~~~~~~~~~
See `The Oslo Team <https://wiki.openstack.org/wiki/Oslo#The_Oslo_Team>`_ on
the wiki.

New Feature Planning
~~~~~~~~~~~~~~~~~~~~
Oslo uses a spec process for major new features. See details
`on the wiki <https://wiki.openstack.org/wiki/Oslo#Design_Proposals>`_.

Task Tracking
~~~~~~~~~~~~~
We track our tasks in Launchpad.

https://bugs.launchpad.net/oslo

Each individual library also has its own Launchpad project.

If you're looking for some smaller, easier work item to pick up and get started
on, search for the 'low-hanging-fruit' tag.

Reporting a Bug
~~~~~~~~~~~~~~~
You found an issue and want to make sure we are aware of it? You can do so on
`Launchpad <https://bugs.launchpad.net/oslo>`_.

How to contribute
~~~~~~~~~~~~~~~~~

If you would like to contribute to the development of OpenStack, you must
follow the steps in this page:

https://docs.openstack.org/infra/manual/developers.html

Once those steps have been completed, changes to OpenStack should be submitted
for review via the Gerrit tool, following the workflow documented at:

https://docs.openstack.org/infra/manual/developers.html#development-workflow

Pull requests submitted through GitHub will be ignored.

Getting Your Patch Merged
~~~~~~~~~~~~~~~~~~~~~~~~~
In general, Oslo requires 2 +2's in order to merge a patch. Under some
circumstances a single +2 may be sufficient. This is generally reserved for
repetitive patches such as trivial tox changes that have been pre-approved by
the team. Some other circumstances (such as gate blocking bugs) may call for
single approval at the discretion of the core team.

Unit tests are preferred for changes that are not already covered by existing
unit tests, and will usually help patches merge more quickly.

Project Team Lead Duties
~~~~~~~~~~~~~~~~~~~~~~~~
PTL duties are documented in the
`Oslo PTL Guide <https://specs.openstack.org/openstack/oslo-specs/specs/policy/ptl.html>`_.

All common PTL duties are enumerated in the `PTL guide
<https://docs.openstack.org/project-team-guide/ptl.html>`_.
