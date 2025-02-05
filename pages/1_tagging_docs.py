import streamlit as st
import pandas as pd
import os
from utils_mongodb import *




st.title("Tagging documents - pdfs, ppts, word docs")

df = pd.read_csv(r"extracted_tags_docs.csv")

#session state for approved tags
if "approved_tags" not in st.session_state:
    st.session_state.approved_tags = {}

#save the dataframe to mongodb if not already done
#save_dataframe_to_mongodb(dataframe = df, collection = DOC_COLLECTION)

#load dataframe from mongodb
#input_df = load_dataframe_from_mongodb(collection = DOC_COLLECTION)
input_df = df
output_df = []

#persist the session state for files where there are approved tags
for _, row in input_df.iterrows():
    if row["file"] not in st.session_state.approved_tags:
        st.session_state.approved_tags[row["file"]] = row.get("approved_tags", "")


for index, row in input_df.iterrows():
    container = st.container(border = True)
    file_name = row["file"]
    text = row["text"]
    approved_tags = row.get("approved_tags", "")

    if file_name not in st.session_state.approved_tags:
        st.session_state.approved_tags[file_name] = approved_tags

    if pd.isna(row["extracted_tags"]):
        extracted_tags = "No tags"
    else:
        extracted_tags = row["extracted_tags"].split(",")

    if pd.isna(row["sheet_name"]):
        sheet_name = None
    else:
        sheet_name = row["sheet_name"]

    with container:
        st.subheader(file_name)
        if sheet_name:
            st.write(f"Sheet: {sheet_name}")
            
        col1, col2 = st.columns(2, border = True)
        
        with col1:
            col1.subheader("Text")
            with st.expander("Text"):
                st.write(text)
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
                #update_dataframe_to_mongodb(dataframe = updated_df, collection = DOC_COLLECTION)

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
                   file_name = "approved_tags_docs.csv",
                   mime = "text/csv")

# save_to_mongodb = st.button("Save to MongoDB")
# if save_to_mongodb:
#     update_dataframe_to_mongodb(dataframe = output_df, collection = DOC_COLLECTION)



