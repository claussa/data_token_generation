import base64
import json
import tempfile

import country_converter as coco
import numpy as np
import pandas as pd
import streamlit as st
from iso639 import Lang

st.title('Data token generation')

social_media = st.radio(
    "Chosse social media",
    ["instagram", "tiktok"],
)

st.text("Import CSV here")
form = st.form("my_form", clear_on_submit=True)
uploaded_files = form.file_uploader('CSV', type='csv', accept_multiple_files=True)
submit = form.form_submit_button("Generate data token")

if submit:
    if uploaded_files is not None and social_media is not None:
        my_bar = st.progress(0, text="Cleaning CSV data ...")
        dfs = []

        # Process each uploaded file
        for i, uploaded_file in enumerate(uploaded_files):
            # Update progress bar
            progress = int((i + 1) / len(uploaded_files) * 20)
            my_bar.progress(progress, text=f"Processing file {i+1} of {len(uploaded_files)}...")

            # Read and clean individual CSV
            temp_df = pd.read_csv(uploaded_file, skiprows=5)
            temp_df = temp_df.replace('', np.nan)

            # Add to list of dataframes
            dfs.append(temp_df)

        df = pd.concat(dfs, ignore_index=True)
        # Remove potential duplicates
        df = df.drop_duplicates(subset=['Username'], keep='first')

        my_bar.progress(20, text="Generate data token ...")

        # Convert country codes
        df['iso_country'] = df['Creator\'s Country'].map(lambda country: coco.convert(country, to='ISO2'))

        # Convert language codes
        df['iso_language'] = df['Creator\'s Language'].map(lambda lang: Lang(lang).pt1)

        if social_media == "instagram":
            df['social_media_url'] = 'https://www.instagram.com/' + df['Username']
        else:
            df['social_media_url'] = 'https://www.tiktok.com/@' + df['Username']

        df['data_token'] = df.apply(lambda row: base64.b64encode(json.dumps({
            "social_media": social_media,
            "social_media_username": row['Username'],
            "social_media_url": row['social_media_url'],
            "email": row['Email'],
            "followers_count": int(row['Followers Count']) if pd.notna(row['Followers Count']) else None,
            "full_name": row['Full Name'],
            "country": row['iso_country'],
            "language": row['iso_language']
        }).encode('utf-8')).decode('utf-8'), axis=1)

        my_bar.progress(65, text="Prepare data for extraction ...")
        df['social_media'] = social_media

        export_df = df[['data_token', 'social_media', 'Username', 'social_media_url', 'Email']].copy()

        # Rename columns to match the requested format
        export_df = export_df.rename(columns={
            'Username': 'social_media_username',
            'Email': 'email'
        })
        my_bar.progress(85, text="Exporting CSV ...")
        with tempfile.NamedTemporaryFile() as temp:
            export_df.to_csv(temp.name, index=False)
            f = open(temp.name, 'rb')
            def on_click():
                f.close()

            my_bar.empty()
            st.download_button(
                'Download the csv',
                f,
                mime='text/csv',
                file_name='output.csv',
                on_click=on_click
            )
    else:
        st.warning("You need to fill all field")
