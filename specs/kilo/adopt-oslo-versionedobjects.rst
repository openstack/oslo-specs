======================
 Adopting nova.objects
======================

https://blueprints.launchpad.net/oslo?searchtext=graduate-oslo-versionedobjects

The nova.objects package abstracts versionable internal objects for use with RPC.

Rather than moving this code into the incubator, I propose that we
move it directly to a new library. The code has been around long
enough that the API is reasonably stable.

Library Name
============

oslo.versionedobjects

Contents
========

* nova/exception.py (with cleanup to remove extraneous parts; tests not needed)
* nova/objects/__init__.py
* nova/objects/base.py
* nova/objects/fields.py
* nova/tests/unit/objects/__init__.py
* nova/tests/unit/objects/test_fields.py
* nova/tests/unit/objects/test_objects.py
* nova/tests/unit/test_utils.py (with cleanup to remove extraneous parts)
* nova/utils.py (with cleanup to remove extraneous parts)

Early Adopters
==============

These projects are already using the code:

* nova
* ironic

The divergence in Ironic is minimal and their version is generally
slightly behind nova, as new things are only copied over as needed.

Public API
==========

The public API is relatively well-defined at this point. Major elements consist of:

* base.VersionedObject - The base object to subclass for each implementation
* base.remotable - A decorator to make an object method into an RPC-able thing
* base.remotable_classmethod - A decorator to make a classmethod into an
  RPC-able thing
* base.ObjectListBase - A mix-in to gain list-of-objects functionality
* base.VersionedObjectSerializer - an oslo.messaging.NoOpSerializer that marshals
  VersionedObject objects over the wire

The following things are fairly nova-specific and should be left in the
Nova tree (for now at least):

* base.obj_make_list()
* base.serialize_args()
* base.NovaPersistentObject

Things that are public now (or, too public for a library) that should be
made private:

* base.make_class_properties()
* base.get_attrname()

Things that need some definition that are currently rather obscure and
nova-centric:

* The base.VersionedObjectMetaclass.indirection_api interface is how
  RPC-able things are remoted. Right now, this is nova's conductor
  class, but a simple base class to define the interface should be
  created for others to subclass. In nova, we set this rather forcibly,
  but in this library, we should provide methods to set/clear the indirection
  service.

Finally, there is one detail of the implementation that deserves some thought
before we codify it in a library. Right now, the simple act of subclassing
NovaObject will register the implementation in the registry, via the metaclass.
This is convenient because the author doesn't have to do anything in order to
use their implementation immediately. However, it may be a little "too magic"
or "too automatic". If you want to subclass NovaObject but not register it,
there is currently no way to do that. We could have an unregister function,
but then it's impossible to avoid the small window of being registered. The
unit tests currently have some weirdness because of this, for their test
objects.

The alternate proposal for registration would be a simple class decorator
that you apply to objects that you wish to be registered.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Dan Smith

Other contributors:
  Doug Hellmann

Primary Maintainer
------------------

Primary Maintainer:
  Dan Smith

Other Contributors:
  Chris Behrens

Security Contact
----------------

Security Contact:
  Dan Smith

Milestones
----------

Target Milestone for completion: kilo-2

Work Items
----------

* Create Initial Repository
* Update MAINTAINERS in incubator with status and name
* Remove Oslo logging calls in incubator
* Run graduate.sh
* Fix the output of graduate.sh
* Use cookiecutter template to make a new project
* Sync tools from nova
* Remove novaisms
* Finish moving should-be-private things to private names
* Make changes to the registry according to review
* Finish documenting any public interfaces lacking proper docs
* Publish git repo
* Oslo team review new repository
* openstack-infra/project-config - gerrit/projects.yaml
* openstack-infra/project-config - gerrit/acls/openstack/project-name.config
* openstack-infra/project-config - jenkins/jobs/projects.yaml
* openstack-infra/project-config - zuul/layout.yaml
* openstack-infra/project-config - gerritbot/channels.yaml
* Update Gerrit Groups and ACLs
* openstack-infra/devstack-gate - devstack-vm-gate-wrap.sh
* openstack/requirements projects.txt
* openstack/governance reference/programs.yaml
* Update list of libraries on Oslo wiki page
* Create Launchpad project
* Create Launchpad bug tracker
* Create Launchpad blueprint tracker
* Change owner of Launchpad project
* Make the library do something
* Give openstackci Owner permissions on PyPI
* Tag a release
* Remove graduated code from oslo-incubator
* Update oslo-incubator/update.py to not rewrite references to the library
* openstack/requirements - global-requirements.txt
* Document Migration Process
* openstack-dev/devstack - lib/oslo
* openstack-dev/devstack - stackrc
* Update project list on docs.openstack.org

Adoption Notes
==============

Adoption will include synchronization with changes that may be going into Nova
at the same time until the point at which nova can move to using the oslo
library.

Dependencies
============

None.

References
==========

* Earlier patch to incubator to import this code: https://review.openstack.org/#/c/60376/


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
