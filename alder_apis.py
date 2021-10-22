import json

import requests
import os
from requests.models import Response

from marshmallow import Schema, fields
from marshmallow import validate


blueprint_api = "https://api.giftango.com"


def common_errors(res):
    if res.status_code == 400:
        return {
            "statusCode": res.status_code,
            "body": "Bad Request",
        }
    elif res.status_code == 401:
        return {
            "statusCode": res.status_code,
            "body": "Unauthorized access: check your token",
        }
    elif res.status_code == 403:
        return {
            "statusCode": res.status_code,
            "body": "Forbidden",
        }
    elif res.status_code == 404:
        return {
            "statusCode": res.status_code,
            "body": "Program not found",
        }
    elif res.status_code == 405:
        return {
            "statusCode": res.status_code,
            "body": "Method Not Allowed",
        }
    elif res.status_code == 500:
        return {
            "statusCode": res.status_code,
            "body": "Internal Server Error",
        }
    elif res.status_code == 502:
        return {
            "statusCode": res.status_code,
            "body": "Bad Gateway",
        }
    elif res.status_code == 503:
        return {
            "statusCode": res.status_code,
            "body": "Service Unavailable",
        }



def get_access_token(event, context):
    """
    event:{
            grant_type: client_credentials
            client_id: string
            client_secret: string
        }

    """
    url = f"{blueprint_api}/auth/token"

    res = requests.post(url=url, data=event)

    if res.status_code == 200:
        # token is successfully received
            return {
                "statusCode": res.status_code,
                "body": res.json(),
            }
    return common_errors(res)


class CatalogueLinkSchema(Schema):
    href = fields.String(required=True,  nullable=False)
    rel = fields.String(required=True,  nullable=False)


class ProgramSchema(Schema):
    id =fields.Integer(required=True,  nullable=False)
    name = fields.String(required=True,  nullable=False)
    links=fields.List(fields.Nested(CatalogueLinkSchema))


class CatalogueSchema(Schema):
    id =fields.Integer(required=True,  nullable=False)
    programId= fields.Integer(required=True,  nullable=False)
    name= fields.String(required=True,  nullable=False)
    productName = fields.String(required=True,  nullable=False)
    brandName = fields.String(required=True,  nullable=False)
    productSku = fields.String(required=True,  nullable=False)
    maxAmount = fields.Integer(required=True,  nullable=False)
    minAmount = fields.Integer(required=True,  nullable=False)
    isDigital = fields.Boolean(required=True,  nullable=False)
    description = fields.String(required=True,  nullable=False)
    modifiedOn = fields.DateTime(required=True,  nullable=False)
    currencyCode = fields.String(required=True,  nullable=False)
    productType = fields.String(required=True,  nullable=False)
    categories = fields.List(fields.Str())


class ProductSkuAssetSchema(Schema):
    productSku = fields.String(required=True,  nullable=False)


class CatalogueAssets(Schema):
    languageCulture = fields.String(required=True,  nullable=False)


def retrieve_programs(event, context):
    url = f"{blueprint_api}/programs/programs"
    res = requests.get(url=url)

    if res.status_code == 200:
        # validate response
        ProgramSchema().loads(res.json())
        return {
            "statusCode": res.status_code,
            "body": res.json(),
        }
    return common_errors(res)


def get_programs_catalogue(event, context):
    programId = "programId"
    url = f"{blueprint_api}/programs/programs/{programId}/catalogs"
    res = requests.get(url=url)

    if res.status_code == 200:
        # validate response
        ProgramSchema().load(res.json())
        return {
            "statusCode": res.status_code,
            "body": res.json(),
        }
    return common_errors(res)


def get_catalogue(event, context):
    programId = "programId"
    catalogId = "catalogId"
    url = f"{blueprint_api}/programs/programs/{programId}/catalogs/{catalogId}"
    res = requests.get(url=url)

    if res.status_code == 200:
        # validate response
        CatalogueSchema().loads(res.json())
        return {
            "statusCode": res.status_code,
            "body": res.json(),
        }
    return common_errors(res)


def get_catalogue_assets(event, context):
    programId = "programId"
    catalogId = "catalogId"
    url = f"{blueprint_api}/programs/programs/{programId}/catalogs/{catalogId}/assets"
    res = requests.get(url=url)

    if res.status_code == 200:
        # TODO create schema
        return {
            "statusCode": res.status_code,
            "body": res.json(),
        }
    return common_errors(res)
