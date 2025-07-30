import json
import logging
import os
import sqlite3
import pandas as pd
import hashlib
from pathlib import Path

from refiner.models.offchain_schema import OffChainSchema
from refiner.models.output import Output
from refiner.config import settings
from refiner.utils.encrypt import encrypt_file
from refiner.utils.ipfs import upload_file_to_ipfs, upload_json_to_ipfs

class Refiner:
    def __init__(self):
        self.db_path = os.path.join(settings.OUTPUT_DIR, 'refined.sqlite')

    def _hash_wallet_address(self, wallet_address: str) -> str:
        """Create a privacy-safe account ID from wallet address."""
        return hashlib.sha256(wallet_address.encode()).hexdigest()[:16]

    def _detect_file_type(self, df: pd.DataFrame) -> str:
        """Detect if CSV is viewing activity or billing history."""
        columns = {col.lower().strip() for col in df.columns}
        
        # Real Netflix viewing activity indicators
        viewing_indicators = {'start time', 'duration', 'title', 'profile name', 'device type', 'bookmark'}
        # Real Netflix billing history indicators  
        billing_indicators = {'transaction date', 'gross sale amt', 'currency', 'payment type', 'pmt status'}
        
        viewing_score = len(columns & viewing_indicators)
        billing_score = len(columns & billing_indicators)
        
        if viewing_score > billing_score:
            return 'viewing'
        elif billing_score > viewing_score:
            return 'billing'
        else:
            return 'unknown'

    def _process_viewing_activity(self, df: pd.DataFrame, account_id: str) -> pd.DataFrame:
        """Process viewing activity CSV into standardized format."""
        # Create account_id column
        df['account_id'] = account_id
        
        # Standardize column names to match real Netflix format
        column_mapping = {
            'start time': 'start_time',
            'duration': 'duration',
            'title': 'title',
            'profile name': 'profile_name',
            'device type': 'device_type',
            'country': 'country',
            'bookmark': 'bookmark',
            'latest bookmark': 'latest_bookmark',
            'supplemental video type': 'supplemental_video_type',
            'attributes': 'attributes'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Add duration_sec column for easier SQL queries
        if 'duration' in df.columns:
            df['duration_sec'] = df['duration'].apply(self._parse_duration)
            logging.info(f"Converted {len(df)} duration values to seconds")
        
        return df

    def _process_billing_history(self, df: pd.DataFrame, account_id: str) -> pd.DataFrame:
        """Process billing history CSV into standardized format."""
        # Create account_id column
        df['account_id'] = account_id
        
        # Standardize column names to match real Netflix format
        column_mapping = {
            'transaction date': 'transaction_date',
            'country': 'country',
            'mop last 4': 'mop_last_4',
            'final invoice result': 'final_invoice_result',
            'mop pmt processor desc': 'mop_pmt_processor_desc',
            'pmt txn type': 'pmt_txn_type',
            'description': 'description',
            'gross sale amt': 'gross_sale_amt',
            'pmt status': 'pmt_status',
            'payment type': 'payment_type',
            'tax amt': 'tax_amt',
            'service period start date': 'service_period_start_date',
            'item price amt': 'item_price_amt',
            'mop creation date': 'mop_creation_date',
            'currency': 'currency',
            'next billing date': 'next_billing_date',
            'service period end date': 'service_period_end_date'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Convert numeric columns to proper types
        numeric_columns = ['gross_sale_amt', 'tax_amt', 'item_price_amt']
        for col in numeric_columns:
            if col in df.columns:
                # Remove currency symbols and convert to float
                df[col] = df[col].astype(str).str.replace('$', '').str.replace(',', '')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        return df

    def _parse_duration(self, duration_str: str) -> int:
        """Parse Netflix duration string to seconds."""
        try:
            if pd.isna(duration_str) or duration_str == "":
                return 0
            
            # Handle formats like "1:23:45" or "23:45"
            parts = str(duration_str).split(':')
            if len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            else:
                return 0
        except:
            return 0

    def transform(self) -> Output:
        """Transform Netflix CSV files into SQLite database."""
        logging.info("Starting Netflix CSV data transformation")
        output = Output()

        # Get wallet address from environment
        wallet_address = os.getenv('WALLET_ADDRESS')
        if not wallet_address:
            logging.warning("No WALLET_ADDRESS provided, using fallback")
            wallet_address = "unknown"
        
        # Generate consistent account_id from wallet address
        account_id = self._hash_wallet_address(wallet_address)
        logging.info(f"Using account_id: {account_id} for wallet: {wallet_address[:10]}...")
        
        # Create SQLite database
        with sqlite3.connect(self.db_path) as conn:
            for input_filename in os.listdir(settings.INPUT_DIR):
                input_file = os.path.join(settings.INPUT_DIR, input_filename)
                if os.path.splitext(input_file)[1].lower() == '.csv':
                    logging.info(f"Processing {input_filename}")
                    
                    # Read CSV file
                    df = pd.read_csv(input_file)
                    
                    # Detect file type
                    file_type = self._detect_file_type(df)
                    
                    if file_type == 'viewing':
                        # Process viewing activity
                        processed_df = self._process_viewing_activity(df, account_id)
                        processed_df.to_sql("viewing_activity", conn, if_exists="append", index=False)
                        logging.info(f"Added {len(processed_df)} viewing activity records")
                        
                    elif file_type == 'billing':
                        # Process billing history
                        processed_df = self._process_billing_history(df, account_id)
                        processed_df.to_sql("billing_history", conn, if_exists="append", index=False)
                        logging.info(f"Added {len(processed_df)} billing history records")
                        
                    else:
                        logging.warning(f"Unknown file type for {input_filename}")

        # Load schema from file
        schema_file = os.path.join(settings.BASE_DIR, 'schema.json')
        with open(schema_file, 'r') as f:
            schema_data = json.load(f)
        
        # Create schema object
        schema = OffChainSchema(
            name="netflix-csv",
            version="1.0.0",
            description="Netflix viewing activity and billing history data",
            dialect="sqlite",
            schema=schema_data
        )
        output.schema = schema
        
        # Upload schema to IPFS
        schema_ipfs_hash = upload_json_to_ipfs(schema.model_dump())
        logging.info(f"Schema uploaded to IPFS with hash: {schema_ipfs_hash}")
        
        # Encrypt and upload database to IPFS
        encrypted_path = encrypt_file(settings.REFINEMENT_ENCRYPTION_KEY, self.db_path)
        ipfs_hash = upload_file_to_ipfs(encrypted_path)
        output.refinement_url = f"{settings.IPFS_GATEWAY_URL}/{ipfs_hash}"
        
        logging.info("Netflix CSV data transformation completed successfully")
        return output