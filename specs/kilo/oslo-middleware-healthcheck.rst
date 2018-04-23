=============================
 oslo middleware healthcheck
=============================

https://blueprints.launchpad.net/oslo.middleware/+spec/oslo-middleware-healthcheck

A generic and extendabled healthcheck middleware

Problem description
===================

They are no simple and common ways to ensure that an Openstack API endpoints
can handle requests.
But a deployer that use loadbalancers want to have easy way to known if a
API endpoint can handle request or not.

For API endpoint that rely on a backend (like a database), checking that API
endpoint does not return a 50x errors on the root url of the endpoint is not
sufficient. An application like nova can return 200 on '/' even the database
is unreachable.

Proposed change
===============

The idea is to create a wsgi middleware that all openstack components can use:

.. code-block:: ini

  [filter:healthcheck]
  paste.filter_factory = oslo.middleware.healthcheck:Healthcheck
  path = /healthcheck (default)
  backends = database,disable_by_file (optional, default: empty)
  # used by the 'disable_by_file' backend
  disable_by_file_path = /var/run/nova/healthcheck_disable (optional, default: empty)

The middleware will return "200 OK" if everything is OK,
or "503 <REASON>" if not with the reason of why this API should not be used.

"backends" will the name of a stevedore extensions in the namespace "oslo.middleware.healthcheck".

oslo.middleware will also provide a base class for these extensions:

.. code-block:: python

  HealthcheckResult = namedtuple('HealthcheckResult', ['available', 'reason'], verbose=True)

  class HealthcheckBaseExtension(object):
      def __init__(self, conf):
          self.conf = conf

      @abc.abstractmethod
      def healthcheck():
          """method called by the healthcheck middleware

          return: HealthcheckResult object
          """

  class MyDBHealthcheck(HealthcheckBaseExtension):
      def healthcheck():
          ...
          return HealthcheckResult(available=False,
                                   reason="Fail to connect to the database")

And so the setup.cfg will have entry_point like that:

.. code-block:: ini

  [entry_points]
  healthcheck =
      database = oslo.db:DBHealthcheck
      disable_by_file = oslo.middleware.healthcheck:DisableByFileHealthcheck


The 'DisableByFileHealthcheck' extension will return if the 'disable_by_file_path'
file is missing:

.. code-block:: python

  return HealthcheckResult(available=False, reason="DISABLED BY FILE")

otherwise:

.. code-block:: python

  return HealthcheckResult(available=True, reason="")


Also, but not part of this blueprint, oslo.db can provide a generic
implementation for database checks.


Alternatives
------------

Some works on different project have already been proposed to do that but
never get merged:

* https://review.openstack.org/#/c/12759/
* https://review.openstack.org/#/c/120257/
* https://review.openstack.org/#/c/105311/

A deployer could prepare resources in their cloud and build a HTTP request to
query these resources to check that everything works, but this method is not
efficient, it need to prepare some resources, the HTTP request will have some
credentails that need to stored on the loadbalancer. So this method is a bit
heavy when we can just do a simple 'select now();' into a database to known if
a backend works.

Impact on Existing APIs
-----------------------

Swift already have this kind of middleware, we must ensure we keep the same
behavior:

https://github.com/openstack/swift/blob/master/swift/common/middleware/healthcheck.py

Security impact
---------------

It's recommanded to block this url or to randomize the url used for healthcheck,
because this feature it's cleary dedicated for tools used by a deployer like load balancer.

Performance Impact
------------------

None.

Configuration Impact
--------------------

The middleware will be configurable:

* path: url path of this middleware (default: /healthcheck)
* backends: list of stevedore extension to use

And the DisablebyfileHealthcheck with:

* disable_by_file_path location of the file to administratively return 503 (optional)


Developer Impact
----------------

N/A

Testing Impact
--------------

Middleware will be covered by the unittest
And also have a tempest test for each services that have integrated it.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Mehdi Abaakouk (sileht)

Other contributors:
  Julien Danjou (jdanjou)

Milestones
----------

Target Milestone for completion:

* Kilo-1

Work Items
----------

* Write the middleware
* Update applications to use it

Incubation
==========

N/A


Documentation Impact
====================

N/A

Dependencies
============

None

References
==========

None

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

