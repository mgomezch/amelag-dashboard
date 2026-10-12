#!/usr/bin/env python3
"""
test_tooltip.py
Automated Headless Firefox verification of tooltip boundary clamping and visibility
at left edge, right edge, and center across mobile viewports.
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

TEST_PORT = 8852
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

def run_tooltip_tests():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(root_dir)

    socketserver.TCPServer.allow_reuse_address = True
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", TEST_PORT), handler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    print(f"HTTP test server started on port {TEST_PORT}")

    firefox_proc = None
    all_passed = True

    try:
        cmd = ["firefox", "--headless", "--marionette", "about:blank"]
        firefox_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", MARIONETTE_PORT))
        recv_msg(s)

        msg_id = 1
        send_msg(s, msg_id, "WebDriver:NewSession", {})
        recv_msg(s)

        # Test on mobile viewports: 320px (iPhone SE 1st gen), 375px (standard), 412px (Android)
        viewports = [
            ("mobile_320", 320, 568),
            ("mobile_375", 375, 667),
            ("mobile_412", 412, 915),
        ]

        for name, w, h in viewports:
            msg_id += 1
            send_msg(s, msg_id, "WebDriver:SetWindowRect", {"width": w, "height": h})
            recv_msg(s)

            msg_id += 1
            url = f"http://127.0.0.1:{TEST_PORT}/index.html"
            send_msg(s, msg_id, "WebDriver:Navigate", {"url": url})
            recv_msg(s)

            time.sleep(2.5) # Wait for chart data to render

            # Test interactions at:
            # 1) Far right edge of plot (triggering closest point at latest date)
            # 2) Far left edge of plot (triggering earliest date)
            # 3) Center
            test_positions = [
                ("right_edge", 0.96, 0.5),
                ("left_edge", 0.12, 0.5),
                ("center", 0.5, 0.3),
            ]

            for pos_name, frac_x, frac_y in test_positions:
                msg_id += 1
                script = f"""
                    const svg = document.querySelector('.amelag-chart-svg');
                    const vp = document.getElementById('chart-viewport');
                    const tooltip = document.getElementById('chart-tooltip');

                    if (!svg || !vp || !tooltip) {{
                        return {{ error: 'Elements not found' }};
                    }}

                    const rect = svg.getBoundingClientRect();
                    const targetClientX = rect.left + rect.width * {frac_x};
                    const targetClientY = rect.top + rect.height * {frac_y};

                    // Trigger click event on svg at the target position
                    const clickEvt = new MouseEvent('click', {{
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        clientX: targetClientX,
                        clientY: targetClientY
                    }});
                    svg.dispatchEvent(clickEvt);

                    const vpRect = vp.getBoundingClientRect();
                    const tipRect = tooltip.getBoundingClientRect();

                    const isVisible = tooltip.classList.contains('visible');
                    const leftInside = tipRect.left >= vpRect.left - 1;
                    const rightInside = tipRect.right <= vpRect.right + 1;
                    const topInside = tipRect.top >= vpRect.top - 1;
                    const bottomInside = tipRect.bottom <= vpRect.bottom + 1;

                    return {{
                        isVisible,
                        leftInside,
                        rightInside,
                        topInside,
                        bottomInside,
                        tipWidth: Math.round(tipRect.width),
                        tipHeight: Math.round(tipRect.height),
                        vpWidth: Math.round(vpRect.width),
                        tipLeft: Math.round(tipRect.left - vpRect.left),
                        tipRight: Math.round(tipRect.right - vpRect.left),
                        tooltipText: tooltip.innerText.replace(/\\n/g, ' | ')
                    }};
                """
                send_msg(s, msg_id, "WebDriver:ExecuteScript", {"script": script})
                res = recv_msg(s)
                val = res[3].get("value", {}) if (len(res) > 3 and isinstance(res[3], dict)) else {}

                is_ok = (
                    val.get("isVisible") and
                    val.get("leftInside") and
                    val.get("rightInside") and
                    val.get("topInside") and
                    val.get("bottomInside")
                )

                if is_ok:
                    print(f"[PASS] {name} at {pos_name}: Tooltip fully contained! Left={val.get('tipLeft')}, Right={val.get('tipRight')}, VpW={val.get('vpWidth')}")
                    print(f"       Content: {val.get('tooltipText')}")
                else:
                    all_passed = False
                    print(f"[FAIL] {name} at {pos_name}: {val}")

    finally:
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

    print(f"\nFinal Result: {'ALL TOOLTIP TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_tooltip_tests()
