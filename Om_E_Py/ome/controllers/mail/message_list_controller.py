"""
Message List Controller

Controller for message list operations including search, sort, and selection.
Uses the same app focus pattern as mailMessageBody_controller.py.
"""

import PyXA
from datetime import datetime


class MessageListController:
    """
    Controller for message list operations.
    Handles searching, sorting, and selecting messages in the current mailbox.
    """
    
    def __init__(self, mail_controller):
        """
        Initialize with a MailController instance.
        
        Args:
            mail_controller: MailController instance for app context
        """
        self.mail_controller = mail_controller
        self.current_messages = []
        self.selected_message = None
    
    def get_messages(self, mailbox_name=None, account_name=None):
        """
        Get all messages from the current or specified mailbox.
        
        Args:
            mailbox_name (str, optional): Mailbox name. If None, uses current mailbox.
            account_name (str, optional): Account name. If None, uses current account.
            
        Returns:
            list: List of message objects
        """
        if not self.mail_controller.app:
            return []
        
        try:
            # Switch to specified mailbox if provided
            if mailbox_name:
                self.mail_controller.switch_mailbox(mailbox_name, account_name)
            
            if not self.mail_controller.current_mailbox:
                print("[MessageListController] No mailbox selected")
                return []
            
            messages = self.mail_controller.current_mailbox.messages()
            self.current_messages = list(messages)
            print(f"[MessageListController] Found {len(self.current_messages)} messages in '{self.mail_controller.current_mailbox.name}'")
            return self.current_messages
        except Exception as e:
            print(f"[MessageListController] Error getting messages: {e}")
            return []
    
    def search_messages(self, search_term, search_fields=None):
        """
        Search messages by term in specified fields.
        
        Args:
            search_term (str): Term to search for
            search_fields (list, optional): Fields to search in. Default: ['subject', 'sender', 'content']
            
        Returns:
            list: List of matching message objects
        """
        if search_fields is None:
            search_fields = ['subject', 'sender', 'content']
        
        if not self.current_messages:
            self.get_messages()
        
        search_term_lower = search_term.lower()
        matches = []
        
        for message in self.current_messages:
            for field in search_fields:
                try:
                    if field == 'subject' and hasattr(message, 'subject'):
                        if search_term_lower in str(message.subject).lower():
                            matches.append(message)
                            break
                    elif field == 'sender' and hasattr(message, 'sender'):
                        if search_term_lower in str(message.sender).lower():
                            matches.append(message)
                            break
                    elif field == 'content' and hasattr(message, 'content'):
                        if search_term_lower in str(message.content).lower():
                            matches.append(message)
                            break
                except Exception:
                    continue
        
        print(f"[MessageListController] Found {len(matches)} messages matching '{search_term}'")
        return matches
    
    def sort_messages(self, sort_by='date', reverse=True):
        """
        Sort messages by specified field.
        
        Args:
            sort_by (str): Field to sort by ('date', 'sender', 'subject')
            reverse (bool): Sort in descending order if True
            
        Returns:
            list: Sorted list of message objects
        """
        if not self.current_messages:
            self.get_messages()
        
        try:
            if sort_by == 'date':
                sorted_messages = sorted(
                    self.current_messages,
                    key=lambda msg: getattr(msg, 'date_received', datetime.min),
                    reverse=reverse
                )
            elif sort_by == 'sender':
                sorted_messages = sorted(
                    self.current_messages,
                    key=lambda msg: str(getattr(msg, 'sender', '')),
                    reverse=reverse
                )
            elif sort_by == 'subject':
                sorted_messages = sorted(
                    self.current_messages,
                    key=lambda msg: str(getattr(msg, 'subject', '')),
                    reverse=reverse
                )
            else:
                print(f"[MessageListController] Unknown sort field: {sort_by}")
                return self.current_messages
            
            self.current_messages = sorted_messages
            print(f"[MessageListController] Sorted {len(sorted_messages)} messages by {sort_by}")
            return sorted_messages
        except Exception as e:
            print(f"[MessageListController] Error sorting messages: {e}")
            return self.current_messages
    
    def select_message_by_index(self, index):
        """
        Select a message by its index in the current list.
        
        Args:
            index (int): Index of the message to select (0-based)
            
        Returns:
            XAMailMessage: Selected message object or None
        """
        if not self.current_messages:
            self.get_messages()
        
        if 0 <= index < len(self.current_messages):
            self.selected_message = self.current_messages[index]
            print(f"[MessageListController] Selected message at index {index}: {getattr(self.selected_message, 'subject', 'No Subject')}")
            return self.selected_message
        else:
            print(f"[MessageListController] Index {index} out of range (0-{len(self.current_messages)-1})")
            return None
    
    def select_message_by_subject(self, subject):
        """
        Select a message by its subject.
        
        Args:
            subject (str): Subject of the message to select
            
        Returns:
            XAMailMessage: Selected message object or None
        """
        if not self.current_messages:
            self.get_messages()
        
        for message in self.current_messages:
            try:
                if hasattr(message, 'subject') and str(message.subject) == subject:
                    self.selected_message = message
                    print(f"[MessageListController] Selected message with subject: {subject}")
                    return message
            except Exception:
                continue
        
        print(f"[MessageListController] No message found with subject: {subject}")
        return None
    
    def get_message_info(self, message=None):
        """
        Get basic information about a message.
        
        Args:
            message (XAMailMessage, optional): Message object. If None, uses selected message.
            
        Returns:
            dict: Message information
        """
        if message is None:
            message = self.selected_message
        
        if not message:
            return {}
        
        try:
            info = {
                'subject': str(getattr(message, 'subject', 'No Subject')),
                'sender': str(getattr(message, 'sender', 'Unknown')),
                'date_received': str(getattr(message, 'date_received', 'Unknown')),
                'read': getattr(message, 'read', False),
                'flagged': getattr(message, 'flagged', False),
                'has_attachments': len(getattr(message, 'mail_attachments', [])) > 0
            }
            return info
        except Exception as e:
            print(f"[MessageListController] Error getting message info: {e}")
            return {}
    
    def get_message_count(self):
        """
        Get the total number of messages in the current list.
        
        Returns:
            int: Number of messages
        """
        if not self.current_messages:
            self.get_messages()
        return len(self.current_messages)
    
    def get_unread_count(self):
        """
        Get the number of unread messages in the current list.
        
        Returns:
            int: Number of unread messages
        """
        if not self.current_messages:
            self.get_messages()
        
        unread_count = 0
        for message in self.current_messages:
            try:
                if not getattr(message, 'read', True):
                    unread_count += 1
            except Exception:
                continue
        
        return unread_count
    
    def mark_selected_as_read(self):
        """
        Mark the selected message as read.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.selected_message:
            print("[MessageListController] No message selected")
            return False
        
        try:
            self.selected_message.read = True
            print("[MessageListController] Marked selected message as read")
            return True
        except Exception as e:
            print(f"[MessageListController] Error marking message as read: {e}")
            return False
    
    def get_current_context(self):
        """
        Get current message list context.
        
        Returns:
            dict: Current context information
        """
        context = {
            'total_messages': self.get_message_count(),
            'unread_messages': self.get_unread_count(),
            'selected_message': self.get_message_info() if self.selected_message else None,
            'mailbox': self.mail_controller.current_mailbox.name if self.mail_controller.current_mailbox else None,
            'account': self.mail_controller.current_account.name if self.mail_controller.current_account else None
        }
        return context 