# Baraza Core Banking API Integration Middleware

An enterprise-grade, serverless cloud integration middleware designed to handle real-time mobile payment callbacks (e.g., M-Pesa), enforce API idempotency, and asynchronously post ledger updates to core banking backends.

Built on **Microsoft Azure**, this repository provides a full Infrastructure-as-Code (IaC) setup and a Python Azure Function processing pipeline.

---

##  Architecture Overview - By Andrew Mwangi
[ Mobile Gateway / Web ]
│ (HTTP POST /v1/payments/callback)
▼
[ Azure Function App (HTTP Ingress) ]
│ (Schema Validation & Standardization)
▼
[ Azure Service Bus Queue ] ◄── (Idempotency / Duplicate Detection Window: 10m)
│
▼
[ Azure Function App (Queue Trigger) ]
│
▼
[ Core Banking Ledger / Database ]
### Key Architectural Characteristics
* **Asynchronous Decoupling:** Returns `202 Accepted` immediately upon payload validation to prevent gateway timeouts during peak loads.
* **Two-Layer Idempotency:** Duplicate payload prevention executed via Azure Service Bus `requires_duplicate_detection` and backend database-level unique constraint checks.
* **Resilience & Fault Tolerance:** Configured with a max delivery count of 3 retries before dead-lettering (`DLQ`) unprocessable messages.
* **Least Privilege Governance:** Managed Identities enabled for secure, keyless Azure service-to-service communication.

---

## Tech Stack

* **Cloud Provider:** Microsoft Azure
* **Infrastructure as Code:** Terraform (>= 1.5.0)
* **Runtime:** Python 3.11 (Azure Functions v2 Programming Model)
* **Messaging & Queuing:** Azure Service Bus
* **Identity & Access:** Microsoft Entra ID (Managed Identities)

---

##  Quickstart & Local Setup

### Prerequisites
* [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
* [Terraform](https://www.terraform.io/downloads)
* [Azure Functions Core Tools v4](https://github.com/Azure/azure-functions-core-tools)
* Python 3.11+

### 1. Provision Infrastructure
```bash
cd terraform
terraform init
terraform plan
terraform apply

2. Run Functions Locally
Bash


cd ../src
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
func start
🧪 API Specification
Endpoint: Process Payment Callback
Method: POST

Path: /api/v1/payments/callback

Headers: Content-Type: application/json

Sample Request Body
JSON


{
  "transaction_id": "TXN_987654321",
  "account_number": "ACC-100203",
  "amount": 1500.00,
  "currency": "KES",
  "provider": "MOBILE_MONEY"
}
Sample Response (202 Accepted)
JSON


{
  "status": "ACCEPTED",
  "message": "Payment callback received and queued for processing.",
  "transaction_id": "TXN_987654321"
}

---

### Step 9: Commit the README

Run these commands in your terminal to complete the repository update:

```bash
git add README.md
git commit -m "docs: Add architecture overview and setup guide to README"
git push origin main