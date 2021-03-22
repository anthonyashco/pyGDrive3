"""Following is an example application of the gdrive.py Drive object.

A long-accreting drive needed to be resorted based on tag data in their filenames,
with duplicates, files with missing tag data, and files missing from a reference table
all moved to different folders for later sorting.
"""


from csv import DictReader
from gdrive import Drive
from googleapiclient.errors import HttpError
from time import sleep
import yaml


def name_fixer():
    """Rename files from a metadata CSV.

    Missing name fields are replaced with !!--UNTITLED--!! to make them easy to
    find later.
    """
    folder_queries = []

    for folder in drive.directory_tree(dump, "print"):
        folder_queries.append(f"'{folder}' in parents")

    request = " or ".join(folder_queries)

    page_token = None
    files_processed = 0

    while True:
        timer = 10
        retry = True

        while retry == True:
            try:
                files = drive.search(
                    f"({request}) and mimeType != 'application/vnd.google-apps.folder' and trashed = false",
                    page_token,
                    1000,
                )
                retry = False
            except HttpError:
                print(e)
                sleep(timer)
                timer += 5

        batch = drive.new_batch_http_request()
        for file in files["files"]:
            try:
                # Identify and separate metadata fields.
                cid = "0" + file["name"].partition("[0")[2].partition("]")[0]
                if len(cid) != 16:
                    raise Exception("Content ID parsing error")
                if cid.startswith("00050000"):
                    cat = "BASE"
                elif cid.startswith("0005000E"):
                    cat = "UPDATE"
                elif cid.startswith("0005000C"):
                    cat = "DLC"
                else:
                    raise Exception("Invalid title id type")

                not_found = False
                if cid[8:16] in metadata:
                    name = metadata[cid[8:16]]["name"]
                else:
                    not_found = True
                    print(f"{file['name']} not found in metadata, parsing...")
                    name = file["name"].partition("[")[0].strip()
                    if len(name) == 0:
                        name = "!!--UNTITLED--!!"
                name = name.replace("[", "(").replace("]", ")").strip()
                if len(name) == 0:
                    raise Exception("File unnamed.")

                dlc = None
                if cat == "DLC":
                    try:
                        dlc = file["name"].partition("][0")[0].partition["["][2].strip()
                    except:
                        dlc = "!!--UNTITLED--!!"
                    if len(dlc) == 0:
                        dlc = "!!--UNTITLED--!!"

                ext = file["name"].rpartition(".")[2]
                if ext not in ["wud", "wux", "nus"]:
                    raise Exception("Invalid extension")

                if ext not in ["wud", "wux"]:
                    ver = file["name"].partition("[v")[2].partition("]")[0]
                    if int(ver) % 65536 != 0:
                        raise Exception("Version parsing error")
                else:
                    ver = 0

                if dlc is None:
                    new_name = f"{name} [{cid}][v{ver}].{ext}"
                else:
                    new_name = f"{name} [{dlc}][{cid}][v{ver}].{ext}"

                if not_found:
                    destination = unknown
                else:
                    destination = renamed

            except Exception as e:
                print(e)
                print(f"{file['name']} name is bad, moving to the naughty list...")
                new_name = file["name"]
                destination = bad_names

            batch.add(
                drive.files().update(
                    fileId=file["id"],
                    addParents=destination["id"],
                    removeParents=",".join(file["parents"]),
                    body={"name": new_name},
                    fields="id, name, parents",
                    supportsAllDrives=shared_drive[0],
                )
            )

        timer = 10
        retry = True

        while retry == True:
            try:
                batch.execute()
                retry = False
            except HttpError as e:
                print(e)
                sleep(timer)
                timer += 5

        files_processed += len(files["files"])
        print(f"{files_processed} files processed.")
        page_token = files.get("nextPageToken", None)
        if page_token is None:
            break

    print("Done!")
    return files_processed


def missing_fields():
    """Locate files with missing fields and move them to the appropriate folders."""
    page_token = None
    files_processed = 0

    while True:
        timer = 10
        retry = True

        while retry == True:
            try:
                files = drive.search(
                    f"name contains '!!--UNTITLED--!!' and '{renamed['id']}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false",
                    page_token,
                    1000,
                )
                retry = False
            except HttpError as e:
                print(e)
                sleep(timer)
                timer += 5

        batch = drive.new_batch_http_request()
        for file in files["files"]:
            if "!!--UNTITLED--!!" in file["name"]:
                destination = missing["id"]
            else:
                destination = ionno["id"]

            batch.add(
                drive.files().update(
                    fileId=file["id"],
                    addParents=destination,
                    removeParents=",".join(file["parents"]),
                    fields="id, name, parents",
                    supportsAllDrives=shared_drive[0],
                )
            )

        timer = 10
        retry = True

        while retry == True:
            try:
                batch.execute()
                retry = False
            except HttpError as e:
                print(e)
                sleep(timer)
                timer += 5

        files_processed += len(files["files"])
        print(f"{files_processed} files processed.")
        page_token = files.get("nextPageToken", None)
        if page_token is None:
            break

    print("Done!")
    return files_processed


def file_clumper():
    """Take all the files from the given folders and move then to the sorting folder."""
    folder_queries = []

    for folder in drive.directory_tree(missing, "print"):
        folder_queries.append(f"'{folder}' in parents")
    for folder in drive.directory_tree(renamed, "print"):
        folder_queries.append(f"'{folder}' in parents")
    for folder in drive.directory_tree(unknown, "print"):
        folder_queries.append(f"'{folder}' in parents")

    request = " or ".join(folder_queries)

    page_token = None
    files_processed = 0

    while True:
        timer = 10
        retry = True

        while retry == True:
            try:
                files = drive.search(
                    f"({request}) and mimeType != 'application/vnd.google-apps.folder' and trashed = false",
                    page_token,
                    1000,
                )
                retry = False
            except HttpError:
                print(e)
                sleep(timer)
                timer += 5

        batch = drive.new_batch_http_request()
        for file in files["files"]:
            batch.add(
                drive.files().update(
                    fileId=file["id"],
                    addParents=dump["id"],
                    removeParents=",".join(file["parents"]),
                    fields="id, name, parents",
                    supportsAllDrives=shared_drive[0],
                )
            )

        timer = 10
        retry = True

        while retry == True:
            try:
                batch.execute()
                retry = False
            except HttpError as e:
                print(e)
                sleep(timer)
                timer += 5

        files_processed += len(files["files"])
        print(f"{files_processed} files processed.")
        page_token = files.get("nextPageToken", None)
        if page_token is None:
            break

    print("Done!")
    return files_processed


def file_sorter():
    """Sort files into a file directory tree based on the base title."""
    page_token = None
    doots = 0
    derps = 0

    while True:
        timer = 10
        retry = True

        while retry == True:
            try:
                files = drive.search(
                    f"'{renamed['id']}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false",
                    page_token,
                    1000,
                )
                retry = False
            except HttpError as e:
                print(e)
                sleep(timer)
                timer += 5

        for file in files["files"]:
            name = file["name"].partition("[")[0].strip()
            ext = file["name"].rpartition(".")[2]
            cid = "0" + file["name"].partition("[0")[2].partition("]")[0]
            if ext not in ["wud", "wux"]:
                drive.mv(file, bad_names, True)
                continue
            if cid.startswith("00050000"):
                base_id = cid
            else:
                base_id = f"00050000{cid[8:16]}"

            query = name.replace("'", "\\'")
            folder = drive.search(
                f"name = '{query} [{base_id}]' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            )
            if len(folder["files"]) == 1:
                folder = folder["files"][0]
            elif len(folder["files"]) == 0:
                folder = drive.mkdir(f"{name} [{base_id}]", archive, True)
            else:
                folder = folder["files"][0]
                derps += 1
                print(f"duplicate folder derp for {name} [{base_id}]")
            query = file["name"].replace("'", "\\'")
            base = drive.search(
                f"name = '{query}' and '{folder['id']}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
            )
            if len(base["files"]) == 1:
                print(f"{base['files'][0]['name']} already exists, tossing")
                drive.mv(file, dupes, True)
            elif len(base["files"]) == 0:
                drive.mv(file, folder, True)
            else:
                derps += 1
                print(f"duplicate file derp for {file['name']}")
            doots += 1

            if doots % 100 == 0:
                print(f"{doots} doots dooted, {derps} derps derped")

        page_token = files.get("nextPageToken", None)
        if page_token is None:
            break

    print(f"Done! {doots} total doots and {derps} total derps")
    return doots


if __name__ == "__main__":
    drive = Drive("credentials.json")
    with open("folder_ids.yml", "r") as f:
        ids = yaml.safe_load(f)

    shared_drive = [True, ids["shared"]]

    dump = drive.get(ids["dump"])
    bad_names = drive.get(ids["bad_names"])
    renamed = drive.get(ids["renamed"])
    unknown = drive.get(ids["unknown"])
    missing = drive.get(ids["missing"])
    ionno = drive.get(ids["ionno"])
    archive = drive.get(ids["archive"])
    dupes = drive.get(ids["dupes"])

    clump_files = False
    fix_names = False
    check_missing_fields = False
    list_unknowns = False
    sort_files = True

    metadata = {}
    with open("parseout_base.csv", mode="r", encoding="utf-8") as file:
        reader = DictReader(file)
        for index, row in enumerate(reader):
            if index > 0:
                metadata[row["application_id"][0:12]] = {
                    "name": row["title_name"],
                    "region": row["region_major"],
                }

    while clump_files:
        print("clumping files...")
        files_processed = file_clumper()
        if files_processed > 0:
            print("repeating...")
        else:
            print("clumping files complete!")
            break

    while fix_names:
        print("fixing names...")
        files_processed = name_fixer()
        if files_processed > 0:
            print("repeating...")
        else:
            print("fixing names complete!")
            break

    while check_missing_fields:
        print("checking missing fields...")
        files_processed = missing_fields()
        if files_processed > 0:
            print("repeating...")
        else:
            print("checking missing fields complete!")
            break

    page_token = None
    while list_unknowns:
        files = drive.search(
            f"'{unknown['id']}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false",
            page_token,
            1000,
        )
        for file in files["files"]:
            print(file["name"])

        page_token = files.get("nextPageToken", None)
        if page_token is None:
            break

    while sort_files:
        try:
            file_sorter()
            break
        except HttpError as e:
            print(e)