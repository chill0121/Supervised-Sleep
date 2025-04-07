import psycopg2
from database import db_utilities, views
from config import settings
from oura_api.fetch_data import fetch_process_save_data, fetch_historical_data
from dashboard.export_to_tableau import generate_tableau_data

from multiprocessing import Process
import uvicorn
from api.server import app
import time

def start_api():
    uvicorn.run('api.server:app', host=settings.API_IP, port=settings.API_PORT, reload=True)

def main():
    """Main function to initialize database and create tables."""
    # fetch_historical_data()

    # Start API in a separate process.
    api_process = Process(target=start_api)
    api_process.start()
    time.sleep(2)

    try:
        
        # Oura Data Fetch
        # fetch_process_save_data()

        connection = psycopg2.connect(database=settings.DB_NAME, user=settings.DB_USER, host=settings.DB_HOST, port=settings.DB_PORT)
        # Delete All for troubleshooting.
        # for table in db_utilities.table_dict.keys():
        #     db_utilities.delete_table(connection, table)
        
        # Create All
        # for table, columns in db_utilities.table_dict.items():
        #     db_utilities.create_table(connection, {table: columns})
        # db_utilities.insert_json_files_to_db(connection, 1)
        
        # Generate Views
        views.initialize_materialized_views(connection)
        # Database to Dashboard API
        generate_tableau_data()
        
        
        # fetch_data_for_tableau()
        

        connection.close()

    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")

    # Do not join the API process, let it continue running.
    print("API is running. Main setup is complete.")

    
    
if __name__ == '__main__':

    main()