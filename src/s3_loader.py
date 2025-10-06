import boto3
import os
import logging
from typing import Optional, List
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from botocore.config import Config
from tenacity import retry, stop_after_attempt, wait_exponential
from config import RAGConfig

logger = logging.getLogger(__name__)

class S3Downloader:
    """Handles downloading files from AWS S3 bucket with retry logic."""

    def __init__(self, config: RAGConfig):
        self.config = config
        self.bucket_name = config.S3_BUCKET_NAME
        self.local_path = config.DATA_DIR
        self.aws_region = config.AWS_REGION
        
        # Configure retry logic
        boto_config = Config(
            region_name=self.aws_region,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        try:
            # boto3 will automatically use IAM role credentials when available
            # No need to explicitly pass credentials if using IAM roles
            self.s3_client = boto3.client("s3", config=boto_config)
            
            # Test connection - this will use IAM role credentials automatically
            logger.info("Testing S3 connection with IAM role credentials...")
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3Downloader initialized for bucket: {self.bucket_name} using IAM role")
            
        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.warning("No AWS credentials found in environment. Assuming IAM role usage.")
            # Try again without explicit credential checking
            self.s3_client = boto3.client("s3", config=boto_config)
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"S3Downloader initialized for bucket: {self.bucket_name} using IAM role")
            except Exception as retry_error:
                logger.error(f"Failed to access S3 bucket even with IAM role: {retry_error}")
                raise
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '403':
                logger.error(f"Access denied to S3 bucket {self.bucket_name}. Check IAM role permissions.")
                raise PermissionError(f"Insufficient permissions for bucket {self.bucket_name}")
            else:
                logger.error(f"Failed to access S3 bucket {self.bucket_name}: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error initializing S3 client: {e}")
            raise
        
        os.makedirs(self.local_path, exist_ok=True)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def download_pdf(self, filename: str) -> str:
        """Download a PDF file from S3 to local storage with retry logic."""
        local_file = os.path.join(self.local_path, filename)
        
        try:
            logger.info(f"Downloading {filename} from S3 bucket {self.bucket_name}")
            
            # Check if file exists first
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=filename)
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    raise FileNotFoundError(f"File {filename} not found in S3 bucket {self.bucket_name}")
                raise
            
            self.s3_client.download_file(self.bucket_name, filename, local_file)
            logger.info(f"Successfully downloaded {filename} to {local_file}")
            return local_file
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f"File {filename} not found in bucket {self.bucket_name}")
            elif error_code == 'NoSuchBucket':
                raise FileNotFoundError(f"Bucket {self.bucket_name} not found")
            elif error_code == '403':
                raise PermissionError(f"Access denied to file {filename} in bucket {self.bucket_name}")
            else:
                logger.error(f"S3 error downloading {filename}: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error downloading {filename}: {e}")
            raise

    def list_pdfs(self) -> List[str]:
        """List all PDF files in the S3 bucket."""
        try:
            logger.info(f"Listing PDF files in bucket: {self.bucket_name}")
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='',  # List all objects
                Delimiter='/'
            )
            
            pdf_files = []
            if 'Contents' in response:
                pdf_files = [
                    obj['Key'] for obj in response['Contents'] 
                    if obj['Key'].lower().endswith('.pdf')
                ]
            
            logger.info(f"Found {len(pdf_files)} PDF files in bucket {self.bucket_name}")
            return pdf_files
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '403':
                logger.error(f"Access denied to list bucket {self.bucket_name}. Check IAM permissions.")
                raise PermissionError(f"Insufficient permissions to list bucket {self.bucket_name}")
            else:
                logger.error(f"Error listing files in S3 bucket: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error listing files in S3 bucket: {e}")
            raise

    def download_all_pdfs(self) -> List[str]:
        """Download all PDF files from S3 bucket."""
        pdf_files = self.list_pdfs()
        downloaded_files = []
        
        logger.info(f"Downloading {len(pdf_files)} PDF files...")
        for filename in pdf_files:
            try:
                local_path = self.download_pdf(filename)
                downloaded_files.append(local_path)
                logger.info(f"Downloaded: {filename}")
            except Exception as e:
                logger.warning(f"Failed to download {filename}: {e}")
                continue
        
        logger.info(f"Successfully downloaded {len(downloaded_files)} PDF files")
        return downloaded_files
