from datetime import datetime, timedelta
from typing import Dict, List


def fill_in_missed_dates(
    result: Dict[str, List], date_from: str, date_to: str
) -> Dict[str, List]:
    def datetime_range(date_from: datetime, date_to: datetime):
        for n in range(int((date_to - date_from).days) + 1):
            yield date_from + timedelta(n)

    date_format = "%Y-%m-%d"
    date_from = datetime.strptime(date_from, date_format)
    date_to = datetime.strptime(date_to, date_format)

    for date in datetime_range(date_from, date_to):
        if not (str_date := date.strftime(date_format)) in result.keys():
            result.update({str_date: []})

    return {k : result[k] for k in sorted(result)}
