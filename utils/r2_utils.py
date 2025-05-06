import boto3
from botocore.client import Config
import streamlit as st

R2_KEY = st.secrets['R2_KEY']
R2_SECRET_KEY = st.secrets['R2_SECRET_KEY']
ENDPOINT_URL = st.secrets['ENDPOINT_URL']

def get_r2_client(R2_KEY, R2_SECRET_KEY, ENDPOINT_URL):
    return boto3.client(
        's3',
        aws_access_key_id=R2_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        endpoint_url=ENDPOINT_URL,
        config=Config(signature_version='s3v4')
    )
