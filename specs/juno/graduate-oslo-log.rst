=====================
 Graduating oslo.log
=====================

https://blueprints.launchpad.net/oslo.log/+spec/graduate-oslo-log

The oslo.log library contains common code for configuring logging in
OpenStack services.

Library Name
============

oslo.log

Contents
========

* openstack/common/context.py
* openstack/common/local.py
* openstack/common/log.py
* openstack/common/fixture/logging.py
* tests/unit/test_context.py
* tests/unit/test_local.py
* tests/unit/test_log.py
* tests/unit/fixture/test_logging.py

Early Adopters
==============

No projects have stepped forward. I'll probably experiment with
ceilometer, if none of the liaisons volunteer first.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Doug Hellmann (doug-hellmann)

Other contributors:
  Chuck Short (zulcss)
  dims

Primary Maintainer
------------------

Primary Maintainer:
  Doug Hellmann (doug-hellmann)

Other Contributors:
  None

Security Contact
----------------

Security Contact:
  Doug Hellmann (doug-hellmann)


Milestones
----------

Target Milestone for completion:
  Juno-2

Work Items
----------

* https://blueprints.launchpad.net/oslo/+spec/fix-import-cycle-log-and-versionutils
* https://wiki.openstack.org/wiki/Oslo/CreatingANewLibrary#Checklist
* Organizational changes:

  * Move the option definitions into a private file.
  * Add a :func:`register_options` function to be called before
    parsing command line options and before calling :func:`setup` to
    register the command line (and other) options for logging.
  * Keep :func:`setup` in log.py, but change its API to take a config
    object as argument.
  * Move the formatter classes to separate files.
  * Move handler classes to separate files.
  * Expose :func:`set_defaults` in log.py but move it to the options
    file and change the API to take a config object as an argument.
  * Keep :func:`getLogger` in log.py
  * Move :class:`WritableLogger` to a separate public module.
  * Make the :mod:`local` module private (:mod:`_local`). We may move
    the module to another library in the future, but for now only the
    context and logging code uses it.

Adoption Notes
==============

The code changes described above should allow all apps to import with
a statement like::

   from oslo.log import log

replacing the current form::

   from foo.openstack.common import log

Dependencies
============

Prerequisites:

* https://blueprints.launchpad.net/oslo/+spec/fix-import-cycle-log-and-versionutils

Related blueprints:

* https://blueprints.launchpad.net/oslo/+spec/fix-import-cycle-log-and-versionutils
* https://blueprints.launchpad.net/oslo/+spec/app-agnostic-logging-parameters

References
==========

* Discussion from the Juno summit: https://etherpad.openstack.org/p/juno-oslo-release-plan



.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
