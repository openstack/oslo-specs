..
  This template should be in ReSTructured text.  For help with syntax,
  see http://sphinx-doc.org/rest.html

  To test out your formatting, build the docs using tox, or see:
  http://rst.ninjs.org

  The filename in the git repository should match the launchpad URL,
  for example a URL of
  https://blueprints.launchpad.net/oslo?searchtext=awesome-thing should be
  named awesome-thing.rst.

  Wrap text at 79 columns.

  Do not delete any of the sections in this template.  If you have
  nothing to say for a whole section, just write: None

  If you would like to provide a diagram with your spec, ascii diagrams are
  required.  http://asciiflow.com/ is a very nice tool to assist with making
  ascii diagrams.  The reason for this is that the tool used to review specs is
  based purely on plain text.  Plain text will allow review to proceed without
  having to look at additional files which can not be viewed in gerrit.  It
  will also allow inline feedback on the diagram itself.

=============================
 The title of your blueprint
=============================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/oslo?searchtext=awesome-thing

Introduction paragraph -- why are we doing anything?

Problem description
===================

A detailed description of the problem.

* For a new feature this might be use cases. Ensure you are clear about the
  actors in each use case: End User vs Deployer

* For a major reworking of something existing it would describe the
  problems in that feature that are being addressed.

Proposed change
===============

Here is where you cover the change you propose to make in detail. How do you
propose to solve this problem?

If this is one part of a larger effort make it clear where this piece ends. In
other words, what's the scope of this effort?

Include information about which oslo repository will receive the
change, including creating new repositories for libraries being
graduated and backports to the incubator if necessary. List the files
to be updated or added.

Alternatives
------------

What other ways could we do this thing? Why aren't we using those? This doesn't
have to be a full literature review, but it should demonstrate that thought has
been put into why the proposed solution is an appropriate one.

If this is a new module or library, what other similar libraries were
considered why were they rejected as unsuitable?

If this is a new feature, why does it belong in an Oslo module or
library instead of an existing third-party library?

Impact on Existing APIs
-----------------------

If the change requires modifying the API of an existing oslo module or
library, summarize those changes ("add foo argument to Blah
constructor"). Describe how the changes can be made in a
backwards-compatible way (required for libraries) or why that is not
needed (desired but not required for incubated code).

Security impact
---------------

Describe any potential security impact on the system.  Some of the items to
consider include:

* Does this change touch sensitive data such as tokens, keys, or user data?

* Does this change alter the API in a way that may impact security, such as
  a new way to access sensitive information or a new way to login?

* Does this change involve cryptography or hashing?

* Does this change require the use of sudo or any elevated privileges?

* Does this change involve using or parsing user-provided data? This could
  be directly at the API level or indirectly such as changes to a cache layer.

* Can this change enable a resource exhaustion attack, such as allowing a
  single API interaction to consume significant server resources? Some examples
  of this include launching subprocesses for each connection, or entity
  expansion attacks in XML.

For more detailed guidance, please see the OpenStack Security Guidelines as
a reference (https://wiki.openstack.org/wiki/Security/Guidelines).  These
guidelines are a work in progress and are designed to help you identify
security best practices.  For further information, feel free to reach out
to the OpenStack Security Group at openstack-security@lists.openstack.org.

Performance Impact
------------------

Describe any potential performance impact on the system, for example
how often will new code be called, and is there a major change to the calling
pattern of existing code.

Examples of things to consider here include:

* A periodic task might look like a small addition but if it calls conductor or
  another service the load is multiplied by the number of nodes in the system.

* Scheduler filters get called once per host for every instance being created,
  so any latency they introduce is linear with the size of the system.

* A small change in a utility function or a commonly used decorator can have a
  large impacts on performance.

* Calls which result in database queries (whether direct or via conductor)
  can have a profound impact on performance when called in critical sections of
  the code.

* Will the change include any locking, and if so what considerations are there
  on holding the lock?

Configuration Impact
--------------------

Does this change introduce any new configuration options? Describe the
possible valid settings.

Will the default values work well in real deployments?

Should the new options be more generic than proposed (for example a
flag that other drivers might want to implement as well)?

Why is a new configuration option needed, instead of choosing a single
behavior?

If a configuration option is being renamed, or moved into an option
group, describe those changes.

Describe plans to deprecate configuration options, including the
upgrade/migration path for anyone doing continuous deployment.

Developer Impact
----------------

Discuss things that will affect other developers working on OpenStack,
such as:

* If the blueprint proposes a change to a driver API within a library
  like oslo.messaging, discuss how other drivers would implement the
  feature.

* If the blueprint proposes modifying an existing module being used by
  one or more apps, what will need to change in those apps to
  accommodate the change here? For example, when graduating a module
  from the incubator, does the app need a new "interface module" to
  hold global values previously held in the incubated module? Have the
  semantics of the module changed enough to require significant
  modifications to the consuming applications?  API changes described
  above can be referenced here without repeating the details.

Testing Impact
--------------

Please discuss how the change will be tested. It is assumed that unit
test coverage will be added so that doesn't need to be mentioned
explicitly, but if you think unit tests are sufficient and we don't
need to add more integration tests, please explain here. If we do need
integration tests, especially if the change introduces a dependency on
a service or new library for which we might need to support multiple
versions, describe the testing strategy.

Is this untestable in gate given current limitations (specific hardware /
software configurations available)? If so, are there mitigation plans (3rd
party testing, gate enhancements, etc).

Implementation
==============

Assignee(s)
-----------

Who is leading the writing of the code? Or is this a blueprint where you're
throwing it out there to see who picks it up?

If more than one person is working on the implementation, please designate the
primary author and contact.

Primary assignee:
  <launchpad-id or None>

Other contributors:
  <launchpad-id or None>

Milestones
----------

Target Milestone for completion:

Work Items
----------

Work items or tasks -- break the feature up into the things that need to be
done to implement it. Those parts might end up being done by different people,
but we're mostly trying to understand the timeline for implementation.

For graduation blueprints, start with
https://wiki.openstack.org/wiki/Oslo/CreatingANewLibrary#Checklist and
add any additional steps necessary at the appropriate place in the
sequence. If no extra work is needed, referencing the checklist
without reproducing it is sufficient.

Incubation
==========

If this work reflects the addition of a new module through the
incubator process, we want to ensure that the full life-cycle for the
module has been thought out.

Adoption
--------

Which applications would like to share the modules? We usually prefer
at least 2 applications, but if too many applications share the
incubated version graduation becomes more difficult.

Library
-------

Which library will the new module eventually graduate into? If this is
a new library, explain why no existing library is suitable (circular
dependencies, no existing related library, etc.) and give a brief
description of the new library.

Remember to consider the dependencies of the library. Will it depend
on other oslo libraries that it does not already use? Will those
dependencies introduce a cycle?

Anticipated API Stabilization
-----------------------------

What API changes are anticipated before the code will be stable enough
to graduate? How many release cycles are needed for that API to prove
itself?

Documentation Impact
====================

What is the impact on the docs team of this change? Some changes might require
donating resources to the docs team to have the documentation updated. Don't
repeat details discussed above, but please reference them here.

Dependencies
============

- Include specific references to specs and/or blueprints in oslo, or in other
  projects, that this one either depends on or is related to.

- Does this feature require any new library dependencies or code otherwise not
  included in OpenStack? Or does it depend on a specific version of library?

References
==========

Please add any useful references here. You are not required to have any
reference. Moreover, this specification should still make sense when your
references are unavailable. Examples of what you could include are:

* Links to mailing list or IRC discussions

* Links to notes from a summit session

* Links to relevant research, if appropriate

* Related specifications as appropriate (e.g.  if it's an EC2 thing, link the
  EC2 docs)

* Anything else you feel it is worthwhile to refer to



.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

