import pymysql
import pandas as pd
import time
import datetime
import numpy as np
import sqlalchemy as sa
# def connect_dw(sql,server_name = 'rkhrimdb01',tcon = 'yes'):
#     # return pandas dataframe
#     conn = pyodbc.connect(Driver='{ODBC Driver 11 for SQL Server}', host=server_name, trusted_connection=tcon)
#     cursor = conn.cursor()
#     return pd.read_sql(sql,conn) , cursor

# pd.options.display.max_rows = 2000
# pd.options.display.max_columns = 2000


class connect_sql():
    def __init__(self, user, pwd ,host='localhost', database = None):
        # return pandas dataframe
        self.host = host
        self.user = user
        if database == None:
            self.conn = pymysql.connect(host,
                                        user=user,
                                        passwd=pwd,                        
                                        connect_timeout=5)
        else:
            self.conn = pymysql.connect(host,
                                        user=user,
                                        passwd=pwd,
                                        db=database,
                                        connect_timeout=5)
        
        self.cursor = self.conn.cursor()

    def to_sql(self, data, database, table_name, dtype = None,if_exists = 'fail' ):
#         check = input("Caution!! Type 'Confirm to continue'")
#         if check != "Confirm":
#             print ("no action")
#             return 

        engine = sa.create_engine("mysql+pymysql://%s:@%s/%s"%(self.user,self.host,database), poolclass=sa.pool.StaticPool, creator=lambda: self.conn,fast_executemany = True)
        

        
    
        if dtype == None:
            data.to_sql(name=table_name,
                      con=engine,
                      schema=database,
                      index=False,
                      if_exists=if_exists)    
        else:
            data.to_sql(name=table_name,
                      con=engine,
                      schema=database,
                      index=False,
                      if_exists=if_exists,dtype=dtype)
            
        
        print ("If no error message, task completed")
#         self.conn.close()

    def get_data(self, sql):
        get = pd.DataFrame()
        for chunk in pd.read_sql(sql, self.conn,chunksize = 10000):
            get = get.append(chunk)
#             print("Finish 1 chunk")
        
        return get
    

def read_file(path):
    with open(path, 'r') as f:
        return f.read()
    
    
def get_columns(database,table):
    conn = connect_sql(database =  database)

    col_list = []
    for row in conn.cursor.columns(table =table):
        col_list.append(row.column_name)

    return col_list
