#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo "AMELAG Dashboard - Terminal Browser Accessibility Test"
echo "=========================================================="

echo -e "\n--- 1. Testing German version with Lynx (UTF-8 Plain Text Dump) ---"
nix shell nixpkgs#lynx --command lynx -display_charset=utf-8 -dump index.html | head -n 60

echo -e "\n--- 2. Testing English version with Lynx (UTF-8 Plain Text Dump) ---"
nix shell nixpkgs#lynx --command lynx -display_charset=utf-8 -dump en.html | head -n 60

echo -e "\n--- 3. Testing with Links (Text Browser Dump) ---"
nix shell nixpkgs#links2 --command links -dump en.html | head -n 60

echo -e "\n✓ All terminal browser tests completed successfully!"
