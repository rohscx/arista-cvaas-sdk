import requests
import re
import json
import uuid
from json.decoder import JSONDecodeError
from tqdm import tqdm
from typing import Any, Dict, List, Optional
from collections import deque

class AristaCVAAS:
    def __init__(self, server_url, token):
        self.server_url = server_url
        self.token = token
        self.session = requests.Session()
        self.headers = {
            'Authorization': f'Bearer {self.token}'
        }

    def _check_response(self, response):
        try:
            json_data = response.json()
            if isinstance(json_data, dict):
                if json_data.get('code') == 24 and json_data.get('message') == 'Status unauthenticated':
                    return json_data
            elif isinstance(json_data, list):
                # Handle list response if necessary
                pass  # or replace with actual handling code
        except JSONDecodeError:
            return {'error': 'Invalid JSON response', 'original_response': response.text}
        return None

    def _find_matching_dicts(self, dic: Dict[str, Any], value_pattern: str) -> List[Dict[str, Any]]:
        regex = re.compile(value_pattern, re.IGNORECASE)
        matching_dicts = []

        def traverse_dict(current_dict: Dict[str, Any]):
            if 'name' in current_dict and regex.match(current_dict['name']):
                matching_dicts.append({'list':current_dict})
            for key, value in current_dict.items():
                if isinstance(value, dict):
                    traverse_dict(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            traverse_dict(item)

        traverse_dict(dic)
        return matching_dicts

    @staticmethod
    def _print_tree(container, prefix=""):
        print(f"{prefix}+- {container['name']}")
        new_prefix = f"{prefix}|  "
        for child in container['childContainerList']:
            AristaCVAAS._print_tree(child, new_prefix)

    @staticmethod
    def generate_topology_hierarchy_post_data(input_dict, parent_id='root', uuid_length=13, print_ascii=False):
        hierarchy_dicts = []
        ascii_tree = []

        def traverse_hierarchy(input_dict, parent_id, prefix=""):
            for parent, children in input_dict.items():
                parent_node_id = f"New_Container_{str(uuid.uuid4().int)[:uuid_length]}"
                parent_dict = {
                    "data": [{
                        "info": f"Container {parent} created",
                        "infoPreview": f"Container {parent} created",
                        "action": "add",
                        "nodeType": "container",
                        "nodeId": parent_node_id,
                        "toId": parent_id,
                        "fromId": "",
                        "nodeName": parent,
                        "fromName": "",
                        "toName": "" if parent_id == 'root' else parent_id,
                        "toIdType": "container"
                    }]
                }
                hierarchy_dicts.append(parent_dict)
                if print_ascii:
                    ascii_tree.append(f"{prefix}+-{parent}")
                new_prefix = f"{prefix}| "
                if isinstance(children, list):
                    for child in children:
                        if isinstance(child, dict):
                            traverse_hierarchy(child, parent_node_id, new_prefix)
                        else:
                            child_node_id = f"New_Container_{str(uuid.uuid4().int)[:uuid_length]}"
                            child_dict = {
                                "data": [{
                                    "info": f"Container {child} created",
                                    "infoPreview": f"Container {child} created",
                                    "action": "add",
                                    "nodeType": "container",
                                    "nodeId": child_node_id,
                                    "toId": parent_node_id,
                                    "fromId": "",
                                    "nodeName": child,
                                    "fromName": "",
                                    "toName": parent,
                                    "toIdType": "container"
                                }]
                            }
                            hierarchy_dicts.append(child_dict)
                            if print_ascii:
                                ascii_tree.append(f"{new_prefix}+-{child}")

        traverse_hierarchy(input_dict, parent_id)
        if print_ascii:
            print('\n'.join(ascii_tree))  # Print the ASCII tree only if print_ascii is True
        return hierarchy_dicts
    
    @staticmethod
    def _post_order_traversal(container: Dict[str, Any], order: List[str]):
        for child_container in container.get('childContainerList', []):
            AristaCVAAS._post_order_traversal(child_container, order)
        order.append(container['key'])
        
    @staticmethod
    def _extract_hierarchy_structure(container):
        name = container['name']
        child_structures = [
            AristaCVAAS._extract_hierarchy_structure(child)
            for child in container['childContainerList']
        ]

        hierarchy_structure = {}
        if child_structures:
            # Group children by whether they are strings or dictionaries
            string_children = [child for child in child_structures if isinstance(child, str)]
            dict_children = [child for child in child_structures if isinstance(child, dict)]
            # Merge all children into a single list
            children = string_children + [{k: v} for d in dict_children for k, v in d.items()]
            hierarchy_structure[name] = children
        else:
            # If no children, just return the name
            hierarchy_structure = name

        return hierarchy_structure
            

    @staticmethod
    def extract_container_ids_by_hierarchy(containers: List[Dict[str, Any]]) -> List[str]:
        deletion_order = []
        for container in containers:
            AristaCVAAS._post_order_traversal(container['list'], deletion_order)
        return deletion_order
    
    def generate_topology_hierarchy_ascii_tree(self, value_pattern: Optional[str] = None, return_structure=False):
        root_container = self.get_provisioning_filter_topology(value_pattern)
        hierarchy_structure = None

        if type(root_container) == list:
            for x in root_container:
                AristaCVAAS._print_tree(x['list']) 
        else:
            AristaCVAAS._print_tree(root_container['list'])

        if return_structure:
            if type(root_container) == list:
                hierarchy_structure = [
                    self._extract_hierarchy_structure(x['list'])
                    for x in root_container
                ]
            else:
                hierarchy_structure = self.extract_hierarchy_structure(root_container['list'])

        return hierarchy_structure  # Returns None if return_structure is False

    def group_devices(self, grouping_key):
        if grouping_key not in ['complianceCode', 'internalVersion']:
            raise ValueError("Invalid grouping_key. Must be 'complianceCode' or 'internalVersion'.")

        # Get the inventory devices
        inventory_devices = self.get_inventory_devices()
        
        grouped_devices = {}
        
        for device in inventory_devices:
            key = device.get(grouping_key)
            device_info = {
                'modelName': device.get('modelName'),
                'systemMacAddress': device.get('systemMacAddress'),
                'internalVersion': device.get('internalVersion'),
                'hostname': device.get('hostname'),
                'complianceCode': device.get('complianceCode'),
                'complianceIndication': device.get('complianceIndication')
            }
            
            if key in grouped_devices:
                grouped_devices[key].append(device_info)
            else:
                grouped_devices[key] = [device_info]

        return grouped_devices

    def get_configlet_ids_by_name(self, configlet_names):
        # Assume get_configlet_names_ids() returns a list of tuples where each tuple contains a configlet name and its ID
        all_configlets = self.get_configlet_names_ids()
        
        # Create a dictionary for faster lookup
        name_to_id_dict = {name: id for name, id in all_configlets}
        
        # Find and return the IDs corresponding to the provided configlet names
        configlet_ids = [name_to_id_dict.get(name) for name in configlet_names]
        
        # Optionally, you might want to filter out None values if any configlet name is not found
        configlet_ids = [id for id in configlet_ids if id is not None]
        
        return configlet_ids


    def get_configlets(self, start_index=0, end_index=2000):
        endpoint = f'/configlet/getConfiglets.do?startIndex={start_index}&endIndex={end_index}'
        response = self.session.get(self.server_url + endpoint, headers=self.headers)
        
        error_response = self._check_response(response)
        if error_response:
            return error_response
        
        return response.status_code, response.json()

    def get_configlet_names_ids(self, regex=None):
        response = self.get_configlets()
        if isinstance(response, dict):  # Check if the response is an error message
            return response

        status_code, response_text = response
        if status_code != 200:
            return []

        configlets = response_text.get('data', [])
        result = [(configlet['name'], configlet['key']) for configlet in configlets]

        if regex:
            pattern = re.compile(regex, re.IGNORECASE)
            result = [(name, key) for name, key in result if pattern.search(name)]

        return result

    def get_configlet_by_id(self, configlet_id):
        endpoint = f'/configlet/getConfigletById.do?id={configlet_id}'
        response = self.session.get(self.server_url + endpoint, headers=self.headers)
        
        error_response = self._check_response(response)
        if error_response:
            return error_response
        
        return response.json()

    def get_configlet_applied_containers(self, configlet_names:list):
        results = []
        for name in configlet_names:
            endpoint = f'/configlet/getAppliedContainers.do?configletName={name}&startIndex=0&endIndex=1000'
            response = self.session.get(self.server_url + endpoint, headers=self.headers)
            error_response = self._check_response(response)
            if error_response:
                return error_response
            response = response.json()
            response["configletName"] = name
            results.append(response)        
        return results

    def get_configlet_applied_devices(self, configlet_names:list):
        results = []
        for name in configlet_names:
            endpoint = f'/configlet/getAppliedDevices.do?configletName={name}&startIndex=0&endIndex=1000'
            response = self.session.get(self.server_url + endpoint, headers=self.headers)
            error_response = self._check_response(response)
            if error_response:
                return error_response
            response = response.json()
            response["configletName"] = name
            results.append(response)        
        return results
   
    def get_inventory_devices(self, provisioned=False, system_mac_addresses: Optional[List[str]] = None):
        endpoint = f'/inventory/devices?provisioned={provisioned}'
        response = self.session.get(self.server_url + endpoint, headers=self.headers)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        devices = response.json()

        if system_mac_addresses:
            devices = [device for device in devices if device.get('systemMacAddress') in system_mac_addresses]

        return devices


    def get_device_configlets(self, mac_address=None, process_all=False):
        if process_all:
            switches = [x for x in self.get_inventory_devices()]
            devices_with_configlets = []
            devices_without_configlets = []
            for switch in tqdm(switches, desc="Processing switches", unit="switch"):
                temp_data = {switch['hostname']: self.get_device_configlets(switch["systemMacAddress"])}
                if 'configletList' in temp_data[switch["hostname"]]:
                    configlet_names = [x["name"] for x in temp_data[switch['hostname']]["configletList"]]
                    if len(configlet_names) > 0:
                        temp_data[switch['hostname']] = configlet_names
                        devices_with_configlets.append(temp_data)
                    else:
                        devices_without_configlets.append(switch['hostname'])
                else:
                    devices_without_configlets.append(switch['hostname'])

            result = {
                "devices_with_configlets": {
                    "count": len(devices_with_configlets),
                    "devices": devices_with_configlets
                },
                "devices_without_configlets": {
                    "count": len(devices_without_configlets),
                    "devices": devices_without_configlets
                }
            }

            return result
        else:
            if mac_address is None:
                raise ValueError("mac_address is required when process_all is False")
            endpoint = f'/ztp/getConfigletsByNetElementId.do?netElementId={mac_address}&queryParam=null&startIndex=0&endIndex=0'
            response = self.session.get(self.server_url + endpoint, headers=self.headers)
            error_response = self._check_response(response)
            if error_response:
                return error_response
            return response.json()
    
    def get_inventory_device_config(self, mac_address):
        endpoint = f'/inventory/device/config?netElementId={mac_address}'
        response = self.session.get(self.server_url + endpoint, headers=self.headers)
        
        # No error checking on this method. Would need to debug the respose and update check_response method. 
        error_response = self._check_response(response)
        if error_response:
            return error_response
        
        return response.json()
    
    def get_inventory_containers(self):
        endpoint = f'/inventory/containers'
        response = self.session.get(self.server_url + endpoint, headers=self.headers)
        
#         # No error checking on this method. Would need to debug the respose and update check_response method. 
#         error_response = self._check_response(response)
#         if error_response:
#             return error_response
        
        return response.json()
    
    def get_users_and_groups(self, filter_status="Any"):
        endpoint = f'/user/getUsers.do?startIndex=0&endIndex=1000'
        response = self.session.get(self.server_url + endpoint, headers=self.headers)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        json_data = response.json()

        # Filter users based on the 'currentStatus' if specified
        if filter_status != "Any":
            filtered_users = [user for user in json_data.get('users', []) if user.get('currentStatus') == filter_status]
            json_data['users'] = filtered_users
        
        return json_data

    def get_roles(self):
        endpoint = f'/role/getRoles.do?startIndex=0&endIndex=1000'
        response = self.session.get(self.server_url + endpoint, headers=self.headers)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        json_data = response.json()

        return json_data
    
    def get_cvp_info(self):
        endpoint = f'/cvpInfo/getCvpInfo.do'
        response = self.session.get(self.server_url + endpoint, headers=self.headers)
        
        error_response = self._check_response(response)
        if error_response:
            return error_response
        
        return response.json()

    def get_copy_configlet(self, source_configlet_identifiers, new_names=None):
        # If new_names is provided, its length should match the number of source_configlet_identifiers
        if new_names and len(source_configlet_identifiers) != len(new_names):
            return {"error": "Mismatch in number of source configlets and new names"}

        copied_configlets = []

        for index, identifier in enumerate(source_configlet_identifiers):
            # Retrieve all configlets
            configlets = self.get_configlet_names_ids()
            if isinstance(configlets, dict):  # Check if the response is an error message
                return configlets

            # Find the source configlet by name or ID
            matched_configlet = next((configlet for configlet in configlets if identifier in configlet), None)
            if not matched_configlet:
                return {"error": f"Configlet {identifier} not found"}

            # Fetch the detailed configuration of the matched configlet
            configlet_details = self.get_configlet_by_id(matched_configlet[1])
            if 'config' not in configlet_details:
                return {"error": "Failed to retrieve configlet details"}

            # Create a copy of the configlet
            endpoint = '/configlet/addConfiglet.do'
            new_name = new_names[index] if new_names else f"{matched_configlet[0]} copy"
            body = {
                "config": configlet_details['config'],
                "name": new_name
            }
            response = self.session.post(self.server_url + endpoint, headers=self.headers, json=body)

            error_response = self._check_response(response)
            if error_response:
                return error_response

            copied_configlets.append(response.json())

        return copied_configlets
    
    
    def get_applied_configlets_per_container(self):
        all_configlet_names = [x[0] for x in self.get_configlet_names_ids()]
        all_applied_containers = self.get_configlet_applied_containers(all_configlet_names)

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
        return result

    def post_append_configlet(self, source_configlet_identifier, target_configlet_identifier):
        # Retrieve all configlets
        configlets = self.get_configlet_names_ids()
        if isinstance(configlets, dict):  # Check if the response is an error message
            return configlets

        # Find the source and target configlets by name or ID
        source_configlet = next((configlet for configlet in configlets if source_configlet_identifier in configlet), None)
        target_configlet = next((configlet for configlet in configlets if target_configlet_identifier in configlet), None)

        if not source_configlet or not target_configlet:
            return {"error": "Configlet not found"}

        # Fetch the detailed configuration of the source and target configlets
        source_configlet_details = self.get_configlet_by_id(source_configlet[1])
        target_configlet_details = self.get_configlet_by_id(target_configlet[1])

        if 'config' not in source_configlet_details or 'config' not in target_configlet_details:
            return {"error": "Failed to retrieve configlet details"}

        # Append the source configlet configuration to the target configlet configuration
        appended_config = f"{target_configlet_details['config']}\n! APPENDED FROM {source_configlet[0]}\n{source_configlet_details['config']}"

        # Update the target configlet with the appended configuration
        endpoint = '/configlet/updateConfiglet.do'
        body = {
            "config": appended_config,
            "name": target_configlet[0],
            "key": target_configlet[1]
        }
        response = self.session.post(self.server_url + endpoint, headers=self.headers, json=body)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        return response.json()
    
    def post_assign_configlets_to_container(self, container_id:str, configlets:list):
        post_data = [{'data': [{'action': 'associate',
           'configletBuilderList': [],
           'configletBuilderNamesList': [],
           'configletList': configlets,
           'fromId': '',
           'fromName': '',
           'ignoreConfigletBuilderList': [],
           'ignoreConfigletBuilderNamesList': [],
           'ignoreConfigletList': [],
           'ignoreConfigletNamesList': [],
           'nodeId': '',
           'nodeName': '',
           'nodeType': 'configlet',
           'toId': container_id,
           'toIdType': 'container'}]}]
        return self.post_provisioning_add_temp_actions(data_list = post_data)

    def post_provisioning_save_temp_actions(self, data):
        endpoint = f'/ztp/saveTopology.do'
        response = self.session.post(self.server_url + endpoint, headers = self.headers, data=json.dumps(data))

        error_response = self._check_response(response)
        if error_response:
            return error_response

        return response.json()
    
    def post_provisioning_add_temp_actions(self, data_list, nodeId="root"):
        results = []  # List to hold the results of each POST request
        for data in data_list:
            endpoint = f'/ztp/addTempAction.do?format=list&queryParam=&nodeId={nodeId}'
            response = self.session.post(self.server_url + endpoint, headers=self.headers, data=json.dumps(data))
            error_response = self._check_response(response)
            if error_response:
                results.append({'error': error_response})
            else:
                results.append(response.json())
        return results
    
    def get_provisioning_temp_actions(self):
        endpoint = f'/ztp/getAllTempActions.do?startIndex=0&endIndex=1000'
        response = self.session.get(self.server_url + endpoint, headers = self.headers)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        return response.json()
    
    def get_provisioning_filter_topology(self, value_pattern: Optional[str] = None):
        endpoint = f'/provisioning/v3/filterTopology.do?queryParam=a&format=list&startIndex=0&endIndex=1000'
        response = self.session.get(self.server_url + endpoint, headers=self.headers)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        response_data = response.json()
        if value_pattern:
            return self._find_matching_dicts(response_data, value_pattern)
        else:
            return response_data

    def delete_provisioning_temp_action_all(self, value_pattern: Optional[str] = None):
        endpoint = f'/provisioning/deleteAllTempAction.do'
        response = self.session.delete(self.server_url + endpoint, headers=self.headers)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        response_data = response.json()
        if value_pattern:
            return self._find_matching_dicts(response_data, value_pattern)
        else:
            return response_data

    def get_service_accounts(self):
        endpoint = f'/arista.serviceaccount.v1.TokenService/GetAll'

        response = self.session.get(self.server_url + endpoint, headers = self.headers)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        return response.json()
    
    def get_container_ids_by_name(self, container_names):
        # Ensure the input is a list, even if it's a single string
        if not isinstance(container_names, list):
            container_names = [container_names]
            
        # Assume get_provisioning_filter_topology() returns the topology data
        topology_data = self.get_provisioning_filter_topology()
        
        # Recursively search for the container ID based on the container name
        def search_container(containers_list, name):
            for container in containers_list:
                if container.get('name') == name:
                    return container.get('key')
                child_containers = container.get('childContainerList', [])
                container_id = search_container(child_containers, name)
                if container_id:
                    return container_id
            return None
        
        # Store container ids in a list
        container_ids_list = []
        for name in container_names:
            container_id = search_container(topology_data['list']['childContainerList'], name)
            if container_id:  # Only add to list if a matching container ID is found
                container_ids_list.append(container_id)
        
        return container_ids_list
    
    
