## About

pyGDrive3 simplifies some common Google Drive API requests, wrapping them up using
familiar Python object construction.

## Usage

1.  Head to the Google Drive Python Quickstart page and complete step 1 to create your
    project and download your `credentials.json`. Remember that this credential allows
    full read and write access to your GDrive files, including any Shared Drives you
    have! Keep it safe! Make sure it's named `credentials.json` and place it at the
    root of the folder.

2.  Fill out `folder_ids_template.yml` with the file ids of your folders. These appear
    in the address bar as you browse into them:
    ```
    https://drive.google.com/drive/u/0/folders/<file_id>
    ```