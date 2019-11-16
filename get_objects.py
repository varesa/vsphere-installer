from pyVmomi import vim


def get_objects(content, vimtype) -> list:
    recursive = True
    container_view = content.viewManager.CreateContainerView(content.rootFolder, vimtype, recursive)
    return container_view.view


def get_networks(content):
    networks = get_objects(content, [vim.Network])
    for network in networks:
        if network.name.startswith('vm-'):
            yield network


def get_resourcepools(content):
    pools = get_objects(content, [vim.ResourcePool])
    return pools


def get_folders(content):
    folders = get_objects(content, [vim.Folder])
    for folder in folders:
        if 'VirtualMachine' in folder.childType:
            yield folder


def get_templates(content):
    vms = get_objects(content, [vim.VirtualMachine])
    for vm in vms:
        if vm.summary.config.template:
            yield vm


def get_datastores(content):
    datastores = get_objects(content, [vim.Datastore])
    return datastores


def get_vms(content):
    vms = get_objects(content, [vim.VirtualMachine])
    return vms


def recurse_name(obj):
    if isinstance(obj.parent, vim.ResourcePool) or isinstance(obj.parent, vim.Folder):
        return recurse_name(obj.parent) + '/' + obj.name
    else:
        return obj.name
