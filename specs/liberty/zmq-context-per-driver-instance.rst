=========================================================
ZeroMQ Context should be created once per driver instance
=========================================================

https://blueprints.launchpad.net/oslo.messaging/+spec/zmq-context-per-driver-instance

ZeroMQ context object has singleton nature, so producing it
more than once per driver is inefficient consuming of resources.

Now it is created per socket.

Proposed change
===============

oslo-messaging
--------------

Move creation of zmq context from ZmqSocket constructor
:meth:`ZmqSocket.__init__`

::

   # oslo_messaging/_drivers/impl_zmq.py

   class ZmqSocket(object):

      def __init__(self, addr, zmq_type, bind=True, subscribe=None):
         self.ctxt = zmq.Context(CONF.rpc_zmq_contexts)
         self.sock = self.ctxt.socket(zmq_type)


to ZmqDriver constructor :meth:`ZmqDriver.__init__`

::

   # oslo_messaging/_drivers/impl_zmq.py

   class ZmqDriver(base.BaseDriver):

       def __init__(self, conf, url, default_exchange=None,
                    allowed_remote_exmods=None):
       self.ctxt = zmq.Context(CONF.rpc_zmq_contexts)

Update :meth:`ZmqSocket.__init__` to pass zmq context as an argument

::

   # oslo_messaging/_drivers/impl_zmq.py

   class ZmqSocket(object):
      ...
      def __init__(self, zmq_ctx, addr, zmq_type, bind=True, subscribe=None):
         self.ctxt = zmq_ctx
         self.sock = self.ctxt.socket(zmq_type)


Alternatives
------------

None

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

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Oleksii Zamiatin (ozamiatin@mirantis.com)

Other contributors:
  None

Milestones
----------

next-kilo

Work Items
----------

1. Perform the code movements
2. Update all places in impl_zmq where socket used


Incubation
==========

N/A

Adoption
--------

N/A

Library
-------

oslo.messaging

Documentation Impact
====================

N/A

Dependencies
============

None

References
==========

.. note::

   Check neutron https://bugs.launchpad.net/neutron/+bug/1364814
