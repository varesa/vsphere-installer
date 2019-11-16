import inquirer

from pyVim.connect import SmartConnectNoSSL, Disconnect

import getpass
import os

from get_objects import \
    get_datastores, get_networks, get_resourcepools, \
    get_folders, get_templates, recurse_name

from create_vm import create_vm


def from_env_or_print(var, prompt, secret=False):
    if var in os.environ.keys():
        if secret:
            print(prompt, '<redacted>')
        else:
            print(prompt, os.environ[var])
        return os.environ[var]
    else:
        if secret:
            return getpass.getpass(prompt)
        else:
            return input(prompt)


def main():
    vcenter = from_env_or_print('VSPHERE_ADDRESS', 'vCenter: ')
    username = from_env_or_print('VSPHERE_USERNAME', 'Username: ')
    password = from_env_or_print('VSPHERE_PASSWORD', 'Password: ', secret=True)
    print('')

    si = SmartConnectNoSSL(
        host=vcenter,
        user=username,
        pwd=password,
        port=443)

    content = si.RetrieveContent()

    templates = {}
    for template in get_templates(content):
        templates[template.summary.config.name] = template

    networks = {}
    for network in get_networks(content):
        networks[network.name] = network

    resourcepools = {}
    for pool in get_resourcepools(content):
        resourcepools[recurse_name(pool)] = pool
        
    datastores = {}
    for datastore in get_datastores(content):
        datastores[datastore.name] = datastore

    folders = {}
    for folder in get_folders(content):
        folders[recurse_name(folder)] = folder

    questions = [
        inquirer.List('template', message='Template', choices=sorted(templates.keys())),
        inquirer.List('resourcepool', message='Resource pool', choices=sorted(resourcepools.keys())),
        inquirer.List('folder', message='Folder', choices=sorted(folders.keys())),
        inquirer.List('network', message='Network', choices=sorted(networks.keys())),
        inquirer.List('datastore', message='Datastore:', choices=sorted(datastores.keys())),
        inquirer.Text('name', message='Name:'),
        inquirer.Text('ip', message='IP address:'),
        inquirer.Text('gateway', message='Gateway:'),
        inquirer.Confirm('confirm', message='Everything correct?', default=True)
    ]

    answers = inquirer.prompt(questions)

    answers['template'] = templates[answers['template']]
    answers['resourcepool'] = resourcepools[answers['resourcepool']]
    answers['folder'] = folders[answers['folder']]
    answers['network'] = networks[answers['network']]
    answers['datastore'] = datastores[answers['datastore']]

    create_vm(content, **answers)

    Disconnect(si)


if __name__ == "__main__":
    main()
