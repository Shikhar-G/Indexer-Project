#    Scripts start below
from functions import create_connection
import json
from psycopg2 import errors

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
        # Edit the query that will be loaded to the database
        query = """
                INSERT INTO cosmwasm_instantiatecontract_msg (tx_id, tx_type, send_address_id, admin_address_id, code_id, label, msg_swap_venues,funds, message_info, comment) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """

        # Define the values
        sender = ids['sender_id']
        admin = ids['admin_id']
        if(sender != ids['sender_id']):
            sender = message['sender']#s
        if(admin != ids['admin_id']):
            admin = message['admin']
        code_id = message['code_id']
        label = message['label']
        msg = list(message['msg']['swap_venues'])
        funds = message['funds']
        message = json.dumps(message)
        comment = f'This is number {message_no} message in number {transaction_no} transaction '


        values = (tx_id, tx_type, sender, admin, code_id, label, msg,funds, message,comment)
        cursor.execute(query, values)

        connection.commit()
        connection.close()

    except KeyError:
        print(f'KeyError happens in type {tx_type}', file=sys.stderr)
    except errors.UniqueViolation as e:
        pass

if __name__ == '__main__':
    main(tx_id, message_no, transaction_no, tx_type, message, ids)
