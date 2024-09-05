
# The BIG-IP REST Data Fetcher

This script fetches data from BIG-IP Classic REST endpoints based on IP addresses or network ranges. It saves the fetched data to YAML files for further analysis.

## Features

- Fetch data from BIG-IP REST endpoints using single IPs, ranges in CIDR notation, or from a list of IPs in a file.
- Saves the responses in YAML format for easy reading and further processing.
- Supports concurrent fetching with multiple threads to speed up the data retrieval process.
- Configurable timeout for API requests.
- Automatically displays help information if no arguments are provided.

## Requirements

- Python 3.6+
- Required Python packages:
  - `requests`
  - `PyYAML`

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/thejerrod/fetch.git
   cd fetch
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

You can run the script with different options to specify how to fetch data from endpoints.

### Fetch from a Single IP or Network Range

Use the `--ip_input` argument to specify a single IP address or a range in CIDR format.

```bash
python fetch.py --ip_input 192.168.1.0/24
```

### Fetch from a File with IP Addresses

Use the `--ip_file` argument to provide a text file containing a list of IP addresses, one per line.

```bash
python fetch.py --ip_file ips.txt
```

### Timeout Configuration

You can adjust the timeout for each API request using the `--timeout` argument (default is 3 seconds).

```bash
python fetch.py --ip_input 192.168.1.1 --timeout 5
```

### Display Help Information

If no arguments are provided, the script will display the help message with usage examples:

```bash
python fetch.py
```

## Command-Line Arguments

- `--ip_input`: Single IP address or IP range in CIDR format (e.g., `192.168.1.0/24`).
- `--ip_file`: Text file containing a list of IP addresses, one per line.
- `--timeout`: Timeout for the API request in seconds (default is 3 seconds).

## How It Works

1. The script identifies the IPs to be processed based on your input.
2. It fetches data from predefined endpoints on each IP address.
3. Responses are saved to YAML files named `response_<ip_address>.yaml`.
4. Logs indicate the success, failure, or timeout status of each request.

## Example Endpoints

The script is pre-configured to fetch data from the following endpoints:

- Health Summary Endpoint: `https://<ip_address>:8888/restconf/data/openconfig-system:system/f5-system-health:health/f5-system-health:summary/f5-system-health:components`
- Hardware Info Endpoint: `https://<ip_address>:443/mgmt/tm/sys/hardware`

## Logging

The script logs all activities, including successful connections, errors, and timeouts, to the console.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## Disclaimer

This script is for informational and educational purposes only. Use it responsibly and ensure you have permission to access the targeted devices.
