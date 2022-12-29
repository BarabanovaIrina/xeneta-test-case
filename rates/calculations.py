from typing import Dict, List


def find_average_for_more_than_n_days(
    result: Dict[str, List], days_num: int
) -> List[Dict]:
    return [
        {
            "day": key,
            "average_price": round(sum(value) / len(value)),
        } if len(value) >= days_num else
        {
            "day": key,
            "average_price": None,
        }
        for key, value in result.items()
    ]
