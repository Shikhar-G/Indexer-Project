#!/usr/bin/python3
'''**********************************************************************************
                                                                                    *
Project Name: address_load.py                                                         *
                                                                                    *
Programming Language: Python 3.11                                                   *
                                                                                    *
Libraries: json                                                                     *
                                                                                    *
Creater Name: Ziqi Yang                                                             *
                                                                                    *
Published Date: 4/15/2024                                                           *
                                                                                    *
Version: 1.0                                                                        *
                                                                                    *
Version: 1.1
Now 'address_load' only needs one input. Also, the info of 'address_type' has
changed to only three condition, 'user', 'validator', and 'contract'.               *
                                                                                    *
**********************************************************************************'''

#    Scripts start below
from functions import create_connection
from datetime import datetime
import json
from psycopg2 import errors
import sys

def main(address):

    with open('info.json', 'r') as f:
        info = json.load(f)

    db_name = info['psql']['db_name']
    db_user = info['psql']['db_user']
    db_password = info['psql']['db_password']
    db_host = info['psql']['db_host']
    db_port = info['psql']['db_port']

    connection = create_connection(db_name, db_user, db_password, db_host, db_port)
    cursor = connection.cursor()

    # Define the values
    comment = ''
    created_time = datetime.now()
    updated_time = created_time

    # Find the index of number 1 in the string
    index_of_1 = address.find('1')
    # Count the length after 1
    substring_after_1 = address[index_of_1 + 1:]
    length_after_1 = len(substring_after_1)
    # If the string contains 'valoper' string, this is a validator address
    validator = 'valoper'
    if validator in address:
        address_type = 'validator'
    # If the length larger than 38, this is a contract address
    elif length_after_1 >= 38:
        address_type = 'contract'
    # If the length after 1 equals 38, this is a user address
    elif length_after_1 == 38:
        address_type = 'user'
    # If the address does not belong to three types above, it will be an unknown type
    else:
        address_type = 'Unknown'
        print("The type of address could not be detected, check address", file=sys.stderr)

    query = """
    INSERT INTO address (address_type, addresses, comment, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)
    RETURNING address_id;
    
    """


    # Load the values
    values = (address_type, address, comment, created_time, updated_time)
    try:
        cursor.execute(query, values)
        address_id = cursor.fetchone()[0]

    except errors.UniqueViolation as e:
        connection.rollback()
        search_query = f"SELECT address_id FROM address WHERE addresses = '{address}'"
        cursor.execute(search_query)
        address_id = cursor.fetchone()[0]

    connection.commit()
    connection.close()
    return address_id

if __name__ == '__main__':
    main(address)
