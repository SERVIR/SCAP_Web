# Author: Githika Tondapu
# Date: 11/11/2024
# Python script to upload data from source directory on server to destination directory on AWS-S3
# This script needs SCAP environment and MFA authorization in order to execute

import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

# method to upload files to S3 bucket based on provided input parameters
def upload_files_to_s3(origin_folder, s3_bucket, destination_folder):
    s3_client = boto3.client('s3')

    for root, dirs, files in os.walk(origin_folder):
        for file in files:
            # replacing 1's from the file name as we do not need it on S3 filenames
            modified_file = file.replace('1.', '', 1)
            local_file_path = os.path.join(root, file)
            # Create the relative file path by removing the origin folder part
            relative_file_path = os.path.relpath(local_file_path, origin_folder)
            modified_relative_path = relative_file_path.replace(file, modified_file)
            # Define the full destination path in the S3 bucket
            s3_file_path = os.path.join(destination_folder, modified_relative_path).replace("\\", "/")

            try:
                # Check if the file exists in the S3 bucket
                exists = False
                # We use list_objects_v2 to check if the file exists in the bucket
                response = s3_client.list_objects(Bucket=s3_bucket, Prefix=s3_file_path)
                for obj in response.get('Contents', []):
                    if obj['Key'] == s3_file_path:
                        exists = True
                        break

                if exists:
                    print(f"File {s3_file_path} already exists in the destination folder. Skipping upload.")
                else:
                    print(f"Uploading {local_file_path} to {s3_file_path}...")
                    s3_client.upload_file(local_file_path, s3_bucket, s3_file_path)
                    print(f"Successfully uploaded {file} to {s3_file_path}.")

            except FileNotFoundError:
                print(f"File {local_file_path} not found.")
            except NoCredentialsError:
                print("AWS credentials not available.")
                break
            except PartialCredentialsError:
                print("Incomplete AWS credentials detected.")
                break
            except ClientError as e:
                # Handle any general AWS service error here
                print(f"AWS ClientError: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")

# Execution starts here
if __name__ == "__main__":
    # Get the source path, S3 bucket name and destination path on S3 from the user
    origin_folder = input("Enter the path of the origin folder (local directory): ")
    s3_bucket = input("Enter the name of the S3 bucket: ")
    destination_folder = input("Enter the path in the S3 bucket to upload the files: ")

    # make sure the origin folder exists
    if not os.path.isdir(origin_folder):
        print(f"The origin folder {origin_folder} does not exist.")
    else:
        # call the method to upload files
        upload_files_to_s3(origin_folder, s3_bucket, destination_folder)