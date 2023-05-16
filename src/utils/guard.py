from typing import List
from fastapi import Depends
from _documents.users.schema import UserList
from _documents.users.service import user_service
from fastapi.exceptions import HTTPException

class RoleGuard:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: UserList = Depends(user_service.get_current_user)):
        if user.status == 'PENDING':
            raise HTTPException(status_code=401, detail="Your email has not been verified.")
        elif user.status == 'LOCKED':
            raise HTTPException(status_code=401, detail="Your account has been locked.")
        if len(
            set.intersection(set(user.roles), set(self.allowed_roles))
        ) == 0:
            raise HTTPException(status_code=403, detail="Permission denied.")
        return user