"""Simple OneDrive uploader using Microsoft Graph Device Code flow.

Usage notes:
- Register an app in Azure AD (App registrations) and note the `client_id`.
- Grant delegated permission `Files.ReadWrite.All` (or `Files.ReadWrite`) and `offline_access`.
- Run the CLI and follow the device-code instructions to authenticate.

This module uploads a local file to the user's OneDrive root (or subpath) and returns
the shareable web link which can be opened in Excel Online.
"""
import json
import os
from typing import Optional

import msal
import requests


DEFAULT_SCOPES = ["Files.ReadWrite.All", "offline_access", "User.Read"]


def acquire_token_device_flow(client_id: str, tenant_id: Optional[str] = None, scopes=None) -> str:
    scopes = scopes or DEFAULT_SCOPES
    authority = f"https://login.microsoftonline.com/{tenant_id}" if tenant_id else "https://login.microsoftonline.com/common"
    app = msal.PublicClientApplication(client_id=client_id, authority=authority)
    flow = app.initiate_device_flow(scopes=scopes)
    if "user_code" not in flow:
        raise RuntimeError("Failed to start device flow: %s" % flow)
    print(flow["message"])  # instructs the user to visit URL and enter code
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        return result["access_token"]
    raise RuntimeError("Failed to acquire token: %s" % json.dumps(result, indent=2))


def upload_file(access_token: str, local_path: str, remote_path: str) -> dict:
    """Upload file and return JSON response from Graph for the created item.

    remote_path is a path relative to OneDrive root, e.g. 'Raid/battle_log.xlsx'.
    """
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{remote_path}:/content"
    headers = {"Authorization": f"Bearer {access_token}"}
    with open(local_path, "rb") as f:
        resp = requests.put(url, headers=headers, data=f)
    resp.raise_for_status()
    return resp.json()


def create_share_link(access_token: str, item_id: str, link_type: str = "view") -> dict:
    url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/createLink"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    body = {"type": link_type}
    resp = requests.post(url, headers=headers, json=body)
    resp.raise_for_status()
    return resp.json()


def upload_file_to_onedrive(local_path: str, remote_path: str, client_id: str, tenant_id: Optional[str] = None) -> str:
    """High-level helper: authenticate, upload, create share link, return webUrl."""
    token = acquire_token_device_flow(client_id, tenant_id)
    item = upload_file(token, local_path, remote_path)
    item_id = item.get("id")
    if not item_id:
        raise RuntimeError("Upload succeeded but no item id returned")
    link = create_share_link(token, item_id, link_type="view")
    return link.get("link", {}).get("webUrl")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--client-id", required=True, help="Azure AD app client id")
    parser.add_argument("--file", required=True, help="Local file to upload")
    parser.add_argument("--remote", required=False, help="Remote path in OneDrive", default=None)
    parser.add_argument("--tenant", required=False, help="Tenant id (optional)")
    args = parser.parse_args()

    local = args.file
    remote = args.remote or os.path.basename(local)
    url = upload_file_to_onedrive(local, remote, args.client_id, tenant_id=args.tenant)
    print("File uploaded. Open in Excel Online:")
    print(url)
