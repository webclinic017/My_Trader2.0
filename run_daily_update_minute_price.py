from my_libs import *



########################
# New Minute Data
########################


try:

    mongod = mongo()
    runtime = mongod.update_db_new_minute_mongo()


    send_email("New Minute Data runtime: " + str(runtime))

except Exception as e:
    send_email("New Minute Data error: " + str(e))
