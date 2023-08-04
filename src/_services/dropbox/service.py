import dropbox

ACCESS_TOKEN = "sl.BOwTyXYGFdNvoTGWvUTuK0G6htnTjqqKn2skFKMiZt8g0z2Ymwun1yovkhUuxHhJlFVh5dirvz6ZSFbbMZELgnhZH3FGAi8VA5LJ5BLM3AKuCYXKGXhTxz3_MwI6JfcJJhNyxFpPpV6QkygDW9g"

dbx = dropbox.DropboxTeam(
    oauth2_access_token=ACCESS_TOKEN,
).as_user("dbmid:AAD6YxDWVi1hLp9jvQtSrYZQuX9xDYpaltk")

def get_folder_shared_link(path: str):
    try:
        shared_link_metadata = dbx.sharing_create_shared_link_with_settings(path)
        return shared_link_metadata.url
    except dropbox.exceptions.ApiError as e:
        if e.error.is_shared_link_already_exists():
            if (shared_link := e.error.get_shared_link_already_exists()) is not None:
                shared_link_metadata = shared_link.get_metadata()
                return shared_link_metadata.url
    return None
    

def invite_to_folder(shared_folder_id, email: str):
    member_selector = dropbox.sharing.MemberSelector.email(email)
    add_member =  dropbox.sharing.AddMember(member_selector)
    members = [add_member] # this can contain more than one member to add

    res = dbx.sharing_add_folder_member(shared_folder_id, members)
