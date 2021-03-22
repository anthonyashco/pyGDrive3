"""The Drive object simplifies some common Google Drive API requests."""


from googleapiclient.discovery import build
from pygauth import get_user_creds_file


class Drive:
    def __init__(self, credentials):
        self.creds = get_user_creds_file(credentials, scopes=["drive"])
        self.drive = build("drive", "v3", credentials=self.creds)
        self.shared_drive = [False, ""]

    def ls(self):
        """List files from the drive.

        Print the first 100 files encountered in the drive.

        From the Drive API Quickstart. Seems to be practically unordered.
        """
        files = self.drive.files().list().execute().get("files", [])
        for f in files:
            print(f["name"], f["mimeType"])

    def search(self, query, page_token=None, page_size=100):
        """Query the drive.

        Query strings follow Google's query format, found here:
        https://developers.google.com/drive/api/v3/search-files

        Args:
            query (str): The query string.
            page_token (str, optional): After a search, invoke a new search with
            page_token = nextPageToken to resume the search. Defaults to None.
            page_size (int, optional): Number of results to return in a single search
            query. Maximum of 1000, but these seems to be inconsistent. Defaults to 100.

        Returns:
            files.nextpagetoken: The token to resume the query.
            files.files: A list of files with the id, name, and parents properties.
        """
        files = (
            self.drive.files()
            .list(
                q=query,
                corpora="drive",
                spaces="drive",
                fields="nextPageToken, files(id, name, parents)",
                orderBy="name",
                pageSize=page_size,
                pageToken=page_token,
                includeItemsFromAllDrives=True,
                supportsAllDrives=self.shared_drive[0],
                driveId=self.shared_drive[1],
            )
            .execute()
        )
        return files

    def directory_tree(self, root=None, print_value=None):
        """Recursively map the directory tree from a root folder.

        If used on the root directory (root=None), this returns a dictionary of folder
        names and ids, nested to match the directory tree. If used on a specific folder,
        the function returns a list of nested folder ids for use with a Google query.

        Args:
            root (file, optional): The file object of the parent folder. Defaults to None.
            print_value (bool, optional): Whether or not to print the directory
            structure. Defaults to None.

        Returns:
            tree (dict): Nested dictionary of the drive's folders, with name and id.
            results (list): List of contained folder ids.
        """
        files = (
            self.drive.files()
            .list(
                q="mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                corpora="drive",
                spaces="drive",
                fields="files(id, name, parents)",
                includeItemsFromAllDrives=True,
                supportsAllDrives=self.shared_drive[0],
                driveId=self.shared_drive[1],
            )
            .execute()
        )
        file_dict = {}
        file_names = {}
        for file in files["files"]:
            if file["parents"][0] not in file_dict:
                file_dict[file["parents"][0]] = {}
            file_dict[file["parents"][0]][file["id"]] = file["name"]
            file_names[file["id"]] = file["name"]
        tree = {}
        results = []

        def recurse(parent_id, tree_pos):
            if len(file_dict) == 0:
                return
            if parent_id in file_dict:
                parent = file_dict[parent_id]
                for folder in parent.keys():
                    tree_pos[folder] = {}
                    results.append(folder)
            if len(tree_pos) > 0:
                for folder in tree_pos.keys():
                    recurse(folder, tree_pos[folder])

        if root is not None:
            results.append(root["id"])
            recurse(root["id"], tree)
        elif self.shared_drive[0]:
            results.append(self.shared_drive[1])
            recurse(self.shared_drive[1], tree)
        else:
            results.append("root")
            recurse("root", tree)

        def tree_name(tree_pos, space):
            if len(tree_pos) == 0:
                return
            for id, folder in tree_pos.items():
                print(f"{' '*space}{file_names[id]} [{id}]")
                if len(folder) > 0:
                    tree_name(tree_pos[id], space + 4)

        if print_value is not None:
            root_title = self.get(results[0])
            print(f"{root_title['name']} [{root_title['id']}]")
            tree_name(tree, 4)

        if root is not None:
            return results
        else:
            return tree

    def get(self, id):
        """Get a file object from its id.

        This script works on Google file objects and not directly with file ids, so
        any object to be worked with should have its file object obtained, first.

        Args:
            id (str): The file_id to obtain.

        Returns:
            (file): A file object the other commands of this script can interact with.
        """
        file = (
            self.drive.files()
            .get(
                fileId=id,
                fields="id, name",
                supportsAllDrives=self.shared_drive[0],
            )
            .execute()
        )
        return file

    def mkdir(self, name, parent=None, execute=False):
        """Make a directory.

        If no parent is specified, the directory will be made in the root directory.
        By default, this won't execute immediately, allowing for mkdir commands to be
        batched.

        Args:
            name (str): The name for the directory.
            parent (file, optional): Parent folder file object. Defaults to None.
            execute (bool, optional): Whether or not to execute now. Defaults to False.

        Returns:
            (file): The file object for the newly-created folder.
        """
        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if self.shared_drive[0]:
            file_metadata["driveId"] = self.shared_drive[1]
            file_metadata["parents"] = [self, self.shared_drive[1]]
        if parent is not None:
            file_metadata["parents"] = [parent["id"]]
        file = self.drive.files().create(
            body=file_metadata,
            fields="name, id, parents",
            supportsAllDrives=self.shared_drive[0],
        )
        if execute:
            file = file.execute()
        return file

    def mv(self, item, destination, execute=False):
        """Move a file to a destination folder.

        Both the file to be moved and the destination folder must be file objects
        obtained from get().

        Args:
            item (file): The file object to move.
            destination (file): The file object of the destination folder.
            execute (bool, optional): Whether or not to execute now. Defaults to False.

        Returns:
            (file): The file object for the recently-moved file.
        """
        file = self.drive.files().update(
            fileId=item["id"],
            addParents=destination["id"],
            removeParents=",".join(item["parents"]),
            fields="id, name, parents",
            supportsAllDrives=self.shared_drive[0],
        )
        if execute:
            file = file.execute()
        return file

    def ren(self, item, new_name, execute=False):
        """Rename a file.

        Args:
            item (file): The file object to rename.
            new_name (str): The string to rename the file as.
            execute (bool, optional): Whether or not to execute now. Defaults to False.

        Returns:
            (file): The file object for the recently-renamed file.
        """
        file_metadata = {"name": new_name}
        file = self.drive.files().update(
            fileId=item["id"],
            body=file_metadata,
            supportsAllDrives=self.shared_drive[0],
        )
        if execute:
            file = file.execute()
        return file