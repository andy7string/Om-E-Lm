"""
Mail Controllers Package

This package contains three main controllers for Mail app automation:

1. mail_controller.py - High-level app, account, and mailbox management
2. message_list_controller.py - Message list operations (search, sort, select)
3. mail_message_controller.py - Individual message operations (body, attachments, actions)
"""

from .mail_controller import MailController
from .message_list_controller import MessageListController
from .mail_message_controller import MailMessageController

__all__ = ['MailController', 'MessageListController', 'MailMessageController'] 