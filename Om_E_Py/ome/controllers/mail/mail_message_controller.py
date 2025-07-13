"""
Mail Message Controller

Controller for individual message operations including body extraction,
attachment handling, and message actions.
Uses the same app focus pattern as mailMessageBody_controller.py.
"""

import os
import json
import subprocess
import sys
from datetime import datetime
from PyXA.apps.Mail import XAMailMessage, XAMailAttachment


class MailMessageController:
    """
    Controller for individual message operations.
    Handles body extraction, attachments, and message actions.
    """
    
    def __init__(self, message_list_controller):
        """
        Initialize with a MessageListController instance.
        
        Args:
            message_list_controller: MessageListController instance for message context
        """
        self.message_list_controller = message_list_controller
        self.current_message = None
        self.body_data = None
        self.attachment_data = None
    
    def set_current_message(self, message):
        """
        Set the current message to work with.
        
        Args:
            message (XAMailMessage): Message object to work with
        """
        self.current_message = message
        self.body_data = None
        self.attachment_data = None
        print(f"[MailMessageController] Set current message: {getattr(message, 'subject', 'No Subject')}")
    
    def extract_message_body(self, message=None):
        """
        Extract the body content of a message.
        
        Args:
            message (XAMailMessage, optional): Message object. If None, uses current message.
            
        Returns:
            dict: Message body data
        """
        if message is None:
            message = self.current_message
        
        if not message:
            print("[MailMessageController] No message to extract body from")
            return {}
        
        try:
            # Get basic message info
            subject = str(getattr(message, 'subject', 'No Subject'))
            sender = str(getattr(message, 'sender', 'Unknown'))
            date_received = getattr(message, 'date_received', datetime.now())
            
            # Format date for filename
            date_str = date_received.strftime('%Y%m%d')
            time_str = date_received.strftime('%H%M')
            
            # Create sender abbreviation (first 4 chars)
            sender_abbr = sender.split()[0][:4] if sender else 'Unkn'
            
            # Create message key
            message_key = f"{date_str},_{time_str}_{sender_abbr}_"
            
            # Get body content
            body_content = ""
            if hasattr(message, 'content'):
                body_content = str(message.content)
            elif hasattr(message, 'text_content'):
                body_content = str(message.text_content)
            
            # Get HTML content if available
            html_content = ""
            if hasattr(message, 'html_content'):
                html_content = str(message.html_content)
            
            # Create body data structure
            self.body_data = {
                'message_key': message_key,
                'subject': subject,
                'sender': sender,
                'date_received': str(date_received),
                'body_content': body_content,
                'html_content': html_content,
                'read': getattr(message, 'read', False),
                'flagged': getattr(message, 'flagged', False),
                'attachments': []
            }
            
            print(f"[MailMessageController] Extracted body for message: {subject}")
            return self.body_data
            
        except Exception as e:
            print(f"[MailMessageController] Error extracting message body: {e}")
            return {}
    
    def extract_attachments(self, message=None):
        """
        Extract attachment information from a message.
        
        Args:
            message (XAMailMessage, optional): Message object. If None, uses current message.
            
        Returns:
            list: List of attachment data
        """
        if message is None:
            message = self.current_message
        
        if not message:
            print("[MailMessageController] No message to extract attachments from")
            return []
        
        try:
            attachments = []
            mail_attachments = getattr(message, 'mail_attachments', [])
            
            for attachment in mail_attachments:
                try:
                    attachment_info = {
                        'name': str(getattr(attachment, 'name', 'Unknown')),
                        'file_name': str(getattr(attachment, 'file_name', 'Unknown')),
                        'file_size': getattr(attachment, 'file_size', 0),
                        'mime_type': str(getattr(attachment, 'mime_type', 'Unknown')),
                        'best_guess_path': None  # Will be filled by attachment finder
                    }
                    attachments.append(attachment_info)
                except Exception as e:
                    print(f"[MailMessageController] Error processing attachment: {e}")
                    continue
            
            self.attachment_data = attachments
            print(f"[MailMessageController] Extracted {len(attachments)} attachments")
            return attachments
            
        except Exception as e:
            print(f"[MailMessageController] Error extracting attachments: {e}")
            return []
    
    def save_message_data(self, output_dir=None):
        """
        Save message body and attachment data to files.
        
        Args:
            output_dir (str, optional): Output directory. If None, uses default.
            
        Returns:
            dict: File paths of saved data
        """
        if not self.body_data:
            self.extract_message_body()
        
        if not self.attachment_data:
            self.extract_attachments()
        
        if not self.body_data:
            print("[MailMessageController] No body data to save")
            return {}
        
        try:
            # Use default output directory if not specified
            if output_dir is None:
                from ome.utils.env.env import MESSAGE_EXPORT_DIR
                output_dir = os.path.join(MESSAGE_EXPORT_DIR, "mailMessageBody")
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Create filename from message key
            message_key = self.body_data['message_key']
            base_filename = f"mail_{message_key}"
            
            # Add attachments to body data
            self.body_data['attachments'] = self.attachment_data
            
            # Save JSON file
            json_file = os.path.join(output_dir, f"{base_filename}.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.body_data, f, indent=2, ensure_ascii=False)
            
            # Save JSONL file
            jsonl_file = os.path.join(output_dir, f"{base_filename}.jsonl")
            with open(jsonl_file, 'w', encoding='utf-8') as f:
                json.dump(self.body_data, f, ensure_ascii=False)
                f.write('\n')
            
            # Start attachment finder in background
            self._start_attachment_finder(json_file)
            
            saved_files = {
                'json_file': json_file,
                'jsonl_file': jsonl_file,
                'message_key': message_key
            }
            
            print(f"[MailMessageController] Saved message data to: {json_file}")
            return saved_files
            
        except Exception as e:
            print(f"[MailMessageController] Error saving message data: {e}")
            return {}
    
    def _start_attachment_finder(self, json_file):
        """
        Start the attachment finder as a background process.
        
        Args:
            json_file (str): Path to the JSON file to update
        """
        try:
            print(f"[MailMessageController] Starting attachment finder in background...")
            subprocess.Popen([
                sys.executable,
                "find_attachments.py",
                "--in", json_file,
                "--timeout", "60"  # 60 second timeout
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(f"[MailMessageController] Error starting attachment finder: {e}")
    
    def get_message_summary(self, message=None):
        """
        Get a summary of message information.
        
        Args:
            message (XAMailMessage, optional): Message object. If None, uses current message.
            
        Returns:
            dict: Message summary
        """
        if message is None:
            message = self.current_message
        
        if not message:
            return {}
        
        try:
            summary = {
                'subject': str(getattr(message, 'subject', 'No Subject')),
                'sender': str(getattr(message, 'sender', 'Unknown')),
                'date_received': str(getattr(message, 'date_received', 'Unknown')),
                'read': getattr(message, 'read', False),
                'flagged': getattr(message, 'flagged', False),
                'has_attachments': len(getattr(message, 'mail_attachments', [])) > 0,
                'attachment_count': len(getattr(message, 'mail_attachments', []))
            }
            return summary
        except Exception as e:
            print(f"[MailMessageController] Error getting message summary: {e}")
            return {}
    
    def mark_as_read(self, message=None):
        """
        Mark a message as read.
        
        Args:
            message (XAMailMessage, optional): Message object. If None, uses current message.
            
        Returns:
            bool: True if successful, False otherwise
        """
        if message is None:
            message = self.current_message
        
        if not message:
            return False
        
        try:
            message.read = True
            print(f"[MailMessageController] Marked message as read: {getattr(message, 'subject', 'No Subject')}")
            return True
        except Exception as e:
            print(f"[MailMessageController] Error marking message as read: {e}")
            return False
    
    def flag_message(self, message=None, flagged=True):
        """
        Flag or unflag a message.
        
        Args:
            message (XAMailMessage, optional): Message object. If None, uses current message.
            flagged (bool): True to flag, False to unflag
            
        Returns:
            bool: True if successful, False otherwise
        """
        if message is None:
            message = self.current_message
        
        if not message:
            return False
        
        try:
            message.flagged = flagged
            action = "flagged" if flagged else "unflagged"
            print(f"[MailMessageController] {action.capitalize()} message: {getattr(message, 'subject', 'No Subject')}")
            return True
        except Exception as e:
            print(f"[MailMessageController] Error flagging message: {e}")
            return False
    
    def delete_message(self, message=None):
        """
        Delete a message.
        
        Args:
            message (XAMailMessage, optional): Message object. If None, uses current message.
            
        Returns:
            bool: True if successful, False otherwise
        """
        if message is None:
            message = self.current_message
        
        if not message:
            return False
        
        try:
            subject = getattr(message, 'subject', 'No Subject')
            message.delete()
            print(f"[MailMessageController] Deleted message: {subject}")
            return True
        except Exception as e:
            print(f"[MailMessageController] Error deleting message: {e}")
            return False
    
    def get_current_context(self):
        """
        Get current message context.
        
        Returns:
            dict: Current context information
        """
        context = {
            'current_message': self.get_message_summary() if self.current_message else None,
            'body_extracted': self.body_data is not None,
            'attachments_extracted': self.attachment_data is not None,
            'attachment_count': len(self.attachment_data) if self.attachment_data else 0
        }
        return context 