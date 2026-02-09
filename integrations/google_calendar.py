"""Google Calendar integration for HealthPilot.

Provides OAuth2 authentication and calendar event management.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from config import get_settings

logger = logging.getLogger(__name__)


class GoogleCalendarClient:
    """Client for Google Calendar API operations.

    Handles OAuth2 authentication and CRUD operations for calendar events.
    """

    def __init__(self) -> None:
        """Initialize the Google Calendar client."""
        self.settings = get_settings()
        self._service = None

    def _get_credentials(self) -> Any:
        """Get OAuth2 credentials for Google Calendar API.

        Returns:
            Google OAuth2 credentials object.

        Raises:
            FileNotFoundError: If credentials file doesn't exist.
        """
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        SCOPES = ["https://www.googleapis.com/auth/calendar"]
        creds = None
        token_path = Path("credentials/token.json")
        creds_path = self.settings.google_credentials_path

        # Token file stores user's access and refresh tokens
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not creds_path.exists():
                    raise FileNotFoundError(
                        f"Google Calendar credentials not found at {creds_path}. "
                        f"Download from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(token_path, "w") as token:
                token.write(creds.to_json())

        return creds

    def _get_service(self) -> Any:
        """Get or create Google Calendar API service.

        Returns:
            Google Calendar API service object.
        """
        if self._service is None:
            from googleapiclient.discovery import build

            creds = self._get_credentials()
            self._service = build("calendar", "v3", credentials=creds)
            logger.info("Google Calendar service initialized")

        return self._service

    def list_events(
        self,
        days_ahead: int = 7,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """List upcoming calendar events.

        Args:
            days_ahead: Number of days to look ahead.
            max_results: Maximum number of events to return.

        Returns:
            List of event dictionaries with simplified structure.
        """
        try:
            service = self._get_service()
            now = datetime.utcnow().isoformat() + "Z"
            end = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + "Z"

            events_result = (
                service.events()
                .list(
                    calendarId=self.settings.google_calendar_id,
                    timeMin=now,
                    timeMax=end,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            logger.info("Retrieved %d calendar events", len(events))

            # Simplify event structure
            simplified = []
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                end = event["end"].get("dateTime", event["end"].get("date"))

                simplified.append({
                    "id": event["id"],
                    "summary": event.get("summary", "No Title"),
                    "description": event.get("description", ""),
                    "start": start,
                    "end": end,
                    "location": event.get("location", ""),
                })

            return simplified

        except FileNotFoundError as e:
            logger.warning("Google Calendar credentials not configured: %s", e)
            return []
        except Exception as e:
            logger.error("Failed to list calendar events: %s", e)
            return []

    def create_event(
        self,
        title: str,
        start_time: str,
        duration_minutes: int = 60,
        description: str = "",
        location: str = "",
    ) -> dict[str, Any] | None:
        """Create a new calendar event.

        Args:
            title: Event title/summary.
            start_time: Start time in ISO format (e.g., "2026-02-10T07:00:00").
            duration_minutes: Event duration in minutes.
            description: Event description.
            location: Event location.

        Returns:
            Created event dict or None if failed.
        """
        try:
            service = self._get_service()

            # Parse start time and calculate end time
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_dt = start_dt + timedelta(minutes=duration_minutes)

            event = {
                "summary": title,
                "description": description,
                "location": location,
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": "UTC",
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 30},
                    ],
                },
            }

            created = (
                service.events()
                .insert(calendarId=self.settings.google_calendar_id, body=event)
                .execute()
            )

            logger.info("Created calendar event: %s at %s", title, start_time)
            return {
                "id": created["id"],
                "summary": created["summary"],
                "start": created["start"]["dateTime"],
                "link": created.get("htmlLink", ""),
            }

        except FileNotFoundError as e:
            logger.warning("Google Calendar credentials not configured: %s", e)
            return None
        except Exception as e:
            logger.error("Failed to create calendar event: %s", e)
            return None

    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event.

        Args:
            event_id: ID of the event to delete.

        Returns:
            True if successful, False otherwise.
        """
        try:
            service = self._get_service()
            service.events().delete(
                calendarId=self.settings.google_calendar_id, eventId=event_id
            ).execute()
            logger.info("Deleted calendar event: %s", event_id)
            return True
        except Exception as e:
            logger.error("Failed to delete calendar event: %s", e)
            return False


# Module-level client instance
_calendar_client: GoogleCalendarClient | None = None


def get_calendar_client() -> GoogleCalendarClient:
    """Get or create the Google Calendar client singleton.

    Returns:
        GoogleCalendarClient instance.
    """
    global _calendar_client
    if _calendar_client is None:
        _calendar_client = GoogleCalendarClient()
    return _calendar_client
