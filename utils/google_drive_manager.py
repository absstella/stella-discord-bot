import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from config import GOOGLE_DRIVE_FOLDER, GOOGLE_DRIVE_SERVICE_ACCOUNT

logger = logging.getLogger(__name__)

class GoogleDriveManager:
    """Google Drive integration for conversation memory"""
    
    def __init__(self):
        self.service = None
        self.folder_id = None
        self.initialized = False

    async def initialize(self):
        """Initialize Google Drive service"""
        try:
            if not GOOGLE_DRIVE_SERVICE_ACCOUNT:
                logger.warning("Google Drive service account not configured")
                self.initialized = False
                return
            
            # Check if the service account data is valid JSON
            try:
                if os.path.isfile(GOOGLE_DRIVE_SERVICE_ACCOUNT):
                    credentials = service_account.Credentials.from_service_account_file(
                        GOOGLE_DRIVE_SERVICE_ACCOUNT,
                        scopes=['https://www.googleapis.com/auth/drive']
                    )
                else:
                    # Assume it's JSON string
                    service_account_info = json.loads(GOOGLE_DRIVE_SERVICE_ACCOUNT)
                    credentials = service_account.Credentials.from_service_account_info(
                        service_account_info,
                        scopes=['https://www.googleapis.com/auth/drive']
                    )
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Invalid Google Drive service account JSON: {e}")
                self.initialized = False
                return
            except Exception as e:
                logger.error(f"Error creating credentials: {e}")
                self.initialized = False
                return
            
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive service created successfully")
            
            # Create or find conversation folder
            await self.ensure_folder_exists()
            
            if self.folder_id:
                self.initialized = True
                logger.info("Google Drive manager initialized successfully")
            else:
                logger.error("Failed to initialize: folder_id is None")
                self.initialized = False
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive: {e}")

    async def ensure_folder_exists(self):
        """Create conversation folder if it doesn't exist"""
        try:
            if not self.service:
                return
            
            # Search for existing folder
            query = f"name='{GOOGLE_DRIVE_FOLDER}' and mimeType='application/vnd.google-apps.folder'"
            results = await asyncio.to_thread(
                self.service.files().list,
                q=query,
                spaces='drive'
            )
            
            files = results.execute().get('files', [])
            
            if files:
                self.folder_id = files[0]['id']
                logger.info(f"Found existing conversation folder: {self.folder_id}")
            else:
                # Create new folder
                folder_metadata = {
                    'name': GOOGLE_DRIVE_FOLDER,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                
                folder = await asyncio.to_thread(
                    self.service.files().create,
                    body=folder_metadata,
                    fields='id'
                )
                
                self.folder_id = folder.execute()['id']
                logger.info(f"Created conversation folder: {self.folder_id}")
                
        except Exception as e:
            logger.error(f"Error ensuring folder exists: {e}")

    async def save_conversation(self, channel_id: int, user_id: int, message: str, response: str):
        """Save conversation to Google Drive"""
        if not self.initialized or not self.service or not self.folder_id:
            logger.warning("Google Drive not initialized, skipping save")
            return
        
        # Validate inputs
        if user_id is None or message is None or response is None:
            logger.warning("Invalid conversation data, skipping save")
            return
        
        try:
            logger.info(f"Starting conversation save - Channel: {channel_id}, User: {user_id}")
            
            # Create conversation data
            conversation_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "channel_id": channel_id,
                "user_id": user_id,
                "message": str(message),
                "response": str(response)
            }
            
            # Convert to JSONL format
            jsonl_line = json.dumps(conversation_data) + '\n'
            logger.debug(f"Created JSONL line: {jsonl_line[:100]}...")
            
            # Generate filename based on date
            date_str = datetime.utcnow().strftime('%Y-%m-%d')
            filename = f"conversations_{date_str}.jsonl"
            logger.info(f"Target filename: {filename}")
            
            # Check if file exists
            query = f"name='{filename}' and parents='{self.folder_id}'"
            logger.debug(f"Searching for existing file with query: {query}")
            
            results = await asyncio.to_thread(
                self.service.files().list,
                q=query
            )
            
            files = results.execute().get('files', [])
            logger.info(f"Found {len(files)} existing files with name {filename}")
            
            if files:
                # File exists, append to it
                file_id = files[0]['id']
                
                # Download existing content
                content = await asyncio.to_thread(
                    self.service.files().get_media,
                    fileId=file_id
                )
                
                existing_content = content.execute().decode('utf-8')
                new_content = existing_content + jsonl_line
                
                # Upload updated content
                media = MediaIoBaseUpload(
                    io.BytesIO(new_content.encode('utf-8')),
                    mimetype='application/json'
                )
                
                result = await asyncio.to_thread(
                    self.service.files().update,
                    fileId=file_id,
                    media_body=media
                )
                
                result.execute()
                logger.info(f"Updated existing file: {filename}")
                
            else:
                # Create new file
                logger.info(f"Creating new file: {filename}")
                file_metadata = {
                    'name': filename,
                    'parents': [self.folder_id]
                }
                
                media = MediaIoBaseUpload(
                    io.StringIO(jsonl_line),
                    mimetype='application/json'
                )
                
                result = await asyncio.to_thread(
                    self.service.files().create,
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                )
                
                created_file = result.execute()
                logger.info(f"Created file with ID: {created_file.get('id')}")
            
            logger.info(f"Successfully saved conversation to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")

    async def save_user_profiles(self, profiles_data: List[Dict]):
        """Save user profiles backup to Google Drive"""
        if not self.initialized or not self.service or not self.folder_id:
            logger.warning("Google Drive not initialized, skipping profiles backup")
            return
        
        try:
            logger.info("Starting user profiles backup to Google Drive")
            
            # Generate filename based on date
            date_str = datetime.utcnow().strftime('%Y-%m-%d')
            filename = f"user_profiles_backup_{date_str}.json"
            
            # Create backup data
            backup_data = {
                "backup_timestamp": datetime.utcnow().isoformat(),
                "profiles": profiles_data
            }
            
            # Convert to JSON with proper encoding
            json_content = json.dumps(backup_data, indent=2, ensure_ascii=False, separators=(',', ': '))
            
            # Check if file exists
            query = f"name='{filename}' and parents='{self.folder_id}'"
            results = await asyncio.to_thread(
                self.service.files().list,
                q=query
            )
            
            files = results.execute().get('files', [])
            
            if files:
                # Update existing file
                file_id = files[0]['id']
                media = MediaIoBaseUpload(
                    io.BytesIO(json_content.encode('utf-8')),
                    mimetype='application/json'
                )
                
                await asyncio.to_thread(
                    self.service.files().update,
                    fileId=file_id,
                    media_body=media
                )
                logger.info(f"Updated profiles backup: {filename}")
            else:
                # Create new file
                file_metadata = {
                    'name': filename,
                    'parents': [self.folder_id]
                }
                
                media = MediaIoBaseUpload(
                    io.BytesIO(json_content.encode('utf-8')),
                    mimetype='application/json'
                )
                
                result = await asyncio.to_thread(
                    self.service.files().create,
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                )
                
                created_file = result.execute()
                logger.info(f"Created profiles backup with ID: {created_file.get('id')}")
            
        except Exception as e:
            logger.error(f"Error saving profiles backup: {e}")

    async def search_conversations(self, query: str, limit: int = 10) -> List[Dict]:
        """Search conversation history"""
        if not self.initialized or not self.service or not self.folder_id:
            logger.warning("Google Drive not initialized, cannot search")
            return []
        
        try:
            # Get all conversation files
            results = await asyncio.to_thread(
                self.service.files().list,
                q=f"parents='{self.folder_id}' and name contains 'conversations_'",
                orderBy='name desc'
            )
            
            files = results.execute().get('files', [])
            
            matching_conversations = []
            query_lower = query.lower()
            
            # Search through files (most recent first)
            for file in files[:30]:  # Limit to last 30 days
                try:
                    # Download file content
                    content = await asyncio.to_thread(
                        self.service.files().get_media,
                        fileId=file['id']
                    )
                    
                    file_content = content.execute().decode('utf-8')
                    
                    # Parse JSONL and search
                    for line in file_content.strip().split('\n'):
                        if line:
                            try:
                                conversation = json.loads(line)
                                
                                # Search in message and response
                                message_text = conversation.get('message', '').lower()
                                response_text = conversation.get('response', '').lower()
                                
                                if query_lower in message_text or query_lower in response_text:
                                    matching_conversations.append(conversation)
                                    
                                    if len(matching_conversations) >= limit:
                                        return matching_conversations
                                        
                            except json.JSONDecodeError:
                                continue
                                
                except Exception as e:
                    logger.error(f"Error reading conversation file {file['name']}: {e}")
                    continue
            
            return matching_conversations
            
        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            return []

    def get_folder_link(self) -> Optional[str]:
        """Get the shareable link to the conversations folder"""
        if not self.folder_id:
            return None
        
        return f"https://drive.google.com/drive/folders/{self.folder_id}"
    
    async def get_folder_info(self) -> Optional[Dict]:
        """Get detailed information about the conversations folder"""
        if not self.initialized or not self.service or not self.folder_id:
            return None
        
        try:
            folder_info = await asyncio.to_thread(
                self.service.files().get,
                fileId=self.folder_id,
                fields='id,name,webViewLink,createdTime,modifiedTime'
            )
            
            return folder_info.execute()
        except Exception as e:
            logger.error(f"Error getting folder info: {e}")
            return None

    async def share_folder_with_user(self, email: str, role: str = 'writer') -> dict:
        """Share the conversations folder with a specific email address"""
        if not self.initialized or not self.service or not self.folder_id:
            logger.error("Google Drive not initialized")
            return {"success": False, "error": "Google Drive not initialized"}
        
        try:
            permission = {
                'type': 'user',
                'role': role,  # 'owner', 'writer', 'commenter', 'reader'
                'emailAddress': email
            }
            
            # First, try without email notification to avoid issues
            result = await asyncio.to_thread(
                lambda: self.service.permissions().create(
                    fileId=self.folder_id,
                    body=permission,
                    sendNotificationEmail=False,  # Disable notification to avoid email validation
                    fields='id,type,role,emailAddress,displayName'
                ).execute()
            )
            
            logger.info(f"Successfully shared folder with {email} as {role}. Permission ID: {result.get('id', 'unknown')}")
            
            # Verify the permission was created by listing all permissions
            permissions = await self.list_folder_permissions()
            user_found = any(p.get('emailAddress') == email for p in permissions)
            
            return {
                "success": True, 
                "permission_id": result.get('id'),
                "verified": user_found,
                "email": email,
                "role": role
            }
            
        except Exception as e:
            error_msg = f"Error sharing folder with {email}: {e}"
            logger.error(error_msg)
            return {"success": False, "error": str(e), "email": email}

    async def list_folder_permissions(self) -> List[Dict]:
        """List all permissions for the conversations folder"""
        if not self.initialized or not self.service or not self.folder_id:
            return []
        
        try:
            permissions = await asyncio.to_thread(
                self.service.permissions().list,
                fileId=self.folder_id,
                fields='permissions(id,type,role,emailAddress,displayName)'
            )
            
            return permissions.execute().get('permissions', [])
            
        except Exception as e:
            logger.error(f"Error listing folder permissions: {e}")
            return []

    async def get_conversation_summary(self, days: int = 7) -> Dict:
        """Get conversation summary for the last N days"""
        if not self.initialized or not self.service or not self.folder_id:
            return {}
        
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get files in date range
            results = await asyncio.to_thread(
                self.service.files().list,
                q=f"parents='{self.folder_id}' and name contains 'conversations_'",
                orderBy='name desc'
            )
            
            files = results.execute().get('files', [])
            
            total_conversations = 0
            unique_users = set()
            unique_channels = set()
            
            for file in files:
                # Check if file is in date range
                file_date_str = file['name'].replace('conversations_', '').replace('.jsonl', '')
                try:
                    file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                    if start_date <= file_date <= end_date:
                        # Process file
                        content = await asyncio.to_thread(
                            self.service.files().get_media,
                            fileId=file['id']
                        )
                        
                        file_content = content.execute().decode('utf-8')
                        
                        for line in file_content.strip().split('\n'):
                            if line:
                                try:
                                    conversation = json.loads(line)
                                    total_conversations += 1
                                    unique_users.add(conversation.get('user_id'))
                                    unique_channels.add(conversation.get('channel_id'))
                                except json.JSONDecodeError:
                                    continue
                                    
                except ValueError:
                    continue
            
            return {
                'total_conversations': total_conversations,
                'unique_users': len(unique_users),
                'unique_channels': len(unique_channels),
                'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return {}

    async def save_profile_backup(self, backup_data: Dict) -> bool:
        """Save user profile backup to Google Drive"""
        if not self.initialized or not self.service or not self.folder_id:
            logger.warning("Google Drive not initialized for profile backup")
            return False
        
        try:
            # Create backup filename with timestamp
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            user_id = backup_data.get('user_id', 'unknown')
            filename = f"profile_backup_{user_id}_{timestamp}.json"
            
            # Convert backup data to JSON
            import json
            backup_json = json.dumps(backup_data, indent=2, default=str, ensure_ascii=False)
            
            # Create file metadata
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id],
                'description': f"User profile backup for user {user_id} - {backup_data.get('backup_reason', 'unknown')}"
            }
            
            # Upload the backup file
            media = MediaIoBaseUpload(
                io.BytesIO(backup_json.encode('utf-8')),
                mimetype='application/json',
                resumable=True
            )
            
            file = await asyncio.to_thread(
                self.service.files().create,
                body=file_metadata,
                media_body=media,
                fields='id,name'
            )
            result = file.execute()
            
            logger.info(f"Profile backup saved to Google Drive: {filename} (ID: {result['id']})")
            return True
            
        except Exception as e:
            logger.error(f"Error saving profile backup to Google Drive: {e}")
            return False

    async def cleanup_old_conversations(self, days: int = 90):
        """Remove conversation files older than specified days"""
        if not self.initialized or not self.service or not self.folder_id:
            return 0
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all conversation files
            results = await asyncio.to_thread(
                self.service.files().list,
                q=f"parents='{self.folder_id}' and name contains 'conversations_'"
            )
            
            files = results.execute().get('files', [])
            deleted_count = 0
            
            for file in files:
                # Check file date
                file_date_str = file['name'].replace('conversations_', '').replace('.jsonl', '')
                try:
                    file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                    if file_date < cutoff_date:
                        # Delete old file
                        await asyncio.to_thread(
                            self.service.files().delete,
                            fileId=file['id']
                        )
                        deleted_count += 1
                        logger.info(f"Deleted old conversation file: {file['name']}")
                        
                except ValueError:
                    continue
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up conversations: {e}")
            return 0
