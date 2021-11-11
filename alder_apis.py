import csv
import requests

from marshmallow import Schema, fields


blueprint_app_api = "https://app.giftango.com"
blueprint_api = "https://api.giftango.com"


def common_errors(res):
    if res.status_code == 400:
        return {
            "statusCode": res.status_code,
            "error": "Bad Request",
            "message": res.json(),
        }
    elif res.status_code == 401:
        return {
            "statusCode": res.status_code,
            "error": "Unauthorized access: check your token",
            "message": res.json(),
        }
    elif res.status_code == 403:
        return {
            "statusCode": res.status_code,
            "error": "Forbidden",
            "message": res.json(),
        }
    elif res.status_code == 404:
        return {
            "statusCode": res.status_code,
            "error": "Program not found",
            "message": res.reason,
        }
    elif res.status_code == 405:
        return {
            "statusCode": res.status_code,
            "error": "Method Not Allowed",
            "message": res.json(),
        }
    elif res.status_code == 409:
        return {
            "statusCode": res.status_code,
            "error": "Duplicate entity found",
            "message": res.json(),
        }
    elif res.status_code == 500:
        return {
            "statusCode": res.status_code,
            "error": "Internal Server Error",
            "message": res.json(),
        }
    elif res.status_code == 502:
        return {
            "statusCode": res.status_code,
            "error": "Bad Gateway",
            "message": res.json(),
        }
    elif res.status_code == 503:
        return {
            "statusCode": res.status_code,
            "error": "Service Unavailable",
            "message": res.json(),
        }


def get_access_token(event, context):
    """
    event:{
            grant_type: client_credentials
            client_id: string
            client_secret: string
        }

    """
    url = f"{blueprint_app_api}/auth/token"

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


class ProgramWithProductsSchema(Schema):
    id = fields.Integer(required=True, nullable=False)
    name = fields.String(required=True, nullable=False)
    programId = fields.Integer(required=True, nullable=False)
    products = fields.List(
        fields.Nested(CatalogueSchema(exclude=("id", "programId", "name")))
    )


class ProductSkuAssetSchema(Schema):
    productSku = fields.String(required=True, nullable=False)


class CatalogueAssets(Schema):
    languageCulture = fields.String(required=True, nullable=False)


class ProductsSchema(Schema):
    Sku = fields.String(required=True, nullable=False)
    Value = fields.Integer(required=True, nullable=True)
    Quantity = fields.Integer(required=True, nullable=True)
    EmbossedTextId = fields.Integer()
    Packaging = fields.String()
    MessageText = fields.String()
    MessageRecipientName = fields.String()
    MessageSenderName = fields.String()


class RecipientsSchema(Schema):
    ShippingMethod = fields.String(required=True, nullable=False)
    LanguageCultureCode = fields.String()
    FirstName = fields.String(required=True, nullable=False)
    LastName = fields.String(required=True, nullable=False)
    EmailAddress = fields.String(required=True, nullable=False)
    Address1 = fields.String(required=True, nullable=False)
    Address2 = fields.String(required=False, nullable=True)
    City = fields.String(required=True, nullable=False)
    StateProvinceCode = fields.String(required=True, nullable=False)
    PostalCode = fields.String(required=True, nullable=False)
    CountryCode = fields.String(required=True, nullable=False)
    DeliverEmail = fields.Boolean(required=True, nullable=False)
    Products = fields.List(fields.Nested(ProductsSchema))


class OrderSchema(Schema):
    PurchaseOrderNumber = fields.String(required=True, nullable=False)
    CatalogId = fields.Integer(required=True, nullable=True)
    Metadata = fields.String(required=True, nullable=False)
    CustomerOrderId = fields.String(required=True, nullable=False)

    id = fields.Integer()
    name = fields.String()
    OrderUri = fields.String()
    CreatedOn = fields.DateTime()
    OrderStatus = fields.String()
    Message = fields.String()
    TotalFaceValue = fields.Integer()
    ProgramId = fields.Integer()
    TotalFees = fields.Integer()
    TotalDiscounts = fields.Integer()
    TotalCustomerCost = fields.Integer()
    EmailTheme = fields.String()
    Recipients = fields.List(fields.Nested(RecipientsSchema))


class CardsSchema(Schema):
    CertificateLink = (fields.String(),)
    CardNumber = (fields.Integer(),)
    Pin = (fields.Integer(),)
    BarcodeImageUrl = (fields.String(),)
    ImageUrl = (fields.String(),)
    TermsAndConditions = (fields.String(),)
    MarketingDescription = (fields.String(),)
    InitialBalance = (fields.Float(),)
    CardUri = (fields.String(),)
    Sku = (fields.String(),)
    CreatedOn = (fields.DateTime(),)
    UsageInstructions = (fields.String(),)
    ActivationDate = fields.DateTime()


class FulfillmentSchema(Schema):
    FulfillmentStatus = (fields.String(),)
    OrderUri = (fields.String(),)
    CustomerOrderId = (fields.String(),)
    OrderDate = (fields.DateTime(),)
    Sku = (fields.String(),)
    Value = (fields.Float(),)
    Quantity = fields.Integer()


def retrieve_programs(event, context):
    url = f"{blueprint_app_api}/programs/programs"
    headers = {
        "Authorization": "Bearer LSbfKxFTuF75r1vMpkO9UTIiX4Q3TkdAGPoKEE8kumPVPPZSK8ob3ipX8Ix14IJucaHwe0FC-Widy5YuKR7ukjdET4VRoblkQhNitIsHo19neZK-rM-K1CAV_h_NK5lwiuf-YPSLt9Zz9423ZpeCBIZ9VOKfsmKxDtG30kpSUHtzF2wu1-30G00uFPd7PDyM36e_1h0l9MZpel1yrTIMgcRLhHrcP2MiinTIQBhz6yCAXdoiSCOJi3LuJWzAwExS0naTo7Egy6qfR89OF3Cc2tp1bWcgIZpVpAOdN84mo_UiPT6RoLo0evKhvj1-fyaZW-h4fBRrnjJscsffXBxm-DGdGA5Cg6BQapH6L_KRmnKUmGWoTklIM2fAa1hehqd06fGDNFM0U5de8g2ikciKCrTvlmVibIYAuFKXXDFfn7-UOikd216hi1ILz3VPJMPbIj4rt-KW-wi83E3ObMgQPw84S1ZvwLZMBhaU2UjAnGdizzuIzCCIn1_4wfT4uIud"
    }
    res = requests.get(url=url, headers=headers)

    if res.status_code == 200:
        # validate response
        data, errors = ProgramSchema(many=True).load(res.json())
        if errors:
            return {
                "statusCode": res.status_code,
                "body": errors,
            }
        return {
            "statusCode": res.status_code,
            "body": res.json(),
        }
    return common_errors(res)


def get_programs_catalogue(event, context):
    programId = "6416"
    url = f"{blueprint_app_api}/programs/programs/{programId}/catalogs"
    headers = {
        "Authorization": "Bearer rNVajBf_4UAwF0eOxECdZED1jcgkkzKSSxKDmGOT90QQQEVq5lDOR4jTtjPKEUPfs2kEhtBMA4MbW7E77JPk4VQ5N7wQXxoaxGnBGlJY0x5zzqQhCXjldfvK_c-NJhc6bMKbRIWAFUAOHAIKQ6ZzMw9OQMQxEb0k92F3cWXKKA3HbeQHjSQFTGsHSOyGx18-OUGYOqTEWn3Tnn_1H9V3AZZn9cXzT3MN0qMKMzpkm5pTCWIEdvXnGRulciEuYRjCPpKELTuvTKxqb2fP9_T5344HDmnkatQ-ddcH_lQeer2uBZpRDxYWsKtTipmfvQcod_mrmvx6Lu2PeeJhDYiLI_IxBJl6mXGVdIMdNH0DDNIHfhm2A4Rc2-tJxstQGFgUpPbdZjzTskAyoRzM0ChtwrtC6k7DIYIKwcmS3mB5a7e4xjmA-RFMwiH5-PVucI9XZuFgF05ZwCiuCVjhqxX7TrB0KOUgHeVoeDINmRmVhBQTdsLOSiNRtLCjgzbi_Lr2"
    }
    res = requests.get(url=url, headers=headers)

    if res.status_code == 200:
        # validate response
        data, errors = ProgramSchema(many=True).load(res.json())
        if errors:
            return {
                "statusCode": res.status_code,
                "body": errors,
            }
        return {
            "statusCode": res.status_code,
            "body": res.json(),
        }
    return common_errors(res)


def get_catalogue(event, context):
    programId = 6416
    catalogId = "1"
    url = f"{blueprint_app_api}/programs/programs/{programId}/catalogs/{catalogId}"
    headers = {
        "Authorization": "Bearer XX4zeK4cPaimY4PSqNlg8TsOS2LSEjtC-W1jjl9X9OTUpvEcpPw13YdpozzJlvK8ieHyHazO43OnL0zRMlmnk4xhd6RfoRyYhKHeoO358Aexkqpvu_gOiclBLXKnKsSJBDu8orErfoEx5Imkot_Qg-M2d6iv1wgwjhj5sWSO0pPbTj4dAlDhpmDZdqOhu2ZriQyY7Y0P_jR-ZM46cDZXtBIZznQg_XrimGTSzq3tT2MIqtNwxmg-sv8ZPGgq-gxiU23KxWSI2mgOqxTeIAlZs4v6vU12JV0_AjxHuTDOjn2KxKE9TeJZcCLr_KXwB3fOKaEU3Yrjg5TeQ-QYuOv7R6B3ZFdB5sR4iEdvVoRqPChXlc1Yi5xZuO6C5EzOtj1YQGJAeLQ-QnMBgkYUZXtgWbvy8CBIPaOQbE4vOyvIqR3QoVLBUM2v0UMOTptP2dBcqmKwTdasS1wChun5EsCWKOdJ--2o4yl5TJfId_t2sJCprCB1ht-pNLgb7jxBsQbS"
    }
    res = requests.get(url=url, headers=headers)

    if res.status_code == 200:
        # validate response
        data, errors = ProgramWithProductsSchema().load(res.json())
        if errors:
            return {
                "statusCode": res.status_code,
                "body": errors,
            }
        return {
            "statusCode": res.status_code,
            "body": data,
        }
    return common_errors(res)

def get_catalogue_assets(event, context):
    programId = 6416
    catalogId = "1"
    url = (
        f"{blueprint_app_api}/programs/programs/{programId}/catalogs/{catalogId}/assets"
    )
    headers = {
        "Authorization": "Bearer XX4zeK4cPaimY4PSqNlg8TsOS2LSEjtC-W1jjl9X9OTUpvEcpPw13YdpozzJlvK8ieHyHazO43OnL0zRMlmnk4xhd6RfoRyYhKHeoO358Aexkqpvu_gOiclBLXKnKsSJBDu8orErfoEx5Imkot_Qg-M2d6iv1wgwjhj5sWSO0pPbTj4dAlDhpmDZdqOhu2ZriQyY7Y0P_jR-ZM46cDZXtBIZznQg_XrimGTSzq3tT2MIqtNwxmg-sv8ZPGgq-gxiU23KxWSI2mgOqxTeIAlZs4v6vU12JV0_AjxHuTDOjn2KxKE9TeJZcCLr_KXwB3fOKaEU3Yrjg5TeQ-QYuOv7R6B3ZFdB5sR4iEdvVoRqPChXlc1Yi5xZuO6C5EzOtj1YQGJAeLQ-QnMBgkYUZXtgWbvy8CBIPaOQbE4vOyvIqR3QoVLBUM2v0UMOTptP2dBcqmKwTdasS1wChun5EsCWKOdJ--2o4yl5TJfId_t2sJCprCB1ht-pNLgb7jxBsQbS"
    }
    res = requests.get(url=url, headers=headers)

    if res.status_code == 200:
        # TODO create schema
        return {
            "statusCode": res.status_code,
            "body": res.json(),
        }
    return common_errors(res)


def submit_immediate_order(event, context):
    """
    expected payload
            {
          "OrderUri": "string",
          "CreatedOn": "2019-06-13T13:50:31Z",
          "OrderStatus": "Pending",
          "Message": "string",
          "PurchaseOrderNumber": "string",
          "ProgramId": 0,
          "CatalogId": 0,
          "Metadata": "string",
          "TotalFaceValue": 0,
          "TotalFees": 0,
          "TotalDiscounts": 0,
          "TotalCustomerCost": 0,
          "CustomerOrderId": "string",
          "EmailTheme": "string",
          "Recipients": [
            {
              "ShippingMethod": "string",
              "LanguageCultureCode": "string",
              "FirstName": "string",
              "LastName": "string",
              "EmailAddress": "string",
              "Address1": "string",
              "Address2": "string",
              "City": "string",
              "StateProvinceCode": "string",
              "PostalCode": "string",
              "CountryCode": "string",
              "DeliverEmail": True,
              "Products": [
                {
                  "Sku": "string",
                  "Value": 0,
                  "Quantity": 0,
                  "EmbossedTextId": 0,
                  "Packaging": "string",
                  "MessageText": "string",
                  "MessageRecipientName": "string",
                  "MessageSenderName": "string"
                }
              ]
            }
          ]
        }
    """

    event = {
        "PurchaseOrderNumber": "test007",
        "CatalogId": 1,
        "Metadata": "test",
        "CustomerOrderId": "testing002",
        "Recipients": [
            {
                "ShippingMethod": "Email",
                "FirstName": "string f",
                "LastName": "string l",
                "EmailAddress": "phani@storecashapp.com",
                "Address1": "34500 Fremont Blvd",
                "Address2": "string",
                "City": "Fremont",
                "StateProvinceCode": "CA",
                "PostalCode": "94538",
                "CountryCode": "US",
                "DeliverEmail": True,
                "Products": [{"Sku": "VUSA-D-V-00", "Value": 5, "Quantity": 1}],
            }
        ],
    }
    # validate post payload
    data, errors = OrderSchema().load(event)
    if errors:
        return errors

    headers = {
        "Authorization": "Bearer XX4zeK4cPaimY4PSqNlg8TsOS2LSEjtC-W1jjl9X9OTUpvEcpPw13YdpozzJlvK8ieHyHazO43OnL0zRMlmnk4xhd6RfoRyYhKHeoO358Aexkqpvu_gOiclBLXKnKsSJBDu8orErfoEx5Imkot_Qg-M2d6iv1wgwjhj5sWSO0pPbTj4dAlDhpmDZdqOhu2ZriQyY7Y0P_jR-ZM46cDZXtBIZznQg_XrimGTSzq3tT2MIqtNwxmg-sv8ZPGgq-gxiU23KxWSI2mgOqxTeIAlZs4v6vU12JV0_AjxHuTDOjn2KxKE9TeJZcCLr_KXwB3fOKaEU3Yrjg5TeQ-QYuOv7R6B3ZFdB5sR4iEdvVoRqPChXlc1Yi5xZuO6C5EzOtj1YQGJAeLQ-QnMBgkYUZXtgWbvy8CBIPaOQbE4vOyvIqR3QoVLBUM2v0UMOTptP2dBcqmKwTdasS1wChun5EsCWKOdJ--2o4yl5TJfId_t2sJCprCB1ht-pNLgb7jxBsQbS"
                         ,"ProgramId": "6416",
    }

    url = f"{blueprint_api}/Orders/Immediate"
    res = requests.post(url=url, headers=headers, json=event)
    if res.status_code == 201:
        # validate response
        data, errors = OrderSchema().load(res.json())
        if errors:
            return {
                "statusCode": res.status_code,
                "body": errors,
            }
        return {
            "statusCode": res.status_code,
            "body": res.json(),
        }
    return common_errors(res)

submit_immediate_order("","")

def get_order(event, context):
    orderUri = "orderUri"
    orderUri = "08M-LW-1Z7"

    url = f"{blueprint_api}/Orders/{orderUri}"
    headers = {
        "Authorization": "Bearer rNVajBf_4UAwF0eOxECdZED1jcgkkzKSSxKDmGOT90QQQEVq5lDOR4jTtjPKEUPfs2kEhtBMA4MbW7E77JPk4VQ5N7wQXxoaxGnBGlJY0x5zzqQhCXjldfvK_c-NJhc6bMKbRIWAFUAOHAIKQ6ZzMw9OQMQxEb0k92F3cWXKKA3HbeQHjSQFTGsHSOyGx18-OUGYOqTEWn3Tnn_1H9V3AZZn9cXzT3MN0qMKMzpkm5pTCWIEdvXnGRulciEuYRjCPpKELTuvTKxqb2fP9_T5344HDmnkatQ-ddcH_lQeer2uBZpRDxYWsKtTipmfvQcod_mrmvx6Lu2PeeJhDYiLI_IxBJl6mXGVdIMdNH0DDNIHfhm2A4Rc2-tJxstQGFgUpPbdZjzTskAyoRzM0ChtwrtC6k7DIYIKwcmS3mB5a7e4xjmA-RFMwiH5-PVucI9XZuFgF05ZwCiuCVjhqxX7TrB0KOUgHeVoeDINmRmVhBQTdsLOSiNRtLCjgzbi_Lr2"
    }
    res = requests.get(url=url, headers=headers)

    if res.status_code == 200:
        # validate response
        date, errors = OrderSchema().load(res.json())
        if errors:
            return {
                "statusCode": res.status_code,
                "body": errors,
            }
        return {
            "statusCode": res.status_code,
            "body": res.json(),
        }
    return common_errors(res)


def get_cards_from_order(event, context):
    orderUri = "orderUri"
    orderUri = "P8D-KK-SHT"

    url = f"{blueprint_api}/Orders/{orderUri}/cards"
    headers = {
        "Authorization": "Bearer rNVajBf_4UAwF0eOxECdZED1jcgkkzKSSxKDmGOT90QQQEVq5lDOR4jTtjPKEUPfs2kEhtBMA4MbW7E77JPk4VQ5N7wQXxoaxGnBGlJY0x5zzqQhCXjldfvK_c-NJhc6bMKbRIWAFUAOHAIKQ6ZzMw9OQMQxEb0k92F3cWXKKA3HbeQHjSQFTGsHSOyGx18-OUGYOqTEWn3Tnn_1H9V3AZZn9cXzT3MN0qMKMzpkm5pTCWIEdvXnGRulciEuYRjCPpKELTuvTKxqb2fP9_T5344HDmnkatQ-ddcH_lQeer2uBZpRDxYWsKtTipmfvQcod_mrmvx6Lu2PeeJhDYiLI_IxBJl6mXGVdIMdNH0DDNIHfhm2A4Rc2-tJxstQGFgUpPbdZjzTskAyoRzM0ChtwrtC6k7DIYIKwcmS3mB5a7e4xjmA-RFMwiH5-PVucI9XZuFgF05ZwCiuCVjhqxX7TrB0KOUgHeVoeDINmRmVhBQTdsLOSiNRtLCjgzbi_Lr2"
    }
    res = requests.get(url=url, headers=headers)

    if res.status_code == 200:
        # validate response
        data, errors = CardsSchema(many=True).load(res.json())
        if errors:
            return {
                "statusCode": res.status_code,
                "body": errors,
            }
        return {
            "statusCode": res.status_code,
            "body": res.json(),
        }
    return common_errors(res)


def get_fullfillment(event, context):
    url = f"{blueprint_api}/Fulfillment"
    headers = {
        "Authorization": "Bearer lvfVjvNUii7386VTRmx_yYNf9WRzh3wDZEZHD6Mu9SBgVD6qp7syyfpBmQvwLPYS-Jkp5NItOrBPQ2MwZQaLisi1_dUcFcO0v7FU8rlSHemZab1sO1Zx4BFCT_xNBuLjGn4b2exny620Ko2RwmSuowLoKm7nScg9KtZKIZEO1bRpGq15yrV4IITPnuC1tNvDLG8GAkOQf0BjyG3cJdwKVr3zOfLgbRb7silbE6uID794suTGnwobt6Rd_ChVpRjPnuqq9JhVm4svv8nmYyAA2DtRvXtZfPKcyXNZcoD4IoiD16ZZnGZwniuu3mjvbmOBX6bd9QScO21-w44pO5l7s2FauHScGt_q25B30iCDK-WctLhtb9ylWyObFDCRlwu3nIYjZGt8mkBWH8UUZklAxkVgwb3i1FIhjYYcFUhJBNDIR1J3g38I1q2ywm2M2APEzzJlSndvNlhwH9NLI3xd5_6y_jRBevtW2DOlZ6RBBWMPzDReg6gmp7qaOiqQ6nJR",
        "ProgramId": "6416",
    }
    res = requests.get(url=url, headers=headers)

    if res.status_code == 200:
        # validate response
        data, errors = FulfillmentSchema(many=True).load(res.json())
        if errors:
            return {
                "statusCode": res.status_code,
                "body": errors,
            }
        return {
            "statusCode": res.status_code,
            "body": res.json(),
        }
    return common_errors(res)


# def get_card(event, context):
#     cardUri = "4519684766407396"
#     url = f"{blueprint_api}/Cards/{cardUri}"
#     headers = {
#         "Authorization": "Bearer rNVajBf_4UAwF0eOxECdZED1jcgkkzKSSxKDmGOT90QQQEVq5lDOR4jTtjPKEUPfs2kEhtBMA4MbW7E77JPk4VQ5N7wQXxoaxGnBGlJY0x5zzqQhCXjldfvK_c-NJhc6bMKbRIWAFUAOHAIKQ6ZzMw9OQMQxEb0k92F3cWXKKA3HbeQHjSQFTGsHSOyGx18-OUGYOqTEWn3Tnn_1H9V3AZZn9cXzT3MN0qMKMzpkm5pTCWIEdvXnGRulciEuYRjCPpKELTuvTKxqb2fP9_T5344HDmnkatQ-ddcH_lQeer2uBZpRDxYWsKtTipmfvQcod_mrmvx6Lu2PeeJhDYiLI_IxBJl6mXGVdIMdNH0DDNIHfhm2A4Rc2-tJxstQGFgUpPbdZjzTskAyoRzM0ChtwrtC6k7DIYIKwcmS3mB5a7e4xjmA-RFMwiH5-PVucI9XZuFgF05ZwCiuCVjhqxX7TrB0KOUgHeVoeDINmRmVhBQTdsLOSiNRtLCjgzbi_Lr2"
#     }
#     res = requests.get(url=url, headers=headers)
#
#     if res.status_code == 200:
#         # validate response
#         # TODO, dont know cards schema
#         return {
#             "statusCode": res.status_code,
#             "body": res.json(),
#         }
#     return common_errors(res)


def generate_csv():
    """
    get all catalogues
    loop through them
    fetch one asset
    and generate csv for all the fields containing on the left side of the document:
        "https://docs.google.com/spreadsheets/d/10SXqUXZj9OCz0Ebzz26lfRiSCfzDashBlt25F9cYk3c/edit#gid=0"
    """
    programId = 6416
    catalogId = "1"
    url = "https://app.giftango.com/programs/programs/6416/catalogs/1"
    headers = {
        "Authorization": "Bearer rNVajBf_4UAwF0eOxECdZED1jcgkkzKSSxKDmGOT90QQQEVq5lDOR4jTtjPKEUPfs2kEhtBMA4MbW7E77JPk4VQ5N7wQXxoaxGnBGlJY0x5zzqQhCXjldfvK_c-NJhc6bMKbRIWAFUAOHAIKQ6ZzMw9OQMQxEb0k92F3cWXKKA3HbeQHjSQFTGsHSOyGx18-OUGYOqTEWn3Tnn_1H9V3AZZn9cXzT3MN0qMKMzpkm5pTCWIEdvXnGRulciEuYRjCPpKELTuvTKxqb2fP9_T5344HDmnkatQ-ddcH_lQeer2uBZpRDxYWsKtTipmfvQcod_mrmvx6Lu2PeeJhDYiLI_IxBJl6mXGVdIMdNH0DDNIHfhm2A4Rc2-tJxstQGFgUpPbdZjzTskAyoRzM0ChtwrtC6k7DIYIKwcmS3mB5a7e4xjmA-RFMwiH5-PVucI9XZuFgF05ZwCiuCVjhqxX7TrB0KOUgHeVoeDINmRmVhBQTdsLOSiNRtLCjgzbi_Lr2"
    }
    catalog_res = requests.get(url=url, headers=headers)

    catalog_asset_desc_res = requests.get(
        url="https://app.giftango.com/programs/programs/6416/catalogs/1/assets",
        headers=headers,
    )

    if catalog_res.status_code == 200 and catalog_asset_desc_res.status_code == 200:
        # validate response
        CatalogueSchema().load(catalog_res.json())

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


response_ = {
  "name": "StoreCash TEST USD",
  "id": 1,
  "programId": 6416,
  "products": [
    {
      "productName": "Venue 1 - Golf",
      "brandName": "Venue USD",
      "productSku": "VUSD-D-V-00",
      "isDigital": True,
      "maxAmount": 2000,
      "minAmount": 0.01,
      "description": "",
      "modifiedOn": "2019-11-18T10:30:57.7770279",
      "currencyCode": "USD",
      "productType": "GiftCard",
      "categories": []
    },
    {
      "productName": "Venue 2 - Spa",
      "brandName": "Venue USD",
      "productSku": "VUSA-D-2500-00",
      "isDigital": True,
      "maxAmount": 25,
      "minAmount": 25,
      "description": "",
      "modifiedOn": "2019-11-18T10:16:54.6078712",
      "currencyCode": "USD",
      "productType": "GiftCard",
      "categories": []
    },
    {
      "productName": "Venue 2 - Spa",
      "brandName": "Venue USD",
      "productSku": "VUSA-D-5000-00",
      "isDigital": True,
      "maxAmount": 50,
      "minAmount": 50,
      "description": "",
      "modifiedOn": "2019-11-18T10:17:06.3467736",
      "currencyCode": "USD",
      "productType": "GiftCard",
      "categories": []
    },
    {
      "productName": "Venue 3 - Boutique",
      "brandName": "Venue USD",
      "productSku": "VUSD-D-10000-00",
      "isDigital": True,
      "maxAmount": 100,
      "minAmount": 100,
      "description": "",
      "modifiedOn": "2019-11-18T10:17:34.5039384",
      "currencyCode": "USD",
      "productType": "GiftCard",
      "categories": []
    },
    {
      "productName": "Venue 4 - Resorts One Mimosa Brunch Buffet",
      "brandName": "Venue USD",
      "productSku": "VUSA-D-V-00",
      "isDigital": True,
      "maxAmount": 34.99,
      "minAmount": 34.99,
      "description": "One Mimosa Brunch Buffet",
      "modifiedOn": "2019-11-18T10:17:55.8115717",
      "currencyCode": "USD",
      "productType": "Voucher",
      "categories": []
    },
    {
      "productName": "Venue 4 - Resorts One Suite Night Stay",
      "brandName": "Venue USD",
      "productSku": "VUSA-D-V-01",
      "isDigital": True,
      "maxAmount": 234.56,
      "minAmount": 234.56,
      "description": "One Suite Night Stay",
      "modifiedOn": "2019-11-18T10:18:16.6491769",
      "currencyCode": "USD",
      "productType": "Voucher",
      "categories": []
    },
    {
      "productName": "Venue 5 - Fine Dining",
      "brandName": "Venue USD",
      "productSku": "VUSD-D-V-01",
      "isDigital": True,
      "maxAmount": 1000,
      "minAmount": 5,
      "description": "",
      "modifiedOn": "2020-05-26T15:06:18.0254329",
      "currencyCode": "USD",
      "productType": "PrepaidGiftCard",
      "categories": []
    },
    {
      "productName": "Venue 1 - Golf",
      "brandName": "Venue USD",
      "productSku": "VUSD-P-V-00",
      "isDigital": False,
      "maxAmount": 2000,
      "minAmount": 0.01,
      "description": "",
      "modifiedOn": "2020-06-15T15:50:10.8557187",
      "currencyCode": "USD",
      "productType": "GiftCard",
      "categories": []
    },
    {
      "productName": "Venue 2 - Spa",
      "brandName": "Venue USD",
      "productSku": "VUSA-P-2500-00",
      "isDigital": False,
      "maxAmount": 25,
      "minAmount": 25,
      "description": "",
      "modifiedOn": "2019-11-18T10:17:18.2696908",
      "currencyCode": "USD",
      "productType": "GiftCard",
      "categories": []
    },
    {
      "productName": "Venue 3 - Boutique",
      "brandName": "Venue USD",
      "productSku": "VUSD-P-10000-00",
      "isDigital": False,
      "maxAmount": 100,
      "minAmount": 100,
      "description": "",
      "modifiedOn": "2019-11-18T10:17:44.1436828",
      "currencyCode": "USD",
      "productType": "GiftCard",
      "categories": []
    },
    {
      "productName": "Venue 4 - Resorts One Mimosa Brunch Buffet",
      "brandName": "Venue USD",
      "productSku": "VUSA-P-V-00",
      "isDigital": False,
      "maxAmount": 34.99,
      "minAmount": 34.99,
      "description": "One Mimosa Brunch Buffet",
      "modifiedOn": "2019-11-18T10:18:07.3944766",
      "currencyCode": "USD",
      "productType": "Voucher",
      "categories": []
    },
    {
      "productName": "Venue 5 - Prepaid",
      "brandName": "Venue USD",
      "productSku": "VUSD-P-V-01",
      "isDigital": False,
      "maxAmount": 2000,
      "minAmount": 10,
      "description": "",
      "modifiedOn": "2020-06-15T15:57:47.9598741",
      "currencyCode": "USD",
      "productType": "PrepaidGiftCard",
      "categories": []
    },
    {
      "productName": "Venue 4 - Resorts One Suite Night Stay",
      "brandName": "Venue USD",
      "productSku": "VUSA-P-V-01",
      "isDigital": False,
      "maxAmount": 234.56,
      "minAmount": 234.56,
      "description": "One Suite Night Stay",
      "modifiedOn": "2019-11-18T10:18:25.3608446",
      "currencyCode": "USD",
      "productType": "Voucher",
      "categories": []
    },
    {
      "productName": "Venue 2 - Spa",
      "brandName": "Venue USD",
      "productSku": "VUSA-P-7500-00",
      "isDigital": False,
      "maxAmount": 75,
      "minAmount": 75,
      "description": "",
      "modifiedOn": "2019-11-18T10:17:26.619329",
      "currencyCode": "USD",
      "productType": "GiftCard",
      "categories": []
    }
  ]
}

# ProgramWithProductsSchema().load(response_)