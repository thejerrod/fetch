import os
import requests
import yaml
import argparse
import ipaddress
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_data(ip_address: str, endpoints: list, timeout: int, output: str) -> None:
    """
    Fetch data from the given endpoints for a specified IP address.

    Args:
        ip_address (str): The IP address to fetch data from.
        endpoints (list): List of endpoints to query.
        timeout (int): Timeout for the requests in seconds.
        output (str): Output type, either 'file' or 'stdout'.
    """
    file_path = f"response_{ip_address}.yaml"
    is_new_device = not os.path.exists(file_path)
    if is_new_device:
        logging.info(f"New device detected: {ip_address}")

    for endpoint in endpoints:
        try:
            response = requests.get(
                endpoint["url"].format(ip_address),
                headers=endpoint["headers"],
                auth=("admin", "admin"),  # Consider securing these credentials
                verify=False,
                timeout=timeout
            )
            if response.status_code == 200:
                logging.info(f"Success: {ip_address} on port {endpoint['port']}")
                response_data = response.json()
                if output == 'file':
                    save_response(ip_address, response_data)
                else:
                    display_response(ip_address, response_data)
                return
            else:
                logging.warning(f"Failed: {ip_address} on port {endpoint['port']} (HTTP {response.status_code})")
        except requests.exceptions.Timeout:
            logging.error(f"Timeout: {ip_address} on port {endpoint['port']}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error: {ip_address} on port {endpoint['port']} - {e}")

def save_response(ip_address: str, json_data: dict) -> None:
    """
    Save the response data to a YAML file.

    Args:
        ip_address (str): The IP address associated with the response.
        json_data (dict): The JSON data to save.
    """
    file_path = f"response_{ip_address}.yaml"
    with open(file_path, "w") as yaml_file:
        yaml.dump(json_data, yaml_file)
    logging.info(f"Response saved to {file_path}")

def display_response(ip_address: str, json_data: dict) -> None:
    """
    Display the response data in a human-readable format to stdout.

    Args:
        ip_address (str): The IP address associated with the response.
        json_data (dict): The JSON data to display.
    """
    print(f"\n--- Response for {ip_address} ---")
    print(json.dumps(json_data, indent=4))  # Convert JSON to pretty-printed string

def read_ip_file(filename: str) -> list:
    """
    Read IP addresses from a file.

    Args:
        filename (str): Path to the file containing IP addresses.

    Returns:
        list: List of IP addresses.
    """
    with open(filename, 'r') as f:
        ips = f.read().splitlines()
    logging.info(f"Reading from file {filename}. Found {len(ips)} IP addresses.")
    return ips

def process_ip_input(ip_input: str, endpoints: list, timeout: int, output: str) -> None:
    """
    Process single IP or CIDR range input.

    Args:
        ip_input (str): Single IP address or IP range in CIDR format.
        endpoints (list): List of endpoints to query.
        timeout (int): Timeout for the requests in seconds.
        output (str): Output type, either 'file' or 'stdout'.
    """
    try:
        ip_single = ipaddress.IPv4Address(ip_input)
        fetch_data(str(ip_single), endpoints, timeout, output)
    except ipaddress.AddressValueError:
        try:
            ip_network = ipaddress.IPv4Network(ip_input, strict=False)
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(fetch_data, str(ip), endpoints, timeout, output) for ip in ip_network.hosts()]
                for future in as_completed(futures):
                    future.result()  # handle individual exceptions if needed
        except ValueError:
            logging.error("Invalid IP or IP range provided.")

def main():
    parser = argparse.ArgumentParser(
        description="Fetch data from BIG-IP REST endpoints based on IP or Network range.",
        epilog="Example usage:\n"
               "  python fetch.py --ip_input 192.168.1.0/24 --output file\n"
               "  python fetch.py --ip_file ips.txt --output stdout\n",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--ip_input", type=str, help="Single IP address or IP range in CIDR format (e.g., 192.168.1.0/24)")
    parser.add_argument("--ip_file", type=str, help="Text file containing a list of IP addresses, one per line.")
    parser.add_argument("--timeout", type=int, default=3, help="Timeout for the API request in seconds.")
    parser.add_argument("--output", type=str, choices=['file', 'stdout'], default='stdout',
                        help="Output type: 'stdout' to print responses (default), 'file' to save responses to files.")
    args = parser.parse_args()

    # Explicitly check if neither IP input nor IP file is provided
    if not args.ip_input and not args.ip_file:
        parser.print_help()
        exit(0)

    logging.info("Running script to fetch data from API endpoints.")
    logging.info(f"Options chosen: Timeout = {args.timeout} seconds, Output = {args.output}")

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
        logging.info(f"Fetching data for IP(s) from command line input: {args.ip_input}")
        process_ip_input(args.ip_input, endpoints, args.timeout, args.output)

    if args.ip_file:
        ips = read_ip_file(args.ip_file)
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(fetch_data, ip, endpoints, args.timeout, args.output) for ip in ips]
            for future in as_completed(futures):
                future.result()  # handle individual exceptions if needed

if __name__ == "__main__":
    main()
