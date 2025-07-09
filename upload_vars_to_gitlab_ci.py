#!/usr/bin/env python

import requests

project_group = "PROJECT GROUP"
gitlab_url = "GITLAB INSTANCE"
service_name = "SERVICE NAME"
csrf_token = "TOKEN"
session = "SESSION"

url = f"https://{gitlab_url}/{project_group}/{service_name}/-/variables"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://{gitlab_url}/{project_group}/{service_name}/-/settings/ci_cd",
    "X-CSRF-Token": csrf_token,
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json",
    "Origin": gitlab_url,
    "DNT": "1",
    "Connection": "keep-alive",
    "Cookie": f"_gitlab_session={session}; event_filter=all",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=0",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


def create_variable(key, value):
    data = {
        "variables_attributes": [
            {
                "description": None,
                "environment_scope": "*",
                "key": f"APP_{key}",
                "masked": False,
                "hidden": False,
                "protected": True,
                "raw": False,
                "value": value,
                "variable_type": "env_var",
                "id": None,
                "secret_value": value,
                "_destroy": False,
            }
        ]
    }

    response = requests.patch(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"Variable APP_{key} created successfully.")
    else:
        print(f"Failed to create variable APP_{key}: {response.text}")


if __name__ == "__main__":
    with open(".env") as file:
        for line in file:
            if "=" in line:
                key = line.split("=")[0]
                val = line.split("=")[1]
                create_variable(key, val)
