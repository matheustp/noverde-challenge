import json
import uuid
import os
import boto3
from decimal import Decimal
from datetime import datetime

table = boto3.resource('dynamodb', region_name=os.getenv("REGION", None)).Table(os.getenv("TABLE_NAME", None))

def append_error(errors_array, key, message):
    errors_array.append({"key": key, "message": message})

def validate_required(required_keys, inp, errors_array):
    for k in required_keys:
        if not k in inp:
            append_error(errors_array, k, "The field is required")

def validate_amount(inp, errors_array):
    try: 
        amount = Decimal(inp["amount"].replace(",", "."))
        inp["amount"] = amount
        if amount < 1000 or amount > 4000:
           append_error(errors_array, "amount", "Amount must be a value between 1000 and 4000")
    except:
        append_error(errors_array, "amount", "Amount value must be a Decimal")

def validate_birthdate(inp, errors_array):
    try:
        birthdate = datetime.strptime(inp["birthdate"], "%Y-%m-%d").date()
        inp["birthdate"] = birthdate
    except:
        append_error(errors_array, "birthdate", "Birthdate should be valid, the format is YYYY-MM-DD")

def validate_terms(inp, errors_array):
    try: 
        terms = int(inp["terms"])
        inp["terms"] = terms
        if not terms in [6, 9, 12]:
            append_error(errors_array, "terms", "Terms should be 6, 9 or 12")
    except:
            append_error(errors_array, "terms", "Terms should be 6, 9 or 12")

def validate_income(inp, errors_array):
    try:
        income = Decimal(inp["income"].replace(",","."))
        inp["income"] = income
    except:
        append_error(errors_array, "income", "Income should be a valid decimal number")

def validate_input(inp):
    errors_array = []
    validate_required(["name", "cpf", "birthdate", "amount", "terms", "income"], inp, errors_array)
    if len(errors_array) != 0:
        return errors_array
    validate_birthdate(inp, errors_array)
    validate_amount(inp, errors_array)
    validate_terms(inp, errors_array)
    validate_income(inp, errors_array)
    return errors_array


def loan_post_handler(event, context):
    sqs = boto3.client('sqs')
    r = sqs.get_queue_url(QueueName=os.getenv("QUEUE_NAME", None))
    queue_url = r["QueueUrl"]
    body = json.loads(event["body"])
    errors = validate_input(body)
    if len(errors) != 0:
        return {
            "statusCode": 400,
            "body": json.dumps({"errors": errors})
        }
    
    id = str(uuid.uuid4())
    table.put_item(Item={
        "id": id,
        "name": body["name"],
        "cpf": body["cpf"],
        "birthdate": body["birthdate"].strftime("%Y-%m-%d"),
        "desired_amount": body["amount"],
        "desired_terms": body["terms"],
        "income": body["income"],
        "status": "processing"
    })
    sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=0,
        MessageBody=id
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "id": id,
        }),
    }

def loan_get_handler(event, context):
    try:
        response = table.get_item(
            Key={
                'id': event["pathParameters"]["id"]
        })
        item = response['Item']
        if item is None:
            return {
                "statusCode": 404
            }
        return {
            "statusCode": 200,
            "body": json.dumps({
                "id": item["id"],
                "status": item["status"],
                "result": item["result"] if "result" in item else None,
                "refused_policy": item["refused_policy"] if "refused_policy" in item else None,
                "amount": float(item["amount"]) if "amount" in item else None,
                "terms": int(item["terms"]) if "terms" in item else None
            })
        }
    except:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }       