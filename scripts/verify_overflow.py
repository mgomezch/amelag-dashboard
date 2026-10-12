#!/usr/bin/env python3
"""
verify_overflow.py
Automated Headless Firefox verification of viewport width, horizontal overflow,
and interactivity across mobile viewports (320px, 360px, 375px, 390px, 412px, 768px, 1280px).
"""
import http.server
import json
import os
import socket
import socketserver
import subprocess
import sys
import threading
import time

TEST_PORT = 8849
MARIONETTE_PORT = 2828

def send_msg(sock, msg_id, cmd, params):
    payload = json.dumps([0, msg_id, cmd, params])
    sock.sendall(f"{len(payload)}:{payload}".encode("utf-8"))

def recv_msg(sock):
    raw_len = b""
    while True:
        ch = sock.recv(1)
        if not ch or ch == b":":
            break
        raw_len += ch
    if not raw_len:
        return None
    msg_len = int(raw_len.decode("utf-8"))
    data = b""
    while len(data) < msg_len:
        chunk = sock.recv(msg_len - len(data))
        if not chunk:
            break
        data += chunk
    return json.loads(data.decode("utf-8"))

def run_overflow_tests():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(root_dir)

    # 1. Start HTTP Server
    socketserver.TCPServer.allow_reuse_address = True
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", TEST_PORT), handler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    print(f"HTTP test server started on port {TEST_PORT}")

    firefox_proc = None
    all_passed = True

    try:
        # 2. Launch Firefox with Marionette
        cmd = [
            "firefox",
            "--headless",
            "--marionette",
            "about:blank"
        ]
        firefox_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", MARIONETTE_PORT))
        recv_msg(s) # initial marionette handshake

        msg_id = 1
        send_msg(s, msg_id, "WebDriver:NewSession", {})
        recv_msg(s)

        viewports = [
            ("mobile_320", 320, 568, "index.html"),
            ("mobile_360", 360, 640, "index.html"),
            ("mobile_375", 375, 667, "index.html"),
            ("mobile_390", 390, 844, "index.html"),
            ("mobile_412", 412, 915, "index.html"),
            ("en_mobile_375", 375, 667, "en.html"),
            ("tablet_768", 768, 1024, "index.html"),
            ("desktop_1280", 1280, 800, "index.html"),
        ]

        for name, w, h, page in viewports:
            url = f"http://127.0.0.1:{TEST_PORT}/{page}"
            msg_id += 1
            send_msg(s, msg_id, "WebDriver:SetWindowRect", {"width": w, "height": h})
            recv_msg(s)

            msg_id += 1
            send_msg(s, msg_id, "WebDriver:Navigate", {"url": url})
            recv_msg(s)

            time.sleep(2) # wait for render and data fetch

            msg_id += 1
            script = """
                const docEl = document.documentElement;
                const clientW = docEl.clientWidth;
                const scrollW = docEl.scrollWidth;
                const bodyScrollW = document.body.scrollWidth;

                // Try scrolling window horizontally
                window.scrollTo(100, 0);
                const windowScrollX = window.scrollX || window.pageXOffset || 0;
                window.scrollTo(0, 0);

                // Helper to check if an element is inside an horizontally scrollable container
                function isInsideScrollable(el) {
                    let parent = el.parentElement;
                    while (parent && parent !== document.body && parent !== document.documentElement) {
                        const style = window.getComputedStyle(parent);
                        const overflowX = style.overflowX;
                        if (overflowX === 'auto' || overflowX === 'scroll' || overflowX === 'hidden') {
                            return true;
                        }
                        parent = parent.parentElement;
                    }
                    return false;
                }

                const overflowing = [];
                document.querySelectorAll('*').forEach(el => {
                    if (isInsideScrollable(el)) return;
                    const rect = el.getBoundingClientRect();
                    if (rect.right > clientW + 1.5) {
                        overflowing.push({
                            tag: el.tagName,
                            id: el.id,
                            className: (el.className && typeof el.className === 'string') ? el.className.slice(0, 40) : '',
                            right: Math.round(rect.right),
                            width: Math.round(rect.width)
                        });
                    }
                });

                return {
                    clientWidth: clientW,
                    scrollWidth: scrollW,
                    bodyScrollWidth: bodyScrollW,
                    windowScrollX: windowScrollX,
                    hasHorizontalOverflow: scrollW > clientW || windowScrollX > 0,
                    overflowCount: overflowing.length,
                    overflowingElements: overflowing.slice(0, 5)
                };
            """
            send_msg(s, msg_id, "WebDriver:ExecuteScript", {"script": script})
            res = recv_msg(s)
            val = res[3].get("value", {}) if (len(res) > 3 and isinstance(res[3], dict)) else {}

            cw = val.get("clientWidth")
            sw = val.get("scrollWidth")
            has_ov = val.get("hasHorizontalOverflow")
            ov_count = val.get("overflowCount", 0)
            win_scroll_x = val.get("windowScrollX", 0)

            if has_ov or ov_count > 0:
                all_passed = False
                print(f"[FAIL] {name} ({w}x{h}): clientWidth={cw}, scrollWidth={sw}, windowScrollX={win_scroll_x}, overflowingElements={val.get('overflowingElements')}")
            else:
                print(f"[PASS] {name} ({w}x{h}): clientWidth={cw}, scrollWidth={sw}, windowScrollX={win_scroll_x} (No overflow, page cannot pan!)")

        # 3. Interactive test on mobile_375: toggle log scale, check chart and overflow
        print("\n--- Testing Interactive Controls on Mobile (375x667) ---")
        msg_id += 1
        send_msg(s, msg_id, "WebDriver:SetWindowRect", {"width": 375, "height": 667})
        recv_msg(s)

        msg_id += 1
        test_interaction_script = """
            const logBtn = document.getElementById('btn-scale-log');
            if (logBtn) {
                logBtn.click();
            }
            const docEl = document.documentElement;
            window.scrollTo(100, 0);
            const winScrollX = window.scrollX || 0;
            window.scrollTo(0, 0);

            return {
                logBtnActive: logBtn ? logBtn.classList.contains('active') : false,
                clientWidth: docEl.clientWidth,
                scrollWidth: docEl.scrollWidth,
                windowScrollX: winScrollX,
                hasOverflow: docEl.scrollWidth > docEl.clientWidth || winScrollX > 0
            };
        """
        send_msg(s, msg_id, "WebDriver:ExecuteScript", {"script": test_interaction_script})
        res = recv_msg(s)
        val = res[3].get("value", {}) if (len(res) > 3 and isinstance(res[3], dict)) else {}
        print(f"Log scale button clicked: active={val.get('logBtnActive')}, overflow={val.get('hasOverflow')} (cw={val.get('clientWidth')}, sw={val.get('scrollWidth')}, winScrollX={val.get('windowScrollX')})")
        if not val.get("logBtnActive") or val.get("hasOverflow"):
            all_passed = False

        # Test temporal preset button / dropdown
        print("\n--- Testing Temporal Preset on Mobile ---")
        msg_id += 1
        test_preset_script = """
            const selectPreset = document.getElementById('slicer-preset-select');
            if (selectPreset) {
                selectPreset.value = '90d';
                selectPreset.dispatchEvent(new Event('change', { bubbles: true }));
            }
            const docEl = document.documentElement;
            window.scrollTo(100, 0);
            const winScrollX = window.scrollX || 0;
            window.scrollTo(0, 0);

            return {
                presetVal: selectPreset ? selectPreset.value : null,
                clientWidth: docEl.clientWidth,
                scrollWidth: docEl.scrollWidth,
                windowScrollX: winScrollX,
                hasOverflow: docEl.scrollWidth > docEl.clientWidth || winScrollX > 0
            };
        """
        send_msg(s, msg_id, "WebDriver:ExecuteScript", {"script": test_preset_script})
        res = recv_msg(s)
        val = res[3].get("value", {}) if (len(res) > 3 and isinstance(res[3], dict)) else {}
        print(f"Preset changed to 90d: val={val.get('presetVal')}, overflow={val.get('hasOverflow')} (cw={val.get('clientWidth')}, sw={val.get('scrollWidth')})")
        if val.get("hasOverflow"):
            all_passed = False

    finally:
        print("Cleaning up processes...")
        if firefox_proc:
            try:
                firefox_proc.terminate()
                firefox_proc.wait(timeout=5)
            except Exception:
                try:
                    firefox_proc.kill()
                except Exception:
                    pass
        httpd.shutdown()
        httpd.server_close()

    print(f"\nFinal Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_overflow_tests()
