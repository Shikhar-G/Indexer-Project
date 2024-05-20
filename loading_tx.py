#!/usr/bin/python3
'''**********************************************************************************
                                                                                    *
Project Name: loading_tx.py                                                         *
                                                                                    *
Programming Language: Python 3.11                                                   *
                                                                                    *
Libraries: json    importlib       os                                               *
                                                                                    *
Creater Name: Ziqi Yang                                                             *
                                                                                    *
Published Date: 4/15/2024                                                           *
                                                                                    *
Version: 1.0                                                                        *
                                                                                    *
Version: 1.1
Height now will also be loaded to transaction table, in which 'height' is a column  *
Transaction hash now is included in transaction table as well                       *
                                                                                    *
Version: 1.2                                                                        *
For 'cursor.execute' command, there is 'try' and 'except' to catch UniqueViolation  *
And if UniqueViolation happens, there will be search query to search needed value   *
New package: psycopg2 now applies on this script                                    *
                                                                                    *
**********************************************************************************'''

#    Scripts start below
from functions import check_file
from functions import create_connection
from functions import decode_tx
from functions import hash_to_hex
import json
import importlib
import address_load
import os
from pathlib import Path
import sys


# import the login info for psql from 'info.json'
with open('info.json', 'r') as f:
    info = json.load(f)

db_name = info['psql']['db_name']
db_user = info['psql']['db_user']
db_password = info['psql']['db_password']
db_host = info['psql']['db_host']
db_port = info['psql']['db_port']

connection = create_connection(db_name, db_user, db_password, db_host, db_port)
cursor = connection.cursor()

# Set the path of file
file_path = os.getenv('FILE_PATH')
file_name = os.getenv('FILE_NAME')

# Set the values that will be loaded to database
content = check_file(file_path, file_name)
num = os.getenv('x')
# decoded_response = decode_tx(content['block']['data']['txs'][int(num)])
transaction_string = content['block']['data']['txs'][int(num)]
decoded_response = decode_tx(transaction_string)
tx_hash = hash_to_hex(transaction_string)
chain_id = content['block']['header']['chain_id']
height = content['block']['header']['height']
search_query = f"SELECT block_id FROM blocks WHERE height = '{height}'" # Search the block hash from the block
cursor.execute(search_query)
result = cursor.fetchall()
block_id = result[0][0]
memo = decoded_response['tx']['body']['memo']
fee_denom = decoded_response['tx']['auth_info']['fee']['amount'][0]['denom']
fee_amount = decoded_response['tx']['auth_info']['fee']['amount'][0]['amount']
gas_limit = decoded_response['tx']['auth_info']['fee']['gas_limit']
created_time = content['block']['header']['time']
tx_info = json.dumps(decoded_response)

# Edit the query that will be loaded to the database
query = """
INSERT INTO transactions (block_id, tx_hash, chain_id, height, memo, fee_denom, fee_amount, gas_limit, created_at, tx_info) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING tx_id;
"""
values = (block_id, tx_hash, chain_id, height, memo, fee_denom, fee_amount, gas_limit, created_time, tx_info)

try:
    cursor.execute(query, values)
    tx_id = cursor.fetchone()[0]
except errors.UniqueViolation as e:
    connection.rollback()
    search_query = f"SELECT tx_id FROM transactions WHERE block_id = '{block_id}'"
    cursor.execute(search_query)
    tx_id = cursor.fetchone()
connection.commit()



# ----------------------------------------------------------- Line for message loading ---------------------

# Read the type.json file
with open('type.json', 'r') as f:
    type_json = json.load(f)


# Use FOR LOOP to load every message in the transaction
for message in decoded_response['tx']['body']['messages']:

    ids = {}
    for key in message:
        # Use keywords to catch address keys
        if 'send' in key or 'receiver' in key or 'address' in key or 'grante' in key or 'admin' in key:
            # Define the address value and run the address_load script to load address
            address = message[key]
            ids[f'{key}_id'] = address_load.main(key, address)

    # Define the type of message to find the corresponding python script
    type = message['@type']

    # Load the type and height to type table
    try:
        cursor.execute('INSERT INTO type (type, height) VALUES (%s, %s);', (type, height))
    except errors.UniqueViolation as e:
        pass
    connection.commit()

    try:
        # Find the corresponding value by matching the key
        table_type = type_json[type]
        print(table_type)
        # Go to the diectory that contains the scripts
        module_path = Path(f"{info['path']['types_script_path']}")
        expanded_script_path = os.path.expanduser(module_path)
        sys.path.append(expanded_script_path)
        # Import the corresponding script
        table = importlib.import_module(table_type)
        # If the message contains the address, address_id will be added
        if len(ids) > 0:
            table.main(tx_id,  type, message, ids)
        # If not, address_id will not
        else:
            table.main(tx_id,  type, message)
    except KeyError:
        print(f'Did not find {type} in type.json file')
    except AttributeError:
        print(f'Script {table_type} does not have a main function')
    except ImportError:
        print(f'Script {table_type} could not be found')

cursor.close()
connection.close()


