..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==============================
External Policy Decision Point
==============================

`bp external-pdp-for-keystone <https://blueprints.launchpad.net/oslo.policy/+spec/external-pdp-for-oslo-policy>`_


Keystone, together with Oslo_policy, provides a native authorization policy engine for OpenStack.
There are several defaults about the solution:

* based on a file: policy.yaml (or policy.json) owned by each OpenStack component (Nova, Glance, Neutron, ...)
* hard to understand
* not flexible to configure
* based only on one authorization (access control) model

As OpenStack may be deployed by different users with different requirements,
a generic yet flexible approach is needed through which users may define,
apply and manage their own authorization policy.
External PDP (Policy Decision Point) disables the default way and delegates authorization
to an external authorization policy engine.

Existing works [Fortress_, Moon_] show the feasibility of this approach with the Fortress and Moon
policy engines.
This specification proposes a generic hook which will re-direct authorization requests to an
external PDP instead of using the native one.
Each policy engine stores and manages related information of their policy, grants or denies requests
based on these information and their own rules.

.. _Fortress: https://review.openstack.org/#/c/237521/
.. _Moon: https://git.opnfv.org/cgit/moon/tree/keystone-moon

Problem Description
===================

Currently, if a user wants to modify the authorization policy for his/her OpenStack platform,
he/she must update the policy.yaml file for each component (Nova, Glance, Neutron, ...).

The only authorization model allowed is based on a RBAC model (Role Based Access Control) and the
operator cannot modify this model.
But in some case, he/she may want to add new information like membership and authorize actions in
his/her platform based on his membership, e.g. MLS (Multi-Level Security) is widely used for
information flow access control.

The policy modification must be done on all component with the risk of error appearing.
The policy modification is not centralized.

Proposed Change
===============

This change proposes to allow users to chose their PDP (Policy Decision Point).
User will be able to choose between:

* standard local policy.yaml file
* external Fortress policy engine platform
* external Moon policy engine platform
* ...

The switch between those PDP can be configured and done through the modification of policy.json/yaml.
For each rule, a URL need to be set.
Thus every components that use Oslo_Policy can benefit from this improvement. For example in Glance
policy.json file:

.. code-block:: json

    {
        "context_is_admin":  "role:admin",
        "default": "role:admin",
        ...
        "get_images": "http://external_pdp_server:8080/{name}s",
        ...
    }



To be able to communicate with one of those PDP, the hook is based on HTTP_Check of Oslo_Policy.
This API can be as simple as:

.. code:: javascript

    POST /authz

Where the body of POST includes:

* `target` request-related information
* `credentials` user authentication information
* `rule` this is the new data that we need to add in HTTP_Check function which identify requested operation

For example, here are some possible requests:

.. code:: javascript

    POST /authz/

The response can just be an HTTP Code return:

* 200 when the request is authorized
* 403 when the request is not authorized

Alternatives
------------

The original spec https://review.openstack.org/491565 was submitted to the keystone project. Due to
the scope responsability, a new spec (this one) is proposed here.

Through this spec/feature, we could add configuration options to oslo.policy to tell it to bypass
its default rule evaluation system and use an external PDP system.
Doing that would simplify deployer configuration, because they would only need to specify the
location of the PDP system.
It would make the library implementation more complicated, though, so we are going to use this 
simpler approach to start.

Security Impact
---------------

As it deals with authorization process, such a change can be a risk for the security.
User data is not modify because data like user ID, object ID and so on are only used in reading mode.
But if the PDP is external, data could be listen or tampered by malicious network sniffers.
Those connections must be highly secured in order to assured that the response of the request
can be truly accepted.

The only data which could be listened by malicious sniffers will be :

* the Keystone project ID
* the user ID
* the object targeted by the action
* the action of the user on the object

Tokens, keys and other sensitive data will not be exposed.
No API change is required by this change.

This change can lead to a denial of service attack. Specifically if the PDP is external.
If an attacker is able to send a lot of requests through the external interface of the PDP,
he can slow down the authorization computing in the PDP and then slow down the end user
because the end user depends on this authorization process.
To remediate this problem, the external PDP must be place in the network architecture
so that it cannot be accessed by the end user or by a malicious user.
Once OpenStack is configured to use the external PDP and the external PDP is down, no OpenStack
operations will be possible.


Notifications Impact
--------------------

**TODO**: None

Please specify any changes to notifications. Be that an extra notification,
changes to an existing notification, or removing a notification.

Other End User Impact
---------------------

The end user will not interact with this change, on the other hand,
the operator will have to configure this.
In particular, he/she must select the internal/external PDP and select some configuration items including:

* URL of the external PDP
* username to connect to the external PDP (if needed)
* password to connect to the external PDP (if needed)


Performance Impact
------------------

Because the authorization process is called every time and because this authorization process
can request an external server, it may have performance impact.
Preliminary tests show that in the Moon_ platform a authorization process can take up from 0.2 to 1 second.


Other Deployer Impact
---------------------

This change forces to update the code of Oslo_Policy which is used by a lot of OpenStack component.
But the choice must always allow the operator to use the good old internal PDP (ie the policy.yaml file).
In that case, no change will be visible for him/her.
But if a deployer wants to use this new feature, one external PDP (like the Fortress or Moon
platform) must be ready.
He/she only needs to add the URL of his/her external PDP for the corresponding rules in policy.json
files.


Developer Impact
----------------

None


Implementation
==============

Assignee(s)
-----------

Primary assignee:

* Ruan He
* Thomas Duval


Work Items
----------

1. specify the configuration options needed to use an external PDP

2. modify the Oslo_Policy code by updating the HTTP_Check class to pass rule name being evaluated

3. test the solution, we only need to use the exsting tests for HTTP_Check.


Dependencies
============

In order to make the external PDP understand POST data from the HTTP_Check function:

1. a HTTP proxy_ has been contributed to Moon for the interpretation work as a PoC

.. _proxy: https://git.opnfv.org/moon/commit/?id=eadfb789322a1a9887c8a4f23c8f125a39ebc8f4


Documentation Impact
====================

The specific configuration for external PDP must be documented.


References
==========

* OpenStack meeting on Keystone Policy: https://etherpad.openstack.org/p/keystone-policy-meeting
* Keystone policies moving into code: https://governance.openstack.org/tc/goals/queens/policy-in-code.html
* Proposed modification of Oslo_Policy for the Apache fortress solution: https://review.openstack.org/#/c/237521/
* Proposed modification of Oslo_Policy for adding information in the HTTPCheck: https://review.openstack.org/#/c/498467/
* Moon implementation of the OPNFV project: https://git.opnfv.org/cgit/moon/tree/keystone-moon

