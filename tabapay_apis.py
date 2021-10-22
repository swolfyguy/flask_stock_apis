import json

import requests
import os
from requests.models import Response

from marshmallow import Schema, fields
from marshmallow import validate


class nameSchema(Schema):
    company = fields.Str()
    first = fields.Str()
    middle = fields.Str()
    last = fields.Str()
    suffix = fields.Str()


class addressSchema(Schema):
    line1 = fields.Str(required=True)
    line2 = fields.Str()
    city = fields.Str(required=True)
    state = fields.Str(required=True)
    zipcode = fields.Str(required=True, validate=validate.Length(2))
    country = fields.Str(required=True)


class phoneSchema(Schema):
    countryCode = fields.Integer()
    number = fields.Integer(required=True, validate=validate.Range(min=4, max=12))


class ownerSchema(Schema):
    name = fields.Nested(nameSchema, required=True)
    address = fields.Nested(nameSchema)
    phone = fields.Nested(phoneSchema)


class cardSchema(Schema):
    keyId = fields.Str(required=True)
    data = fields.Str(required=True)


class bankSchema(Schema):
    routingNumber = fields.Integer(validate=validate.Length(9))
    accountNumber = fields.Integer(validate=validate.Range(4, 17))
    accountType = fields.Str(validate=validate.Length(1))


class accountSchema(Schema):
    referenceID = fields.Str(required=True, validate=validate.Range(1, 15))
    bank = fields.Nested(bankSchema)
    owner = fields.Nested(ownerSchema)
    card = fields.Nested(cardSchema)


def validate_card(event, context):
    """
    Query Card information

    # case that has been handled is when we receive card details encrypted
    event = {"card": {"keyID": "encrypted_key", "data": "encrypted_card_details"}}

    """

    # Assuming i have FQDN and ClientIDISO
    uri = "https://<FQDN>/v1/clients/<ClientIDISO>/cards"
    cardSchema().load(event)

    res = requests.post(url=uri, json=json)
    json_res = json.loads(res)
    if json_res["SC"] == 200 and json_res["AVS"]["networkRC"] == 00:
        # card is successfully verified

        # check if card is available for pull
        if json_res["card"]["pull"]["enabled"]:
            return {
                "statusCode": res.status_code,
                # TODO filter out information thats not necessary to be sent to UI
                "body": json_res["card"]["pull"],
            }
        else:
            # statuscode 403 denotes card if forbidden for Pull
            return {
                "statuscode": 403,
                "body": json.dumps("Pull is disabled for the Card"),
            }
    else:
        return {
            "statuscode": json_res["SC"],
            # Enter error message returned from API instead of hard code
            "body": "error occurred while validating card detail",
        }


def create_account(event, context):
    """
    create Account


    event = {
        "referenceID": "1",
        "card": {"accountNumber": "9999999999999999", "expirationDate": "202012"},
        "owner": {
            "name": {"first": "John", "last": "Customer"},
            "address": {
                "line1": "465 Fairchild Drive",
                "line2": "Suite #222",
                "city": "Mountain View",
                "state": "CA",
                "zipcode": "94043",
            },
            "phone": {"number": "4159808222"},
        },
    }
    """
    # Assuming i have FQDN and ClientIDISO
    uri = "https://<FQDN>/v1/clients/<ClientIDISO>/accounts"
    # validate event
    accountSchema().load(event)

    res = requests.post(url=uri, data=event)
    json_res = json.loads(res)
    if json_res["SC"] == 200 and json_res["EC"] == 00:
        # account is successfully created
        return {
            "statusCode": res.status_code,
            "accountId": json_res["accountID"],
            "message": "account is successfully created",
        }

    elif json_res["SC"] == 207:
        return {
            "statusCode": res.status_code,
            "message": "Account created, but Duplicate Card Check Failed",
        }
    elif json_res["SC"] == 409:
        return {"statusCode": res.status_code, "message": "Duplicate Card Check"}


def retrieveAccount(event, context):
    uri = "https://<FQDN>/v1/clients/<ClientIDISO>/accounts/<ClientIDISO>"

    # Assuming we have FQDN, ClientIDISO, and ClientIDISO
    res = requests.get(url=uri)
    json_res = json.loads(res)

    # Validate Json Response
    accountSchema().load(json_res)

    if json_res["SC"] == 200 and json_res["EC"] == 00:
        # account is successfully created
        return {
            "statusCode": res.status_code,
            "account": json_res,
            "message": "account is successfully retrieved",
        }

    elif json_res["SC"] == 421:
        return {
            "statusCode": res.status_code,
            "message": "Too late to Retrieve Account by ReferenceID, use AccountID",
        }


def updateAccount(event, context):
    """
     event = {
        "card": {"accountNumber": "9999999999999999", "expirationDate": "202012"},
        "owner": {
            "name": {"first": "John", "last": "Customer"},
            "address": {
                "line1": "465 Fairchild Drive",
                "line2": "Suite #222",
                "city": "Mountain View",
                "state": "CA",
                "zipcode": "94043",
            },
            "phone": {"number": "4159808222"},
        },
    }
    """
    uri = "https://<FQDN>/v1/clients/<ClientIDISO>/accounts/<AccountID>"

    # validate event
    accountSchema().load(event)

    res = requests.put(url=uri, data=event)
    json_res = json.loads(res)
    if json_res["SC"] == 200 and json_res["EC"] == 00:
        # account is successfully created
        return {
            "statusCode": res.status_code,
            "accountId": json_res["accountID"],
            "message": "account is successfully created",
        }
    elif json_res["SC"] == 207:
        return {
            "statusCode": res.status_code,
            "message": "Account updated, but Update Duplicate Card Check Failed",
            "error": json_res["EM"],
        }
    elif json_res["SC"] == 409:
        return {
            "statusCode": res.status_code,
            "message": "Duplicate Card Check Matched",
            "error": json_res["EM"],
        }


def deleteAccount(event, context):
    uri = "https://<FQDN>/v1/clients/<ClientIDISO>/accounts/<AccountID>"
    res = requests.delete(url=uri)
    json_res = json.loads(res)

    if json_res["SC"] == 200 and json_res["EC"] == 00:
        # account is successfully marked for deletion
        return {
            "statusCode": res.status_code,
            "message": "The Account is marked for deletion",
        }
    elif json_res["SC"] == 207:
        return {
            "statusCode": res.status_code,
            "message": "Account marked for deletion, but Delete Duplicate Card Check Failed",
            "error": json_res["EM"],
        }


class bankOwnerCard(Schema):
    bank = fields.Nested(bankSchema, required=True)
    owner = fields.Nested(ownerSchema, required=True)
    card = fields.Nested(cardSchema, required=True)


class accountsSchema(Schema):
    sourceAccountID = fields.String(validate=validate.Length(22))
    sourceAccount = fields.Nested(bankOwnerCard)
    destinationAccountID = fields.String(validate=validate.Length(22))
    destinationAccount = fields.Nested(bankOwnerCard)


class TransactionSchema(Schema):
    referenceID = fields.Str(required=True, validate=validate.Range(min=1, max=15))
    type = fields.Str(required=True)
    amount = fields.Str(required=True)
    accounts = fields.Nested(accountsSchema)


def createTransaction(event, context):
    """
     event = {
        "referenceID": "1",
        "type": "pull",
        "accounts": {
            "sourceAccount": {
                "card": {
                    "accountNumber": "9999999999999999",
                    "expirationDate": "202012",
                },
                "owner": {
                    "name": {"first": "John", "last": "Benson"},
                    "address": {
                        "line1": "465 Fairchild Drive",
                        "line2": "Suite #222",
                        "city": "Mountain View",
                        "state": "CA",
                        "zipcode": "94043",
                    },
                    "phone": {"number": "4159808222"},
                },
            },
            "destinationAccountID": "TabaPay_AccountID_22-c",
        },
        "amount": "0.10",
    }
    """
    uri = "https://<FQDN>/v1/clients/<ClientIDISO>/transactions"
    # validate event
    TransactionSchema().load(event)

    res = requests.post(url=uri, data=event)
    json_res = json.loads(res)
    if json_res["SC"] == 200 and json_res["EC"] == 00:
        return {
            "statusCode": res.status_code,
            "transactionID": json_res["transactionID"],
            "message": "A Transaction is created and processing is completed",
        }
    elif json_res["SC"] == 201:
        return {
            "statusCode": res.status_code,
            "transactionID": json_res["transactionID"],
            "message": "A Transaction is created, but the transaction is waiting to be processed (batch)",
        }

    elif json_res["SC"] == 207:
        return {
            "statusCode": res.status_code,
            "message": "One or more Failures occurred while processing the Request",
        }
    elif json_res["SC"] == 429:
        return {
            "statusCode": res.status_code,
            "message": "Over your Daily (24-hour rolling) Approximation Limit",
        }


def retrieveTransaction(event, context):
    uri = "https://<FQDN>/v1/clients/<ClientIDISO>/transactions/<TransactionID>"

    res = requests.get(url=uri)
    TransactionSchema().load(res)

    json_res = json.loads(res)
    if json_res["SC"] == 200 and json_res["EC"] == 00:
        return {
            "statusCode": res.status_code,
            "transactionID": json_res["transactionID"],
            "message": "The Transaction is retrieved",
        }
    elif json_res["SC"] == 421:
        return {
            "statusCode": res.status_code,
            "message": "Too late to Retrieve Transaction by ReferenceID, use TransactionID",
        }


def deleteTransaction(event, context):
    """
    event = {"amount": "1.00"}
    """
    uri = (
        "https://<FQDN>/v1/clients/<ClientIDISO>/transactions/<TransactionID>?reversal"
    )

    res = requests.delete(url=uri, data=event)

    json_res = json.loads(res)
    if json_res["SC"] == 200 and json_res["EC"] == 00:
        return {
            "statusCode": res.status_code,
            "message": "A Request for a Reversal of the previous Transaction is successful",
        }
    elif json_res["SC"] == 207:
        return {
            "statusCode": res.status_code,
            "message": "One or more Failures occurred while processing the Request",
        }
