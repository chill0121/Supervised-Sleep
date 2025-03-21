import psycopg2
from database import db_utilities, views #create_table, delete_table, table_list
from config import settings #BASE_DIR, TOKEN_PATH, DATA_DIR, TODAY, TODAY_DATETIME
from oura_api.fetch_data import fetch_process_save_data, fetch_historical_data

def main():
    """Main function to initialize database and create tables."""
    # fetch_historical_data()
    try:
        fetch_process_save_data()

        connection = psycopg2.connect(database=settings.DB_NAME, user=settings.DB_USER, host=settings.DB_HOST, port=settings.DB_PORT)
        # Delete All for troubleshooting.
        # for table in db_utilities.table_dict.keys():
        #     db_utilities.delete_table(connection, table)
        
        # Create All
        for table, columns in db_utilities.table_dict.items():
            db_utilities.create_table(connection, {table: columns})
        db_utilities.insert_json_files_to_db(connection, 1)

        views.initialize_materialized_views(connection)

        connection.close()

    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")

    
    
if __name__ == '__main__':
    main()