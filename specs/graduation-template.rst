..
  This template should be in ReSTructured text.  For help with syntax,
  see http://sphinx-doc.org/rest.html

  To test out your formatting, build the docs using tox, or see:
  http://rst.ninjs.org

  The filename in the git repository should match the launchpad URL,
  for example a URL of
  https://blueprints.launchpad.net/oslo/+spec/awesome-thing should be
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
 Graduating X
=============================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/oslo/+spec/graduate-example

Provide a brief description of the focus of the new library.

Library Name
============

What is the name of the new library?: 

Refer to
https://wiki.openstack.org/wiki/Oslo/CreatingANewLibrary#Choosing_a_Name
for the policies related to Oslo library names.

Contents
========

List the files to be included in the new library, using their existing
incubator names.

Early Adopters
==============

List the projects that have agreed to participate as early adopters of
the new library.

Implementation
==============

Assignee(s)
-----------

Who is handling the graduation work?

If more than one person is working on the implementation, please
designate the primary author and contact.

Primary assignee:
  <launchpad-id or None>

Other contributors:
  <launchpad-id or None>

Primary Maintainer
------------------

Each graduated library needs a primary maintainer. That may be the
same person who started the code, the person who graduated it, or it
may be someone who is taking over maintenance duties.

If more than one person *who is not already on the oslo-core team*
intends to participate as a core reviewer for the new library, list
them under "Other Contributors".

Primary Maintainer:
  <launchpad-id or None>

Other Contributors:
  <launchpad-id or None>

Security Contact
----------------

Each graduated library needs a contact for the OpenStack Vulnerability
Management team. It may be the same as the primary maintainer, an
existing Oslo team member who helps with security issues, or it may be
someone else on the development team for the new library.

Talk with the Oslo and Vulnerability management teams about who the
person is, and make sure they agree to their participation before
proceeding.

Security Contact:
  <launchpad-id or None>

Milestones
----------

Target Milestone for completion:

Work Items
----------

Start with
https://wiki.openstack.org/wiki/Oslo/CreatingANewLibrary#Checklist and
add any additional steps necessary at the appropriate place in the
sequence. If no extra work is needed, referencing the checklist
without reproducing it is sufficient.

Link to any blueprints that need to be completed in the incubator
before the library can be graduated.

Describe any organizational or API changes to the code that need to be
made after the code is moved to its new repository but before the
library can be considered ready for use. Complex changes should be
separate blueprints.

Adoption Notes
==============

In this section, provide any advice possible to make adopting the new
library easier. Will the library will behave differently than the
incubated code in some significant way? Will it need specific
integration work across all projects (e.g., creating an integration
module to hold globals)?

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

