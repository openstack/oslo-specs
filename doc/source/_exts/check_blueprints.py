# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""Ensure that the name of the spec file matches the name of a blueprint.
"""

import os

import requests
from launchpadlib.launchpad import Launchpad


class BlueprintChecker(object):

    def __init__(self, app):
        self.app = app
        cachedir = os.path.expanduser('~/.launchpadlib')
        self.lp = Launchpad.login_anonymously('check-spec-filename',
                                              'production',
                                              cachedir)
        # Use the launchpad API to figure out which projects we need
        # to check instead of hard-coding a list.
        self.oslo = self.lp.project_groups['oslo']
        self.projects = self.oslo.projects
        self.project_names = [p.name for p in self.projects]
        self._good_bps = set()
        self._prefix = None

    @property
    def desired_prefix(self):
        """We only care about blueprints in the current release, if the option
        is set.

        """
        if self._prefix is None:
            release = self.app.config.check_blueprints_release
            if release:
                self._prefix = 'specs/%s/' % release
            else:
                self._prefix = 'specs/'
        return self._prefix

    def doctree_resolved(self, app, doctree, docname):
        """Hook registered as event handler."""
        if not docname.startswith(self.desired_prefix):
            return
        bp_name = docname.split('/')[-1]
        if bp_name == 'index':
            return
        self.check(bp_name)

    BP_URL_TEMPLATE = 'https://api.launchpad.net/devel/%s/+spec/%s'

    def blueprint_exists(self, project_name, bp_name):
        # We can't use the getSpecification() API because we're logged
        # in anonymously, so we have to build the URL to the
        # blueprint's API endpoint ourselves and then poke it to see
        # if it exists.
        url = self.BP_URL_TEMPLATE % (project_name, bp_name)
        response = requests.get(url)
        return response.status_code == 200

    def check(self, bp_name):
        """Given one blueprint name, check to see if it is valid."""
        if bp_name in self._good_bps:
            return True
        self.app.info('')  # emit newline
        for project_name in self.project_names:
            self.app.info('Checking for %s in %s' % (bp_name, project_name))
            if self.blueprint_exists(project_name, bp_name):
                self.app.info('Found %s in %s' % (bp_name, project_name))
                self._good_bps.add(bp_name)
                break
        else:
            self.app.warn(
                'Could not find a blueprint called %r in the oslo project group'
                % bp_name,
                location=(bp_name, 0),
            )
            raise ValueError('Document %s does not match any blueprint name'
                             % bp_name)


def setup(app):
    app.info('Initializing %s' % __name__)
    checker = BlueprintChecker(app)
    app.connect('doctree-resolved', checker.doctree_resolved)
    app.add_config_value('check_blueprints_release', '', 'env')
