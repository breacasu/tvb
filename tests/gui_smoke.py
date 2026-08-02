#!/usr/bin/env python3
"""Drive the installed Windows GUI through UI Automation and CDP."""

import argparse
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

import websocket
from pywinauto import Application, Desktop


class DevTools:
    def __init__(self, port):
        self.port = port
        self.message_id = 0
        self.socket = None

    def connect(self):
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json", timeout=2) as response:
                    targets = json.loads(response.read().decode("utf-8"))
                target = next(item for item in targets if item.get("type") == "page")
                self.socket = websocket.create_connection(
                    target["webSocketDebuggerUrl"], timeout=10, http_proxy_host=None
                )
                return
            except Exception:
                time.sleep(0.25)
        raise RuntimeError("Electron DevTools endpoint did not become available")

    def call(self, method, params=None):
        self.message_id += 1
        message_id = self.message_id
        self.socket.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.socket.recv())
            if message.get("id") == message_id:
                return message

    def evaluate(self, expression):
        result = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True,
            },
        )
        if "exceptionDetails" in result.get("result", {}):
            raise RuntimeError(result["result"]["exceptionDetails"])
        return result["result"]["result"].get("value")

    def close(self):
        if self.socket:
            self.socket.close()


def wait_for(predicate, timeout, description):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(0.25)
    raise TimeoutError(f"Timed out waiting for {description}")


def js_string(value):
    return json.dumps(str(value))


def set_text(devtools, index, value):
    expression = f"""
    (() => {{
      const element = document.querySelectorAll('input[type="text"]')[{index}];
      if (!element) return false;
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(element, {js_string(value)});
      element.dispatchEvent(new Event('input', {{ bubbles: true }}));
      element.dispatchEvent(new Event('change', {{ bubbles: true }}));
      return element.value;
    }})()
    """
    if not devtools.evaluate(expression):
        raise RuntimeError(f"Text input {index} was not found")


def click_button(devtools, text):
    expression = f"""
    (() => {{
      const button = [...document.querySelectorAll('button')]
        .find(element => element.textContent.trim() === {js_string(text)});
      if (!button) return false;
      button.click();
      return true;
    }})()
    """
    if not devtools.evaluate(expression):
        raise RuntimeError(f"Button not found: {text}")


def set_options(devtools):
    expression = """
    (() => {
      const select = document.querySelector('select');
      if (!select) return false;
      select.value = 'custom';
      select.dispatchEvent(new Event('change', { bubbles: true }));
      const control = document.querySelector('.transcode-control');
      if (!control) return false;
      const checks = [...control.querySelectorAll('input[type="checkbox"]')];
      if (checks.length < 3) return false;
      if (!checks[0].checked) checks[0].click();
      if (!checks[1].checked) checks[1].click();
      if (checks[2].checked) checks[2].click();
      return checks.map(element => element.checked);
    })()
    """
    result = devtools.evaluate(expression)
    time.sleep(0.5)
    format_value = devtools.evaluate("document.querySelector('select')?.value")
    if result != [True, True, False] or format_value != "custom":
        raise RuntimeError(f"Unexpected GUI options: {result}")


def open_section(devtools, title):
    expression = f"""
    (() => {{
      const header = [...document.querySelectorAll('.collapsible-header')]
        .find(element => element.textContent.trim().endsWith({js_string(title)}));
      if (!header) return false;
      const section = header.parentElement;
      if (section.classList.contains('closed')) header.click();
      return true;
    }})()
    """
    if not devtools.evaluate(expression):
        raise RuntimeError(f"Section not found: {title}")


def collect_subtitle_inputs(root):
    video_extensions = {".mkv", ".mp4", ".m4v", ".mov", ".avi", ".wmv", ".flv"}
    ffprobe = Path(__file__).resolve().parent.parent / "bin" / "ffprobe.exe"
    candidates = []
    seen_names = set()

    for input_file in sorted(root.rglob("*")):
        relative = input_file.relative_to(root)
        if input_file.suffix.lower() not in video_extensions:
            continue
        if "output" in relative.parts:
            continue
        if "tvb_test" in relative.parts and input_file.name in seen_names:
            continue

        result = subprocess.run(
            [
                str(ffprobe),
                "-v", "error",
                "-show_entries", "stream=codec_type,codec_name",
                "-of", "json",
                str(input_file),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            continue
        streams = json.loads(result.stdout).get("streams", [])
        subtitles = [
            stream.get("codec_name")
            for stream in streams
            if stream.get("codec_type") == "subtitle"
        ]
        if subtitles:
            candidates.append((input_file, subtitles))
            seen_names.add(input_file.name)

    return candidates


def verify_subtitle_output(input_file, subtitles, output_file):
    ffprobe = Path(__file__).resolve().parent.parent / "bin" / "ffprobe.exe"
    if not output_file.is_file():
        raise RuntimeError(f"Output file was not created: {output_file}")
    result = subprocess.run(
        [
            str(ffprobe),
            "-v", "error",
            "-show_entries", "stream=codec_type,codec_name",
            "-of", "json",
            str(output_file),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe rejected output: {output_file}\n{result.stderr}")
    streams = json.loads(result.stdout).get("streams", [])
    output_subtitles = [
        stream.get("codec_name")
        for stream in streams
        if stream.get("codec_type") == "subtitle"
    ]
    if not output_subtitles:
        raise RuntimeError(f"No subtitles in output: {output_file}")
    if "hdmv_pgs_subtitle" in subtitles and "hdmv_pgs_subtitle" not in output_subtitles:
        raise RuntimeError(f"PGS subtitles were lost: {output_file}")


def run_matrix_case(devtools, input_file, subtitles, output_dir, index):
    set_text(devtools, 0, input_file)
    set_text(devtools, 1, output_dir)
    time.sleep(0.5)
    set_options(devtools)
    click_button(devtools, "Start Transcoding")
    wait_for(
        lambda: "Stop" in (devtools.evaluate("document.body.innerText") or ""),
        30,
        f"matrix job {index} start",
    )
    wait_for(
        lambda: "Start Transcoding" in (devtools.evaluate("document.body.innerText") or "")
        and "Stop" not in (devtools.evaluate("document.body.innerText") or ""),
        900,
        f"matrix job {index} completion",
    )
    body = devtools.evaluate("document.body.innerText") or ""
    if "Transcode failed" in body or "Encoding failed" in body:
        raise RuntimeError(f"Matrix input failed: {input_file}\n{body[-3000:]}")
    verify_subtitle_output(input_file, subtitles, Path(output_dir) / input_file.name)
    print(f"[{index}] OK {input_file}")


def run_case(devtools, input_file, output_dir, label):
    set_text(devtools, 0, input_file)
    set_text(devtools, 1, output_dir)
    time.sleep(0.5)
    set_options(devtools)
    click_button(devtools, "Start Transcoding")

    wait_for(
        lambda: "Stop" in (devtools.evaluate("document.body.innerText") or ""),
        30,
        f"{label} job start",
    )
    wait_for(
        lambda: "Start Transcoding" in (devtools.evaluate("document.body.innerText") or "")
        and "Stop" not in (devtools.evaluate("document.body.innerText") or ""),
        900,
        f"{label} job completion",
    )

    body = devtools.evaluate("document.body.innerText") or ""
    if "Transcode failed" in body or "Encoding failed" in body:
        raise RuntimeError(f"{label} reported an encoding error:\n{body[-3000:]}")

    open_section(devtools, "Stats")
    wait_for(
        lambda: label in (devtools.evaluate("document.body.innerText") or ""),
        15,
        f"{label} statistics",
    )
    open_section(devtools, "Log")
    open_section(devtools, "Config")
    click_button(devtools, "Save Config")
    return devtools.evaluate("document.body.innerText") or ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui", type=Path, required=True)
    parser.add_argument("--atmos", type=Path, required=False)
    parser.add_argument("--pgs", type=Path, required=False)
    parser.add_argument("--subtitle-root", type=Path, required=False)
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--port", type=int, default=9223)
    args = parser.parse_args()

    args.output_root.mkdir(parents=True, exist_ok=True)
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    os.environ["no_proxy"] = "127.0.0.1,localhost"

    process = subprocess.Popen(
        [str(args.gui), f"--remote-debugging-port={args.port}", "--remote-allow-origins=*"]
    )
    app = Application(backend="uia").connect(process=process.pid)
    devtools = DevTools(args.port)
    try:
        wait_for(
            lambda: any(
                window.window_text() == "TVB - Transcode Video Batch"
                for window in Desktop(backend="uia").windows(visible_only=True)
            ),
            30,
            "tvb GUI window",
        )
        devtools.connect()
        wait_for(
            lambda: "Start Transcoding" in (devtools.evaluate("document.body.innerText") or ""),
            30,
            "tvb GUI content",
        )

        if args.subtitle_root:
            matrix = collect_subtitle_inputs(args.subtitle_root)
            print(f"subtitle_matrix_inputs={len(matrix)}")
            for index, (input_file, subtitles) in enumerate(matrix, 1):
                if index < args.start_index:
                    continue
                output_dir = args.output_root / f"{index:02d}"
                run_matrix_case(devtools, input_file, subtitles, output_dir, index)
            open_section(devtools, "Stats")
            open_section(devtools, "Log")
            open_section(devtools, "Config")
            click_button(devtools, "Save Config")
        else:
            if not args.atmos or not args.pgs:
                raise RuntimeError("--atmos and --pgs are required without --subtitle-root")
            atmos_output = args.output_root / "atmos"
            pgs_output = args.output_root / "pgs"
            run_case(devtools, args.atmos, atmos_output, args.atmos.name)
            run_case(devtools, args.pgs, pgs_output, args.pgs.name)
        print("GUI smoke test passed")
    finally:
        devtools.close()
        try:
            app.kill()
        except Exception:
            process.terminate()


if __name__ == "__main__":
    main()
