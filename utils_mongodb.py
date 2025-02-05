import pymongo
import pandas as pd
import streamlit as st

MONGODB_URI = "mongodb+srv://sahil:c%40talysts@cluster0.avpob.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
#MONGODB_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "tagging_feedback"
DOC_COLLECTION = "documents_tagging"
IMG_COLLECTION = "images_tagging"


def save_dataframe_to_mongodb(dataframe: pd.DataFrame, collection: str):
    myclient = pymongo.MongoClient(MONGODB_URI)
    db = myclient[DATABASE_NAME]
    col = db[collection]

    new_records = dataframe

    existing_records = list(col.find({}))
    existing_records = pd.DataFrame(existing_records)
    
    if not existing_records.empty:
        new_rows = new_records[~new_records["file"].isin(existing_records["file"])]
    else:
        new_rows = new_records

    if not new_rows.empty:
        col.insert_many(new_rows.to_dict(orient = "records"))
        st.success(f"Inserted {len(new_rows)} new records into MongoDB")
    else:
        st.info("No new unique records to insert")


def load_dataframe_from_mongodb(collection: str) -> pd.DataFrame:
    myclient = pymongo.MongoClient(MONGODB_URI)
    db = myclient[DATABASE_NAME]
    col = db[collection]

    df = pd.DataFrame(list(col.find()))
    return df

def update_dataframe_to_mongodb(dataframe: pd.DataFrame, collection: str):
    myclient = pymongo.MongoClient(MONGODB_URI)
    db = myclient[DATABASE_NAME]
    col = db[collection]

    output_df_dict = dataframe.to_dict(orient = "records")

    for record in output_df_dict:
        col.update_one({"file": record["file"]}, {"$set": record}, upsert = True)
    st.success("Saved to MongoDB successfully")
