import json
import requests
import os
from requests.models import Response


def lambda_handler(event, context):
    # TODO implement

    BASE_URL_EMAIL = 'https://ipqualityscore.com/api/json/email/OiLpcG2AvsoMh3QdXXG6C8zhJEtnTxxx/'
    BASE_URL_ADDR = 'https://ipqualityscore.com/api/json/ip/OiLpcG2AvsoMh3QdXXG6C8zhJEtnTxxx/61.1.132.196?'
    BASE_URL_ADDR_T = 'https://ipqualityscore.com/api/json/ip/OiLpcG2AvsoMh3QdXXG6C8zhJEtnTxxx/2601:647:4100:6f2:28b2:53c7:a43b:ee0b?strictness=1'
    # &billing_email=myemail@example.com&billing_phone=5555555555&billing_country=US

    print('event :', event)
    # default
    type = "email"
    email = None
    resp = None

    if 'type' in event:
        type = event['type']
    else:
        type = 'email'

    if type == 'email':
        email = event['email']
        print("email url:", (BASE_URL_EMAIL + email))
        resp = requests.get((BASE_URL_EMAIL + email)).json()
        print('email check resp :', resp)

    if type == 'address':
        addr = ""
        addr = 'billing_address_1=' + event['street_1']
        if 'street_2' in event:
            addr = addr + '&billing_address_2=' + event['street_2']
        addr = addr + '&billing_city=' + event['city'] + '&billing_region=' + event['state'] + '&billing_postcode=' + \
               event['zipcode'] + '&billing_country=' + 'US'
        if 'phone' in event:
            addr = addr + '&billing_phone=' + event['phone']
        if 'email' in event:
            addr = addr + '&billing_email=' + event['email']

        print("addr check url:", (BASE_URL_ADDR + addr))
        resp = requests.get((BASE_URL_ADDR + addr)).json()
        print('address resp :', resp)

    # https://ipqualityscore.com/api/json/ip/YOUR_API_KEY_HERE/2601:647:4100:6f2:28b2:53c7:a43b:ee0b?
    # strictness=1&billing_email=myemail@example.com&billing_phone=5555555555&billing_country=US
    if type == 'transaction':
        billing_email = '&billing_email=' + 'phanimullapudi9@gmail.com'
        billing_phone = '&billing_phone=' + '5712946666'
        billing_country = '&billing_country=' + 'US'
        billing_fname = '&billing_first_name=' + 'Phani'
        billing_lname = '&billing_last_name=' + 'Mullapudi'
        # billing_address_1 = '&billing_address_1=' + '34500 Fremont Blvd'
        # billing_address_2 = '&billing_address_2=' + 'Apt 101'
        # billing_city = '&billing_city=' + 'Fremont'
        # billing_region = '&billing_region=' + 'CA'
        # billing_postcode = '&billing_postcode=' + '94555'
        # URL_T = BASE_URL_ADDR_T + billing_email + billing_phone + billing_country + billing_fname + billing_lname
        #           + billing_address_1 + billing_address_2 + billing_city + billing_region + billing_postcode

        URL_T = BASE_URL_ADDR_T + billing_email + billing_phone + billing_country + billing_fname + billing_lname
        print("url:", URL_T)
        resp = requests.get((URL_T)).json()
        print('Trx check resp :', resp)

    if resp is not None and (resp['success'] == True):
        statusCode = 200
        message = 'success'
    else:
        statusCode = 400
        message = 'failure'

    return {
        'statusCode': statusCode,
        'body': json.dumps(message)
    }


def lambda_handler_practice(event, context):
    """
    Query Card information
    """

    pass