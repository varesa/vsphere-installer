
from pyVmomi import vim
import time
import json
import base64

from get_objects import get_vms, recurse_name

def clone_template(content, template, resourcepool, folder, datastore, name):
    relospec = vim.vm.RelocateSpec()
    relospec.datastore = datastore
    relospec.pool = resourcepool

    clonespec = vim.vm.CloneSpec()
    clonespec.location = relospec
    clonespec.powerOn = False

    print("Cloning template", end='', flush=True)
    task = template.Clone(folder=folder, name=name, spec=clonespec)
    time.sleep(1)
    while task.info.state == vim.TaskInfo.State.running:
        time.sleep(2)
        print('.', end='', flush=True)
    print('')

    if task.info.state != vim.TaskInfo.State.success:
        raise Exception('Clone failed')

    # Find our new VM
    for vm in get_vms(content):
        if vm.name == name and recurse_name(vm.parent) == recurse_name(folder):
            return vm
    
    assert False, "Can't find cloned VM"


def change_nic(vm, network):
    nic_change = None
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualEthernetCard):
            nic_change = vim.vm.device.VirtualDeviceSpec()
            nic_change.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            nic_change.device = device

            dvs_port_connection = vim.dvs.PortConnection()
            dvs_port_connection.portgroupKey = network.key
            dvs_port_connection.switchUuid = network.config.distributedVirtualSwitch.uuid
            nic_change.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
            nic_change.device.backing.port = dvs_port_connection

            nic_change.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            nic_change.device.connectable.startConnected = True
            nic_change.device.connectable.allowGuestControl = True
            break

    config_spec = vim.vm.ConfigSpec(deviceChange=[nic_change])
    print("Changing network", end='', flush=True)
    task = vm.ReconfigVM_Task(config_spec)
    time.sleep(1)
    while task.info.state == vim.TaskInfo.State.running:
        time.sleep(2)
        print('.', end='', flush=True)
    print('')

    if task.info.state != vim.TaskInfo.State.success:
        raise Exception('Network change failed')


def set_guestinfo(vm, ip, gateway):
    network_config = {
        "version": 1,
        "config": [{
            "type": "physical",
            "name": "ens192",
            "subnets": [{
                "type": "static",
                "address": ip,
                "gateway": gateway,
                "dns_nameservers": ["10.0.110.30", "10.0.110.90"],
                "dns_search": ["tre.esav.fi"]
            }]
        }]
    }
    network_config_base64 = base64.b64encode(json.dumps(network_config).encode()).decode()
    
    metadata = {
        "network": network_config_base64,
        "network.encoding": "base64",
        "local-hostname": vm.name,
        "instance-id": str(vm)
    }
    metadata_base64 = base64.b64encode(json.dumps(metadata).encode()).decode()
    
    userdata = """
    #cloud-config
    """
    userdata_base64 = base64.b64encode(userdata[1:].encode()).decode()

    cspec = vim.vm.ConfigSpec()
    cspec.extraConfig = [
        vim.option.OptionValue(key="guestinfo.metadata", value=metadata_base64),
        vim.option.OptionValue(key="guestinfo.metadata.encoding", value="base64"),
        vim.option.OptionValue(key="guestinfo.userdata", value=userdata_base64),
        vim.option.OptionValue(key="guestinfo.userdata.encoding", value="base64")
    ]
    vm.Reconfigure(cspec)


def configure_network(vm, network, ip, gateway):
    change_nic(vm, network)
    set_guestinfo(vm, ip, gateway)


def create_vm(content, template, resourcepool, folder, network, datastore, name, ip, gateway, confirm):
    assert confirm

    vm = clone_template(content, template, resourcepool, folder, datastore, name)
    configure_network(vm, network, ip, gateway)
