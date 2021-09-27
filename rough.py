import datetime
import time

from apis.utils import get_constructed_data

ce_data = get_constructed_data()['38100_ce']

result = [ce_data]
time_result = []

for _ in range(60):
    new_ce_data=get_constructed_data()['38100_ce']
    if new_ce_data != result[-1]:
        time_result.append(datetime.datetime.now())
        result.append(new_ce_data)
    time.sleep(1)

print(time_result)