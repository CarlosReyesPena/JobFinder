from typing import Optional, List
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user import User


class UserManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_user(self, **kwargs) -> User:
        """
        Adds a new user to the database.
        Args:
            kwargs (dict): User fields.
        Returns:
            User: The created user.
        """
        # Required fields validation
        required_fields = ["first_name","last_name", "email", "password", "username"]
        for field in required_fields:
            if not kwargs.get(field):
                raise ValueError(f"The field {field} is required.")

        # Create user
        user = User.from_dict(kwargs)
        self.session.add(user)
        await self.session.commit()
        return user

    async def get_users(self) -> List[User]:
        """
        Retrieves all users.
        Returns:
            List[User]: List of users.
        """
        result = await self.session.execute(select(User))
        return result.scalars().all()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieves a user by their ID.
        Args:
            user_id (int): User ID.
        Returns:
            Optional[User]: The found user or None.
        """
        return await self.session.get(User, user_id)


    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """
        Updates user information.
        Args:
            user_id (int): ID of the user to update.
            kwargs (dict): Fields to update.
        Returns:
            Optional[User]: The updated user.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"Cannot update user with ID {user_id}: not found.")

        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        self.session.add(user)
        await self.session.commit()
        return user

    async def add_reference_letter(self, user_id: int, reference_text :str) -> Optional[User]:
        """
        Adds a reference letter to a user.
        Args:
            user_id (int): User ID.
            reference_text (str): Reference letter content.
        Returns:
            Optional[User]: The updated user.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"Cannot add reference letter to user with ID {user_id}: not found.")

        user.reference_letter = reference_text
        self.session.add(user)
        await self.session.commit()
        return user

    async def delete_reference_letter(self, user_id: int) -> bool:
        """
        Deletes a user's reference letter.
        Args:
            user_id (int): User ID.
        Returns:
            bool: True if the letter was deleted, False otherwise.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        user.reference_letter = None
        self.session.add(user)
        await self.session.commit()
        return True


    async def add_signature_from_path(self, user_id: int, path: str) -> Optional[User]:
        """
        Adds a signature to a user from a file.
        Args:
            user_id (int): User ID.
            path (str): Signature file path.
        Returns:
            Optional[User]: The updated user.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"Cannot add signature to user with ID {user_id}: not found.")

        with open(path, "rb") as file:
            user.signature = file.read()

        self.session.add(user)
        await self.session.commit()
        return user

    async def get_user_signature(self, user_id: int) -> Optional[bytes]:
        """
        Retrieves a user's signature.
        Args:
            user_id (int): User ID.
        Returns:
            Optional[bytes]: User's signature.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        return user.signature

    async def delete_user(self, user_id: int) -> bool:
        """
        Deletes a user from the database.
        Args:
            user_id (int): ID of the user to delete.
        Returns:
            bool: True if the user was deleted, False otherwise.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        await self.session.delete(user)
        await self.session.commit()
        return True
