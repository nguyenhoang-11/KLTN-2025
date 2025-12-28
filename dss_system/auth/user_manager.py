"""
Simple user authentication manager for DSS system
Stores users in a JSON file for simplicity
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, List


class UserManager:
    """Manages user authentication and user data"""

    def __init__(self, users_file='data/users.json'):
        """
        Initialize user manager

        Args:
            users_file: Path to users JSON file
        """
        self.users_file = Path(users_file)
        self.users = self._load_users()

    def _load_users(self) -> Dict:
        """Load users from JSON file"""
        if self.users_file.exists():
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create default admin user
            default_users = {
                'admin': {
                    'username': 'admin',
                    'password': self._hash_password('admin123'),
                    'full_name': 'Administrator',
                    'email': 'admin@dss.com',
                    'role': 'admin'
                },
                'user': {
                    'username': 'user',
                    'password': self._hash_password('user123'),
                    'full_name': 'Regular User',
                    'email': 'user@dss.com',
                    'role': 'user'
                }
            }
            self._save_users(default_users)
            return default_users

    def _save_users(self, users: Dict):
        """Save users to JSON file"""
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate user

        Args:
            username: Username
            password: Plain text password

        Returns:
            User dict if authenticated, None otherwise
        """
        if username not in self.users:
            return None

        user = self.users[username]
        hashed_password = self._hash_password(password)

        if user['password'] == hashed_password:
            # Return user without password
            return {
                'username': user['username'],
                'full_name': user['full_name'],
                'email': user.get('email', ''),
                'role': user['role']
            }
        return None

    def create_user(self, username: str, password: str, full_name: str,
                    role: str = 'user', email: str = '') -> bool:
        """
        Create new user

        Args:
            username: Username
            password: Plain text password
            full_name: Full name
            role: User role (user or admin)
            email: Email address

        Returns:
            True if created, False if username exists
        """
        if username in self.users:
            return False

        self.users[username] = {
            'username': username,
            'password': self._hash_password(password),
            'full_name': full_name,
            'email': email,
            'role': role
        }
        self._save_users(self.users)
        return True

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Change user password

        Args:
            username: Username
            old_password: Current password
            new_password: New password

        Returns:
            True if changed, False if old password incorrect
        """
        if username not in self.users:
            return False

        user = self.users[username]
        old_hashed = self._hash_password(old_password)

        if user['password'] != old_hashed:
            return False

        user['password'] = self._hash_password(new_password)
        self._save_users(self.users)
        return True

    def list_users(self) -> List[Dict]:
        """
        List all users (without passwords)

        Returns:
            List of user dicts
        """
        users_list = []
        for username, user in self.users.items():
            users_list.append({
                'username': user['username'],
                'full_name': user['full_name'],
                'email': user.get('email', ''),
                'role': user['role']
            })
        return users_list


# Global user manager instance
_user_manager = None


def get_user_manager() -> UserManager:
    """Get global user manager instance"""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager
