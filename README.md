# Arista CVaaS SDK

This Python SDK facilitates interaction with Arista's Cloud Vision as a Service (CVaaS), aiding in the management, monitoring, and automation of network services within the Arista ecosystem. The SDK is encapsulated as a class, providing a structured and object-oriented approach. This SDK was developed to be utilized within a Jupyter Notebook environment.

## Getting Started

### Requirements

- **Python Version:** 3.10.8 (packaged by conda-forge)
- **Dependencies:** None

### Installation

Clone the repository to your local machine.

```bash
git clone https://github.com/rohscx/arista-cvaas-sdk.git
```

## Configuration

Place the SDK in a suitable directory and update your system path. For example, in a Jupyter Notebook, you might use:

```python
import sys
sys.path.insert(1, '/home/jovyan/SciPy/utils/arista-cvaas-sdk/')
```

## Usage

### Within a Jupyter Notebook

```python
from arista_cvaas_sdk import AristaCVAAS, DependencyTracker
import pprint as pp
import json

# Configuration:
token = input(prompt="API Key:")
host_url = input(prompt="API URL:")

sdk = AristaCVAAS(host_url, token)
```

### Outside a Jupyter Notebook

Clone the repository and navigate to the repository folder. Then, run your script file from the command line or an IDE of your choice.

```bash
cd arista-cvaas-sdk
```

Create a Python script (e.g., `main.py`) and include the following code:

```python
from arista_cvaas_sdk import AristaCVAAS, DependencyTracker
import pprint as pp
import json

# Configuration:
token = "your_api_key_here"
host_url = "your_api_url_here"

sdk = AristaCVAAS(host_url, token)

# Further code to interact with CVaaS using the sdk object
```

Run your script from the command line:

```bash
python main.py
```

## Examples

For example purposes, refer to the `examples` directory in this repository, or review the methods available in the `arista_cvaas_sdk.py` file

### GET A LIST OF ALL CVASS CONFIGLETS


```python
[x[0] for x in sdk.get_configlet_names_ids()]
```




    ['dc_WESTMINSTER_snmp_conf',
     'dc_snmp_conf',
     'device_devdeirt99_hostname_conf',
     'device_devdeirt99_interfaces_conf',
     'device_devdeirt99_routing_conf',
     'device_devdeirt99_vlan_conf',
     'device_devfrirt98_hostname_conf',
     'device_devfrirt98_interfaces_conf',
     'device_devfrirt98_routing_conf',
     'global_aaa_conf',
     'global_acl_conf',
     'global_cvaas_conf',
     'global_dns_conf',
     'global_lldp_conf',
     'global_logging_conf',
     'global_login_banner_conf',
     'global_snmp_conf',
     'global_spanning-tree_conf',
     'global_time_conf',
     'override_device_build_conf',
     'site_123_main_snmp_conf',
     'site_snmp_conf']



### GET A TUPLE OF DEVICE NAMES AND THEIR DEVICE ID


```python
sdk.get_configlet_names_ids("device")
```




    [('device_devdeirt99_hostname_conf',
      'configlet_fe862bbf-3e79-4d32-acdf-096a2c8669a7'),
     ('device_devdeirt99_interfaces_conf',
      'configlet_9c2e5833-06b7-49b8-b68b-0117cbfface7'),
     ('device_devdeirt99_routing_conf',
      'configlet_831f7d91-da66-4472-a556-70f15c6ad905'),
     ('device_devdeirt99_vlan_conf',
      'configlet_c4986a98-e117-4939-8d3e-23a7dcf33716'),
     ('device_devfrirt98_hostname_conf',
      'configlet_4d39d2ac-b19c-43f0-a015-5071f96ba373'),
     ('device_devfrirt98_interfaces_conf',
      'configlet_faf5b7ee-2e79-450f-b327-046404238bdf'),
     ('device_devfrirt98_routing_conf',
      'configlet_5025646b-9847-4469-8ca0-52410f92b4f3'),
     ('override_device_build_conf',
      'configlet_110a294a-a7c5-402a-87d5-84c287e57e8f')]



### GET THE CONTAINERS A CONFIGLET IS ASSIGNED TO


```python
sdk.get_configlet_applied_containers(["global_aaa_conf"])
```




    [{'total': 1,
      'data': [{'containerName': 'WESTMINSTER',
        'appliedBy': 'joe',
        'appliedDate': 1695338987520,
        'hostName': None,
        'ipAddress': None,
        'totalDevicesCount': 1}],
      'configletName': 'global_aaa_conf'}]



### GET THE DEVICES A CONFIGLETS IS ASSIGNED TO


```python
sdk.get_configlet_applied_devices(["device_devfrirt98_hostname_conf"])
```




    [{'total': 1,
      'data': [{'containerName': 'WESTMINSTER',
        'appliedBy': 'joe',
        'appliedDate': 1695907952674,
        'hostName': 'devfrIrt98.corpo.net',
        'ipAddress': '192.168.1.32',
        'totalDevicesCount': 0}],
      'configletName': 'device_devfrirt98_hostname_conf'}]



### GET CVASS DEVICE INVENTORY FOR ALL DEVICES


```python
sdk.get_inventory_devices()
```




    [{'modelName': 'CCS-720DT-48S-2',
      'internalVersion': '4.30.3M',
      'systemMacAddress': 'ba:dd:ea:db:ee:f0',
      'bootupTimestamp': 0,
      'version': '4.30.3M',
      'architecture': '',
      'internalBuild': '',
      'hardwareRevision': '',
      'domainName': 'corpo.net',
      'hostname': 'devfrIrt98',
      'fqdn': 'devfrIrt98.corpo.net',
      'serialNumber': 'ZTW6041P1A9',
      'deviceType': 'eos',
      'danzEnabled': False,
      'mlagEnabled': False,
      'streamingStatus': 'active',
      'parentContainerKey': 'container_b7732c25-19cf-413e-9f7d-d61f6e5134e5',
      'status': 'Registered',
      'complianceCode': '0000',
      'complianceIndication': '',
      'ztpMode': False,
      'unAuthorized': False,
      'ipAddress': '192.168.1.32'}]



### GET CVASS DEVICE INVENTORY FOR A SINGLE DEVICE ADDRESS OR MULTIPLE DEVICES


```python
sdk.get_inventory_devices(system_mac_addresses = ["c4:ca:2b:bc:44:3d"])
```

### GET USER INFORMATION, INCLUDING ONLINE STATUS


```python
# Any[Default], Online, Offline
sdk.get_users_and_groups(filter_status='Online')
```

### GET AN INVENTORY OFF ALL CONTAINERS


```python
# Any[Default], Online, Offline
sdk.get_inventory_containers()
```




    [{'Key': 'root',
      'Name': 'Tenant',
      'CreatedBy': 'cvp system',
      'CreatedOn': 1692114661341,
      'Mode': 'expand'},
     {'Key': 'undefined_container',
      'Name': 'Undefined',
      'CreatedBy': 'cvp system',
      'CreatedOn': 1692114661584,
      'Mode': 'expand'},
     {'Key': 'container_0483fbdd-1e34-4626-9fc9-07803d1651f8',
      'Name': 'deeper',
      'CreatedBy': 'joe',
      'CreatedOn': 1696212041809,
      'Mode': 'expand'},
     {'Key': 'container_0865637c-38e4-422b-92cf-acea6e488556',
      'Name': 'rightman',
      'CreatedBy': 'rick_hunter_service_account',
      'CreatedOn': 1696211841172,
      'Mode': 'expand'},
     {'Key': 'container_2a2ac4f4-ba4d-42f8-88b7-468db3abee76',
      'Name': 'SITE',
      'CreatedBy': 'joe',
      'CreatedOn': 1695917288214,
      'Mode': 'expand'},
     {'Key': 'container_f88f36cc-70d9-41d0-86eb-33b6c8704c73',
      'Name': 'aaaadfasd',
      'CreatedBy': 'joe',
      'CreatedOn': 1696212040576,
      'Mode': 'expand'},
     {'Key': 'container_fafa4f9a-c7f1-44e8-b0f9-ac65c3cdc539',
      'Name': 'deep',
      'CreatedBy': 'joe',
      'CreatedOn': 1696212041161,
      'Mode': 'expand'},
     {'Key': 'container_467797aa-b4d8-40aa-8029-53b38f7074f1',
      'Name': 'rightman2',
      'CreatedBy': 'rick_hunter_service_account',
      'CreatedOn': 1696211928731,
      'Mode': 'expand'},
     {'Key': 'container_5e45091a-6425-42b0-a889-4d6b6d025643',
      'Name': 'WEST-WESTMINSTER',
      'CreatedBy': 'joe',
      'CreatedOn': 1695107496066,
      'Mode': 'expand'},
     {'Key': 'container_a896016f-d133-4171-8fec-8d9a207c6049',
      'Name': '123123',
      'CreatedBy': 'joe',
      'CreatedOn': 1696182039845,
      'Mode': 'expand'},
     {'Key': 'container_b7732c25-19cf-413e-9f7d-d61f6e5134e5',
      'Name': 'WESTMINSTER',
      'CreatedBy': 'joe',
      'CreatedOn': 1695917494586,
      'Mode': 'expand'},
     {'Key': 'container_eac2545e-ec49-4a83-819a-6366211bc7b6',
      'Name': 'yap',
      'CreatedBy': 'joe',
      'CreatedOn': 1696181563951,
      'Mode': 'expand'}]



### GET A DEVICES COMPLETE CONFIG GIVEN A ITS SYSTEM MAC ADDRESS 


```python
pp.pprint(sdk.get_inventory_device_config("ba:dd:ea:db:ee:f0"))
```

    {'deviceConfigTimeStamp': '2023-09-28T17:30:41.472621691Z',
     'output': '! Command: show running-config\n'
               '! device: devfrIrt98 (CCS-720DT-48S-2, EOS-4.30.3M)\n'
               '!\n'
               '! boot system flash:/EOS-4.30.3M.swi\n'
               '!\n'
               'no aaa root\n'
               ...}
 


### GET A LIST OF ALL CVAAS ROLES


```python
pp.pprint(sdk.get_roles())
```

    {'roles': [{'createdBy': 'cvp system',
                'createdOn': 1699994450504,
                'description': '',
                'key': 'cloud-deploy',
                'moduleList': [{'mode': 'rw', 'name': 'task'},
                               {'mode': 'rw', 'name': 'networkProvisioning'},
                               {'mode': 'rw', 'name': 'inventory'},
                               ...]
                
                'moduleListSize': 10,
                'name': 'cloud-deploy'},
               {'createdBy': 'cvp system',
                'createdOn': 1612334436633,
                'description': '',
                'key': 'network-admin',
                'moduleList': [{'mode': 'rw', 'name': 'eventConfiguration'},
                               {'mode': 'rw', 'name': 'workspaceSubmit'},
                               {'mode': 'rw', 'name': 'ipam'},
                                ...],
                'moduleListSize': 65,
                'name': 'network-admin'},
               {'createdBy': 'cvp system',
                'createdOn': 1698524443596,
                'description': '',
                'key': 'network-operator',
                'moduleList': [{'mode': 'r', 'name': 'events'},
                               {'mode': 'r', 'name': 'aaa'},
                               {'mode': 'r', 'name': 'licensing'},
                                ...],
                'moduleListSize': 61,
                'name': 'network-operator'},
               {'createdBy': 'cvp system',
                'createdOn': 1692134452546,
                'description': '',
                'key': 'no-access',
                'moduleList': [],
                'moduleListSize': 0,
                'name': 'no-access'}],
     'total': 4,
     'users': {'cloud-deploy': 0,
               'network-admin': 5,
               'network-operator': 1,
               'no-access': 0}}


### GET A LIST OF ALL CVASS USERS AND GROUPS


```python
pp.pprint(sdk.get_users_and_groups())
```

    {'roles': {'admin': ['network-admin'],
               'arista-support': ['network-operator'],
               'emma_frost': ['network-admin'],
               'joe_rogan': ['network-admin'],
               'jack_black': ['network-admin'],
               'james_brown': ['network-admin']},
     'total': 6,
     'users': [{'addedByUser': 'cvp system',
                'contactNumber': '',
                'currentStatus': 'Online',
                ...}]}


### CREATE A COPY OF A MULTIPLE CONFIGLETS USING MY STANDARD NAMING CONVENTION
#### CONFIGLET-TYPE_NAME_FUNCTION_conf
#### REPLACES THE CONFIGLET NAME WITH THE SPECIFIED NAME


```python
# Usage:

# Copy multiple configlets with specified new names
# pp.pprint(sdk.copy_configlet([x[0] for x in configlet_names_ids], repace_name([x[0] for x in configlet_names_ids],"devdeirt99")))
```

    [{'data': {'config': 'hostname devdeIrt99',
               'containerCount': 0,
               'dateTimeInLongFormat': 1697346108758,
               'editable': True,
               'isAutoBuilder': '',
               'isDefault': 'no',
               'isDraft': False,
               'key': 'configlet_4efc2d7a-a207-401f-b201-a26dd429d96a',
               'name': 'devdeirt99_devdeirt99_hostname_conf',
               'netElementCount': 0,
               'note': '',
               'reconciled': False,
               'sslConfig': False,
               'type': 'Static',
               'typeStudioConfiglet': False,
               'user': 'rick_hunter_service_account',
               'visible': True}},
     {'data': {'config': '! PHYSICAL INTERFACE CONFIGURATION\n'
                         'interface Loopback0\n'
                         ...,
               'containerCount': 0,
               'dateTimeInLongFormat': 16867320110063,
               'editable': True,
               'isAutoBuilder': '',
               'isDefault': 'no',
               'isDraft': False,
               'key': 'configlet_46378233-9d94-4b49-b225-90f2e45db243',
               'name': 'devdeirt99_devdeirt99_interfaces_conf',
               'netElementCount': 0,
               'note': '',
               'reconciled': False,
               'sslConfig': False,
               'type': 'Static',
               'typeStudioConfiglet': False,
               'user': 'rick_hunter_service_account',
               'visible': True}},
     {'data': {'config': 'ip route 0.0.0.0/0 192.168.1.1',
               'containerCount': 0,
               'dateTimeInLongFormat': 16934568111302,
               'editable': True,
               'isAutoBuilder': '',
               'isDefault': 'no',
               'isDraft': False,
               'key': 'configlet_5362159b-4e74-47f4-a96f-ba4b43c1e0ab',
               'name': 'devdeirt99_devdeirt99_routing_conf',
               'netElementCount': 0,
               'note': '',
               'reconciled': False,
               'sslConfig': False,
               'type': 'Static',
               'typeStudioConfiglet': False,
               'user': 'rick_hunter_service_account',
               'visible': True}},
     {'data': {'config': '! VLAN Configuration\n'
                         ...,
               'containerCount': 0,
               'dateTimeInLongFormat': 1695983572433,
               'editable': True,
               'isAutoBuilder': '',
               'isDefault': 'no',
               'isDraft': False,
               'key': 'configlet_8111c8b5-b2c2-4272-a73f-897ae62e9ff2',
               'name': 'devdeirt99_devdeirt99_vlan_conf',
               'netElementCount': 0,
               'note': '',
               'reconciled': False,
               'sslConfig': False,
               'type': 'Static',
               'typeStudioConfiglet': False,
               'user': 'rick_hunter_service_account',
               'visible': True}},
     {'data': {'config': 'hostname devfrIrt98',
               'containerCount': 0,
               'dateTimeInLongFormat': 1695238733623,
               'editable': True,
               'isAutoBuilder': '',
               'isDefault': 'no',
               'isDraft': False,
               'key': 'configlet_defae14d-584f-43da-b014-18ca11821999',
               'name': 'devdeirt99_devfrirt98_hostname_conf',
               'netElementCount': 0,
               'note': '',
               'reconciled': False,
               'sslConfig': False,
               'type': 'Static',
               'typeStudioConfiglet': False,
               'user': 'rick_hunter_service_account',
               'visible': True}},
     {'data': {'config': 'interface Loopback0\n'
                         ' ip address 10.248.1.12 255.255.255.255\n'
                         'interface Ethernet1\n'
                         ...,
               'containerCount': 0,
               'dateTimeInLongFormat': 1695650114821,
               'editable': True,
               'isAutoBuilder': '',
               'isDefault': 'no',
               'isDraft': False,
               'key': 'configlet_988616a3-6d17-425a-9c72-85832d9be7c9',
               'name': 'devdeirt99_devfrirt98_interfaces_conf',
               'netElementCount': 0,
               'note': '',
               'reconciled': False,
               'sslConfig': False,
               'type': 'Static',
               'typeStudioConfiglet': False,
               'user': 'rick_hunter_service_account',
               'visible': True}},
     {'data': {'config': 'ip route 0.0.0.0/0 192.168.1.1',
               'containerCount': 0,
               'dateTimeInLongFormat': 1695650116305,
               'editable': True,
               'isAutoBuilder': '',
               'isDefault': 'no',
               'isDraft': False,
               'key': 'configlet_4425690c-5913-457e-88f7-44019804712b',
               'name': 'devdeirt99_devfrirt98_routing_conf',
               'netElementCount': 0,
               'note': '',
               'reconciled': False,
               'sslConfig': False,
               'type': 'Static',
               'typeStudioConfiglet': False,
               'user': 'rick_hunter_service_account',
               'visible': True}}]


### CREATE A COPY OF A CONFIGLET
#### COPY WILL HAVE SUFFIX "copy"


```python
# Copy a configlet by name or ID
# print(sdk.copy_configlet(["devfricr01_hostname_conf"]))
```

  


### APPEND ONE CONFIGLET TO ANOTHER


```python
# print(sdk.append_configlet("RECONCILE_ZTW285931A9", "global_aaa_conf"))
```

### GET CONFIGLET NAMES AND IDs FILTERED BY A REGEX PATTERN


```python
print(sdk.get_configlet_names_ids(regex="cr"))
```

### FOR EVERY DEVICE DETERMINCE WHICH CONFIGLETS IF ANY ARE ASSIGNED
#### ALSO RETURNS A COUNT FOR DEVICES WITH AND WITHOUT CONFIGLETS


```python
sdk.get_device_configlets(process_all=True)
```

    Processing switches: 100%|██████████| 1/1 [00:01<00:00,  1.70s/switch]





    {'devices_with_configlets': {'count': 1,
      'devices': [{'devfrIrt98': ['global_cvaas_conf',
         'global_time_conf',
         'global_snmp_conf',
         'global_login_banner_conf',
         'global_logging_conf',
         'global_dns_conf',
         'global_acl_conf',
         'global_aaa_conf',
         'global_spanning-tree_conf',
         'global_lldp_conf',
         'dc_snmp_conf',
         'dc_WESTMINSTER_snmp_conf',
         'device_devfrirt98_hostname_conf',
         'device_devfrirt98_interfaces_conf',
         'device_devfrirt98_routing_conf',
         'override_device_build_conf']}]},
     'devices_without_configlets': {'count': 0, 'devices': []}}



### GIVEN A DEVICES MAC ADDRESS, RETURN ALL ASSOSIATED CONFIGLETS


```python
# pp.pprint(sdk.get_device_configlets("ba:dd:ea:db:ee:f0"))
[x["name"]for x in sdk.get_device_configlets("ba:dd:ea:db:ee:f0")["configletList"]]
```




    ['global_cvaas_conf',
     'global_time_conf',
     'global_snmp_conf',
     'global_login_banner_conf',
     'global_logging_conf',
     'global_dns_conf',
     'global_acl_conf',
     'global_aaa_conf',
     'global_spanning-tree_conf',
     'global_lldp_conf',
     'dc_snmp_conf',
     'dc_WESTMINSTER_snmp_conf',
     'device_devfrirt98_hostname_conf',
     'device_devfrirt98_interfaces_conf',
     'device_devfrirt98_routing_conf',
     'override_device_build_conf']



### SEARCH FOR CONTAINERS USING A REGEX EXPRESSION.


```python
sdk.get_provisioning_filter_topology(value_pattern=r'^WESTMINSTER.*')
```




    [{'list': {'key': 'container_610b77bf-c4b6-47d5-94e6-61kdhfdjf7w24',
       'name': 'WESTMINSTER',
       'type': 'container',
       'childContainerCount': 2,
       'childNetElementCount': 0,
       'parentContainerId': 'root',
       'mode': 'expand',
       'deviceStatus': {'critical': 0,
        'warning': 0,
        'normal': 0,
        'imageUpgrade': 0,
        'task': 0,
        'unAuthorized': 0},
       'childTaskCount': 0,
       'childContainerList': [{'key': 'container_802f55a7-f85e-4285-b63d-279d0bdfc9d2',
         'name': 'MAIN_HUB',
         'type': 'container',
         'childContainerCount': 3,
         'childNetElementCount': 0,
         'parentContainerId': 'container_610b77bf-c4b6-47d5-94e6-61kdhfdjf7w24',
         'mode': 'expand',
         'deviceStatus': {'critical': 0,
          'warning': 0,
          'normal': 0,
          'imageUpgrade': 0,
          'task': 0,
          'unAuthorized': 0},
         'childTaskCount': 0,
         ...}]



### FILTERS CURRENT CONTAINER PROVISIONING HIERARCHY AND RETUNS A SORTED LIST OF PARENTS FOLLOWED BY CHILDREN.
##### CAN BE USED TO DELETE A CONTAINER WITH CONTAINERS SO LONG AS DEVICES ARE NOT ATTACHED.


```python
sdk.extract_container_ids_by_hierarchy(sdk.get_provisioning_filter_topology(value_pattern=r'^THE.*'))
```



### CREATES A SINGLE TEMPORARY PROVISIONING ACTION IN CVASS


```python
import json
data = [{'data': [{'action': 'add',
           'fromId': '',
           'fromName': '',
           'info': 'Container rightman created',
           'infoPreview': 'Container rightman created',
           'nodeId': 'New_Container_1696279183359',
           'nodeName': 'rightman24',
           'nodeType': 'container',
           'toId': 'root',
           'toIdType': 'container',
           'toName': 'Tenant'}]}]
# sdk.post_provisioning_add_temp_actions(data_list = data)
```

### RETREIVES ALL TEMPORARY PROVISIONING ACTIONS IN CVASS


```python
sdk.get_provisioning_temp_actions()
```




    {'total': 6,
     'data': [{'ccId': '',
       'sessionId': '',
       'containerKey': '',
       'taskId': 1,
       'info': '',
       'infoPreview': '',
       'note': '',
       'action': 'delete',
       'nodeType': 'container',
       'nodeId': 'container_4ddejl5b-3541-4b87-9976-c8b35899c1e0',
       'toId': '',
       'fromId': 'root',
       ...}]}



### SAVES ALL TEMPORARY PROVISIONING ACTIONS IN CVASS


```python
sdk.post_provisioning_save_temp_actions(data=[])
```




    {'data': 'No tasks triggered'}



### DELETES ALL TEMPORARY PROVISIONING ACTIONS IN CVASS


```python
# sdk.delete_provisioning_temp_action_all()
```




    {'data': 'success'}




```python
sdk.get_provisioning_filter_topology(value_pattern=r'^rightman2.*')
```




    []



### DELETES A TUPLE OF CONTAINER IDS
##### NESTED FOLDERS MAY NOT CONTAIN DEVICES AND MUST HAVE THEIR CHILDREN DELETED FIRST. "extract_container_ids_by_hierarchy" CREATES THE CORRECT DELETION ORDER


```python
data = []
for x in sdk.extract_container_ids_by_hierarchy(sdk.get_provisioning_filter_topology(value_pattern=r'^campus.*')):
    data.append({'data': [{'action': 'delete',
           'fromId': 'root',
           'nodeId': x,
           'nodeName': 'name_not_required',
           'nodeType': 'container',
                 }]})

sdk.post_provisioning_add_temp_actions(data_list = data)
```

### DELETES A SIGNLE CONTAINER BY ID
##### FOLDERS MAY NOT CONTAIN DEVICES


```python
data = {'data': [{'action': 'delete',
           'fromId': 'root',
           'nodeId': 'container_8e1g8l25-1fc6-4819-87ec-a3e172mmdj103',
           'nodeName': 'name_not_required',
           'nodeType': 'container',
                 }]}
# sdk.post_provisioning_add_temp_actions(data = data)
```




    {'type': 'list',
     'list': {'key': 'root',
      'name': 'Tenant',
      'type': 'container',
      'childContainerCount': 4,
      'childNetElementCount': 0,
      'parentContainerId': None,
      'mode': 'expand',
      'deviceStatus': {'critical': 0,
       'warning': 0,
       'normal': 0,
       'imageUpgrade': 0,
       'task': 0,
       'unAuthorized': 0},
      'childTaskCount': 0,
      'childContainerList': [{'key': 'undefined_container',
        'name': 'Undefined',
        'type': 'container',
          ...}]}}



### GIVEN A CONTAINER HIERARCHY AS A DICTONARY, RETURNS A LIST OF DICTIONARY USED TO CREATE THE HIERARCHY IN CVP 


```python
input_dict = {
    'HQ': ['floor1', 'floor2', 'floor3'],
    'B_DAM': [{'closet1': ['rack1', 'rack2']}],
    'CAMPUS21': ['BUILDING1', 'BUILDING2', {'BUILDING3': ['FLOOR1', 'FLOOR2',{'FLOOR3':['1','2','3']}]}]
}
hierarchy_dict = sdk.generate_topology_hierarchy_post_data(input_dict,print_ascii=True)
```

    +-HQ
    | +-floor1
    | +-floor2
    | +-floor3
    +-B_DAM
    | +-closet1
    | | +-rack1
    | | +-rack2
    +-CAMPUS21
    | +-BUILDING1
    | +-BUILDING2
    | +-BUILDING3
    | | +-FLOOR1
    | | +-FLOOR2
    | | +-FLOOR3
    | | | +-1
    | | | +-2
    | | | +-3


### GIVEN A CONTAINER HIERARCHY AS A DICTONARY, CREATES THE A TEMPORARY PROVISIONING HIERARCHY IN CVP 


```python
# sdk.post_provisioning_add_temp_actions(data = hierarchy_dict)
```

### GIVEN VISUALIZE THE DIRECTORY HIERARCHY


```python
sdk.generate_topology_hierarchy_ascii_tree(value_pattern=r'^WESTMINSTER.*',return_structure=True)
```

    +- WESTMINSTER
    |  +- MAIN_HUB
    |  |  +- WESTMINSTER
    |  |  +- SPRINGFIELD
    |  |  +- WEST-WESTMINSTER
    |  +- SITE
    |  |  +- BUILDING1
    |  |  +- BUILDING2
    |  |  +- BUILDING3
    |  |  +- BUILDING4
    |  |  +- BUILDING5
    |  |  +- BUILDING6
    |  |  +- BUILDING7
    |  |  +- BUILDING8
    |  |  +- BUILDING9
    |  |  +- BUILDING10
    |  |  +- BUILDING11
    |  |  +- BUILDING12
    |  |  +- BUILDING13
    |  |  +- BUILDING14
    |  |  +- BUILDING15
    |  |  +- BUILDING16
    |  |  +- BUILDING17
    |  |  +- BUILDING18





    [{'WESTMINSTER': [{'MAIN_HUB': ['WESTMINSTER', 'SPRINGFIELD', 'WEST-WESTMINSTER']},
       {'SITE': ['BUILDING1',
         'BUILDING2',
         'BUILDING3',
         'BUILDING4',
         'BUILDING5',
         'BUILDING6',
         'BUILDING7',
         'BUILDING8',
         'BUILDING9',
         'BUILDING10',
         'BUILDING11',
         'BUILDING12',
         'BUILDING13',
         'BUILDING14',
         'BUILDING15',
         'BUILDING16',
         'BUILDING17',
         'BUILDING18']}]}]



### CREATE LISTS TO DETERMINE WHICH CONFIGLETS ARE ASSIGNED TO CONTAINERS


```python
all_configlet_names = [x[0] for x in sdk.get_configlet_names_ids()]
all_applied_containers = sdk.get_configlet_applied_containers(all_configlet_names)

result_dict = {}
for container_info in all_applied_containers:
    if 'data' not in container_info or not container_info['data']:
        continue
    for data_entry in container_info['data']:
        container_name = data_entry['containerName']
        configlet_name = container_info['configletName']
        if container_name in result_dict:
            result_dict[container_name].append(configlet_name)
        else:
            result_dict[container_name] = [configlet_name]

result = [[key, value] for key, value in result_dict.items()]
pp.pprint(result)
```

    [['WESTMINSTER', ['dc_WESTMINSTER_snmp_conf']],
     ['MAIN_HUB', ['dc_snmp_conf']],
     ['WESTMINSTER',
      ['global_aaa_conf',
       'global_acl_conf',
       'global_cvaas_conf',
       'global_dns_conf',
       'global_lldp_conf',
       'global_logging_conf',
       'global_login_banner_conf',
       'global_snmp_conf',
       'global_spanning-tree_conf',
       'global_time_conf']],
     ['BUILDING15', ['site_123_main_snmp_conf']],
     ['SITE', ['site_snmp_conf']]]


### GIVEN CONFIGLET NAMES RETURN LIST OF IDS


```python
names_conf = ['global_aaa_conf',
   'global_acl_conf',
   'global_cvaas_conf',
   'global_dns_conf',
   'global_lldp_conf',
   'global_logging_conf',
   'global_login_banner_conf',
   'global_snmp_conf',
   'global_spanning-tree_conf',
   'global_time_conf']
sdk.get_configlet_ids_by_name(names_conf)
```


### GIVEN CONTAINER NAME RETURN LIST OF IDS


```python
sdk.get_container_id_by_name("WESTMINSTER")
```



### ASSIGN CONFIGLETS TO CONTAINER


```python
container_id = sdk.get_container_ids_by_name('SITE')[0]
configlet_id = sdk.get_configlet_ids_by_name(['site_snmp_conf'])
print(container_id,configlet_id)
post_result = sdk.post_assign_configlets_to_container(container_id = container_id, configlets= configlet_id)
```



### GROUP DEVICES BY COMPLIANCECODE OR VERSION


```python
sdk.group_devices(grouping_key = "complianceCode")
```




```python
sdk.group_devices(grouping_key = "internalVersion")
```



### RETRIEVE THE DEVICE SYSTEM ID "filter_devices_by_regex". 
##### IF A REGEX PARAMETER IS PROVIDED, IT WILL FILTER THE DEVICES BASED ON WHETHER THE REGEX MATCHES EITHER THE HOSTNAME OR SYSTEM MAC ADDRESS OF A DEVICE. IF NO REGEX PARAMETER IS PROVIDED, IT WILL RETURN ALL HOSTNAME AND SYSTEM MAC ADDRESS PAIRS FROM THE DEVICES.


```python
api.get_system_mac_address_by_name("HYP.*SW[0-9]")
```



## Contribution

Feel free to clone the repository, create a new branch, make changes, and submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
