#!/usr/bin/python
# Copyright (c) 2017 Akira Yoshiyama <akirayoshiyama@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: bergenholm_host
short_description: Manage Bergenholm Hosts
extends_documentation_fragment: bergenholm
version_added: "1.0"
author: "Akira Yoshiyama <akirayoshiyama@gmail.com>"
description:
    - Manage Bergenholm hosts. Hosts can be created,
      updated or deleted using this module. A host will be updated
      if I(name) matches an existing host and I(state) is present.
options:
   uuid:
     description:
        - System UUID for the host
     required: true
   params:
     description:
        - Parameters for the host as a hash (key: value)
     required: false
     default: None
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent, installed, uninstalled]
     default: present
   url:
     description:
       - REST API endpoint of the bergenholm
     required: false
     default: http://localhost/api/1.0
requirements:
    - "python >= 2.6"
    - "requests"
'''

EXAMPLES = '''
# Create/update a host
- bergenholm_host:
    uuid: e9fe8fb3-c58c-43eb-a96d-88fb630d1ee7
    state: present
    params:
      groups:
        - "rhel7"
        - "centos.amd64"
      hostname: eval5
      ipaddr: "192.168.0.11"

# Delete a host
- bergenholm_host:
    uuid: e9fe8fb3-c58c-43eb-a96d-88fb630d1ee7
    state: absent

# Mark a host installed
- bergenholm_host:
    uuid: e9fe8fb3-c58c-43eb-a96d-88fb630d1ee7
    state: installed

# Unmark a host installed
- bergenholm_host:
    uuid: e9fe8fb3-c58c-43eb-a96d-88fb630d1ee7
    state: installed
'''


RETURN = '''
uuid:
    description: UUID of the host
    type: string
    sample: "f59382db809c43139982ca4189404650"
state:
    description: Whether the host is present
    type: string
    sample: "present"
params:
    description: Dictionary describing the host.
    returned: On success when I(state) is 'present'
    type: complex
installed:
    description: Whether the host is marked installed
    type: bool
    sample: true
'''

from distutils.version import StrictVersion

try:
    import requests
    HAS_REQUESTS = True
except:
    HAS_REQUESTS = False

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec = dict(
            uuid=dict(required=True),
            params=dict(required=False, type='dict', default=None),
            state=dict(default='present',
                       choices=['absent', 'present',
                                'installed', 'uninstalled']),
            url=dict(required=False, default='http://localhost/api/1.0')
        ),
        supports_check_mode=True
    )

    if not HAS_REQUESTS:
        module.fail_json(msg='requests is required for this module')

    # 'run' displays non check mode.
    run = not module.check_mode

    try:
        # Module parameters
        uuid = module.params['uuid']
        params = module.params['params']
        state = module.params['state']
        url = module.params['url']

        # Aquire an URL for the host
        if not url.endswith('/'):
            url += '/'
        host_url = url + 'hosts/' + uuid

        # Remove 'installed' from 'groups' list.
        # It should be specified as 'state=installed'.
        if params:
            params.setdefault('groups', [])
            if 'installed' in params.get('groups', []):
                params['groups'].remove('installed')

        # Check current state.
        # is_present: whether the host exists now
        # is_installed: whether the host has 'installed' group
        is_present = True
        is_installed = False
        old_params = None
        r = requests.get(host_url)
        if r.status_code == 404:
            is_present = False
        else:
            r.raise_for_status()
            old_params = r.json()
            if 'installed' in old_params.get('groups', []):
                old_params['groups'].remove('installed')
                is_installed = True
        if params is None:
            params = old_params

        if is_present:
            if state == 'absent':
                if run:
                    r = requests.delete(host_url)
                    r.raise_for_status()
                module.exit_json(changed=True, uuid=uuid, state='absent')
            elif state == 'installed':
                if old_params != params or not is_installed:
                    if run:
                        params.setdefault('groups', [])
                        params['groups'].append('installed')
                        r = requests.put(host_url, json=params)
                        r.raise_for_status()
                    module.exit_json(changed=True, uuid=uuid, state='present',
                                     installed=True, params=params)
            elif state == 'uninstalled':
                if old_params != params or is_installed:
                    if run:
                        r = requests.put(host_url, json=params)
                        r.raise_for_status()
                    module.exit_json(changed=True, uuid=uuid, state='present',
                                     installed=False, params=params)
            elif state == 'present':
                if old_params != params:
                    if is_installed:
                        params.setdefault('groups', [])
                        params['groups'].append('installed')
                    if run:
                        r = requests.put(host_url, json=params)
                        r.raise_for_status()
                    module.exit_json(changed=True, uuid=uuid, state='present',
                                     installed=is_installed, params=params)
            module.exit_json(changed=False, uuid=uuid, state='present',
                             installed=is_installed, params=params)
        else:
            if state == 'absent':
                module.exit_json(changed=False, uuid=uuid, state='absent')
            else:
                if run:
                    if state == 'installed':
                        params.setdefault('groups', [])
                        params['groups'].append('installed')
                    r = requests.post(host_url, json=params)
                    r.raise_for_status()
                module.exit_json(changed=True, uuid=uuid, state='present',
                                 installed=is_installed, params=params)

    except Exception as e:
        #module.fail_json(msg=str(type(params)))
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
