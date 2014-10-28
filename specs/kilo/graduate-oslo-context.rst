=========================
 Graduating oslo.context
=========================

https://blueprints.launchpad.net/oslo-incubator/+spec/graduate-oslo-context

oslo.context holds the context base class, which defines APIs used by
oslo.messaging and oslo.log.

Library Name
============

What is the name of the new library?: oslo.context

Contents
========

- openstack/common/context.py
- tests/unit/test_context.py

Early Adopters
==============

- oslo.log
- oslo.messaging

Public API
==========

::

  import oslo_context

.. The package name will depend on the outcome of our discussion about
   namespace packages.

All of the existing public functions and classes will remain public.

::

  def generate_request_id():
      "Return a unique request identifier."

  class RequestContext(object):

      """Helper class to represent useful information about a request context.

      Stores information about the security context under which the user
      accesses the system, as well as additional request information.
      """

  def get_admin_context(show_deleted=False):
      "Return a RequestContext configured as an admin user"

  def get_context_from_function_and_args(function, args, kwargs):
      """Find an arg of type RequestContext and return it.

         This is useful in a couple of decorators where we don't
         know much about the function we're wrapping.
      """

  def is_user_context(context):
      """Indicates if the request context is a normal user."""

A private registry of context objects will be kept using a
threading.local() instance and logic based on
nova.context.RequestContext. A new public API for accessing the
context will be added:

::

    def get_current():
        "Return this thread's current context"


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  doug-hellmann

Other contributors:
  None

Primary Maintainer
------------------

Primary Maintainer:
  Unknown

Other Contributors:
  None

Security Contact
----------------

Security Contact:
  doug-hellmann

Milestones
----------

Target Milestone for completion: kilo-1

Work Items
----------

- https://wiki.openstack.org/wiki/Oslo/CreatingANewLibrary#Checklist
- Add registry management logic.
- We will evolve the API for RequestContext after exporting it, based
  on needs for oslo.messaging and oslo.log. Those changes have not yet
  been worked out, and will come in another spec.

Adoption Notes
==============

Projects using oslo.context should subclass
oslo_context.RequestContext and create their own application-specific
context class.

Dependencies
============

None

References
==========

- https://etherpad.openstack.org/p/kilo-oslo-library-proposals
- https://blueprints.launchpad.net/oslo.log/+spec/remove-context-adapter
- https://blueprints.launchpad.net/oslo.log/+spec/app-agnostic-logging-parameters

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

