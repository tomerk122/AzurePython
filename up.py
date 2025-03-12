
try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.resource import ResourceManagementClient
    print("All libraries are installed and working!")
except ImportError as e:
    print(f"Missing library: {e}")
    print("Please run: pip install azure-mgmt-compute azure-mgmt-resource azure-identity")
    
from azure.identity import DefaultAzureCredential # for authentication
from azure.mgmt.compute import ComputeManagementClient # for creating VM
from azure.mgmt.resource import ResourceManagementClient # for creating resource group
from azure.mgmt.network import NetworkManagementClient # for creating network resources
from azure.mgmt.network.models import VirtualNetwork, Subnet, PublicIPAddress, NetworkInterface # for creating network resources


import subprocess

SUBSCRIPTION_ID = subprocess.run(
    ["az", "account", "show", "--query", "id", "--output", "tsv"],
    capture_output=True, text=True
).stdout.strip()

RESOURCE_GROUP_NAME = "TomerNewResourceGroup"
LOCATION = "eastus"
VM_NAME = "Tomer-vm-name"
VNET_NAME = "TomerVNet"
SUBNET_NAME = "TomerSubnet"
NSG_NAME = "TomerNSG" # for network security group and it used to allow or deny inbound or outbound traffic
PUBLIC_IP_NAME = "TomerPublicIP"
NIC_NAME = "TomerNIC" # for network interface card and it used to connect the VM to the network


credentials = DefaultAzureCredential() # the default credential will be used to authenticate the client
# and it is based on the environment variables, managed identity, or shared token cache

# create clients for the resource group, compute, and network
resource_client = ResourceManagementClient(credentials, SUBSCRIPTION_ID)
compute_client = ComputeManagementClient(credentials, SUBSCRIPTION_ID)
network_client = NetworkManagementClient(credentials, SUBSCRIPTION_ID)


resource_client.resource_groups.create_or_update(RESOURCE_GROUP_NAME, {"location": LOCATION})

# create a virtual network
vnet_params = {
    "location": LOCATION,
    "address_space": {"address_prefixes": ["10.0.0.0/16"]},
}
network_client.virtual_networks.begin_create_or_update(RESOURCE_GROUP_NAME, VNET_NAME, vnet_params).result() # the result is used to wait for the completion of the
# long-running operation and to return the result of the operation

subnet_params = {"address_prefix": "10.0.0.0/24"}
subnet = network_client.subnets.begin_create_or_update(RESOURCE_GROUP_NAME, VNET_NAME, SUBNET_NAME, subnet_params).result()
# create a public IP address
public_ip_params = {"location": LOCATION, "sku": {"name": "Standard"}, "public_ip_allocation_method": "Static"}
public_ip = network_client.public_ip_addresses.begin_create_or_update(RESOURCE_GROUP_NAME, PUBLIC_IP_NAME, public_ip_params).result()

# create a network interface
nic_params = {
    "location": LOCATION,
    "ip_configurations": [{
        "name": "ipconfig1",
        "subnet": {"id": subnet.id},
        "public_ip_address": {"id": public_ip.id}
    }]
}
nic = network_client.network_interfaces.begin_create_or_update(RESOURCE_GROUP_NAME, NIC_NAME, nic_params).result()


vm_parameters = {
    "location": LOCATION,
    "hardware_profile": {"vm_size": "Standard_DS1_v2"},
    "storage_profile": {
        "image_reference": {
            "publisher": "Canonical",
            "offer": "UbuntuServer",
            "sku": "18.04-LTS",
            "version": "latest"
        }
    },
    "os_profile": {
        "computer_name": VM_NAME,
        "admin_username": "azureuser",
      "admin_password": "Secure@123"

    },
    "network_profile": {
        "network_interfaces": [{"id": nic.id}]
    }
}


async_vm_creation = compute_client.virtual_machines.begin_create_or_update(RESOURCE_GROUP_NAME, VM_NAME, vm_parameters)
vm_result = async_vm_creation.result()

print(f"VM {vm_result.name} created successfully in {vm_result.location}")