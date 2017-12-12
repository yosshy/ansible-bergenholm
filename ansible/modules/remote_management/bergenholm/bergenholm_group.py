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
module: bergenholm_group
short_description: Manage Bergenholm Groups
extends_documentation_fragment: bergenholm
version_added: "1.0"
author: "Akira Yoshiyama <akirayoshiyama@gmail.com>"
description:
    - Manage Bergenholm groups. Groups can be created,
      updated or deleted using this module. A group will be updated
      if I(name) matches an existing group and I(state) is present.
options:
   name:
     description:
        - Group name
     required: true
   params:
     description:
        - Parameters for the group as a hash (key: value)
     type: complex
     required: false
     default: None
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
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
# Create/update a group
- bergenholm_group:
    name: centos7
    params:
      groups:
        - centos
      version: 7
    state: present

# Delete a group
- bergenholm_group:
    name: centos7
    state: absent
'''


RETURN = '''
name:
    description: Group name
    type: string
    sample: "centos7"
state:
    description: Whether the group is present
    type: string
    sample: "present"
params:
    description: Dictionary describing the group.
    returned: On success when I(state) is 'present'
    type: complex
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
            name=dict(required=True),
            params=dict(required=False, type='dict', default=None),
            state=dict(default='present',
                       choices=['absent', 'present']),
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
        name = module.params['name']
        params = module.params['params']
        state = module.params['state']
        url = module.params['url']

        # Aquire an URL for the group
        if not url.endswith('/'):
            url += '/'
        group_url = url + 'groups/' + name

        # is_present: whether the group exists now
        is_present = True
        old_params = None
        r = requests.get(group_url)
        if r.status_code == 404:
            is_present = False
        else:
            r.raise_for_status()
            old_params = r.json()
        if params is None:
            params = old_params

        if is_present:
            if state == 'absent':
                if run:
                    r = requests.delete(group_url)
                    r.raise_for_status()
                module.exit_json(changed=True, name=name, state='absent')
            else:
                if old_params != params:
                    if run:
                        r = requests.put(group_url, json=params)
                        r.raise_for_status()
                    module.exit_json(changed=True, name=name, state='present',
                                     params=params)
            module.exit_json(changed=False, name=name, state='present',
                             params=params)
        else:
            if state == 'absent':
                module.exit_json(changed=False, name=name, state='absent')
            else:
                if run:
                    r = requests.post(group_url, json=params)
                    r.raise_for_status()
                module.exit_json(changed=True, name=name, state='present',
                                 params=params)

    except Exception as e:
        #module.fail_json(msg=str(type(params)))
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
