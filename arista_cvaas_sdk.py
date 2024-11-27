import requests
import re
import json
import uuid
import sys
import copy
import pprint as pp
import tempfile
import os
import pandas as pd
import logging
from json.decoder import JSONDecodeError
from tqdm import tqdm
from typing import Any, Dict, List, Tuple, Optional, Union
from collections import deque
from requests import Response
from datetime import datetime


class DependencyTracker:
    dependencies = {}

    def track_dependencies(self, *args):
        self.__class__.dependencies[self.__class__.__name__] = {
            'dependencies': [],
            'python_version': sys.version
        }
        for arg in args:
            if isinstance(arg, DependencyTracker):
                self.__class__.dependencies[self.__class__.__name__]['dependencies'].append(arg.__class__.__name__)

    @classmethod
    def output_dependencies(cls):
        for class_name, info in cls.dependencies.items():
            print(f'{class_name}:')
            print(f'    Dependencies: {", ".join(info["dependencies"]) if info["dependencies"] else "None"}')
            print(f'    Python Version: {info["python_version"]}')
class AristaCVAAS(DependencyTracker):
    def __init__(self, host_url: str, token: str, path: str = "/cvpservice", *args) -> None:
        super().track_dependencies(*args)  # call to track dependencies
        self.host_url = host_url
        self.path = path
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
    def _print_tree(container: Dict[str, Any], prefix: str = "") -> None:
        """
        Prints a visual tree structure for a given container.

        Parameters:
        - container (Dict[str, Any]): The container to print, with at least the keys 'name' and 'childContainerList'.
        - prefix (str, optional): The prefix for each line of the tree structure. Defaults to an empty string.

        Returns:
        - None
        """
        print(f"{prefix}+- {container['name']}")
        new_prefix = f"{prefix}|  "
        for child in container['childContainerList']:
            AristaCVAAS._print_tree(child, new_prefix)

    @staticmethod
    def convert_date_time_from_long_format(timestamp_milliseconds: int) -> str:
        """
        Convert a timestamp in milliseconds to a human-readable date-time string.

        Parameters:
            timestamp_milliseconds (int): The timestamp in milliseconds.

        Returns:
            str: The human-readable date-time string in 'YYYY-MM-DD HH:MM:SS' format.
        """

        # Convert milliseconds to seconds
        timestamp_seconds = timestamp_milliseconds / 1000.0

        # Convert the timestamp to a datetime object and then to a string in the desired format
        date_str = datetime.utcfromtimestamp(timestamp_seconds).strftime('%Y-%m-%d %H:%M:%S')

        return date_str

    @staticmethod
    def compare_models(model_a: Any, model_b: Any) -> List[str]:
        """Compare two models and return items that exist in model_a but not in model_b."""
        model_a
        diff_list = []
        for item in model_a:
            if item not in model_b:
                diff_list.append(item)
        return diff_list
            
    @staticmethod
    def generate_topology_hierarchy_post_data(
        input_dict: Dict[str, Union[str, List[Union[str, Dict[str, Any]]]]],
        parent_id: str = 'root',
        uuid_length: int = 13,
        print_ascii: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generates a list of dictionaries representing a topology hierarchy based on the input dictionary.

        Parameters:
        - input_dict (Dict[str, Union[str, List[Union[str, Dict[str, Any]]]]]): The input dictionary representing the hierarchy.
        - parent_id (str, optional): The ID of the parent node. Defaults to 'root'.
        - uuid_length (int, optional): The length of the generated UUIDs. Defaults to 13.
        - print_ascii (bool, optional): Whether to print the ASCII representation of the tree. Defaults to False.

        Returns:
        - List[Dict[str, Any]]: A list of dictionaries representing the topology hierarchy.
        """
        hierarchy_dicts = []
        ascii_tree = []

        def traverse_hierarchy(
            input_dict: Dict[str, Union[str, List[Union[str, Dict[str, Any]]]]],
            parent_id: str,
            prefix: str = ""
        ) -> None:
            """Recursively traverses the hierarchy and populates hierarchy_dicts and ascii_tree."""
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
    def _post_order_traversal(container: Dict[str, Any], order: List[str]) -> None:
        """
        Performs a post-order traversal on the given container and appends container keys to the order list.

        Parameters:
        - container (Dict[str, Any]): The container to be traversed. Expected to have a 'key' key and optionally a 'childContainerList' key.
        - order (List[str]): The list to which container keys will be appended during the traversal.

        Returns:
        - None
        """
        for child_container in container.get('childContainerList', []):
            AristaCVAAS._post_order_traversal(child_container, order)
        order.append(container['key'])
        
    @staticmethod
    def _extract_hierarchy_structure(container: Dict[str, Any]) -> Union[str, Dict[str, List[Union[str, Dict[str, Any]]]]]:
        """
        Extracts the hierarchy structure from a given container.

        Parameters:
        - container (Dict[str, Any]): The container to extract the hierarchy from. 
                                      Expected to have a 'name' key and a 'childContainerList' key.

        Returns:
        - Union[str, Dict[str, List[Union[str, Dict[str, Any]]]]]: 
            The extracted hierarchy structure. If the container has no children, a string representing the 
            container's name is returned. If the container has children, a dictionary representing the 
            hierarchy structure is returned.
        """
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
        """
        Extracts container IDs from a list of containers by performing a post-order traversal.

        Parameters:
        - containers (List[Dict[str, Any]]): The list of containers to extract IDs from. 
                                             Each container is expected to have a 'list' key.

        Returns:
        - List[str]: The list of container IDs in post-order traversal.
        """
        deletion_order = []
        for container in containers:
            AristaCVAAS._post_order_traversal(container['list'], deletion_order)
        return deletion_order
    
    
#     start
    @staticmethod
    def find_container_key(topology_data: Dict[str, Any], 
                           name: str, 
                           fallback_value: Optional[str] = None) -> Optional[str]:
        """
        Find the container key for a given name in a topology data structure.

        Parameters:
            topology_data: Dictionary containing topology information.
            name: Name of the container to search for.
            fallback_value: Fallback value to return if the key is not found.

        Returns:
            The container key if found, fallback_value otherwise.
        """
        # Helper function to search recursively in child containers
        def search_in_child(child_list: List[Dict[str, Any]]) -> Optional[str]:
            for child in child_list:
                if child['name'] == name:
                    return child['key']
                found_key = search_in_child(child.get('childContainerList', []))
                if found_key:
                    return found_key
            return None

        # Call the helper function and return its result or the fallback_value
        result = search_in_child(topology_data['list'].get('childContainerList', []))
        return result if result is not None else fallback_value
    
    @staticmethod
    def prune_existing_containers(array_to_prune: List[Dict[str, List[Dict[str, Union[str, None]]]]]) -> List[Dict[str, List[Dict[str, Union[str, None]]]]]:
        """
        Prune the list of dictionaries to only include entries where nodeId contains 'New_Container_'.

        Parameters:
        - array_to_prune (List[Dict[str, List[Dict[str, Union[str, None]]]]]): The array to be pruned.

        Returns:
        - List[Dict[str, List[Dict[str, Union[str, None]]]]]: The pruned array.
        """
        pruned_array = []
        for entry in array_to_prune:
            data_list = entry.get('data', [])
            pruned_data_list = [data_entry for data_entry in data_list if 'New_Container_' in str(data_entry.get('nodeId', ''))]
            if pruned_data_list:
                pruned_array.append({'data': pruned_data_list})
        return pruned_array

    @staticmethod
    def find_longer_prefixes(df: pd.DataFrame, network: str, le: Optional[int] = None, ge: Optional[int] = None, eq: Optional[int] = None) -> pd.DataFrame:
        """
        Filter a DataFrame to find networks that are supernets of a given network and meet optional prefix length criteria.
    
        Parameters:
        df (pd.DataFrame): DataFrame containing a column 'Prefixes' with network prefixes as strings.
        network (str): The network prefix to compare against, in CIDR notation.
        le (Optional[int]): Optional maximum prefix length to filter by (inclusive).
        ge (Optional[int]): Optional minimum prefix length to filter by (inclusive).
        eq (Optional[int]): Optional exact prefix length to filter by.
    
        Returns:
        pd.DataFrame: A DataFrame containing the prefixes that are supernets of the given network and meet the specified criteria.
        """
    
        # Type checks
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")
        if not isinstance(network, str):
            raise TypeError("network must be a string")
        if le is not None and not isinstance(le, int):
            raise TypeError("le must be an integer or None")
        if ge is not None and not isinstance(ge, int):
            raise TypeError("ge must be an integer or None")
        if eq is not None and not isinstance(eq, int):
            raise TypeError("eq must be an integer or None")
    
        # Convert the user input string to an IP network object
        try:
            network = ipaddress.ip_network(network)
        except ValueError as e:
            raise ValueError(f"Invalid network: {network}") from e
    
        # Function to check if the network in the DataFrame is a supernet of the input
        def is_relevant_prefix(prefix: str) -> bool:
            try:
                net = ipaddress.ip_network(prefix)
                if not net.subnet_of(network):
                    return False
                if le is not None and net.prefixlen > le:
                    return False
                if ge is not None and net.prefixlen < ge:
                    return False
                if eq is not None and net.prefixlen != eq:
                    return False
                return True
            except ValueError:
                return False
    
        # Apply the function across the DataFrame
        filtered_df = df[df['Prefixes'].apply(is_relevant_prefix)].copy()  # Create a copy explicitly
    
        # Convert prefixes to ipaddress.IPv4Network objects and sort
        filtered_df['Network'] = filtered_df['Prefixes'].apply(lambda x: ipaddress.ip_network(x))
        filtered_df.sort_values(by='Network', inplace=True)
        
        # Optionally, remove the helper 'Network' column if not needed
        filtered_df.drop(columns='Network', inplace=True)
        
        return filtered_df
    
    @staticmethod
    def filter_configlets_with_list(configlets):
        """
        Filters out configlet objects that do not contain the 'configletList' key.
    
        Parameters:
        - configlets (list of dicts): The list of configlet objects to filter.
    
        Returns:
        list of dicts: A filtered list of configlet objects that include the 'configletList' key.
        """
        return [configlet for configlet in configlets if 'configletList' in configlet]
   
    @staticmethod
    def search_config_patterns(config:str, patterns:str, print_matches=True):
        """
        Checks a configuration against a list of regex patterns and returns the match results along with the matched text in a structured dictionary.
        Optionally prints the matched text based on a control flag.
        
        Parameters:
        - config (str): The multi-line configuration string to be checked.
        - patterns (list of str): A list of regex patterns used for fuzzy matching.
        - print_matches (bool, optional): Flag to control whether to print the matched text. Defaults to True.
    
        Returns:
        dict: A dictionary with each pattern as a key, and each value is another dictionary with 'matched' (bool) and 'text' (str or None).
        """
        results = {}
        for pattern in patterns:
            # Compile the regex pattern for more efficient matching
            regex = re.compile(pattern.strip(), re.MULTILINE | re.DOTALL)
            
            # Search for the pattern in the config string
            match = regex.search(config)
            if match:
                # If a match is found, store both the match status and the matched text
                results[pattern] = {'matched': True, 'text': match.group(0)}
                if print_matches:
                    print(f"<------>\nPattern:\n{pattern}")
                    print(f"Matched: {True}")
                    print(f"Matched text:\n{match.group(0)}\n")
            else:
                # If no match is found, indicate no match and provide None for the text
                results[pattern] = {'matched': False, 'text': None}
                if print_matches:
                    print(f"<------>\nPattern:\n{pattern}")
                    print(f"Matched: {False}")
                    print(f"No matched text.\n")
        
        return results    
    
    def flatten_array(self, arr):
        """
        Recursively flattens a nested list.
        
        Parameters:
        - arr (list): A potentially nested list to be flattened.

        Returns:
        - list: A flattened version of the input list.
        """
        flattened_list = []
        for item in arr:
            if isinstance(item, list):
                flattened_list.extend(self.flatten_array(item))
            else:
                flattened_list.append(item)
        return flattened_list
    
    def search_configlets(self, system_name: str, filter_substring: str, regex_pattern: str, context_lines: int = 0):
        """
        Searches for configlets by system name, filters them by a substring, and searches within their configurations using a regular expression,
        highlighting the matches. Depending on 'context_lines', it either returns the entire configuration, just the matching lines, or the
        matching lines with a specified number of context lines above and below. The device and configlet name are always included in the output.

        Parameters:
        - system_name (str): The name pattern to match systems from which to retrieve configlets.
        - filter_substring (str): A substring to filter configlets by their name.
        - regex_pattern (str): The regular expression pattern to search for within configlet configurations.
        - context_lines (int, optional): Defines the number of context lines above and below the match to return. Defaults to 0,
          which returns only the matching lines. If set to a negative number, the entire configuration is returned for matches.

        Returns:
        None. This method directly prints the configurations meeting the criteria defined by 'context_lines'.
        """

        device_macs = self.get_system_mac_address_by_name(system_name)
        configlets = [self.get_device_configlets(x[1]) for x in device_macs[:]]
        
        # Ensure only configlets with 'configletList' are processed
        configlets = self.filter_configlets_with_list(configlets)  

        # Use regex for filtering target configlets
        filter_pattern = re.compile(filter_substring, re.IGNORECASE)
        # really complicated way to filter on configlets in the list and remove all empty lists generated by the list comprehension.
        configlets = [filtered_list for filtered_list in 
              [[x for y in x['configletList'] if filter_pattern.search(y["name"])] 
               for x in configlets if x["total"] >= 1] if filtered_list]
        configlets = self.flatten_array(configlets)

        # Matches the string in the configlet to be retuned
        pattern = re.compile(regex_pattern, re.IGNORECASE)

        for x in configlets:
            if (x["total"] >= 1):
                for y in  x["configletList"]:
                    config_name = y["name"]
                    config = y["config"]
                    config_lines = config.split('\n')
                    matches_found = False
                    output_lines = []
        
                    for i, line in enumerate(config_lines):
                        if pattern.search(line):
                            matches_found = True
                            if context_lines < 0:
                                output_lines = config_lines
                                break
                            else:
                                start = max(i - context_lines, 0)
                                end = min(i + context_lines + 1, len(config_lines))
                                output_lines.extend(config_lines[start:end])
                                # output_lines.append("********")  # Separator for multiple matches
        
                    if matches_found or context_lines < 0:
                        applied_systems = self.flatten_array([[y["hostName"] for y in x['data']] for x in self.get_configlet_applied_devices([config_name])])
                        print(f'Device(s): {", ".join(applied_systems)}, Configlet: {config_name}')
                        if output_lines:
                            print('\n'.join(output_lines) + '\n')
                        else:
                            print("No matches found.\n")

    def search_missing_context_lines(self, system_name: str, filter_substring: str, expected_string: str):
        """
        Searches for configlets by system name, filters them by a substring, and checks if the configurations are missing a specified expected string, avoiding duplicate reports.
        
        Parameters:
        - system_name (str): The name pattern to match systems from which to retrieve configlets.
        - filter_substring (str): A substring to filter configlets by their name.
        - expected_string (str): The string to check for in the configlet configurations.
    
        Returns:
        None. This method directly prints the configlets that are missing the expected string, ensuring each is reported only once.
        """
        device_macs = self.get_system_mac_address_by_name(system_name)
        configlets = [self.get_device_configlets(x[1]) for x in device_macs[:]]
        
        # Ensure only configlets with 'configletList' are processed
        configlets = self.filter_configlets_with_list(configlets)  
    
        filter_pattern = re.compile(filter_substring, re.IGNORECASE)
        reported_configlets = set()  # Set to track reported configlets to avoid duplicates
    
        for configlet in configlets:
            filtered_configlets = [item for item in configlet['configletList'] if filter_pattern.search(item["name"])]
            for item in filtered_configlets:
                config_name = item['name']
                config = item['config']
                # Check if the expected string is present in the config string and if not already reported
                if expected_string not in config and config_name not in reported_configlets:
                    reported_configlets.add(config_name)  # Add to the set of reported configlets
                    applied_systems = self.flatten_array([[y["hostName"] for y in x['data']] for x in self.get_configlet_applied_devices([config_name])])
                    print(f'Issue found in Configlet applied to Device(s): {", ".join(applied_systems)}, Configlet: {config_name}\n')
                    print(f"Missing expected string. Expected to find: '{expected_string}' in configuration, but it was not found.\n")
    


    
    def batfish_analyze_network_configs(self, device_list: list, bf_host: str = "172.16.100.1", snapshot_name: str = "snapshot") -> object:
        """
        Analyze a list of network device configurations to identify unused and undefined structures using the Batfish service. 
        BATFISH server should be running on a local or remote host running Docker:
        docker run --name batfish -v batfish-data:/data -p 8887:8888 -p 9997:9997 -p 9996:9996 batfish/allinone

        Parameters:
            device_list (list): List of dictionaries, each containing device information with keys 'hostname' and 'systemMacAddress'.
            bf_host (str, optional): The IP address of the Batfish service. Defaults to "172.16.100.1".
            snapshot_name (str, optional): The name to be used for the snapshot in Batfish. Defaults to "snapshot".

        Returns:
            pybatfish.client.session.Session: A Batfish Session object initialized with the provided configurations.

        Raises:
            ImportError: If pybatfish is not installed.
        """

        try:
            import pybatfish
        except ImportError:
            print("pybatfish is not installed. Please install it before proceeding. !pip install --upgrade pybatfish")

        import pybatfish
        from pybatfish.client.session import Session

        # Suppress log messages from Batfish
        logging.getLogger('pybatfish').setLevel(logging.CRITICAL)

        # Create temporary directory and sub-directory for configs
        with tempfile.TemporaryDirectory() as temp_dir:
            config_subdir = os.path.join(temp_dir, 'configs')
            os.mkdir(config_subdir)

            # Write all configurations to files in the sub-directory
            for device in device_list:
                hostname = device['hostname']
                systemMacAddress = device['systemMacAddress']

                # Fetch config text (replace with your actual API call)
                config_text = self.get_inventory_device_config(systemMacAddress)["output"]

                # Create and write the configuration file
                config_filename = hostname
                config_path = os.path.join(config_subdir, config_filename)
                with open(config_path, 'w') as f:
                    f.write(config_text)

            # Initialize Batfish session and snapshot
            bf = pybatfish.client.session.Session(host=bf_host)
            bf.init_snapshot(temp_dir, name=snapshot_name, overwrite=True)
            # Assign pybatfish to self.pybatfish
            self.pybatfish = pybatfish
            self.pybatfish_instance = bf

        return bf

    def batfish_load_network_config(self, config_text:str, config_name: str = "config_1", snapshot_name: str = "C1" , bf_host: str = "172.16.100.1"):

        with tempfile.TemporaryDirectory() as temp_dir:
            config_subdir = os.path.join(temp_dir, 'configs')
            os.mkdir(config_subdir)

            # Create and write the configuration file
            config_filename = config_name
            config_path = os.path.join(config_subdir, config_filename)
            with open(config_path, 'w') as f:
                f.write(config_text)

            # Initialize Batfish session and snapshot
            # bf = Session(host=bf_host)
            self.pybatfish_instance.init_snapshot(temp_dir, name=snapshot_name, overwrite=True)
        return self.pybatfish_instance.list_snapshots()

    def update_node_and_to_ids(self,
            topology_data: Dict[str, Union[str, List[Dict[str, Union[str, List[Dict[str, str]]]]]]],
            array_to_update: List[Dict[str, List[Dict[str, str]]]]
        ) -> List[Dict[str, List[Dict[str, str]]]]:
        """
        Update 'nodeId' and related 'toId' fields in array_to_update where 'nodeName' matches name.

        Parameters:
            topology_data: Dictionary containing topology information.
            array_to_update: List of dictionaries to update.

        Returns:
            Updated array if new 'nodeId' is found, otherwise the original array.
        """
        copy_array_to_update = copy.deepcopy(array_to_update)
        check_containers = self.generate_topology_hierarchy_ascii_tree(return_structure = True, return_no_ascii = True)
        for entry in copy_array_to_update:
            for data in entry['data']:
                original_node_name = data['nodeName']
                original_node_id = data['nodeId']

                # Use find_container_key to determine new_node_id
                new_node_id = self.find_container_key(topology_data, original_node_name, original_node_id)

                # If new_node_id is different from original_node_id, update it
                if new_node_id != original_node_id:
                    data['nodeId'] = new_node_id

                    # Update 'toId' and 'toName' in all entries where it matches original_node_id
                    for to_entry in copy_array_to_update:
                        for to_data in to_entry['data']:
                            if (to_data['toId'] == original_node_id):                                
                                to_data['toId'] = new_node_id
                                to_data['toName'] = original_node_name

        return copy_array_to_update

    def flatten_model_recursive(self, model: Union[dict, list]) -> List[Union[str, int]]:
        """Flattens the model into a one-dimensional list."""
        flat_list = []

        if isinstance(model, dict):
            for key, value in model.items():
                flat_list.extend(self.flatten_model_recursive(value))

        elif isinstance(model, list):
            for item in model:
                flat_list.extend(self.flatten_model_recursive(item))

        else:
            return [model]

        return flat_list

    def generate_topology_hierarchy_ascii_tree(
        self,
        value_pattern: Optional[str] = None,
        return_structure: bool = False,
        return_no_ascii: bool = False
    ) -> Optional[Union[Dict[str, List[Union[str, Dict[str, Any]]]], List[Dict[str, List[Union[str, Dict[str, Any]]]]]]]:
        """
        Generates an ASCII tree of the topology hierarchy and optionally returns the hierarchy structure.

        Parameters:
        - value_pattern (Optional[str], optional): The value pattern to filter containers. Defaults to None.
        - return_structure (bool, optional): Whether to return the hierarchy structure. Defaults to False.
        - return_no_ascii (bool, optional): Whether to return the hierarchy ASCII structure. Defaults to False.

        Returns:
        - Optional[Union[Dict[str, List[Union[str, Dict[str, Any]]]], List[Dict[str, List[Union[str, Dict[str, Any]]]]]]:
            The hierarchy structure if return_structure is True. None otherwise.
        """
        root_container = self.get_provisioning_filter_topology(value_pattern)
        hierarchy_structure = None
        if return_no_ascii == False:
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
                hierarchy_structure = self._extract_hierarchy_structure(root_container['list'])

        return hierarchy_structure  # Returns None if return_structure is False
    
    def group_devices(self, grouping_key: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Groups devices based on a specified key.

        Parameters:
        - grouping_key (str): The key to group the devices by. Must be 'complianceCode' or 'internalVersion'.

        Returns:
        - Dict[str, List[Dict[str, str]]]: The grouped devices. Each key in the dictionary corresponds to a value of the grouping_key, 
                                           and each value is a list of dictionaries representing the grouped devices.
        """
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
    
    def search_duplicate_lines(self, target_configlet_name: str, exclusion_strings: list, terse: bool = True):
        """
        Searches all configlets for duplicate lines from the target configlet,
        excluding those configlets that contain any of the specified exclusion strings in their name.

        Parameters:
        - target_configlet_name (str): The name of the target configlet whose non-empty lines are to be matched.
        - exclusion_strings (list): A list of strings; configlets containing any of these strings in their name are excluded.
        - terse (bool): A flag passed to the get_configlets_by_regex_match method; defaults to True.

        Returns:
        - list: A list of dictionaries representing the configlets with duplicate lines.
        """
        # Get the target configlet's data by its name
        target_configlet_data = self.get_configlet_by_name(target_configlet_name)["config"]

        # Process the target configlet's data to get a list of non-empty lines,
        # splitting on either '\n' or '\r\n'
        non_empty_lines = [line for line in re.split(r'\n|\r\n', target_configlet_data) if not re.search("(!)", line)]

        # Filter out lines that contain no characters before escaping special characters
        filtered_non_empty_lines = [line for line in non_empty_lines if line.strip()]

        # Escape special characters in each line before attempting regex matching
        escaped_lines = [re.escape(line) for line in filtered_non_empty_lines]

        # Get a list of configlets that match the non-empty lines from the target configlet
        matching_configlets = self.get_configlets_by_regex_match(escaped_lines, terse=terse)

        # Filter out configlets that contain any of the exclusion strings in their name
        filtered_configlets = {target_configlet_name:[configlet for configlet in matching_configlets
                               if not any(exclusion_string in configlet["configlet"] for exclusion_string in exclusion_strings)]}

        return filtered_configlets

    def get_configlets_by_regex_match(self, configlet_search_strings: List[str], readable_only: bool = False, terse: bool = False) -> Union[Dict[str, Any], None]:
        """
        Searches for configlets whose contents match any of the specified regex patterns.

        Parameters:
        - configlet_search_strings (List[str]): The regex patterns to search for within the configlets.
        - readable_only (bool): If True, prints the matched configlets in a readable format instead of returning the data.
        - terse (bool): If True, returns terse details about the matched configlets.

        Returns:
        - The data of matched configlets, or None if `readable_only` is True or no configlets are found.
        """

        configlet_ids = [item[1] for item in self.get_configlet_names_ids()]
        configlet_data = [self.get_configlet_by_id(configlet_id) for configlet_id in configlet_ids]

        results = {}
        for configlet_search_string in configlet_search_strings:
            regex = re.compile(configlet_search_string)
            matches = {
                configlet["name"]: {
                    "config": configlet["config"],
                    "assignment": self.get_configlet_applied_devices([configlet["name"]]),
                    "matched": re.findall(regex, configlet["config"])
                }
                for configlet in configlet_data if re.search(regex, configlet["config"])
            }
            results.update(matches)

        if terse:
            accum_list = [
                {
                    'configlet': configlet_name,
                    'matched': configlet_info['matched'],
                    # 'assignment': [host['hostName'] for device in configlet_info['assignment'] for host in device['data']]
                    'assignment': [host['hostName'] for device in configlet_info['assignment'] for host in device.get('data', [])]

                }
                for configlet_name, configlet_info in results.items()
            ]
            return accum_list

        if readable_only and results:
            self.print_readable(results)
            return None

        return results

    def print_readable(self, results: Dict[str, Any]) -> None:
        pp = pprint.PrettyPrinter(indent=4)
        for configlet_name, configlet_info in results.items():
            print(f"Configlet Name: {configlet_name}")
            pp.pprint(configlet_info["assignment"])
            pp.pprint(configlet_info["matched"])
            print("\n", configlet_info["config"])

    def get_image_bundles(self, start=0, end=0) -> Dict[str, Any]:
        """
        Retrieves a configlet by its ID.

        Parameters:
        - configlet_id (str): The ID of the configlet to retrieve.

        Returns:
        - Dict[str, Any]: The JSON response containing the configlet data.
        """
        endpoint = f'/image/getImageBundles.do?startIndex={start}&endIndex={end}'
        response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        return response.json()

    def get_system_mac_address_by_name(self, regex: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        Filters devices based on a regex pattern matching either the hostname or the system MAC address.

        Parameters:
        - regex (Optional[str], optional): The regex pattern to filter devices. Defaults to None.

        Returns:
        - List[Tuple[str, str]]: A list of tuples, each containing a hostname and system MAC address of a device that matches the regex pattern.
        """
        devices = self.get_inventory_devices()
        result = []

        if regex:
            pattern = re.compile(regex)
            for device in devices:
                hostname = device.get('hostname', '')
                system_mac_address = device.get('systemMacAddress', '')
                if pattern.match(hostname) or pattern.match(system_mac_address):
                    result.append((hostname, system_mac_address))
        else:
            for device in devices:
                result.append((device.get('hostname', ''), device.get('systemMacAddress', '')))

        return result

    def get_configlet_ids_by_name(self, configlet_names: List[str]) -> List[str]:
        """
        Retrieves the IDs of configlets based on their names.

        Parameters:
        - configlet_names (List[str]): The names of the configlets to look up.

        Returns:
        - List[str]: The list of configlet IDs corresponding to the provided names.
        """
        # Assume get_configlet_names_ids() returns a list of tuples where each tuple contains a configlet name and its ID
        all_configlets = self.get_configlet_names_ids()

        # Create a dictionary for faster lookup
        name_to_id_dict = {name: id for name, id in all_configlets}

        # Find and return the IDs corresponding to the provided configlet names
        configlet_ids = [name_to_id_dict.get(name) for name in configlet_names]

        # Optionally, you might want to filter out None values if any configlet name is not found
        configlet_ids = [id for id in configlet_ids if id is not None]

        return configlet_ids

    def get_configlets(self, start_index: int = 0, end_index: int = 2000) -> Tuple[int, Dict[str, Any]]:
        """
        Retrieves a list of configlets.

        Parameters:
        - start_index (int, optional): The starting index of configlets to retrieve. Defaults to 0.
        - end_index (int, optional): The ending index of configlets to retrieve. Defaults to 2000.

        Returns:
        - Tuple[int, Dict[str, Any]]: A tuple containing the status code and the response JSON.
        """
        endpoint = f'/configlet/getConfiglets.do?startIndex={start_index}&endIndex={end_index}'
        response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        return response.status_code, response.json()
    

    def get_configlet_by_name(self, configlet_name: str) -> Union[Dict[str, Any], None]:
        """
        Retrieves a configlet by its name.

        Parameters:
        - configlet_name (str): The name of the configlet to retrieve.

        Returns:
        - Union[Dict[str, Any], None]: The JSON response containing the configlet data, 
                                        or None if the configlet is not found.
        """
        configlet_names_ids = self.get_configlet_names_ids()
        if isinstance(configlet_names_ids, dict):  # Check if the response is an error message
            return configlet_names_ids  # Return the error message
        
        # Find the ID of the configlet with the specified name
        configlet_id = next((id for name, id in configlet_names_ids if name == configlet_name), None)
        if not configlet_id:
            return None  # Configlet not found
        
        # Retrieve and return the configlet data using the found ID
        return self.get_configlet_by_id(configlet_id)

    def get_configlet_names_ids(self, regex: Optional[str] = None) -> Union[Dict[str, Any], List[Tuple[str, str]]]:
        """
        Retrieves a list of configlet names and IDs, optionally filtered by a regex pattern.

        Parameters:
        - regex (Optional[str], optional): The regex pattern to filter configlet names. Defaults to None.

        Returns:
        - Union[Dict[str, Any], List[Tuple[str, str]]]: The list of tuples containing configlet names and IDs, 
                                                        or an error message dictionary if the response is an error message.
        """
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

    def get_configlet_by_id(self, configlet_id: str) -> Dict[str, Any]:
        """
        Retrieves a configlet by its ID.

        Parameters:
        - configlet_id (str): The ID of the configlet to retrieve.

        Returns:
        - Dict[str, Any]: The JSON response containing the configlet data.
        """
        endpoint = f'/configlet/getConfigletById.do?id={configlet_id}'
        response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        return response.json()

    def get_configlet_applied_containers(self, configlet_names: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieves the containers to which specified configlets are applied.

        Parameters:
        - configlet_names (List[str]): The names of the configlets to look up.

        Returns:
        - List[Dict[str, Any]]: A list of dictionaries, each representing the containers a configlet is applied to, along with the configlet name.
        """
        results = []
        for name in configlet_names:
            endpoint = f'/configlet/getAppliedContainers.do?configletName={name}&startIndex=0&endIndex=1000'
            response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)
            error_response = self._check_response(response)
            if error_response:
                return error_response
            response = response.json()
            response["configletName"] = name
            results.append(response)        
        return results

    def get_configlet_applied_devices(self, configlet_names: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieves the devices to which specified configlets are applied.

        Parameters:
        - configlet_names (List[str]): The names of the configlets to look up.

        Returns:
        - List[Dict[str, Any]]: A list of dictionaries, each representing the devices a configlet is applied to, along with the configlet name.
        """
        results = []
        for name in configlet_names:
            endpoint = f'/configlet/getAppliedDevices.do?configletName={name}&startIndex=0&endIndex=1000'
            response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)
            error_response = self._check_response(response)
            if error_response:
                return error_response
            response = response.json()
            response["configletName"] = name
            results.append(response)        
        return results

    def get_tasks(self) -> Dict[str, Any]:
        """
        Retrieves a list of tasks.

        Returns:
        - Dict[str, Any]: The JSON response containing the configlet data.
        """
        endpoint = f'/task/getTasks.do?startIndex=0&endIndex=0'
        response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        return response.json()

    def get_inventory_devices(self, provisioned: bool = False, system_mac_addresses: Optional[List[str]] = None, system_serial_number: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Retrieves a list of inventory devices, optionally filtered by their provisioning status and/or system MAC addresses.

        Parameters:
        - provisioned (bool, optional): Whether to filter devices by their provisioning status. Defaults to False.
        - system_mac_addresses (Optional[List[str]], optional): The list of system MAC addresses to filter devices. Defaults to None.
        - system_serial_number (Optional[List[str]], optional): The list of system Serial Numbers to filter devices. Defaults to None.

        Returns:
        - List[Dict[str, Any]]: A list of dictionaries, each representing a device.
        """
        endpoint = f'/inventory/devices?provisioned={provisioned}'
        response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        devices = response.json()

        if system_mac_addresses:
            devices = [device for device in devices if device.get('systemMacAddress') in system_mac_addresses]
            
        if system_serial_number:
            devices = [device for device in devices if device.get('serialNumber') in system_serial_number]

        return devices

    def get_device_configlets(self, mac_address: Optional[str] = None, process_all: bool = False) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Retrieves configlets associated with a device or all devices.

        Parameters:
        - mac_address (Optional[str], optional): The MAC address of the device to retrieve configlets for. Defaults to None.
        - process_all (bool, optional): Whether to retrieve configlets for all devices. Defaults to False.

        Returns:
        - Union[Dict[str, Any], List[Dict[str, Any]]]: If process_all is True, returns a dictionary containing devices with and without configlets.
                                                       If process_all is False, returns a list of configlets associated with the specified device.
        """
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
            response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)
            error_response = self._check_response(response)
            if error_response:
                return error_response
            return response.json()

    def get_inventory_device_config(self, mac_address: str) -> Dict[str, Any]:
        """
        Retrieves the configuration of a device from inventory based on its MAC address.

        Parameters:
        - mac_address (str): The MAC address of the device to retrieve the configuration for.

        Returns:
        - Dict[str, Any]: The JSON response containing the device configuration.
        """
        endpoint = f'/inventory/device/config?netElementId={mac_address}'
        response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)

        # No error checking on this method. Would need to debug the response and update check_response method.
        error_response = self._check_response(response)
        if error_response:
            return error_response
        
        return response.json()
    
    def get_inventory_containers(self) -> Dict[str, Any]:
        """
        Retrieves a list of inventory containers.

        Returns:
        - Dict[str, Any]: The JSON response containing the list of inventory containers.
        """
        endpoint = f'/inventory/containers'
        response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)
        
        # No error checking on this method. Would need to debug the response and update check_response method.
        # error_response = self._check_response(response)
        # if error_response:
        #     return error_response
        
        return response.json()

    def get_users_and_groups(self, filter_status: str = "Any") -> Dict[str, Any]:
        """
        Retrieves users and groups, with an optional filter on user status.

        Parameters:
        - filter_status (str, optional): Status filter for users. Defaults to "Any".

        Returns:
        - Dict[str, Any]: The JSON response containing users and groups.
        """
        endpoint = f'/user/getUsers.do?startIndex=0&endIndex=1000'
        response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        json_data = response.json()

        # Filter users based on the 'currentStatus' if specified
        if filter_status != "Any":
            filtered_users = [user for user in json_data.get('users', []) if user.get('currentStatus') == filter_status]
            json_data['users'] = filtered_users
        
        return json_data

    def get_roles(self) -> Dict[str, Any]:
        """
        Retrieves roles.

        Returns:
        - Dict[str, Any]: The JSON response containing roles.
        """
        endpoint = f'/role/getRoles.do?startIndex=0&endIndex=1000'
        response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        json_data = response.json()

        return json_data
    
    def get_cvp_info(self) -> Dict[str, Any]:
        """
        Retrieves CVP (CloudVision Portal) information.

        Returns:
        - Dict[str, Any]: The JSON response containing CVP information.
        """
        endpoint = f'/cvpInfo/getCvpInfo.do'
        response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)
        
        error_response = self._check_response(response)
        if error_response:
            return error_response
        
        return response.json()

    def get_copy_configlet(self, source_configlet_identifiers: List[str], new_names: Optional[List[str]] = None) -> Union[Dict[str, str], List[Dict[str, Any]]]:
        """
        Copies configlets and optionally assigns new names to the copies.

        Parameters:
        - source_configlet_identifiers (List[str]): The identifiers of the source configlets to be copied.
        - new_names (Optional[List[str]], optional): The new names for the copied configlets. Defaults to None.

        Returns:
        - Union[Dict[str, str], List[Dict[str, Any]]]: A list of dictionaries representing the copied configlets, or an error message dictionary.
        """
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
            response = self.session.post(self.host_url + self.path + endpoint, headers=self.headers, json=body)

            error_response = self._check_response(response)
            if error_response:
                return error_response

            copied_configlets.append(response.json())

        return copied_configlets

    def get_applied_configlets_per_container(self) -> List[List[str]]:
        """
        Retrieves a list of applied configlets for each container.

        Returns:
        - List[List[str]]: A list where each element is a list containing a container name and its applied configlets.
        """
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

    def post_create_config_diff(self, device_id: str, output_diff: bool = False, output_config: bool = False) -> dict:
        """
        Generates a configuration diff for a specific device in the CVaaS (CloudVision as a Service) platform.

        Args:
            device_id (str): The unique identifier of the device for which the configuration diff is required.
            output_diff (bool): If True, prints the detailed configuration diff in a structured format.
            output_config (bool): If True, prints the configuration lines that would be applied to the device.

        Returns:
            dict: A JSON response from the server containing the configuration difference between
                the designed (intended) configuration and the running configuration.
                The response includes information regarding the differences in configuration.

        Raises:
            Exception: If an error occurs during the request or if the response indicates a failure.
        """
        endpoint = "/api/v3/services/compliancecheck.Compliance/GetConfigDiff"
        body = {
            "lhs": {"device_id": device_id, "type": "DESIGNED_CONFIG"},
            "rhs": {"device_id": device_id, "type": "RUNNING_CONFIG"}
        }

        try:
            response = self.session.post(self.host_url + endpoint, headers=self.headers, json=body)
            response.raise_for_status()  # Raises an HTTPError if the response status is 4xx or 5xx

            # Assuming `_check_response` is a custom method to parse and raise appropriate errors
            error_response = self._check_response(response)
            if error_response:
                return error_response

            response_data = response.json()

            # Corrected: Access the diff entries using the response data structure you've shared
            if len(response_data) > 1 and 'diff' in response_data[1]:
                diff_entries = response_data[1]['diff'].get('entries', [])
            else:
                diff_entries = []

            # Output detailed diff if requested
            if output_diff:
                print(f"!Detailed Diff for Device {device_id}")
                for i in diff_entries:
                    if 'CHANGE' in i['op']:
                        print(f"(CH) {i['a_lineno']} {i['a_line']:<25}".ljust(50) +
                            f"{i['b_lineno']:>25}{i['b_line']:<25}".ljust(12))
                    elif 'DELETE' in i['op']:
                        print(f"(-) {i['b_lineno']} {i['b_line']:<25}")
                    elif 'ADD' in i['op']:
                        print(f"(+) {i['a_lineno']} {i['a_line']:<25}")

            # Output configuration to be applied if requested
            if output_config:
                printed_parents = list()  # Track parent line numbers that have already been printed
                print(f"\n!Configuration to be Applied to Device {device_id}:")
                for i in diff_entries:
                    if 'CHANGE' in i['op']:
                        if i['a_parent_lineno'] != -1:
                            # print(f"{diff_entries[i['a_parent_lineno']]['a_line']}")
                            printed_parents.append(f"{diff_entries[i['a_parent_lineno']]['a_line']}")
                        # Print the new line that replaces the old one
                        # print(f"{i['a_line']}")
                        printed_parents.append(f"{i['a_line']}")
                    elif 'ADD' in i['op']:
                        if i['a_parent_lineno'] != -1:
                            printed_parents.append(f"{diff_entries[i['a_parent_lineno']]['a_line']}")
                        # Print the added line
                        printed_parents.append(f"{i['a_line']}")
                    # Note: Deletions are typically not part of the configuration that is "applied"
                    #       but are instead removed, so they are not included in this section.
                print("\n".join(printed_parents))


            return response_data

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create configuration diff for device {device_id}: {e}")

    def post_create_configlet(self, cvaas_config: dict, cvaas_configlet_name: str) -> dict:
        """
        Creates a new configlet in the CVaaS (Cloud Vision as a Service) platform.

        Args:
            cvaas_config (dict): The configuration details for the new configlet.
                This should contain all necessary information needed to create the configlet.
            cvaas_configlet_name (str): The name to assign to the new configlet. Should be unique.

        Returns:
            dict: A JSON response from the server containing details of the created configlet.
                The response includes information such as the configlet ID, name, and any
                other metadata associated with the new configlet.

        Raises:
            Exception: If an error occurs during the request or the response indicates a failure.
        """
        endpoint = '/configlet/addConfiglet.do'
        body = {
            'config': cvaas_config,
            'name': cvaas_configlet_name
        }

        response = self.session.post(self.host_url + self.path + endpoint, headers=self.headers, json=body)

        # Assuming `_check_response` is a method that checks the response for errors
        error_response = self._check_response(response)
        if error_response:
            return error_response

        return response.json()

    def post_append_configlet(self, source_configlet_identifier: str, target_configlet_identifier: str) -> Union[Dict[str, str], Dict[str, Any]]:
        """
        Appends the configuration of a source configlet to a target configlet.

        Parameters:
        - source_configlet_identifier (str): The identifier of the source configlet.
        - target_configlet_identifier (str): The identifier of the target configlet.

        Returns:
        - Union[Dict[str, str], Dict[str, Any]]: The JSON response containing the updated configlet details or an error message.
        """
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
        response = self.session.post(self.host_url + self.path + endpoint, headers=self.headers, json=body)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        return response.json()
    
    def post_get_device_managment_ip_addresses(self, device_id: str,configlets: List[Dict[str, Any]]) -> Union[Dict[str, str], Dict[str, Any]]:
        """
        This API is used to get a list of management IPs from Designed config

        Parameters:
        - container_id (str): The ID of the container.
        - configlets (List[Dict[str, Any]]): A list of configlets to be assigned.

        Returns:
        - Union[Dict[str, str], Dict[str, Any]]: The JSON response containing managment IP Addresses from configlets, and default Proposed Management Ip.
        """

        # Update the target configlet with the appended configuration
        endpoint = '/configlet/getManagementIp.do?startIndex=0&endIndex=0'

        body = {
          "configIdList": configlets,
          "netElementId": device_id,
          "pageType": "validatePage"
        }
        response = self.session.post(self.host_url + self.path + endpoint, headers=self.headers, json=body)

        error_response = self._check_response(response)
        if error_response:
            return error_response

        return response.json()

    def post_assign_image_to_device(self, device_id: str, node_ip_address: str, image= dict, id_type= 'netelement')  -> Union[Dict[str, str], Dict[str, Any]]:
        """
        Assigns an EOS image to a device.

        Parameters:
        - device_id (str): The ID of the device (System MAC Address).
        - node_ip_address(str): The Management IP address as seen in CVAAS.

        Returns:
        - Union[Dict[str, str], Dict[str, Any]]: The JSON response or an error message.
        """
        # remove ignore_list from configlets
        info = f"Apply image: {image['name']} to {id_type} {device_id}"
        node_id = image['imageBundleKeys'][0]
        post_data = [{'data': [{'info': info,
                        'infoPreview': info,
                        'note': '',
                        'action': 'associate',
                        'nodeType': 'imagebundle',
                        'nodeId': node_id,
                        'toId': device_id,
                        'toIdType': id_type,
                        'fromId': '',
                        'nodeName': image['name'],
                        'fromName': '',
                        'toName': '',
                        'childTasks': [],
                        'parentTask': ''}]}
]
        return self.post_provisioning_add_temp_actions(data_list=post_data)

    def post_assign_configlets_to_container(self, container_id: str, configlets: List[Dict[str, Any]], ignore_list: List[Dict[str, Any]] = []) -> Union[Dict[str, str], Dict[str, Any]]:
        """
        Assigns a list of configlets to a device.

        Parameters:
        - container_id (str): The ID of the container.
        - configlets (List[Dict[str, Any]]): A list of configlets to be assigned.
        - ignore_list (List[Dict[str, Any]]): A list of configlets to be ignored and removed from configlets.

        Returns:
        - Union[Dict[str, str], Dict[str, Any]]: The JSON response or an error message.
        """
        # remove ignore_list from configlets
        configlets = [x for x in configlets if x not in ignore_list]
        post_data = [{'data': [{'action': 'associate',
           'configletBuilderList': [],
           'configletBuilderNamesList': [],
           'configletList': configlets,
           'fromId': '',
           'fromName': '',
           'ignoreConfigletBuilderList': [],
           'ignoreConfigletBuilderNamesList': [],
           'ignoreConfigletList': ignore_list,
           'ignoreConfigletNamesList': [],
           'nodeId': '',
           'nodeName': '',
           'nodeType': 'configlet',
           'toId': container_id,
           'toIdType': 'container'}]}]
        return self.post_provisioning_add_temp_actions(data_list=post_data)
    
    def post_assign_configlets_to_device(self, device_id: str, node_ip_address: str, configlets: List[Dict[str, Any]], ignore_list: List[Dict[str, Any]] = [])  -> Union[Dict[str, str], Dict[str, Any]]:
        """
        Assigns a list of configlets to a device.

        Parameters:
        - device_id (str): The ID of the device (System MAC Address).
        - node_ip_address(str): The Management IP address as seen in CVAAS.
        - configlets (List[Dict[str, Any]]): A list of configlets to be assigned.
        - ignore_list (List[Dict[str, Any]]): A list of configlets to be ignored and removed from configlets.

        Returns:
        - Union[Dict[str, str], Dict[str, Any]]: The JSON response or an error message.
        """
        # remove ignore_list from configlets
        configlets = [x for x in configlets if x not in ignore_list]
        post_data = [{'data': [{'action': 'associate',
           'configletBuilderList': [],
           'configletBuilderNamesList': [],
           'configletList': configlets,
           'fromId': '',
           'fromName': '',
           'ignoreConfigletBuilderList': [],
           'ignoreConfigletBuilderNamesList': [],
           'ignoreConfigletList': ignore_list,
           'ignoreConfigletNamesList': [],
           'nodeId': '',
           'nodeName': '',
           'nodeTargetIpAddress': node_ip_address,                     
           'nodeType': 'configlet',
           'toId': device_id,
           'toIdType': 'netelement'}]}]
        return self.post_provisioning_add_temp_actions(data_list=post_data)

    def post_provisioning_save_temp_actions(self, data: Dict[str, Any]) -> Union[Dict[str, str], Dict[str, Any]]:
        """
        Sends a POST request to save temporary provisioning actions.
        
        Parameters:
        - data (Dict[str, Any]): The data to be sent in the POST request.
        
        Returns:
        - Union[Dict[str, str], Dict[str, Any]]: Error message or JSON response from the server.
        """
        endpoint = f'/ztp/saveTopology.do'
        response = self.session.post(self.host_url + self.path + endpoint, headers=self.headers, data=json.dumps(data))
        error_response = self._check_response(response)
        if error_response:
            return error_response
        return response.json()
    
    def post_provisioning_add_temp_actions(self, data_list: List[Dict[str, Any]], nodeId: str = "root") -> List[Union[Dict[str, str], Dict[str, Any]]]:
        """
        Sends multiple POST requests to add temporary provisioning actions.
        
        Parameters:
        - data_list (List[Dict[str, Any]]): The list of data to be sent in each POST request.
        - nodeId (str): The node ID for the request, defaults to "root".
        
        Returns:
        - List[Union[Dict[str, str], Dict[str, Any]]]: List of error messages or JSON responses from the server.
        """
        results = []
        for data in data_list:
            endpoint = f'/ztp/addTempAction.do?format=list&queryParam=&nodeId={nodeId}'
            response = self.session.post(self.host_url + self.path + endpoint, headers=self.headers, data=json.dumps(data))
            error_response = self._check_response(response)
            if error_response:
                results.append({'error': error_response})
            else:
                results.append(response.json())
        return results
    
    def get_provisioning_temp_actions(self) -> Union[Dict[str, str], Dict[str, Any]]:
        """
        Sends a GET request to retrieve all temporary provisioning actions.
        
        Returns:
        - Union[Dict[str, str], Dict[str, Any]]: Error message or JSON response from the server.
        """
        endpoint = f'/ztp/getAllTempActions.do?startIndex=0&endIndex=1000'
        response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)
        error_response = self._check_response(response)
        if error_response:
            return error_response
        return response.json()
    
    def get_provisioning_filter_topology(self, value_pattern: Optional[str] = None) -> Union[Dict[str, str], Dict[str, Any]]:
        """
        Sends a GET request to retrieve provisioning filter topology.
        
        Parameters:
        - value_pattern (Optional[str]): A pattern to filter the response data, defaults to None.
        
        Returns:
        - Union[Dict[str, str], Dict[str, Any]]: Error message or JSON response from the server.
        """
        endpoint = f'/provisioning/v3/filterTopology.do?queryParam=a&format=list&startIndex=0&endIndex=1000'
        response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)
        error_response = self._check_response(response)
        if error_response:
            return error_response
        response_data = response.json()
        if value_pattern:
            return self._find_matching_dicts(response_data, value_pattern)
        else:
            return response_data

    def delete_provisioning_temp_action_all(self, value_pattern: Optional[str] = None) -> Union[Dict[str, str], Dict[str, Any]]:
        """
        Sends a DELETE request to remove all temporary provisioning actions.
        
        Parameters:
        - value_pattern (Optional[str]): A pattern to filter the response data, defaults to None.
        
        Returns:
        - Union[Dict[str, str], Dict[str, Any]]: Error message or JSON response from the server.
        """
        endpoint = f'/provisioning/deleteAllTempAction.do'
        response = self.session.delete(self.host_url + self.path + endpoint, headers=self.headers)
        error_response = self._check_response(response)
        if error_response:
            return error_response
        response_data = response.json()
        if value_pattern:
            return self._find_matching_dicts(response_data, value_pattern)
        else:
            return response_data

    def get_service_accounts(self) -> Union[Dict[str, str], Dict[str, Any]]:
        """
        Sends a GET request to retrieve all service accounts.
        
        Returns:
        - Union[Dict[str, str], Dict[str, Any]]: Error message or JSON response from the server.
        """
        endpoint = f'/arista.serviceaccount.v1.TokenService/GetAll'
        response = self.session.get(self.host_url + self.path + endpoint, headers=self.headers)
        error_response = self._check_response(response)
        if error_response:
            return error_response
        return response.json()
    
    def get_container_ids_by_name(self, container_names: Union[str, List[str]]) -> List[Optional[str]]:
        """
        Retrieves the container IDs corresponding to the specified container names.
        
        Parameters:
        - container_names (Union[str, List[str]]): The name(s) of the container(s) whose IDs are to be retrieved.
        
        Returns:
        - List[Optional[str]]: A list of container IDs corresponding to the specified container names.
        """
        # Ensure the input is a list, even if it's a single string
        if not isinstance(container_names, list):
            container_names = [container_names]
        
        # Assume get_provisioning_filter_topology() returns the topology data
        topology_data = self.get_provisioning_filter_topology()
        
        # Recursively search for the container ID based on the container name
        def search_container(containers_list: List[Dict[str, Any]], name: str) -> Optional[str]:
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
