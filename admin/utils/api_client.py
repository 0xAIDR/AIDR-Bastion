"""
API Client for AIDR Bastion Admin Panel.

This module provides a simple interface to interact with the AIDR Bastion API.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

# Load environment variables from admin/.env
admin_dir = Path(__file__).parent.parent
env_path = admin_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)


class APIClient:
    """Client for interacting with AIDR Bastion API."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize API client.

        Args:
            base_url: Base URL of the AIDR Bastion API (overrides environment variable)
        """
        self.base_url = base_url or os.getenv(
            "ADMIN_API_BASE_URL", "http://localhost:8000"
        )
        self.api_prefix = os.getenv("ADMIN_API_PREFIX", "/api/v1")
        self.timeout = int(os.getenv("ADMIN_API_TIMEOUT", "30"))

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters

        Returns:
            Response JSON data
        """
        url = f"{self.base_url}{self.api_prefix}{endpoint}"
        try:
            response = requests.request(
                method, url, json=data, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")

    # Flow endpoints
    def get_flows(self) -> List[Dict]:
        """Get list of available flows."""
        return self._make_request("GET", "/flow/list").get("flows", [])

    def run_flow(
        self, prompt: str, pipeline_flow: str, task_id: Optional[str] = None
    ) -> Dict:
        """Run pipeline flow analysis."""
        data = {"prompt": prompt, "pipeline_flow": pipeline_flow}
        if task_id:
            data["task_id"] = task_id
        return self._make_request("POST", "/flow/run", data=data)

    # Manager endpoints
    def get_managers(self) -> List[Dict]:
        """Get list of all managers."""
        return self._make_request("GET", "/manager/list").get("managers", [])

    def get_manager(self, manager_id: str) -> Dict:
        """Get specific manager by ID."""
        return self._make_request("GET", f"/manager/{manager_id}")

    def switch_active_client(self, manager_id: str, client_id: str) -> Dict:
        """
        Switch active client for a manager.

        Args:
            manager_id: Manager identifier (e.g., 'similarity', 'llm')
            client_id: Client identifier (e.g., 'opensearch', 'elasticsearch')

        Returns:
            Response with client_id and status
        """
        data = {"manager_id": manager_id, "client_id": client_id}
        return self._make_request("POST", "/manager/switch_active_client", data=data)

    # Rules endpoints
    def get_rules(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Dict:
        """Get list of rules with optional filters."""
        params = {"skip": skip, "limit": limit}
        if category:
            params["category"] = category
        if enabled is not None:
            params["enabled"] = enabled
        return self._make_request("GET", "/rules", params=params)

    def get_rule(self, rule_id: int) -> Dict:
        """Get specific rule by ID."""
        return self._make_request("GET", f"/rules/{rule_id}")

    def create_rule(self, rule_data: Dict) -> Dict:
        """Create new rule."""
        return self._make_request("POST", "/rules", data=rule_data)

    def update_rule(self, rule_id: int, rule_data: Dict) -> Dict:
        """Update existing rule."""
        return self._make_request("PUT", f"/rules/{rule_id}", data=rule_data)

    def delete_rule(self, rule_id: int) -> None:
        """Delete rule."""
        self._make_request("DELETE", f"/rules/{rule_id}")

    def toggle_rule(self, rule_id: int) -> Dict:
        """Toggle rule enabled/disabled status."""
        return self._make_request("PATCH", f"/rules/{rule_id}/toggle")

    # Events endpoints
    def get_events(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        flow_name: Optional[str] = None,
    ) -> Dict:
        """Get list of events with optional filters."""
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        if flow_name:
            params["flow_name"] = flow_name
        return self._make_request("GET", "/events", params=params)

    def get_event(self, event_id: int) -> Dict:
        """Get specific event by ID."""
        return self._make_request("GET", f"/events/{event_id}")

    def get_event_by_task(self, task_id: str) -> Dict:
        """Get event by task ID."""
        return self._make_request("GET", f"/events/task/{task_id}")

    def get_recent_events(self, limit: int = 50) -> Dict:
        """Get recent events."""
        return self._make_request("GET", "/events/recent", params={"limit": limit})

    def get_event_stats(self) -> Dict:
        """Get event statistics."""
        return self._make_request("GET", "/events/stats")


# Global client instance
api = APIClient()
