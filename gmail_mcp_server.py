"""
Gmail MCP Server
================

A Model Context Protocol (MCP) server exposing tools to interact with Gmail.
It allows sending email, creating drafts, reading and searching messages,
managing labels and filters, and triggering n8n workflows. Configuration
is done via environment variables:

- GMAIL_CREDENTIALS_PATH: path to OAuth client secrets file.
- GMAIL_TOKEN_PATH: path to token storage file.
- N8N_WEBHOOK_BASE_URL: base URL for n8n webhook.

Run with:

    python gmail_mcp_server.py
"""

import asyncio
import base64
import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from mcp.server.fastmcp import FastMCP

SCOPES: List[str] = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GmailService:
    """Encapsulates Gmail API operations."""

    def __init__(self,
                 credentials_path: Optional[str] = None,
                 token_path: Optional[str] = None) -> None:
        self.credentials_path = credentials_path or os.getenv(
            "GMAIL_CREDENTIALS_PATH", "credentials.json")
        self.token_path = token_path or os.getenv(
            "GMAIL_TOKEN_PATH", "token.json")
        self.creds: Optional[Credentials] = None
        self.service = self._get_service()

    def _get_service(self) -> Any:
        creds: Optional[Credentials] = None
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(
                    self.token_path, SCOPES)
            except Exception as exc:
                logger.warning("Failed to load token: %s", exc)
                creds = None
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as exc:
                    logger.warning("Token refresh failed: %s", exc)
                    creds = None
            if not creds or not creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            try:
                with open(self.token_path, "w", encoding="utf-8") as token_file:
                    token_file.write(creds.to_json())
            except OSError as exc:
                logger.warning("Could not write token file: %s", exc)
        self.creds = creds
        return build("gmail", "v1", credentials=creds, cache_discovery=False)

    def get_user_email(self) -> str:
        profile = self.service.users().getProfile(userId="me").execute()
        return profile.get("emailAddress", "me")

    def _compose(self, sender: str, to: List[str], subject: str, body: str,
                 mime_type: str = "text/plain",
                 cc: Optional[List[str]] = None,
                 bcc: Optional[List[str]] = None,
                 html_body: Optional[str] = None,
                 attachments: Optional[List[str]] = None) -> MIMEMultipart | MIMEText:
        to_header = ", ".join(to) if to else ""
        cc_header = ", ".join(cc) if cc else None
        bcc_header = ", ".join(bcc) if bcc else None
        headers = {"From": sender, "To": to_header, "Subject": subject}
        if cc_header:
            headers["Cc"] = cc_header
        if bcc_header:
            headers["Bcc"] = bcc_header
        if attachments:
            message = MIMEMultipart()
            for k, v in headers.items():
                message[k] = v
            if mime_type == "multipart/alternative" and html_body:
                alt = MIMEMultipart("alternative")
                alt.attach(MIMEText(body, "plain"))
                alt.attach(MIMEText(html_body, "html"))
                message.attach(alt)
            else:
                subtype = "html" if mime_type == "text/html" else "plain"
                message.attach(MIMEText(body, subtype))
            for file_path in attachments:
                try:
                    with open(file_path, "rb") as fh:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(fh.read())
                    encoders.encode_base64(part)
                    filename = os.path.basename(file_path)
                    part.add_header("Content-Disposition",
                                    f"attachment; filename=\"{filename}\"")
                    message.attach(part)
                except OSError as exc:
                    logger.warning("Attachment error %s: %s", file_path, exc)
            return message
        else:
            if mime_type == "multipart/alternative" and html_body:
                message = MIMEMultipart("alternative")
                for k, v in headers.items():
                    message[k] = v
                message.attach(MIMEText(body, "plain"))
                message.attach(MIMEText(html_body, "html"))
                return message
            subtype = "html" if mime_type == "text/html" else "plain"
            msg = MIMEText(body, subtype)
            for k, v in headers.items():
                msg[k] = v
            return msg

    def send_email(self, to: List[str], subject: str, body: str,
                   cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None,
                   mime_type: str = "text/plain",
                   attachments: Optional[List[str]] = None,
                   html_body: Optional[str] = None) -> str:
        mime_message = self._compose(
            sender=self.get_user_email(),
            to=to,
            subject=subject,
            body=body,
            mime_type=mime_type,
            cc=cc,
            bcc=bcc,
            html_body=html_body,
            attachments=attachments,
        )
        raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
        body_obj = {"raw": raw}
        result = self.service.users().messages().send(
            userId="me", body=body_obj).execute()
        return result.get("id")

    def create_draft(self, to: List[str], subject: str, body: str,
                     cc: Optional[List[str]] = None,
                     bcc: Optional[List[str]] = None,
                     mime_type: str = "text/plain",
                     attachments: Optional[List[str]] = None,
                     html_body: Optional[str] = None) -> str:
        mime_message = self._compose(
            sender=self.get_user_email(),
            to=to,
            subject=subject,
            body=body,
            mime_type=mime_type,
            cc=cc,
            bcc=bcc,
            html_body=html_body,
            attachments=attachments,
        )
        raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
        draft_body = {"message": {"raw": raw}}
        result = self.service.users().drafts().create(
            userId="me", body=draft_body).execute()
        return result.get("id")

    def read_email(self, message_id: str) -> str:
        message = self.service.users().messages().get(
            userId="me", id=message_id, format="full").execute()
        headers = message.get("payload", {}).get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "")
        snippet = message.get("snippet", "")
        body_parts: List[str] = []
        def walk(part):
            if part.get("parts"):
                for p in part["parts"]:
                    walk(p)
            else:
                data = part.get("body", {}).get("data")
                if data:
                    decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    body_parts.append(decoded)
        walk(message.get("payload", {}))
        body = "\n".join(body_parts) if body_parts else snippet
        return f"Subject: {subject}\nFrom: {sender}\n\n{body}"

    def search_emails(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        response = self.service.users().messages().list(
            userId="me", q=query, maxResults=max_results).execute()
        result: List[Dict[str, str]] = []
        for item in response.get("messages", []):
            meta = self.service.users().messages().get(
                userId="me", id=item["id"], format="metadata",
                metadataHeaders=["Subject","From"]).execute()
            headers = meta.get("payload", {}).get("headers", [])
            subject = next((h["value"] for h in headers if h["name"]=="Subject"), "")
            sender = next((h["value"] for h in headers if h["name"]=="From"), "")
            result.append({"id": item["id"], "subject": subject, "from": sender})
        return result

    def modify_labels(self, message_id: str,
                      add_label_ids: Optional[List[str]] = None,
                      remove_label_ids: Optional[List[str]] = None) -> None:
        body = {"addLabelIds": add_label_ids or [], "removeLabelIds": remove_label_ids or []}
        self.service.users().messages().modify(
            userId="me", id=message_id, body=body).execute()

    def list_labels(self) -> List[Dict[str, Any]]:
        resp = self.service.users().labels().list(userId="me").execute()
        return resp.get("labels", [])

    def create_label(self, name: str,
                     message_list_visibility: str = "show",
                     label_list_visibility: str = "labelShow") -> Dict[str, Any]:
        body = {
            "name": name,
            "messageListVisibility": message_list_visibility,
            "labelListVisibility": label_list_visibility,
        }
        return self.service.users().labels().create(
            userId="me", body=body).execute()

    def delete_label(self, label_id: str) -> None:
        self.service.users().labels().delete(userId="me", id=label_id).execute()

    def list_filters(self) -> List[Dict[str, Any]]:
        resp = self.service.users().settings().filters().list(userId="me").execute()
        return resp.get("filter", [])

    def get_filter(self, filter_id: str) -> Dict[str, Any]:
        return self.service.users().settings().filters().get(userId="me", id=filter_id).execute()

    def create_filter(self, criteria: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
        body = {"criteria": criteria, "action": action}
        return self.service.users().settings().filters().create(
            userId="me", body=body).execute()

    def delete_filter(self, filter_id: str) -> None:
        self.service.users().settings().filters().delete(userId="me", id=filter_id).execute()

    def trigger_n8n_workflow(self, path: str, payload: Dict[str, Any]) -> str:
        base_url = os.getenv("N8N_WEBHOOK_BASE_URL")
        if not base_url:
            raise RuntimeError("N8N_WEBHOOK_BASE_URL is not set")
        url = base_url.rstrip("/") + "/" + path.lstrip("/")
        with httpx.Client() as client:
            response = client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
        return f"n8n workflow triggered successfully (HTTP {response.status_code})."

# Instantiate service and MCP server
_gmail_service = GmailService()
mcp = FastMCP("gmail_server")

# Asynchronous wrappers

@mcp.tool()
async def send_email(to: List[str], subject: str, body: str,
                     cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None,
                     mime_type: str = "text/plain",
                     attachments: Optional[List[str]] = None,
                     html_body: Optional[str] = None) -> str:
    loop = asyncio.get_running_loop()
    try:
        msg_id = await loop.run_in_executor(
            None,
            _gmail_service.send_email,
            to,
            subject,
            body,
            cc,
            bcc,
            mime_type,
            attachments,
            html_body,
        )
        return f"Email sent successfully. Message ID: {msg_id}"
    except HttpError as e:
        logger.error("send_email failed: %s", e)
        raise

@mcp.tool()
async def create_draft(to: List[str], subject: str, body: str,
                       cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None,
                       mime_type: str = "text/plain",
                       attachments: Optional[List[str]] = None,
                       html_body: Optional[str] = None) -> str:
    loop = asyncio.get_running_loop()
    try:
        draft_id = await loop.run_in_executor(
            None,
            _gmail_service.create_draft,
            to,
            subject,
            body,
            cc,
            bcc,
            mime_type,
            attachments,
            html_body,
        )
        return f"Draft created with ID: {draft_id}"
    except HttpError as e:
        logger.error("create_draft failed: %s", e)
        raise

@mcp.tool()
async def read_email(message_id: str) -> str:
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _gmail_service.read_email, message_id)
    except HttpError as e:
        logger.error("read_email failed: %s", e)
        raise

@mcp.tool()
async def search_emails(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _gmail_service.search_emails, query, max_results)
    except HttpError as e:
        logger.error("search_emails failed: %s", e)
        raise

@mcp.tool()
async def modify_email_labels(message_id: str,
                              add_label_ids: Optional[List[str]] = None,
                              remove_label_ids: Optional[List[str]] = None) -> str:
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(
            None,
            _gmail_service.modify_labels,
            message_id,
            add_label_ids,
            remove_label_ids,
        )
        return "Labels modified successfully."
    except HttpError as e:
        logger.error("modify_email_labels failed: %s", e)
        raise

@mcp.tool()
async def list_labels() -> List[Dict[str, Any]]:
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _gmail_service.list_labels)
    except HttpError as e:
        logger.error("list_labels failed: %s", e)
        raise

@mcp.tool()
async def create_label(name: str,
                       message_list_visibility: str = "show",
                       label_list_visibility: str = "labelShow") -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(
            None,
            _gmail_service.create_label,
            name,
            message_list_visibility,
            label_list_visibility,
        )
    except HttpError as e:
        logger.error("create_label failed: %s", e)
        raise

@mcp.tool()
async def delete_label(label_id: str) -> str:
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, _gmail_service.delete_label, label_id)
        return "Label deleted successfully."
    except HttpError as e:
        logger.error("delete_label failed: %s", e)
        raise

@mcp.tool()
async def list_filters() -> List[Dict[str, Any]]:
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _gmail_service.list_filters)
    except HttpError as e:
        logger.error("list_filters failed: %s", e)
        raise

@mcp.tool()
async def get_filter(filter_id: str) -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _gmail_service.get_filter, filter_id)
    except HttpError as e:
        logger.error("get_filter failed: %s", e)
        raise

@mcp.tool()
async def create_filter(criteria: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _gmail_service.create_filter, criteria, action)
    except HttpError as e:
        logger.error("create_filter failed: %s", e)
        raise

@mcp.tool()
async def delete_filter(filter_id: str) -> str:
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, _gmail_service.delete_filter, filter_id)
        return "Filter deleted successfully."
    except HttpError as e:
        logger.error("delete_filter failed: %s", e)
        raise

@mcp.tool()
async def trigger_n8n_workflow(path: str, payload: Dict[str, Any]) -> str:
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _gmail_service.trigger_n8n_workflow, path, payload)
    except Exception as exc:
        logger.error("trigger_n8n_workflow failed: %s", exc)
        raise

def main() -> None:
    mcp.run()

if __name__ == "__main__":
    main()
