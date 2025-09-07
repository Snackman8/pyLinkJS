import argparse
import logging
import json
import binascii
from pylinkjs.PyLinkJS import run_pylinkjs_app

def _hex_preview(b, n=64):
    if not b:
        return ""
    return binascii.hexlify(b[:n]).decode("ascii")

def handle_404(path, uri, host, extra_settings, headers, body, method, *args):
    """
    Unified GET/POST handler.
    Returns: (bytes, content_type, status_code, headers_out)
    """
    ct = (headers.get("Content-Type") or "").split(";")[0].strip().lower()

    resp = {
        "ok": True,
        "method": method,
        "path": path,
        "uri": uri,
        "host": host,
        "content_type": ct,
        "received_headers": headers,
    }

    if body:
        if ct == "application/json":
            try:
                resp["json_body"] = json.loads(body.decode("utf-8"))
            except Exception as e:
                resp["json_body_error"] = "{}: {}".format(type(e).__name__, str(e))
                resp["body_len"] = len(body)
                resp["body_hex_preview"] = _hex_preview(body)
        else:
            resp["body_len"] = len(body)
            resp["body_hex_preview"] = _hex_preview(body)
    else:
        resp["body_len"] = 0

    out = json.dumps(resp, indent=2).encode("utf-8")
    return (out, "application/json", 200, {"X-Router": "PyLinkJS-Min"})

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8300)
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG, format="%(relativeCreated)6d %(threadName)s %(message)s")
    run_pylinkjs_app(
        default_html="post_example.html",
        on_404=handle_404,
        port=args.port,
    )
