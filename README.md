# Sentiment Analysis Function App

A serverless application using Azure Functions to perform real-time sentiment analysis on text messages with interactive visualization. The application uses TextBlob for sentiment analysis and provides a real-time dashboard for monitoring sentiment trends.

## Prerequisites

Before running this application locally, ensure you have the following installed:

### Required Software
- Python 3.9 or later
- [Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local) version 4.x
- [Azurite](https://github.com/Azure/Azurite) for local Azure Storage emulation
- [Visual Studio Code](https://code.visualstudio.com/) (recommended)
- [Azure Functions extension for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions)

### Azure Requirements
- An Azure account with an active subscription
- Azure Functions resource
- Azure Storage account
- Azure Application Insights (optional, for monitoring)

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd sentiment-analysis-function
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/MacOS
python -m venv .venv
source .venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Local Development Setup

1. Start Azurite for local storage emulation:
```bash
# Using npm
npm install -g azurite
azurite --silent --location c:\azurite --debug c:\azurite\debug.log

# Or using Docker
docker run -p 10000:10000 -p 10001:10001 -p 10002:10002 mcr.microsoft.com/azure-storage/azurite
```

2. Create a `local.settings.json` file in your project root:
```json
{
    "IsEncrypted": false,
    "Values": {
        "AzureWebJobsStorage": "UseDevelopmentStorage=true",
        "FUNCTIONS_WORKER_RUNTIME": "python",
        "AZURE_STORAGE_CONNECTION_STRING": "UseDevelopmentStorage=true"
    }
}
```

3. Configure VS Code Azure Functions extension:
   - Install the Azure Functions extension
   - Sign in to your Azure account
   - Select your subscription

## Running the Application Locally

1. Start the function app:
```bash
func start
```

2. The following endpoints will be available:
   - `http://localhost:7071/api/get_messages` - Submit text for analysis
   - `http://localhost:7071/api/view_visualization` - View sentiment analysis dashboard

## Testing the Application

1. Submit a message for analysis:
```bash
# Using curl
curl -X POST http://localhost:7071/api/get_messages -H "Content-Type: application/json" -d "{\"text\": \"This is a test message\"}"

# Using PowerShell
Invoke-WebRequest -Uri "http://localhost:7071/api/get_messages" -Method POST -Body "{\"text\": \"This is a test message\"}" -ContentType "application/json"
```

2. Open your browser and navigate to:
```
http://localhost:7071/api/view_visualization
```

## Project Structure
```
sentiment-analysis-function/
├── function_app.py         # Main function app code
├── requirements.txt        # Python dependencies
├── host.json              # Function host configuration
├── local.settings.json    # Local settings (not in source control)
└── README.md             # This file
```

## Dependencies
Check requirements.txt for full list:
```
azure-functions>=1.17.0
textblob>=0.17.1
matplotlib>=3.5.0
pandas>=1.3.0
azure-storage-blob>=12.24.0
```

## Deployment

1. Create required Azure resources:
   - Azure Function App
   - Azure Storage Account
   - Application Insights (optional)

2. Deploy using VS Code:
   - Right-click on the project folder
   - Select "Deploy to Function App..."
   - Follow the prompts

3. Or deploy using Azure Functions Core Tools:
```bash
func azure functionapp publish <FunctionAppName>
```

## Monitoring

- Use Azure Portal to monitor function execution
- Check Application Insights for detailed telemetry
- View logs using:
```bash
func logs
```

## Common Issues and Troubleshooting

1. Azurite Connection Issues:
```bash
# Check if Azurite is running
netstat -ano | findstr "10000"
netstat -ano | findstr "10001"
netstat -ano | findstr "10002"
```

2. Python Version Conflicts:
```bash
# Verify Python version
python --version

# Should be 3.9 or later
```

## Acknowledgments

- TextBlob for sentiment analysis
- Azure Functions team for the serverless platform
- Matplotlib for visualization capabilities

## Support

For support, please open an issue in the GitHub repository
