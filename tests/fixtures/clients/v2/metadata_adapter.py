"""Runner self-test only: independent fake client with selectable reducer defects."""

import json
import sys
import time

mode = sys.argv[1] if len(sys.argv) > 1 else "correct"
stored = {}

for line in sys.stdin:
    request = json.loads(line)
    method = request["method"]
    if method == "_tck/reset":
        stored = {}
        result = [] if mode == "bad-reset" else {}
    elif method == "_tck/apply":
        if mode == "exit":
            sys.exit(1)
        if mode == "silent":
            time.sleep(60)
        params = request["params"]["message"]["params"]
        update = params["update"]
        if mode == "envelope":
            stored.update(params["_meta"])
        if "_meta" in update:
            patch = update["_meta"]
            if patch is None:
                if mode != "ignore-clear":
                    stored = {}
            elif mode == "replace":
                stored = patch
            else:
                for key, value in patch.items():
                    if value is None:
                        if mode == "store-null":
                            stored[key] = value
                        else:
                            stored.pop(key, None)
                    elif mode == "recursive" and isinstance(value, dict):
                        stored[key] = {**stored.get(key, {}), **value}
                    else:
                        stored[key] = value
        result = {"_meta": stored}
        if mode == "bad-snapshot":
            result = {"unexpected": stored}
        elif mode == "error":
            print(json.dumps({"jsonrpc": "2.0", "id": request["id"],
                              "error": {"code": -32601, "message": "unsupported"}}), flush=True)
            continue
    else:
        raise ValueError(method)
    print(json.dumps({"jsonrpc": "1.0" if mode == "wrong-version" else "2.0",
                      "id": True if mode == "boolean-id" and method == "_tck/reset" else request["id"],
                      "result": result}), flush=True)

if mode == "exit-after-eof":
    sys.exit(1)
