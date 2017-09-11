============================================
Provide a set of examples for oslo libraries
============================================

https://blueprints.launchpad.net/oslo.messaging/+spec/oslo-examples

For each oslo library provide a set of examples to illustrate
a use case of a specific library API.


Problem description
===================

For now we have no any example (except tests) of how to use each
oslo library. Functional tests are close to be, but they are
more abstract and serve to check the functionality, not to illustrate
the way how it can be used in the application.

It is desirable to have some expressive examples which could serve
as documentation for the code.


Proposed change
===============

In each oslo library repository create an examples folder, where put
some examples for the library API.

It is preferrable that example be like a mini application, and built
in terms of some application domain, not as "ClientA calls ServerB with
request1".

We can implement a set of examples for oslo.messaging in the same manner as
in taskflow:

https://github.com/openstack/taskflow/tree/master/taskflow/examples
The examples all get tested during unit test runs to ensure they work as expected.

They are also should be part of the documentation, and be built as docs.
There will be a separate file in the docs folder that includes the code
in the examples folder.

https://raw.githubusercontent.com/openstack/taskflow/master/doc/source/examples.rst

An example may look like the following:

.. code-block:: python

   bobMessenger = messenger.Client(cfg, 'Bob')
   aliceMessenger = messenger.Client(cfg, 'Alice')

   server = messenger.Server(cfg)

   server.run()
   bobMessenger.run()
   aliceMessenger.run()

   time.sleep(2) # wait for all participants discover each other

   assertEqual(server.clientsList,
                bobMessenger.clientsList,
                aliceMessenger.clientsList)

   bobMessenger.sendMessage('Alice', 'Hi, there!')

   assertEqual(bobMessenger.history['Alice'],
                aliceMessenger.history['Bob'])


Or for the request-reply pattern:

.. code-block:: python

    fibServer = fibonacci.Server(cfg)
    fibClient = fibonacci.Client(cfg)

    fibServer.run()

    value = fibClient.getFibonacci(20)
    assertEqual(value, 6765)


Alternatives
------------

Functional tests built on top of some real-world application which uses
oslo libraries for its implementation. A kind of indirect testing
which may show the way how the library could be improved or optimised.
Such testing also serves as an example of usage, because we test the application
which uses the library and therefore demonstrates how to use the API.

https://blueprints.launchpad.net/oslo.messaging/+spec/oslo-functional-testing-apps

Impact on Existing APIs
-----------------------

None

Security impact
---------------

None

Performance Impact
------------------

None

Configuration Impact
--------------------

None

Developer Impact
----------------

Any future changes to oslo.* API should be reflected in the examples.


Testing Impact
--------------

All examples should run with unit tests.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  ozamiatin@mirantis.com

Other contributors:
  dmakogon@mirantis.com

Milestones
----------

Target Milestone for completion:
* liberty-3


Work Items
----------

* Develop examples for each oslo library

taskflow - got as a pattern

We are going to start with oslo.messaging and oslo.concurrency
and move on to the other libraries when the work is done.


Incubation
==========

N/A


Documentation Impact
====================

Example apps should be published in the documentation.

See how it is done in taskflow:

https://raw.githubusercontent.com/openstack/taskflow/master/doc/source/examples.rst

This gets converted into:

http://docs.openstack.org/developer/taskflow/examples.html


Dependencies
============

oslo.*

References
==========

None
