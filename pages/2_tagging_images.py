import streamlit as st
import pandas as pd
import os
from utils_mongodb import *
from utils_gdrive import *
from time import time


st.title("Tagging images")

df = pd.read_csv(r"extracted_tags_images.csv")

#initialize approved tags session state
if "approved_tags" not in st.session_state:
    st.session_state.approved_tags = {}


#save the csv in mongodb
#save_dataframe_to_mongodb(dataframe = df, collection = IMG_COLLECTION)

#load the csv from mongodb
#input_df = load_dataframe_from_mongodb(collection = IMG_COLLECTION)
input_df = df


output_df = []

#persist the session state for files where there are approved tags
for _, row in input_df.iterrows():
    if row["file"] not in st.session_state.approved_tags:
        st.session_state.approved_tags[row["file"]] = row.get("approved_tags", "")

@st.cache_data
def get_cached_file_ids():
    file_ids = get_all_file_ids_from_parent_folder(IMAGES_FOLDER)
    return file_ids

file_ids = get_cached_file_ids()


images_folder = IMAGES_FOLDER

#input_df = input_df.fillna("")
#input_df = input_df[:5]


for index, row in input_df.iterrows():
    container = st.container(border = True)
    file_name = row["file"]
    text = row["text"]
    extracted_tags = row["extracted_tags"].split(",")
    approved_tags = row.get("approved_tags", "")

    #if the session state doen't have approved tags then update it
    if file_name not in st.session_state.approved_tags:
        st.session_state.approved_tags[file_name] = approved_tags

    container = st.container(border = True)
    with container:
        col1, col2 = st.columns(2, border = True)

        with col1:
            col1.subheader(file_name)
            file_id = file_ids.get(file_name, None)

            if file_id is None:
                file_id = get_missing_file_id(file_name)
                if file_id:
                    file_ids[file_name] = file_id

            file_url = display_image_from_file_id(file_id)
           # st.write(file_url)
            if file_url:
                display_image(file_url)
            else:
                st.error("Image not found in Google Drive")

        with col2:
            col2.subheader("Tags")
            
            #load the previous tags if any
            previous_tags = st.session_state.approved_tags.get(file_name, "")
            if isinstance(previous_tags, float) and pd.isna(previous_tags):
                previous_tags = ""
            previous_tags_list = previous_tags.split(", ") if previous_tags else []

            valid_defaults = [tag for tag in previous_tags_list if tag in extracted_tags]

            #wrap multi-select, manual text area & submit button in form structure
            with st.form(key = f"form_{index}"):
                selected_tags = st.multiselect(label = "Select tags",
                                        options = extracted_tags,
                                        default = valid_defaults,
                                        key = f"multi_select_{index}")

                new_tag = st.text_area("Enter new tags separated by commas", key = f"text_input_{index}", placeholder = "Enter tag")
                submitted = st.form_submit_button("Save to database")

            #after clicking on submit button
            if submitted:

                #if tags are entered in text area
                if new_tag:
                    new_tags = [tag.strip() for tag in new_tag.split(",") if tag.strip()]
                    selected_tags.extend(new_tags)

                #update the session state & save to MongoDB
                selected_tags = ", ".join(selected_tags)
                st.session_state.approved_tags[file_name] = selected_tags
                updated_df = pd.DataFrame([{
                    "index": index,
                    "file": file_name,
                    "text": text,
                    "extracted_tags": row["extracted_tags"],
                    "approved_tags": st.session_state.approved_tags[file_name]
                }])
                #update_dataframe_to_mongodb(dataframe = updated_df, collection = IMG_COLLECTION)

            #display the approved tags
            st.markdown(f"🏷️ **Approved Tags:** `{st.session_state.approved_tags[file_name]}`")
     

    output_df.append({
        "index": index,
        "file": file_name,
        "text": text,
        "extracted_tags": row["extracted_tags"],
        "approved_tags": st.session_state.approved_tags[file_name]
    })

output_df = pd.DataFrame(output_df)

st.write("Approved tags")
st.dataframe(output_df[["file", "approved_tags"]], use_container_width = True, hide_index = True)

st.download_button("Download data as csv",
                   data = output_df.to_csv(index = False),
                   file_name = "approved_tags_iamges.csv",
                   mime = "text/csv")


