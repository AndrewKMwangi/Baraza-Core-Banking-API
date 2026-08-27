terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "prefix" {
  default     = "baraza-cb"
  description = "Prefix for all Azure resources"
}

variable "location" {
  default     = "East Africa" # Or your preferred location (e.g., East US)
}

# 1. Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "rg-${var.prefix}-prod"
  location = var.location
}

# 2. Azure Service Bus (Messaging Ingress)
resource "azurerm_servicebus_namespace" "sb_namespace" {
  name                = "sb-${var.prefix}-ns"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "Standard"
}

# Service Bus Queue with Duplicate Detection (Idempotency)
resource "azurerm_servicebus_queue" "payment_queue" {
  name                                    = "mobile-payment-callbacks"
  namespace_id                            = azurerm_servicebus_namespace.sb_namespace.id
  requires_duplicate_detection            = true
  duplicate_detection_history_time_window = "PT10M" # 10-minute duplicate window
  max_delivery_count                      = 3      # Move to Dead-Letter Queue (DLQ) after 3 failures
}

# 3. Storage Account for Azure Function
resource "azurerm_storage_account" "sa" {
  name                     = "st${var.prefix}appdata"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# Service Plan (Consumption Plan for serverless scaling)
resource "azurerm_service_plan" "asp" {
  name                = "asp-${var.prefix}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "Y1"
}

# 4. Azure Function App (Python Runtime)
resource "azurerm_linux_function_app" "function_app" {
  name                = "func-${var.prefix}-api"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  storage_account_name       = azurerm_storage_account.sa.name
  storage_account_access_key = azurerm_storage_account.sa.primary_access_key
  service_plan_id            = azurerm_service_plan.asp.id

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "ServiceBusConnection"     = azurerm_servicebus_namespace.sb_namespace.default_primary_connection_string
  }

  # Enable System-Assigned Managed Identity
  identity {
    type = "SystemAssigned"
  }
}