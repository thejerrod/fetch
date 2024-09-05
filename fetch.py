import os
import requests
import yaml
import argparse
import ipaddress
import logging
from concurrent.futures import ThreadPoolExecutor
 
logging.basicConfig(level=logging.INFO, format='%(message)s')
 
def fetch_data(ip_address, endpoints, timeout):
    file_path = f"response_{ip_address}.yaml"
    if not os.path.exists(file_path):
        print(f"New device detected: {ip_address}")
 
    for endpoint in endpoints:
        try:
            response = requests.get(
                endpoint["url"].format(ip_address),
                headers=endpoint["headers"],
                auth=("admin", "admin"),
                verify=False,
                timeout=timeout
            )
            if response.status_code == 200:
                print(f"Success: {ip_address} on port {endpoint['port']}")
                save_response(ip_address, response.json())
                return
            else:
                print(f"Failed: {ip_address} on port {endpoint['port']} (HTTP {response.status_code})")
        except requests.exceptions.Timeout:
            print(f"Timeout: {ip_address} on port {endpoint['port']}")
        except requests.exceptions.RequestException:
            print(f"Error: {ip_address} on port {endpoint['port']}")
 
def save_response(ip_address, json_data):
    file_path = f"response_{ip_address}.yaml"
    with open(file_path, "w") as yaml_file:
        yaml.dump(json_data, yaml_file)
 
def read_ip_file(filename):
    with open(filename, 'r') as f:
        ips = f.read().splitlines()
    print(f"Reading from file {filename}. Found {len(ips)} IP addresses.")
    return ips
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="This script fetches data from BIG-IP Classic REST endpoints, based on IP or Network range. It saves the output it finds to <ip_address>.yml")
    parser.add_argument("--ip_input", type=str, help="Single IP address or IP range in CIDR format (e.g., 192.168.1.0/24)")
    parser.add_argument("--ip_file", type=str, help="Text file containing a list of IP addresses, one per line.")
    parser.add_argument("--timeout", type=int, default=3, help="Timeout for the API request in seconds.")
    args = parser.parse_args()
 
    if not any(vars(args).values()):
        parser.print_help()
        exit(0)
 
    print("Running script to fetch data from API endpoints.")
    print(f"Options chosen: Timeout = {args.timeout} seconds")
 
    endpoints = [
        {
            "url": "https://{}:8888/restconf/data/openconfig-system:system/f5-system-health:health/f5-system-health:summary/f5-system-health:components",
            "headers": {"Content-Type": "application/yang-data+json"},
            "port": 8888
        },
        {
            "url": "https://{}:443/mgmt/tm/sys/hardware",
            "headers": {"Content-Type": "application/json"},
            "port": 443
        }
    ]
 
    if args.ip_input:
        print(f"Fetching data for IP(s) from command line input: {args.ip_input}")
        try:
            ip_single = ipaddress.IPv4Address(args.ip_input)
            fetch_data(str(ip_single), endpoints, args.timeout)
        except ipaddress.AddressValueError:
            try:
                ip_network = ipaddress.IPv4Network(args.ip_input, strict=False)
                with ThreadPoolExecutor() as executor:
                    executor.map(lambda ip: fetch_data(str(ip), endpoints, args.timeout), ip_network.hosts())
            except ValueError:
                print("Invalid IP or IP range provided.")
 
    if args.ip_file:
        ips = read_ip_file(args.ip_file)
        with ThreadPoolExecutor() as executor:
            executor.map(lambda ip: fetch_data(ip, endpoints, args.timeout), ips)
