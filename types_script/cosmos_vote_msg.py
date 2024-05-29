#!/usr/bin/python3
'''**********************************************************************************
                                                                                    *
Project Name: cosmos_vote_msg.py                                                    *
                                                                                    *
Programming Language: Python 3.11                                                   *
                                                                                    *
Libraries: json   sys                                                                  *
                                                                                    *
Creater Name: Ziqi Yang                                                             *
                                                                                    *
Published Date: 5/27/2024                                                           *
                                                                                    *
Version: 1.0                                                                        *
                                                                                    *
                                                                                    *
**********************************************************************************'''

#    Scripts start below
from functions import create_connection
import json
from psycopg2 import errors
import sys

def main(tx_id, message_no, transaction_no, tx_type, message, ids):

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
    try:
        # Define the values
        proposal_id = message['proposal_id']
        option = message['option']
        if message['metadata'] == None:
            metadata = ''
        else:
            metadata = message['metadata']
        message = json.dumps(message)
        comment = f'This is number {message_no} message in number {transaction_no} transaction '


        # Edit the query that will be loaded to the database
        query = """
        INSERT INTO cosmos_vote_msg (tx_id, tx_type, proposal_id, voter_address_id, options, metadata, message_info, comment) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """

        values = (tx_id, tx_type, proposal_id, ids['voter_id'], option, metadata, message, comment)
        cursor.execute(query, values)

        connection.commit()
        connection.close()

    except KeyError:
        print(f'KeyError happens in type {tx_type}', file=sys.stderr)
    except errors.UniqueViolation as e:
        pass



if __name__ == '__main__':
    main(tx_id, message_no, transaction_no, tx_type, message, ids)
