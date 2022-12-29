from collections import defaultdict
from typing import List, Dict, Tuple

from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection
from rates.utils import fill_in_missed_dates
from rates.calculations import find_average_for_more_than_n_days

app = Flask('app')
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['JSON_SORT_KEYS'] = False

engine = create_engine("postgresql+psycopg2://postgres:ratestask@localhost:5432/postgres")

# Pros of the current db schema:
#   if new region is added -> no need to make an insert to a tree
#   the recursion will "swallow" it
# Ideas to solve the problem:
# 1. Preprocess. Make a preprocessing of the whole database:
#    add additional table with 'region_name': List[PortCode]
#    pros:
#      - in the moment of query take just make select from prices where origin in
#        regions.ports and destination in regions.ports
#      - 1 query and fast response
#    cons:
#      - idk how expensive is to make such a preprocessing for big db
#      - after adding a new port/region this additional table must be updated,
#        so pipeline/triger is needed.
# 2. Cache. Fill an additional table step by step:
#    if the region was already "parsed" then take from additional table its ports
#    otherwise find ports and add to the table.
#    pros:
#      - no need to preprocess the whole db and add rows to this additional tables
#        which might not be ever used
#      - the repetitive requests are processed faster
#      - no need to parse the requests which will never be called
#    cons:
#      - the time of response depends on whether the region has been already parsed
#        or not. On the other hand the repetitive requests are processed faster.
#      - after adding a new port/region this additional table must be updated,
#        so pipeline/trigger is needed.


@app.route('/')
def index():
    return 'Halo'


@app.get('/rates')
def get_list_of_average_prices():
    date_from = request.args.get("date_from", "2016-01-01")
    date_to = request.args.get("date_to", "2016-01-01")
    origin = request.args.get("origin", "")
    destination = request.args.get("destination", "")

    # select by date from prices
    query_by_dates = f"SELECT CAST(day AS VARCHAR), price from prices p where p.day between '{date_from}' and '{date_to}'"
    with engine.connect() as connection:
        _, origin_ports = find_ports_from_all_subregions([origin], [], connection)
        _, destination_ports = find_ports_from_all_subregions([destination], [], connection)

        # might be joined to the main request ?
        # orig_ports = find_ports_for_one_region(origin_sub_regions, connection)
        if not origin_ports:
            origin_ports = [origin]
        sql_like_orig_ports = _make_sql_like_group(origin_ports)

        # dest_ports = find_ports_for_one_region(destination_sub_regions, connection)
        if not destination_ports:
            destination_ports = [destination]
        sql_like_dest_ports = _make_sql_like_group(destination_ports)

        partial_query_by_ports = f" and p.orig_code in ({sql_like_orig_ports}) and p.dest_code in ({sql_like_dest_ports})"
        results = connection.execute(query_by_dates + partial_query_by_ports)

        transformed = defaultdict(list)
        for result in results:
            transformed[result.day].append(result.price)

    if not transformed:
        return "No results found for your request"

    filled_data = fill_in_missed_dates(transformed, date_from, date_to)
    final = find_average_for_more_than_n_days(filled_data, 3)
    return final


def find_ports_from_all_subregions(
    regions: List[str], ports: List[str], connection: Connection
) -> Tuple[List[str], List[str]]:
    for region in regions:
        sub_ports = find_ports_for_one_region([region], connection)
        ports.extend(sub_ports)
        get_sub_regions = f"SELECT slug from regions r where r.parent_slug = '{region}'"
        results = connection.execute(get_sub_regions)
        transformed_results = [result.slug for result in results]
        if not transformed_results:
            return regions, ports
        else:
            regions.remove(region)
            regions.extend(transformed_results)
            return find_ports_from_all_subregions(regions, ports, connection)


def find_ports_for_one_region(
    regions: List[str], connection: Connection
) -> List[str]:
    transformed = (f"'{region}'" for region in regions)
    get_ports = f"SELECT code from ports p where p.parent_slug in ({', '.join(transformed)})"
    results = connection.execute(get_ports)
    return [result.code for result in results]


def _make_sql_like_group(elems: List[str]) -> str:
    transformed = (f"'{elem}'" for elem in elems)
    return ', '.join(transformed)


if __name__ == '__main__':
    app.run()
