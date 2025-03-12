try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.resource import ResourceManagementClient
    from azure.mgmt.network import NetworkManagementClient
    from azure.mgmt.network.models import VirtualNetwork, Subnet, PublicIPAddress, NetworkInterface, NetworkSecurityGroup, SecurityRule
    print("All libraries are installed and working!")
except ImportError as e:
    print(f"Missing library: {e}")
    print("Please run: pip install azure-mgmt-compute azure-mgmt-resource azure-mgmt-network azure-identity")
    exit()

import subprocess

# Get subscription ID
SUBSCRIPTION_ID = subprocess.run(
    ["az", "account", "show", "--query", "id", "--output", "tsv"],
    capture_output=True, text=True
).stdout.strip()

# Configuration variables
RESOURCE_GROUP_NAME = "TomerNewResourceGroup"
LOCATION = "eastus"
VM_NAME = "Tomer-vm-name"
VNET_NAME = "TomerVNet"
SUBNET_NAME = "TomerSubnet"
NSG_NAME = "TomerNSG"
PUBLIC_IP_NAME = "TomerPublicIP"
NIC_NAME = "TomerNIC"

# Authenticate with Azure
credentials = DefaultAzureCredential()

# Create clients
resource_client = ResourceManagementClient(credentials, SUBSCRIPTION_ID)
compute_client = ComputeManagementClient(credentials, SUBSCRIPTION_ID)
network_client = NetworkManagementClient(credentials, SUBSCRIPTION_ID)

# Create resource group
resource_client.resource_groups.create_or_update(RESOURCE_GROUP_NAME, {"location": LOCATION})

# Create virtual network
vnet_params = {
    "location": LOCATION,
    "address_space": {"address_prefixes": ["10.0.0.0/16"]}
}
vnet = network_client.virtual_networks.begin_create_or_update(RESOURCE_GROUP_NAME, VNET_NAME, vnet_params).result()

# Create subnet
subnet_params = {"address_prefix": "10.0.0.0/24"}
subnet = network_client.subnets.begin_create_or_update(RESOURCE_GROUP_NAME, VNET_NAME, SUBNET_NAME, subnet_params).result()

# Create Network Security Group (NSG) with SSH rule
nsg_params = {"location": LOCATION}
nsg = network_client.network_security_groups.begin_create_or_update(RESOURCE_GROUP_NAME, NSG_NAME, nsg_params).result()

# Create security rule to allow SSH (port 22)
ssh_rule_params = {
    "protocol": "Tcp",
    "source_port_range": "*",
    "destination_port_range": "22",
    "source_address_prefix": "*",  # You can restrict this to your IP for better security
    "destination_address_prefix": "*",
    "access": "Allow",
    "priority": 100,
    "direction": "Inbound",
    "description": "Allow SSH"
}
network_client.security_rules.begin_create_or_update(
    RESOURCE_GROUP_NAME, NSG_NAME, "AllowSSH", ssh_rule_params
).result()

# Associate NSG with subnet (alternatively, you could associate with NIC)
subnet_params_with_nsg = {"address_prefix": "10.0.0.0/24", "network_security_group": {"id": nsg.id}}
subnet = network_client.subnets.begin_create_or_update(RESOURCE_GROUP_NAME, VNET_NAME, SUBNET_NAME, subnet_params_with_nsg).result()

# Create public IP
public_ip_params = {
    "location": LOCATION,
    "sku": {"name": "Standard"},
    "public_ip_allocation_method": "Static"
}
public_ip = network_client.public_ip_addresses.begin_create_or_update(RESOURCE_GROUP_NAME, PUBLIC_IP_NAME, public_ip_params).result()

# Create network interface
nic_params = {
    "location": LOCATION,
    "ip_configurations": [{
        "name": "ipconfig1",
        "subnet": {"id": subnet.id},
        "public_ip_address": {"id": public_ip.id}
    }]
}
nic = network_client.network_interfaces.begin_create_or_update(RESOURCE_GROUP_NAME, NIC_NAME, nic_params).result()

# VM configuration
from azure.mgmt.compute.models import LinuxConfiguration, SshConfiguration, SshPublicKey

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
        "linux_configuration": LinuxConfiguration(
            disable_password_authentication=True,
            ssh=SshConfiguration(
                public_keys=[
                    SshPublicKey(
                        path="/home/azureuser/.ssh/authorized_keys",
                        key_data=open("/home/tomer/.ssh/azure_key.pub", "r").read()
                    )
                ]
            )
        )
    },
    "network_profile": {
        "network_interfaces": [{"id": nic.id}]
    }
}

# Create VM
async_vm_creation = compute_client.virtual_machines.begin_create_or_update(RESOURCE_GROUP_NAME, VM_NAME, vm_parameters)
vm_result = async_vm_creation.result()

print(f"VM {vm_result.name} created successfully in {vm_result.location}")
print(f"Connect via SSH: ssh azureuser@{public_ip.public_ip_address}")