from my_libs import * 

api_key = "0fb7208227mshc3a081958186ecfp1679c5jsn018ab7050406"

citys = ["concord","antioch","san leandro","stockton","Tracy","Richmond","Brentwood","Pittsburg"]

try:

    ######################## Get Sold List ####################################
    for city in citys:
        table_name = "sold_list"


        querystring = {
            "sort":"sold_date",
            "city":city,
            "offset":0,
            "state_code":"CA",
            "limit":200,
            "radius":20


        }

        url = "https://realtor.p.rapidapi.com/properties/v2/list-sold"


        headers = {
            'x-rapidapi-host': "realtor.p.rapidapi.com",
            'x-rapidapi-key': api_key
            }

        response = requests.request("GET", url, headers=headers, params=querystring)

        listing = response.json()

        listing= pd.DataFrame(listing["properties"])
        if len(listing) > 0:
            

            listing = listing[["property_id","listing_id","address","baths","baths_full","beds",\
                               "building_size","prop_type","last_update","list_date","lot_size",\
                                "rdc_web_url","year_built","price","page_no"]]

            new_listing = pd.DataFrame()
            address = pd.DataFrame()
            building = pd.DataFrame()
            lot = pd.DataFrame()
            for i in listing.index:
                temp = listing.loc[i]
                if temp["lot_size"] == temp["lot_size"]:
                    lot = lot.append(pd.DataFrame(temp["lot_size"],index =[temp.name]))
                temp = temp.drop("lot_size")
                try:
                    del temp["address"]["neighborhoods"]
                except: 
                    pass
                if temp["address"] == temp["address"]:
                    address = address.append(pd.DataFrame(temp["address"],index =[temp.name]))
                temp = temp.drop("address")
                if temp["building_size"] == temp["building_size"]:
                    building = building.append(pd.DataFrame(temp["building_size"],index =[temp.name]))
                temp = temp.drop("building_size")

                new_listing = new_listing.append(temp)
            new_listing = new_listing.join(address).join(building,rsuffix="_building").join(lot,rsuffix="_lot")

            def format_date(data):
                if data is None:
                    return None
                try:
                    return datetime.strptime(data,"%Y-%m-%dT%H:%M:%SZ")
                except:
                    return datetime.strptime(data,"%Y-%m-%d")

            new_listing.last_update = new_listing.last_update.apply(format_date)

            new_listing.list_date = new_listing.list_date.apply(format_date)

            new_listing["Refresh_Date"] = datetime.now()

            ### append new listing to existing  
            mongod = mongo()
            existing = mongod.conn.get_data("select * from Housing.%s "%table_name)
            existing = existing.append(new_listing).drop_duplicates("property_id")
            existing.to_csv(directory + table_name+"_backup.csv",index = False)
            ### update the table
            mongod = mongo()
            mongod.conn.conn.cursor().execute("drop table Housing.%s"%table_name)
            mongod.conn.to_sql(existing,database="Housing",table_name=table_name,if_exists="append")



        ######################## Get Foreclosure List ####################################

        table_name = "foreclosure_list"

        querystring = {
            "sort":"newest",
            "city":city,
            "offset":0,
            "state_code":"CA",
            "limit":200,
            "radius":20,
            "is_foreclosure":True


        }

        url = "https://realtor.p.rapidapi.com/properties/v2/list-for-sale"


        headers = {
            'x-rapidapi-host': "realtor.p.rapidapi.com",
            'x-rapidapi-key': api_key
            }

        response = requests.request("GET", url, headers=headers, params=querystring)

        listing = response.json()

        listing= pd.DataFrame(listing["properties"])
        if len(listing) > 0:
            listing = listing[["property_id","listing_id","address","baths","baths_full","beds",\
                               "building_size","prop_type","last_update","lot_size",\
                                "rdc_web_url","price","page_no","client_display_flags"]]

            new_listing = pd.DataFrame()
            address = pd.DataFrame()
            building = pd.DataFrame()
            lot = pd.DataFrame()
            flags = pd.DataFrame()
            for i in listing.index:

                temp = listing.loc[i]
                if temp["lot_size"] == temp["lot_size"]:
                    lot = lot.append(pd.DataFrame(temp["lot_size"],index =[temp.name]))
                    temp = temp.drop("lot_size")
                try:
                    del temp["address"]["neighborhoods"]
                except: 
                    pass
                if temp["address"] == temp["address"]:
                    address = address.append(pd.DataFrame(temp["address"],index =[temp.name]))
                temp = temp.drop("address")
                if temp["building_size"] == temp["building_size"]:
                    building = building.append(pd.DataFrame(temp["building_size"],index =[temp.name]))
                temp = temp.drop("building_size")
                if temp["client_display_flags"] == temp["client_display_flags"]:
                    flags = flags.append(pd.DataFrame(temp["client_display_flags"],index =[temp.name])[["is_new_listing","is_turbo","is_foreclosure","is_new_plan","has_open_house"]])
                temp = temp.drop("client_display_flags")

                new_listing = new_listing.append(temp)


            new_listing = new_listing.join(address).join(building,rsuffix="building_").join(lot,rsuffix="lot_").join(flags)

            def format_date(data):
                if data is None:
                    return None
                try:
                    return datetime.strptime(data,"%Y-%m-%dT%H:%M:%SZ")
                except:
                    return datetime.strptime(data,"%Y-%m-%d")

            new_listing.last_update = new_listing.last_update.apply(format_date)

            new_listing["Refresh_Date"] = datetime.now()


            ### append new listing to existing  
            # mongod = mongo()
            # existing = mongod.conn.get_data("select * from Housing.%s "%table_name)
            # existing = existing.append(new_listing).drop_duplicates("property_id")
            # existing.to_csv(directory + table_name+"_backup.csv")

            ### append new listing to existing  
            mongod = mongo()
            existing = mongod.conn.get_data("select * from Housing.%s "%table_name)
            existing = existing.append(new_listing).drop_duplicates("property_id")
            existing.to_csv(directory + table_name+"_backup.csv",index = False)
            ### update the table

            mongod.conn.conn.cursor().execute("drop table Housing.%s"%table_name)
            mongod.conn.to_sql(existing,database="Housing",table_name=table_name,if_exists="append")



        ######################## Get For Sale List ####################################

        table_name = "for_sale_list"


        querystring = {
            "sort":"newest",
            "city":city,
            "offset":0,
            "state_code":"CA",
            "limit":200,
            "radius":20,
            "is_foreclosure":False


        }

        url = "https://realtor.p.rapidapi.com/properties/v2/list-for-sale"


        headers = {
            'x-rapidapi-host': "realtor.p.rapidapi.com",
            'x-rapidapi-key': api_key
            }

        response = requests.request("GET", url, headers=headers, params=querystring)

        listing = response.json()

        listing= pd.DataFrame(listing["properties"])
        if len(listing) > 0:
            listing = listing[["property_id","listing_id","address","baths","baths_full","beds",\
                               "building_size","prop_type","last_update","lot_size",\
                                "rdc_web_url","price","page_no","client_display_flags"]]

            new_listing = pd.DataFrame()
            address = pd.DataFrame()
            building = pd.DataFrame()
            lot = pd.DataFrame()
            flags = pd.DataFrame()
            for i in listing.index:

                temp = listing.loc[i]
                if temp["lot_size"] == temp["lot_size"]:
                    lot = lot.append(pd.DataFrame(temp["lot_size"],index =[temp.name]))
                    temp = temp.drop("lot_size")
                try:
                    del temp["address"]["neighborhoods"]
                except: 
                    pass
                if temp["address"] == temp["address"]:
                    address = address.append(pd.DataFrame(temp["address"],index =[temp.name]))
                temp = temp.drop("address")
                if temp["building_size"] == temp["building_size"]:
                    building = building.append(pd.DataFrame(temp["building_size"],index =[temp.name]))
                temp = temp.drop("building_size")
                if temp["client_display_flags"] == temp["client_display_flags"]:
                    flags = flags.append(pd.DataFrame(temp["client_display_flags"],index =[temp.name])[["is_new_listing","is_turbo","is_new_plan","has_open_house"]])
                temp = temp.drop("client_display_flags")

                new_listing = new_listing.append(temp)


            new_listing = new_listing.join(address).join(building,rsuffix="building_").join(lot,rsuffix="lot_").join(flags)

            def format_date(data):
                if data is None:
                    return None
                try:
                    return datetime.strptime(data,"%Y-%m-%dT%H:%M:%SZ")
                except:
                    return datetime.strptime(data,"%Y-%m-%d")

            new_listing.last_update = new_listing.last_update.apply(format_date)

            new_listing["Refresh_Date"] = datetime.now()



            ### append new listing to existing  
            mongod = mongo()
            existing = mongod.conn.get_data("select * from Housing.%s "%table_name)
            existing = existing.append(new_listing).drop_duplicates("property_id")
            existing.to_csv(directory + table_name+"_backup.csv",index = False)
            ### update the table

            mongod.conn.conn.cursor().execute("drop table Housing.%s"%table_name)
            mongod.conn.to_sql(existing,database="Housing",table_name=table_name,if_exists="append")


    #     ### update the table
    #     mongod = mongo()
    #     # mongod.conn.conn.cursor().execute("drop table Housing.%s"%table_name)
    #     mongod.conn.to_sql(new_listing,database="Housing",table_name=table_name,if_exists="append")

    send_email(title="Housing Data Finished",body_html= "")
except Exception as e:
    send_email(title="Housing Data Error %s"%str(e),body_html= "")