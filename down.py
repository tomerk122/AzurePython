import subprocess
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import VirtualNetwork, Subnet, PublicIPAddress, NetworkInterface

# Check if the necessary libraries are installed
try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.resource import ResourceManagementClient
    print("All libraries are installed and working!")
except ImportError as e:
    print(f"Missing library: {e}")
    print("Please run: pip install azure-mgmt-compute azure-mgmt-resource azure-identity")

SUBSCRIPTION_ID = subprocess.run(
    ["az", "account", "show", "--query", "id", "--output", "tsv"],
    capture_output=True, text=True
).stdout.strip()
RESOURCE_GROUP_NAME = "TomerNewResourceGroup"
LOCATION = "eastus"
VM_NAME = "Tomer-vm-name"
VNET_NAME = "TomerVNet"
SUBNET_NAME = "TomerSubnet"
NSG_NAME = "TomerNSG"
PUBLIC_IP_NAME = "TomerPublicIP"
NIC_NAME = "TomerNIC"

# Initialize credentials and clients
credentials = DefaultAzureCredential()
resource_client = ResourceManagementClient(credentials, SUBSCRIPTION_ID)
compute_client = ComputeManagementClient(credentials, SUBSCRIPTION_ID)
network_client = NetworkManagementClient(credentials, SUBSCRIPTION_ID)

# Ask user if they want to delete the resource group directly
choice = input("Would you like to delete the VM fast by deleting only the resource group? (y/n): ").strip().lower()

if choice == "y":
    print("Deleting the resource group...")
    resource_client.resource_groups.begin_delete(RESOURCE_GROUP_NAME).result()
    print("Resource group deleted!")
else:
    # Deleting the VM directly without trying to update it with no NIC
    print("Deallocating the VM...")
    compute_client.virtual_machines.begin_deallocate(RESOURCE_GROUP_NAME, VM_NAME).result()
    print("VM deallocated!")

    print("Deleting the VM...")
    compute_client.virtual_machines.begin_delete(RESOURCE_GROUP_NAME, VM_NAME).result()
    print("VM deleted!")

    # Now, delete the NIC and other resources
    print("Deleting the NIC...")
    network_client.network_interfaces.begin_delete(RESOURCE_GROUP_NAME, NIC_NAME).result()
    print("NIC deleted!")

    # Deleting the public IP
    print("Deleting the public IP...")
    network_client.public_ip_addresses.begin_delete(RESOURCE_GROUP_NAME, PUBLIC_IP_NAME).result()
    print("Public IP deleted!")

    # Deleting the subnet
    print("Deleting the subnet...")
    network_client.subnets.begin_delete(RESOURCE_GROUP_NAME, VNET_NAME, SUBNET_NAME).result()
    print("Subnet deleted!")

    # Deleting the VNet
    print("Deleting the VNet...")
    network_client.virtual_networks.begin_delete(RESOURCE_GROUP_NAME, VNET_NAME).result()
    print("VNet deleted!")
