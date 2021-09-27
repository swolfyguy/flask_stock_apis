import datetime
import time

from apis.utils import get_constructed_data, get_profit
from extensions import db
from models.nfo import NFO

ce_data = get_constructed_data()


for nfo in NFO.query.filter(NFO.profit == None).all():
    nfo.profit = get_profit(nfo, ce_data[f'{nfo.strike}_ce'])
db.session.commit()

# result = [ce_data]
# time_result = []
#
# for _ in range(60):
#     new_ce_data=get_constructed_data()['38100_ce']
#     if new_ce_data != result[-1]:
#         time_result.append(datetime.datetime.now())
#         result.append(new_ce_data)
#     time.sleep(1)
#
# print(time_result)