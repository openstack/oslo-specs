=========================
 Graduating oslo.service
=========================

https://blueprints.launchpad.net/oslo-incubator/+spec/graduate-oslo-service

The oslo.service library contains common code for running OpenStack services.

Library Name
============

oslo.service

Contents
========

* openstack/common/eventlet_backdoor.py
* tests/unit/test_eventlet_backdoor.py

* openstack/common/loopingcall.py
* tests/unit/test_loopingcall.py

* openstack/common/service.py
* tests/unit/test_service.py
* tests/unit/eventlet_service.py

* openstack/common/sslutils.py
* tests/unit/test_sslutils.py

* openstack/common/systemd.py
* tests/unit/test_systemd.py

* openstack/common/threadgroup.py
* tests/unit/test_threadgroup.py

* openstack/common/periodic_task.py
* tests/unit/test_periodic.py

Early Adopters
==============

* Ironic

Public API
==========

All of the existing public functions and classes will remain public.

New public function :func:`list_opts` that will return a list of oslo.config
options available in the library. will be added.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Sachi King (nakato)

Other contributors:
  Elena Ezhova (eezhova)

Primary Maintainer
------------------

Primary Maintainer:
  To Be Determined

Other Contributors:
  None

Security Contact
----------------

Security Contact:
  To Be Determined

Milestones
----------

Target Milestone for completion:
  liberty-1

Work Items
----------

#. https://wiki.openstack.org/wiki/Oslo/CreatingANewLibrary#Checklist

#. Move the option definitions into a private file.

#. Create a :func:`list_opts` function that will return a list of oslo.config
   options available in the library.

#. Change API of :func:`launch` in service.py to take a config object as
   an argument.

#. Change API of :func:`periodic_task` in periodic_task to take a config
   object as an argument.

#. Remove usage of global config throughout the library and update
   the existing classes/functions to register the options they use
   automatically at runtime.


Adoption Notes
==============

The code changes described above should allow all apps to import with
a statement like::

    from oslo_service import bar

replacing the current form::

    from foo.openstack.common import bar


Dependencies
============

None

References
==========

* https://etherpad.openstack.org/p/kilo-oslo-library-proposals


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
