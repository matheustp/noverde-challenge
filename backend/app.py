import json
import uuid
import boto3
import os
from decimal import *
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests

table = boto3.resource('dynamodb', region_name=os.getenv("REGION", None)).Table(os.getenv("TABLE_NAME", None))

X_API_KEY = os.getenv("X_API_KEY", None)

INTEREST_TABLE = {
    10: {
        6: Decimal(0.039),
        9: Decimal(0.042),
        12: Decimal(0.045) 
    },
    9: {
        6: Decimal(0.039),
        9: Decimal(0.042),
        12: Decimal(0.045) 
    },
    8: {
        6: Decimal(0.047),
        9: Decimal(0.05),
        12: Decimal(0.053)
    },
    7: {
        6: Decimal(0.055),
        9: Decimal(0.058),
        12: Decimal(0.061)
    },
    6: {
        6: Decimal(0.064),
        9: Decimal(0.066),
        12: Decimal(0.069)
    }
}
def age_policy_approval(item):
    birthdate = datetime.strptime(item["birthdate"], "%Y-%m-%d")
    return relativedelta(datetime.now(), birthdate).years >= 18
    
def score_policy_approval(item):
    r = requests.post('https://challenge.noverde.name/score', data=json.dumps({"cpf": item["cpf"]}), headers={"x-api-key": X_API_KEY})
    score = int(r.json()["score"])
    item["score"] = score
    return score > 600

def calc_term_value(desired_value, terms, score):
    interest = INTEREST_TABLE[int(score/100)][terms]
    return desired_value * (((pow((1 + interest), terms)) * interest)/(((pow((1 + interest), terms)) -1)))

def calc_commitment_policy_approval(item):
    r = requests.post('https://challenge.noverde.name/commitment', data=json.dumps({"cpf": item["cpf"]}), headers={"x-api-key": X_API_KEY})
    commitment = Decimal(r.json()["commitment"])
    item["commitment"] = commitment.quantize(Decimal('.01'), rounding=ROUND_UP)
    available_month_income = (1 - commitment) * Decimal(item["income"])
    terms = Decimal(item["desired_terms"])
    item["desired_amount"] = Decimal(item["desired_amount"])
    term_value = calc_term_value(item["desired_amount"], terms, item["score"])
    while term_value > available_month_income:
        if terms == 12:
            return False
        terms = terms + 3
        term_value = calc_term_value(item["desired_amount"], terms, item["score"])
    item["terms"] = terms
    item["amount"] = item["desired_amount"]

def credit_engine_handler(event, context):
    for record in event["Records"]:
        response = table.get_item(
            Key={
                'id': record["body"]
        })
        item = response['Item']
        if age_policy_approval(item) is False:
            item["result"] = "refused"
            item["refused_policy"] = "age"
        elif score_policy_approval(item) is False:
            item["result"] = "refused"
            item["refused_policy"] = "score"
        elif calc_commitment_policy_approval(item) is False:
            item["result"] = "refused"
            item["refused_policy"] = "commitment"
        else:
            item["result"] = "approved"
        item["status"] = "completed"
        table.put_item(Item=item)