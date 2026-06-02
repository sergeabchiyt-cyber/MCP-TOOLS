import os
import json
import httpx
import boto3
from botocore.client import Config
from mcp.server.fastmcp import FastMCP

API_KEY         = os.environ["MCP_API_KEY"]
TGS3_ENDPOINT   = os.environ["TGS3_ENDPOINT"]
TGS3_ACCESS_KEY = os.environ["TGS3_ACCESS_KEY"]
TGS3_SECRET_KEY = os.environ["TGS3_SECRET_KEY"]
TGS3_BUCKET     = os.environ.get("TGS3_BUCKET", "hermes-storage")
PORT            = int(os.environ.get("PORT", 8000))

s3 = boto3.client(
    "s3",
    endpoint_url=TGS3_ENDPOINT,
    aws_access_key_id=TGS3_ACCESS_KEY,
    aws_secret_access_key=TGS3_SECRET_KEY,
    region_name="us-east-1",
    config=Config(signature_version="s3v4"),
)

mcp = FastMCP("Hermes Tools", host="0.0.0.0", port=PORT)


@mcp.tool()
def storage_read(key: str) -> str:
    """Read a file from TG-S3 storage. Returns file contents as string."""
    try:
        response = s3.get_object(Bucket=TGS3_BUCKET, Key=key)
        return response["Body"].read().decode("utf-8")
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def storage_write(key: str, content: str) -> str:
    """Write a string to TG-S3 storage."""
    try:
        s3.put_object(Bucket=TGS3_BUCKET, Key=key, Body=content.encode("utf-8"))
        return f"OK: written to {key}"
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def storage_list(prefix: str = "") -> str:
    """List files in TG-S3 storage under a given prefix."""
    try:
        response = s3.list_objects_v2(Bucket=TGS3_BUCKET, Prefix=prefix)
        files = [obj["Key"] for obj in response.get("Contents", [])]
        return json.dumps(files)
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def storage_delete(key: str) -> str:
    """Delete a file from TG-S3 storage."""
    try:
        s3.delete_object(Bucket=TGS3_BUCKET, Key=key)
        return f"OK: deleted {key}"
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def http_get(url: str, headers: str = "{}") -> str:
    """Make an HTTP GET request. headers is a JSON string."""
    try:
        h = json.loads(headers)
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            response = client.get(url, headers=h)
            return json.dumps({
                "status": response.status_code,
                "body": response.text[:50000],
            })
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def http_post(url: str, body: str, headers: str = "{}") -> str:
    """Make an HTTP POST request. body and headers are JSON strings."""
    try:
        h = json.loads(headers)
        b = json.loads(body)
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            response = client.post(url, json=b, headers=h)
            return json.dumps({
                "status": response.status_code,
                "body": response.text[:50000],
            })
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def json_query(data: str, key_path: str) -> str:
    """Query a JSON string with a dot-separated key path. e.g. 'results.0.name'"""
    try:
        obj = json.loads(data)
        parts = key_path.split(".")
        for part in parts:
            if isinstance(obj, list):
                obj = obj[int(part)]
            else:
                obj = obj[part]
        return json.dumps(obj)
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def health() -> str:
    """Check if the MCP tool server is alive."""
    return json.dumps({"status": "ok", "tools": 7})


if __name__ == "__main__":
    mcp.run(transport="sse")
