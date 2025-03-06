# EASY DRIVE DL
EASY DRIVE DL is a Python program that allows you to easily download files from your Google Drive. Once configured, you only need to run the script to automatically download your files.

## Setup
1. Place the `config.json` and `service-account.json` files in the same directory as the executable file.
2. When you run the program, the `downloads` folder and log files will be automatically created.

## Configuring `config.json`
In `config.json`, you can configure the following settings:
- Folder IDs: The IDs of the folders you want to audit and download from (this is required).
- Allowed Extensions: The file extensions that are allowed for download (this is required).
- Loop Interval (seconds): The interval (in seconds) at which the program checks for new files.

## Setting up the Service Account
1. Visit [Google Cloud Platform](https://console.cloud.google.com/)
2. Add the service account's client email to your folder to grant it access.

## Usage
1. Once you have completed the configuration, simply run the script, and it will automatically download files from the specified folders.
2. The downloaded files will be saved in the `downloads` folder.
