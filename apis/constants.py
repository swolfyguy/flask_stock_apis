import requests


def fetch_data(symbol="BANKNIFTY", expiry="30SEP2021"):
    expiry = "30SEP2021"
    url = f"https://vbiz.in/optionchain/foc.php?symbol={symbol}&expiry={expiry}"
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-IN,en;q=0.9,hi-IN;q=0.8,hi;q=0.7,mr-IN;q=0.6,mr;q=0.5,en-GB;q=0.4,en-US;q=0.3",
        "cookie": "HstCfa4543512=1625977399788; HstCmu4543512=1625977399788; c_ref_4543512=https%3A%2F%2Fwww.google.com%2F; HstCnv4543512=4; HstCns4543512=8; HstCla4543512=1627364251945; HstPn4543512=2; HstPt4543512=13",
        "referer": "https://vbiz.in/nseoptionchain.html",
        "sec-ch-ua": '"Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
        "sec-ch-ua-mobile": "?0",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36",
    }

    return requests.get(url=url, headers=headers)
