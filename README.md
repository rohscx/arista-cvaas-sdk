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

For example purposes, refer to the `examples` directory in this repository, or review the methods available in the `arista_cvaas_sdk.py` file.

## Contribution

Feel free to clone the repository, create a new branch, make changes, and submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
