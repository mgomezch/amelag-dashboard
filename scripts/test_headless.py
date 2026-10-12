#!/usr/bin/env python3
"""
test_headless.py - Headless Browser Testing & Responsive Verification
Tests the AMELAG Dashboard across constrained mobile, tablet, and desktop display resolutions.
"""

import http.server
import os
import signal
import socketserver
import subprocess
import sys
import time

PORT = 8846
RESOLUTIONS = [
    ("mobile_narrow_320", 320, 568, "index.html"),
    ("mobile_narrow_long_320", 320, 1600, "index.html"),
    ("mobile_standard_375", 375, 667, "index.html"),
    ("mobile_standard_long_375", 375, 1800, "index.html"),
    ("tablet_768", 768, 1024, "index.html"),
    ("desktop_1280", 1280, 800, "index.html"),
    ("desktop_long_1280", 1280, 1600, "index.html"),
    ("en_mobile_375", 375, 667, "en.html"),
    ("en_desktop_1280", 1280, 800, "en.html")
]

def run_tests(root_dir="."):
    os.chdir(root_dir)
    screenshots_dir = os.path.join(root_dir, "test_screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    socketserver.TCPServer.allow_reuse_address = True
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    print(f"Starting test HTTP server on port {PORT}...")

    import threading
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)

    results = []
    try:
        for name, width, height, page in RESOLUTIONS:
            url = f"http://127.0.0.1:{PORT}/{page}"
            screenshot_path = os.path.join(screenshots_dir, f"{name}.png")
            print(f"Testing {page} at resolution {width}x{height} ({name})...")
            
            cmd = [
                "firefox",
                "--headless",
                f"--window-size={width},{height}",
                f"--screenshot={screenshot_path}",
                url
            ]
            
            t0 = time.time()
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
            elapsed = time.time() - t0

            if os.path.exists(screenshot_path) and os.path.getsize(screenshot_path) > 0:
                sz = os.path.getsize(screenshot_path)
                print(f"  ✓ Captured {name}.png ({sz:,} bytes in {elapsed:.1f}s)")
                results.append((name, width, height, True, sz))
            else:
                print(f"  ✗ Failed to capture {name}.png: {proc.stderr[:200]}")
                results.append((name, width, height, False, 0))

    finally:
        print("Shutting down test HTTP server...")
        httpd.shutdown()
        httpd.server_close()

    print("\n--- Test Summary ---")
    all_ok = True
    for name, w, h, ok, sz in results:
        status = "PASSED" if ok else "FAILED"
        if not ok:
            all_ok = False
        print(f"[{status}] {name} ({w}x{h}) - Size: {sz:,} bytes")

    if not all_ok:
        sys.exit(1)
    print("All headless browser tests passed successfully!")

if __name__ == "__main__":
    run_tests(os.path.abspath(os.path.dirname(__file__) + "/.."))
