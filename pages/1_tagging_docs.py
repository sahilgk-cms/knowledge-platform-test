import streamlit as st
import pandas as pd
import os


st.title("Tagging documents - pdfs, ppts, word docs, excel/csv")

input_df = pd.read_csv(r"C:\Users\hp\CMS\knowledge_platform\extracted_tags_docs.csv")

output_df = []


for index, row in input_df.iterrows():
    container = st.container(border = True)
    file_name = row["file"]
    text = row["text"]

    if pd.isna(row["extracted_tags"]):
        tags = "No tags"
    else:
        tags = row["extracted_tags"].split(",")

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
            #selected_tags = []
            
            selected_tags = st.multiselect(label = "Select tags",
                                     options = tags,
                                     key = f"multi_select_{index}")
            # for tag in tags:
            #     if st.checkbox(tag, key=f"checkbox_{index}_{tag}"):
            #         selected_tags.append(tag)

            new_tag = st.text_input("Enter new tags separated by commas", key = f"text_input_{index}", placeholder = "Enter tag")

            if new_tag:
                new_tags = [tag.strip() for tag in new_tag.split(",") if tag.strip()]
                selected_tags.extend(new_tags)

            selected_tags = ", ".join(selected_tags)



    output_df.append({
        "index": index,
        "file": file_name,
        "text": text,
        "extracted_tags": row["extracted_tags"],
        "approved_tags": selected_tags
    })


output_df = pd.DataFrame(output_df)

st.write("Approved tags")
st.dataframe(output_df)

st.download_button("Download data as csv",
                   data = output_df.to_csv(index = False),
                   file_name = "approved_tags_docs.csv",
                   mime = "text/csv")




