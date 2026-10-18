"""Isolated production Messages owner and complete records for native UI checks."""

from contextlib import ExitStack
import html
import json
from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, Property, Signal, Slot
from thlib.ui.communication_feed import MessagesController
from thlib.ui.emoji import EmojiCatalog
from thlib.ui.message_attachments import ChatAttachmentController
from thlib.ui.workspace_models.records import RecordListModel
from tests.test_notes_qml import _Application

ROOT = Path(__file__).resolve().parents[1]


class Application(_Application):
    project_changed = Signal(str, str)


class Locale(QObject):
    def __init__(self, language):
        super().__init__()
        self.language = language

    @Property(str, constant=True)
    def current_language(self):
        return self.language


class Profiles(QObject):
    @Slot(str)
    def open_profile(self, login):
        self.opened = login


class Fixture:
    def __init__(self, language="en"):
        self.time_label = (
            json.loads(
                (ROOT / "thlib/ui/translations/ru.json").read_text(encoding="utf-8")
            ).get("Just now", "Just now")
            if language == "ru"
            else "Just now"
        )
        self.data = json.loads(
            (ROOT / "tests/fixtures/frame_messages.json").read_text(encoding="utf-8")
        )
        self.stack = ExitStack()
        for module in ("communication_feed", "message_attachments"):
            self.stack.enter_context(
                patch("thlib.ui." + module + ".env_read_config", return_value={})
            )
            self.stack.enter_context(patch("thlib.ui." + module + ".env_write_config"))
        self.stack.enter_context(
            patch("thlib.environment.env_server.get_user", return_value="admin")
        )
        self.application = Application()
        self.users = RecordListModel(tuple(self.data["users"][0]), self.data["users"])
        self.profiles = Profiles()
        self.attachments = ChatAttachmentController(self.application)
        self.controller = MessagesController(
            self.application, users=self.users, attachments=self.attachments
        )
        self.controller.load = Mock()
        self.controller.set_visible = Mock()
        self.controller._start_worker = Mock()
        self.controller._initialized = True
        self.controller._conversation_id = "favorites"
        conversations = []
        for row in self.data["conversations"]:
            record = {name: "" for name in self.controller.conversations._roles}
            record.update(
                {
                    name: 0
                    for name in (
                        "unread",
                        "mentionCount",
                        "participantCount",
                        "messageCount",
                        "attachmentCount",
                        "colorIndex",
                    )
                }
            )
            record.update(
                recipients=[],
                selected=False,
                isPersonalNotes=False,
                canManage=False,
                canRename=False,
                canDelete=False,
                canAddMembers=False,
                canClearPersonal=False,
                presenceKnown=False,
                online=False,
                acronym="LR",
                initials="LR",
            )
            record.update(row)
            record["colorIndex"] = min(4, len(row.get("recipients", [])))
            conversations.append(record)
        self.controller.conversations.replace(conversations)
        self.controller.messages.replace(self.records())
        self.emoji = EmojiCatalog(ROOT)

    def records(self):
        result = []
        for row in self.data["messages"]:
            user = next(
                user for user in self.data["users"] if user["login"] == row["login"]
            )
            delivery = row.get("__delivery__", {})
            reference = dict(row.get("__reply__", {}))
            record = dict(
                messageId=row["code"],
                sender=row["login"],
                senderDisplay=user["displayName"],
                avatarUrl="",
                initials=user["initials"],
                senderColor=user["avatarColor"],
                body=row["message"],
                bodyHtml=html.escape(row["message"]).replace("\n", "<br>"),
                skeyPreviews=[],
                timestamp=row["timestamp"],
                timePretty=self.time_label,
                timeSimple=row["timestamp"],
                isOwn=row["login"] == "admin",
                unread=False,
                attachments=[
                    dict(
                        title=snapshot["__files__"][0]["file_name"],
                        previewUrl="",
                        token=snapshot["code"],
                        extension="txt",
                        local=False,
                        size=12,
                        hasWebPreview=False,
                    )
                    for snapshot in row.get("__attachments__", [])
                ],
                attachmentCount=0,
                canEdit=True,
                edited=False,
                pinned=False,
                editedBy="",
                editedAt="",
                editHistory=[],
                replyTo=reference,
                forwardedFrom={},
                forwardSelected=False,
                reactions=[],
                reactionPending=False,
                deliveryStatus=delivery.get("status", "sent"),
                deliveryRecipientCount=delivery.get("recipientCount", 0),
                deliveryDeliveredCount=delivery.get("deliveredCount", 0),
                deliveryReadCount=delivery.get("readCount", 0),
                groupFirst=True,
                groupLast=True,
            )
            record["displayHtml"] = record["bodyHtml"]
            result.append(record)
        return result

    def context(self):
        return dict(
            messagesController=self.controller,
            messageConversationModel=self.controller.conversations,
            messageSurfaceModel=self.controller.message_surfaces,
            userController=self.profiles,
            userListModel=self.users,
            messageAttachments=self.attachments,
            messageAttachmentDraftModel=self.attachments.model,
            emojiCatalog=self.emoji,
        )

    def close(self):
        self.controller.shutdown()
        self.attachments.shutdown()
        self.stack.close()
