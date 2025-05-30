import botocore
import duckdb
import boto3

import os

class FileRepository():
    def __init__(self, path):
        self.path = path
        self.is_s3_path = path.startswith("s3://")
        if self.is_s3_path:
            self.s3 = boto3.client('s3')
            self.s3_bucket = path.split('/')[2]
            self.s3_key = '/'.join(path.split('/')[3:])
        else:
            # Local path
            self.path = path
           
    def set_path(self, path):
        self.path = path
     
    def load(self):
        try:
            if self.is_s3_path:
                response = self.s3.get_object(Bucket=self.s3_bucket, Key=self.s3_key)
                return response['Body'].read().decode('utf-8')
            else:
                with open(self.path, 'r', encoding='utf-8') as file:
                    return file.read()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
        except FileNotFoundError:
            return None
        except PermissionError:
            print(f"Error: Permission denied when accessing {self.path}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")           
            
        
    def save(self, data_as_str):
        try:
            if self.is_s3_path:
                self.s3.put_object(Bucket=self.s3_bucket, Key=self.s3_key, Body=data_as_str)
            else:
                with open(self.path, 'w', encoding='utf-8') as file:
                    file.write(data_as_str)
        except (OSError, IOError) as file_error:
            print(f"Failed to write to file {self.path}: {file_error}")
        except self.s3.exceptions.S3UploadFailedError as s3_error:
            print(f"Failed to upload to S3 bucket {self.s3_bucket}/{self.s3_key}: {s3_error}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            
    def delete_all_files_in_path(self):
        s3 = boto3.client('s3')
        # List objects under the path
        response = s3.list_objects_v2(Bucket=self.s3_bucket, Prefix=self.s3_key)
        if 'Contents' in response:
            delete_keys = [{'Key': obj['Key']} for obj in response['Contents']]
            # Delete objects in a single call
            response = s3.delete_objects(
                Bucket=self.s3_bucket,
                Delete={'Objects': delete_keys}
            )
            if response.get('Errors', None):
                raise Exception(f"Failed to delete objects: {response['Errors']}")
            print(f"Deleted {len(delete_keys)} objects from {self.s3_bucket}/{self.s3_key}")
        else:
            print(f"No objects found under {self.s3_bucket}/{self.s3_key}")