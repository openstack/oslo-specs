#!/bin/bash

# Depends on refactored graduation scripts found
# in https://review.openstack.org/#/c/151027/

set -ex

(cd nova && git checkout master && git pull)
new_repo=oslo.versionedobjects-$(date +%Y-%m-%d-%H%M)
git clone nova $new_repo
cd $new_repo

tooldir=~/repos/openstack/oslo-incubator/tools

FILES="
    nova/exception.py
    nova/objects/__init__.py
    nova/objects/base.py
    nova/objects/fields.py
    nova/test.py
    nova/tests/fixtures.py
    nova/tests/unit/objects/__init__.py
    nova/tests/unit/objects/test_fields.py
    nova/tests/unit/objects/test_objects.py
    nova/tests/unit/test_utils.py
    nova/safe_utils.py
    nova/utils.py
"

$tooldir/filter_git_history.sh $FILES

git mv nova oslo_versionedobjects
git mv oslo_versionedobjects/objects/* oslo_versionedobjects/
rmdir oslo_versionedobjects/objects
git mv oslo_versionedobjects/tests/unit/objects/* oslo_versionedobjects/tests/
rmdir oslo_versionedobjects/tests/unit/objects
git mv oslo_versionedobjects/tests/unit/test_utils.py oslo_versionedobjects/tests/
rmdir oslo_versionedobjects/tests/unit

$tooldir/apply_cookiecutter.sh versionedobjects

cat - >requirements.txt <<EOF
six>=1.7.0
Babel>=1.3
netaddr>=0.7.12
oslo.concurrency>=1.4.1         # Apache-2.0
oslo.context>=0.1.0                     # Apache-2.0
oslo.messaging>=1.4.0,!=1.5.0
oslo.serialization>=1.2.0               # Apache-2.0
oslo.utils>=1.2.0                       # Apache-2.0
iso8601>=0.1.9
EOF

cat - >test-requirements.txt <<EOF
hacking>=0.5.6,<0.8
oslotest>=1.2.0  # Apache-2.0
mock>=1.0
testtools>=0.9.36,!=1.2.0
# These are needed for docs generation
oslosphinx>=2.2.0  # Apache-2.0
sphinx>=1.1.2,!=1.2.0,!=1.3b1,<1.3
EOF

echo
echo "Output in $(pwd)"

exit $?


# oslo-incubator modules:
# versionutils
