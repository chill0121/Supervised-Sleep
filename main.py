import psycopg2
from database.db_utilities import * #create_table, delete_table, table_list, DB_NAME, DB_USER, DB_HOST, DB_PORT
from config.settings import * #BASE_DIR, TOKEN_PATH, DATA_DIR, TODAY, TODAY_DATETIME
from oura_api.fetch_data import fetch_process_save_data, fetch_historical_data

def main():
    """Main function to initialize database and create tables."""
    # fetch_historical_data()
    try:
        #fetch_process_save_data()
        connection = psycopg2.connect(database=DB_NAME, user=DB_USER, host=DB_HOST, port=DB_PORT)
        # Delete All for troubleshooting.
        for table in table_dict.keys():
            delete_table(connection, table)
        
        # Create All
        for table, columns in table_dict.items():
            create_table(connection, {table: columns})

        insert_json_files_to_db(connection, 1)
        connection.close()

    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")

    
    
if __name__ == '__main__':
    main()