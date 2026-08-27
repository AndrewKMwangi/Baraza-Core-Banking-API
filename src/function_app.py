import json
import logging
import os
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="ProcessMobilePayment")
@app.route(route="v1/payments/callback", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
@app.service_bus_queue_output(
    arg_name="msg",
    queue_name="mobile-payment-callbacks",
    connection="ServiceBusConnection"
)
def process_mobile_payment(req: func.HttpRequest, msg: func.Out[str]) -> func.HttpResponse:
    """
    HTTP Ingress Trigger: Receives mobile payment callbacks (e.g., M-Pesa),
    validates transaction schema, and decouples execution by writing to Service Bus.
    """
    logging.info("Processing incoming mobile payment callback.")

    try:
        req_body = req.get_json()
    except ValueError:
        logging.error("Invalid JSON payload received.")
        return func.HttpResponse(
            json.dumps({"error": "Malformed JSON payload"}),
            status_code=400,
            mimetype="application/json"
        )

    # Required payload schema validation
    required_fields = ["transaction_id", "account_number", "amount", "currency", "provider"]
    missing_fields = [field for field in required_fields if field not in req_body]

    if missing_fields:
        logging.warning(f"Missing required payload fields: {missing_fields}")
        return func.HttpResponse(
            json.dumps({"error": f"Missing required fields: {missing_fields}"}),
            status_code=422,
            mimetype="application/json"
        )

    transaction_id = req_body["transaction_id"]
    amount = req_body["amount"]
    account_number = req_body["account_number"]

    # Construct standardized integration payload
    event_payload = {
        "transaction_id": transaction_id,
        "account_number": account_number,
        "amount": amount,
        "currency": req_body.get("currency", "KES"),
        "provider": req_body.get("provider", "MOBILE_MONEY"),
        "status": "PENDING_CORE_POSTING"
    }

    # Push to Azure Service Bus Queue (Idempotency duplicate check happens at queue level)
    msg.set(json.dumps(event_payload))

    logging.info(f"Successfully queued transaction {transaction_id} for account {account_number}.")

    return func.HttpResponse(
        json.dumps({
            "status": "ACCEPTED",
            "message": "Payment callback received and queued for processing.",
            "transaction_id": transaction_id
        }),
        status_code=202,
        mimetype="application/json"
    )


@app.function_name(name="PostToCoreBanking")
@app.service_bus_queue_trigger(
    arg_name="msg",
    queue_name="mobile-payment-callbacks",
    connection="ServiceBusConnection"
)
def post_to_core_banking(msg: func.ServiceBusMessage):
    """
    Queue Trigger: Consumes messages from Service Bus, executes core banking ledger updates,
    and handles retries/Dead-Letter Queue routing automatically.
    """
    message_body = msg.get_body().decode("utf-8")
    data = json.loads(message_body)

    transaction_id = data.get("transaction_id")
    account_number = data.get("account_number")
    amount = data.get("amount")

    logging.info(f"Worker processing ledger credit for Transaction: {transaction_id}")

    # Simulated Core Banking Ledger Integration API call
    # In production: Execute database transaction with ROWLOCK or call Core Banking REST endpoint
    success = execute_ledger_credit(account_number, amount, transaction_id)

    if not success:
        logging.error(f"Failed to credit ledger for Transaction: {transaction_id}. Message will retry.")
        raise Exception("Ledger post failed. Triggering Service Bus retry policy.")

    logging.info(f"Transaction {transaction_id} successfully posted to ledger.")


def execute_ledger_credit(account_number: str, amount: float, transaction_id: str) -> bool:
    """
    Business Logic: Performs idempotency verification against SQL ledger database
    and executes balance increment.
    """
    # Defensive check: Ensure amount is positive
    if amount <= 0:
        return False
    
    # Return True simulating successful Core Banking DB updates
    return True