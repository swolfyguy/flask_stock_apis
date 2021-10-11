import requests

strategy_id_name_dct = {
    1: "BankNifty Pyramiding_1",
    2: "Nifty50 Pyramiding_1",
    3: "BankNifty Pyramiding_10",
    4: "Nifty50 Pyramiding_10",
    5: "BajFinance Pyramiding_10",
    6: "AxisBank Pyramiding_10",
    7: "TataMotors Pyramiding_10",
}


def fetch_data(symbol="BANKNIFTY", expiry="14 OCT 2021"):
    if symbol in ["BANKNIFTY", "NIFTY"]:
        atyp = "OPTIDX"
        expiry = expiry
    else:
        atyp = "OPTSTK"
        expiry = "28 OCT 2021"

    return requests.post(
        "https://ewmw.edelweiss.in/api/Market/optionchaindetails",
        data={"exp": expiry, "aTyp": atyp, "uSym": symbol},
    ).json()["opChn"]

    # TODO do not remove this unless you are confident that above code will work for atleast 15 days
    # expiry = "30SEP2021"
    # url = f"https://vbiz.in/optionchain/foc.php?symbol={symbol}&expiry={expiry}"
    # headers = {
    #     "accept": "*/*",
    #     "accept-encoding": "gzip, deflate, br",
    #     "accept-language": "en-IN,en;q=0.9,hi-IN;q=0.8,hi;q=0.7,mr-IN;q=0.6,mr;q=0.5,en-GB;q=0.4,en-US;q=0.3",
    #     "cookie": "_ga=GA1.2.1230482458.1627675123; _gcl_au=1.1.598369330.1627675123; __tawkuuid=e::vbiz.in::vPlQa5Qtjn+TEni/bUWAUpK8oSnd68QMNNjIuP+nfD/Xydd6X71pTiw950uWVEwr::2; HstCfa4543512=1632894969432; HstCla4543512=1632894969432; HstCmu4543512=1632894969432; HstPn4543512=1; HstPt4543512=1; HstCnv4543512=1; HstCns4543512=1",
    #     "referer": "https://vbiz.in/nseoptionchain.html",
    #     "sec-ch-ua": 'Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93',
    #     "sec-ch-ua-mobile": "?0",
    #     "sec-fetch-dest": "empty",
    #     "sec-fetch-mode": "cors",
    #     "sec-fetch-site": "same-origin",
    #     "sec-ch-ua-platform": "macOS",
    #     "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
    # }
    #
    # return requests.get(url=url, headers=headers)
