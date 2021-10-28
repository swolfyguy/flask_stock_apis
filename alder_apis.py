import json

import csv
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
    href = fields.String(required=True, nullable=False)
    rel = fields.String(required=True, nullable=False)


class ProgramSchema(Schema):
    id = fields.Integer(required=True, nullable=False)
    name = fields.String(required=True, nullable=False)
    links = fields.List(fields.Nested(CatalogueLinkSchema))


class CatalogueSchema(Schema):
    id = fields.Integer(required=True, nullable=False)
    programId = fields.Integer(required=True, nullable=False)
    name = fields.String(required=True, nullable=False)
    productName = fields.String(required=True, nullable=False)
    brandName = fields.String(required=True, nullable=False)
    productSku = fields.String(required=True, nullable=False)
    maxAmount = fields.Integer(required=True, nullable=False)
    minAmount = fields.Integer(required=True, nullable=False)
    isDigital = fields.Boolean(required=True, nullable=False)
    description = fields.String(required=True, nullable=False)
    modifiedOn = fields.DateTime(required=True, nullable=False)
    currencyCode = fields.String(required=True, nullable=False)
    productType = fields.String(required=True, nullable=False)
    categories = fields.List(fields.Str())


class ProductSkuAssetSchema(Schema):
    productSku = fields.String(required=True, nullable=False)


class CatalogueAssets(Schema):
    languageCulture = fields.String(required=True, nullable=False)


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


def generate_csv():
    programId = "programId"
    catalogId = "catalogId"
    url = "https://app.giftango.com/programs/programs/6416/catalogs/1"
    headers = {
        "Authorization": "Bearer kDZklY5WR9onYuTs0pgwNWX1XtOhgXZQxNLbJWRzVyfUT_rn731kB9l0mEpD-6oHKrak0ptVDrbz14OZ1J9WWeouIuQm3hqNP621vQ9A2c278B9gPRxs5XVry8lv-C8YfkN61EtK6Ws-aBSCmBdomiz0nY7I203_fxEaex8MvFE0aBJ1GnKwcF-VtpU5IUHIin9N9cyRKTGfKy4kxl3m5S_2txr1CM16Utmn828KJBp0bErIH4JttlhawHFyM4P6m5q4t4Ci6Pt1gw9Hhx4T7DaTfUW_LzXia52R0KjiOy5VoX_bCEyWr6ugsNGjmYVVAVnKyunoOa2jtlv_pMswIEibsFSyp0AkXEDtUFIwJbm4EGA7MRyhjcNY3eK1raEPsleXhmLqTcxzjX74P7KBSGFWcoyqoo3uR4-rEgDJhODqt9RNkpoPhlGVlcVnRyQZ9IFax0yaKFuAK1rR9QIb8hJCfNF0kC0T-y9kTxLAc5o5JsSl2Mv6JkVmIcxi_UPV"
    }
    catalog_res = requests.get(url=url, headers=headers)

    catalog_asset_desc_res = requests.get(
        url="https://app.giftango.com/programs/programs/6416/catalogs/1/assets",
        headers=headers,
    )

    if catalog_res.status_code == 200 and catalog_asset_desc_res.status_code == 200:
        # validate response
        CatalogueSchema().loads(catalog_res.json())

        product_sku_details_dict = {}
        csv_row = []
        for product in catalog_res.json()["products"]:
            product_sku_details_dict.update(
                {
                    product["productSku"]: {
                        "sku": product["productSku"],
                        "name": product["productName"],
                        "max": product["maxAmount"],
                        "min": product["minAmount"],
                        "updated_at": product["modifiedOn"],
                        "currency": product["currencyCode"],
                        "subcategory": product["categories"],
                        "category": "INCOMM",
                    }
                }
            )

        db_field_mappings = {
            "legaldisclaimer": "legald",
            "redemptioninstructions": "inst",
            "termsconditions": "terms",
            "marketingdescription": "description",
            "cardimage": "image",
        }

        breakpoint()
        asset_desc_dict = {}
        for productSku_assets in catalog_asset_desc_res.json()[0]["products"]:
            db_field_mappings_found = {
                "legaldisclaimer": False,
                "redemptioninstructions": False,
                "termsconditions": False,
                "marketingdescription": False,
                "cardimage": False,
            }
            for asset in productSku_assets["assets"]:
                if asset["type"] in db_field_mappings:
                    asset_desc_dict.update(
                        {db_field_mappings[asset["type"]]: asset.get("text", "")}
                    )
                    db_field_mappings_found[asset["type"]] = True
            for mapping, found in db_field_mappings_found.items():
                if not found:
                    asset_desc_dict.update({db_field_mappings[mapping]: ""})

            csv_row.append(
                {
                    **product_sku_details_dict[productSku_assets["productSku"]],
                    **asset_desc_dict,
                }
            )
            asset_desc_dict = {}

        with open("mappings.csv", "w", encoding="utf8", newline="") as output_file:
            fc = csv.DictWriter(
                output_file,
                fieldnames=csv_row[0].keys(),
            )
            fc.writeheader()
            fc.writerows(csv_row)


"""
TODO
get all catalogues
loop through them
fetch one asset
and generate csv for all the fields containing on the left side of the document:
    "https://docs.google.com/spreadsheets/d/10SXqUXZj9OCz0Ebzz26lfRiSCfzDashBlt25F9cYk3c/edit#gid=0"
"""


def updateSKU():
    "populate csv here"
    pass


generate_csv()
