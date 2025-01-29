import streamlit as st
import pandas as pd
import os


st.title("Tagging images")

input_df = pd.read_csv(r"extracted_tags_images.csv")
output_df = []
images_folder = r"images"

for index, row in input_df.iterrows():
    container = st.container(border = True)
    file_name = row["file"]
    text = row["text"]
    tags = row["extracted_tags"].split(",")

    container = st.container(border = True)
    with container:
        col1, col2 = st.columns(2, border = True)

        with col1:
            col1.subheader(file_name)
            file_path = os.path.join(images_folder, file_name)
            st.image(file_path, use_container_width=True)

        with col2:
            col2.subheader("Tags")
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
        "description": text,
        "extracted_tags": row["extracted_tags"],
        "approved_tags": selected_tags
    })

output_df = pd.DataFrame(output_df)

st.write("Approved tags")
st.dataframe(output_df)

st.download_button("Download data as csv",
                   data = output_df.to_csv(index = False),
                   file_name = "approved_tags_iamges.csv",
                   mime = "text/csv")

