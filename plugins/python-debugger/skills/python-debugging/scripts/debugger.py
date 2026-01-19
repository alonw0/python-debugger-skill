#!/usr/bin/env python3
"""
Claude Code Python Debugger

A PyCharm-like debugging experience for Claude Code with breakpoints,
stepping, variable inspection, and stack navigation.

Architecture:
- Uses bdb.Bdb for Python debugging
- Persistent subprocess with Unix socket for IPC
- Session state stored in ~/.claude_debugger/
"""

import argparse
import bdb
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Session directory
SESSION_DIR = Path.home() / ".claude_debugger"
SOCKET_TIMEOUT = 30.0
EVAL_TIMEOUT = 5
MAX_VALUE_LENGTH = 1000
MAX_COLLECTION_ITEMS = 50
MAX_STACK_DEPTH = 50


# =============================================================================
# JSON Formatting Utilities
# =============================================================================

def truncate_value(value: str, max_length: int = MAX_VALUE_LENGTH) -> str:
    """Truncate a string value if it exceeds max length."""
    if len(value) > max_length:
        return value[:max_length - 3] + "..."
    return value


def format_value(obj: Any, max_depth: int = 2, current_depth: int = 0,
                 seen: Optional[set] = None) -> Dict[str, Any]:
    """Format a Python object as a JSON-serializable dict with type info."""
    if seen is None:
        seen = set()

    obj_id = id(obj)
    type_name = type(obj).__name__

    # Handle circular references
    if obj_id in seen and current_depth > 0:
        return {"type": type_name, "value": "<circular reference>"}

    # Basic types
    if obj is None:
        return {"type": "NoneType", "value": "None"}

    if isinstance(obj, bool):
        return {"type": "bool", "value": str(obj)}

    if isinstance(obj, (int, float)):
        return {"type": type_name, "value": str(obj)}

    if isinstance(obj, str):
        return {"type": "str", "value": truncate_value(repr(obj))}

    if isinstance(obj, bytes):
        return {"type": "bytes", "value": truncate_value(repr(obj))}

    # Track this object to detect circular refs
    seen.add(obj_id)

    try:
        # Collections - limit items
        if isinstance(obj, (list, tuple)):
            if current_depth >= max_depth:
                return {"type": type_name, "value": f"<{type_name} with {len(obj)} items>"}

            items = []
            for i, item in enumerate(obj):
                if i >= MAX_COLLECTION_ITEMS:
                    items.append({"type": "...", "value": f"... ({len(obj) - i} more items)"})
                    break
                items.append(format_value(item, max_depth, current_depth + 1, seen.copy()))

            return {
                "type": type_name,
                "value": f"<{type_name} with {len(obj)} items>",
                "items": items
            }

        if isinstance(obj, dict):
            if current_depth >= max_depth:
                return {"type": "dict", "value": f"<dict with {len(obj)} keys>"}

            items = {}
            for i, (k, v) in enumerate(obj.items()):
                if i >= MAX_COLLECTION_ITEMS:
                    items["..."] = {"type": "...", "value": f"... ({len(obj) - i} more keys)"}
                    break
                key_str = truncate_value(str(k), 100)
                items[key_str] = format_value(v, max_depth, current_depth + 1, seen.copy())

            return {
                "type": "dict",
                "value": f"<dict with {len(obj)} keys>",
                "items": items
            }

        if isinstance(obj, set):
            if current_depth >= max_depth:
                return {"type": "set", "value": f"<set with {len(obj)} items>"}

            items = []
            for i, item in enumerate(obj):
                if i >= MAX_COLLECTION_ITEMS:
                    items.append({"type": "...", "value": f"... ({len(obj) - i} more items)"})
                    break
                items.append(format_value(item, max_depth, current_depth + 1, seen.copy()))

            return {
                "type": "set",
                "value": f"<set with {len(obj)} items>",
                "items": items
            }

        # Try to get a reasonable string representation
        try:
            value_str = repr(obj)
        except Exception:
            value_str = f"<{type_name} object>"

        return {"type": type_name, "value": truncate_value(value_str)}

    finally:
        seen.discard(obj_id)


def format_variables(variables: Dict[str, Any], max_depth: int = 2) -> Dict[str, Dict]:
    """Format a dictionary of variables."""
    result = {}
    for name, value in variables.items():
        if name.startswith("__") and name.endswith("__"):
            continue  # Skip dunder variables
        result[name] = format_value(value, max_depth)
    return result


# =============================================================================
# Session Management
# =============================================================================

class SessionManager:
    """Manages debugger session state files."""

    def __init__(self, script_path: str):
        self.script_path = os.path.abspath(script_path)
        self.session_id = self._generate_session_id()
        self.session_file = SESSION_DIR / f"{self.session_id}.json"
        self.socket_path = SESSION_DIR / f"{self.session_id}.sock"

    def _generate_session_id(self) -> str:
        """Generate a unique session ID based on script path."""
        import hashlib
        # Use hash of absolute path for uniqueness
        path_hash = hashlib.md5(self.script_path.encode()).hexdigest()[:8]
        return f"debug_{path_hash}"

    def create_session(self, pid: int) -> None:
        """Create a new session state file."""
        SESSION_DIR.mkdir(parents=True, exist_ok=True)

        session_data = {
            "script": self.script_path,
            "pid": pid,
            "socket": str(self.socket_path),
            "created": time.time(),
            "status": "starting"
        }

        with open(self.session_file, "w") as f:
            json.dump(session_data, f, indent=2)

    def update_session(self, **updates) -> None:
        """Update session state."""
        if self.session_file.exists():
            try:
                with open(self.session_file, "r") as f:
                    data = json.load(f)
                data.update(updates)
                with open(self.session_file, "w") as f:
                    json.dump(data, f, indent=2)
            except (json.JSONDecodeError, IOError):
                # File might be empty or corrupted, create new
                with open(self.session_file, "w") as f:
                    json.dump(updates, f, indent=2)

    def get_session(self) -> Optional[Dict]:
        """Get current session data."""
        if self.session_file.exists():
            try:
                with open(self.session_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def delete_session(self) -> None:
        """Clean up session files."""
        if self.session_file.exists():
            self.session_file.unlink()
        if self.socket_path.exists():
            self.socket_path.unlink()

    @classmethod
    def find_active_session(cls, script_path: str) -> Optional["SessionManager"]:
        """Find an active session for a script."""
        manager = cls(script_path)
        session = manager.get_session()

        if session and cls._is_process_alive(session.get("pid")):
            return manager

        # Clean up stale session
        if session:
            manager.delete_session()

        return None

    @classmethod
    def get_all_sessions(cls) -> List[Dict]:
        """Get all active sessions."""
        sessions = []
        if SESSION_DIR.exists():
            for session_file in SESSION_DIR.glob("debug_*.json"):
                try:
                    with open(session_file, "r") as f:
                        data = json.load(f)
                    if cls._is_process_alive(data.get("pid")):
                        data["session_file"] = str(session_file)
                        sessions.append(data)
                    else:
                        # Clean up stale session
                        session_file.unlink()
                        socket_file = session_file.with_suffix(".sock")
                        if socket_file.exists():
                            socket_file.unlink()
                except (json.JSONDecodeError, IOError):
                    pass
        return sessions

    @staticmethod
    def _is_process_alive(pid: Optional[int]) -> bool:
        """Check if a process is still running."""
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


# =============================================================================
# Socket IPC
# =============================================================================

class DebuggerServer:
    """Unix socket server for the debugger subprocess."""

    def __init__(self, socket_path: Path):
        self.socket_path = socket_path
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.running = False

    def start(self) -> None:
        """Start the socket server."""
        # Remove existing socket file
        if self.socket_path.exists():
            self.socket_path.unlink()

        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(str(self.socket_path))
        self.server_socket.listen(1)
        self.server_socket.settimeout(1.0)  # Allow periodic checks
        self.running = True

    def accept_client(self) -> bool:
        """Accept a client connection (non-blocking with timeout)."""
        try:
            self.client_socket, _ = self.server_socket.accept()
            self.client_socket.settimeout(SOCKET_TIMEOUT)
            return True
        except socket.timeout:
            return False

    def receive_command(self) -> Optional[Dict]:
        """Receive a command from the client."""
        if not self.client_socket:
            return None

        try:
            # Read length prefix (4 bytes)
            length_data = self._recv_exact(4)
            if not length_data:
                # Client disconnected cleanly
                self._close_client()
                return None

            length = int.from_bytes(length_data, "big")

            # Read command data
            data = self._recv_exact(length)
            if not data:
                # Client disconnected during read
                self._close_client()
                return None

            return json.loads(data.decode("utf-8"))

        except (socket.timeout, ConnectionResetError, BrokenPipeError):
            self._close_client()
            return None

    def _close_client(self) -> None:
        """Close the client connection."""
        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception:
                pass
            self.client_socket = None

    def send_response(self, response: Dict) -> bool:
        """Send a response to the client."""
        if not self.client_socket:
            return False

        try:
            data = json.dumps(response).encode("utf-8")
            length = len(data).to_bytes(4, "big")
            self.client_socket.sendall(length + data)
            return True
        except (BrokenPipeError, ConnectionResetError):
            self._close_client()
            return False

    def _recv_exact(self, n: int) -> Optional[bytes]:
        """Receive exactly n bytes."""
        data = b""
        while len(data) < n:
            chunk = self.client_socket.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def close(self) -> None:
        """Close the server."""
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception:
                pass
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        if self.socket_path.exists():
            try:
                self.socket_path.unlink()
            except Exception:
                pass


class DebuggerClient:
    """Unix socket client for sending commands to the debugger."""

    def __init__(self, socket_path: Path):
        self.socket_path = socket_path
        self.socket: Optional[socket.socket] = None

    def connect(self, timeout: float = 5.0) -> bool:
        """Connect to the debugger server."""
        start = time.time()
        while time.time() - start < timeout:
            if self.socket_path.exists():
                try:
                    self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    self.socket.settimeout(SOCKET_TIMEOUT)
                    self.socket.connect(str(self.socket_path))
                    return True
                except (ConnectionRefusedError, FileNotFoundError):
                    self.socket = None
            time.sleep(0.1)
        return False

    def send_command(self, command: Dict) -> Optional[Dict]:
        """Send a command and receive the response."""
        if not self.socket:
            return None

        try:
            # Send command
            data = json.dumps(command).encode("utf-8")
            length = len(data).to_bytes(4, "big")
            self.socket.sendall(length + data)

            # Receive response
            length_data = self._recv_exact(4)
            if not length_data:
                return None

            length = int.from_bytes(length_data, "big")
            response_data = self._recv_exact(length)
            if not response_data:
                return None

            return json.loads(response_data.decode("utf-8"))

        except (socket.timeout, ConnectionResetError, BrokenPipeError) as e:
            return {"error": f"Connection error: {e}"}

    def _recv_exact(self, n: int) -> Optional[bytes]:
        """Receive exactly n bytes."""
        data = b""
        while len(data) < n:
            chunk = self.socket.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def close(self) -> None:
        """Close the connection."""
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass


# =============================================================================
# Claude Debugger (bdb.Bdb Extension)
# =============================================================================

class ClaudeDebugger(bdb.Bdb):
    """Custom debugger extending bdb.Bdb for Claude Code integration."""

    def __init__(self, session_manager: SessionManager):
        super().__init__()
        self.session_manager = session_manager
        self.server = DebuggerServer(session_manager.socket_path)

        # Current state
        self.current_frame: Optional[Any] = None
        self.current_frame_index: int = 0  # For up/down navigation
        self.stack_frames: List[Tuple[Any, int]] = []
        self.stop_reason: str = "starting"
        self.exception_info: Optional[Tuple] = None

        # Exception breakpoints
        self.break_on_exception: bool = False
        self.exception_types: List[str] = []

        # For graceful shutdown
        self.should_quit = False

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle termination signals."""
        self.should_quit = True
        self.server.close()
        self.session_manager.delete_session()
        sys.exit(0)

    def run_script(self, script_path: str, args: List[str]) -> None:
        """Run a Python script under the debugger."""
        # Prepare the script's environment
        script_path = os.path.abspath(script_path)
        script_dir = os.path.dirname(script_path)

        # Set up sys.argv
        sys.argv = [script_path] + args

        # Add script directory to path
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        # Change to script directory
        os.chdir(script_dir)

        # Start socket server
        self.server.start()
        self.session_manager.update_session(status="running")

        # Read and compile the script
        with open(script_path, "r") as f:
            code = f.read()

        compiled = compile(code, script_path, "exec")

        # Create globals for the script
        script_globals = {
            "__name__": "__main__",
            "__file__": script_path,
            "__builtins__": __builtins__,
        }

        # Run the script under debugger control
        try:
            self.run(compiled, script_globals, script_globals)
        except bdb.BdbQuit:
            pass
        except Exception as e:
            self._handle_uncaught_exception(e)
        finally:
            self._cleanup()

    def _handle_uncaught_exception(self, exc: Exception) -> None:
        """Handle uncaught exceptions from the debugged script."""
        self.stop_reason = "exception"
        self.exception_info = (type(exc).__name__, str(exc), traceback.format_exc())

        # Get the frame where the exception occurred
        tb = sys.exc_info()[2]
        if tb:
            while tb.tb_next:
                tb = tb.tb_next
            self.current_frame = tb.tb_frame
            self._build_stack()

        # Enter command loop to allow inspection
        self._handle_stop()

    def _cleanup(self) -> None:
        """Clean up resources."""
        self.server.close()
        self.session_manager.update_session(status="terminated")

    # -------------------------------------------------------------------------
    # bdb.Bdb Overrides
    # -------------------------------------------------------------------------

    def user_line(self, frame) -> None:
        """Called when debugger stops at a line."""
        self.current_frame = frame
        self.current_frame_index = 0
        self._build_stack()
        self.stop_reason = "line"
        self._handle_stop()

    def user_call(self, frame, args) -> None:
        """Called when entering a function."""
        # We typically don't stop on calls, but update state
        pass

    def user_return(self, frame, return_value) -> None:
        """Called when returning from a function."""
        if self.stop_here(frame):
            self.current_frame = frame
            self.current_frame_index = 0
            self._build_stack()
            self.stop_reason = "return"
            self._handle_stop()

    def user_exception(self, frame, exc_info) -> None:
        """Called when an exception is raised."""
        exc_type, exc_value, exc_tb = exc_info
        exc_type_name = exc_type.__name__ if exc_type else "Unknown"

        # Check if we should break on this exception
        should_break = False
        if self.break_on_exception:
            if not self.exception_types:  # Break on all exceptions
                should_break = True
            elif exc_type_name in self.exception_types:
                should_break = True

        if should_break:
            self.current_frame = frame
            self.current_frame_index = 0
            self._build_stack()
            self.stop_reason = "exception"
            self.exception_info = (exc_type_name, str(exc_value),
                                   "".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
            self._handle_stop()

    def _build_stack(self) -> None:
        """Build the stack frame list."""
        self.stack_frames = []
        frame = self.current_frame
        while frame is not None:
            self.stack_frames.append((frame, frame.f_lineno))
            frame = frame.f_back
            if len(self.stack_frames) > MAX_STACK_DEPTH:
                break
        # Stack is ordered from current (index 0) to oldest

    # -------------------------------------------------------------------------
    # Command Loop
    # -------------------------------------------------------------------------

    def _handle_stop(self) -> None:
        """Handle a debugger stop - wait for and process commands."""
        while not self.should_quit:
            # Wait for client connection
            while not self.server.client_socket and not self.should_quit:
                self.server.accept_client()

            if self.should_quit:
                break

            # Receive command
            command = self.server.receive_command()
            if not command:
                continue

            # Process command
            cmd_name = command.get("command", "")
            response = self._process_command(cmd_name, command)

            # Send response
            self.server.send_response(response)

            # Check if we should continue execution
            if response.get("_continue", False):
                break

    def _process_command(self, cmd_name: str, command: Dict) -> Dict:
        """Process a debugger command and return response."""
        handlers = {
            "status": self._cmd_status,
            "continue": self._cmd_continue,
            "step": self._cmd_step,
            "next": self._cmd_next,
            "finish": self._cmd_finish,
            "break": self._cmd_break,
            "delete": self._cmd_delete,
            "breakpoints": self._cmd_breakpoints,
            "locals": self._cmd_locals,
            "globals": self._cmd_globals,
            "eval": self._cmd_eval,
            "inspect": self._cmd_inspect,
            "stack": self._cmd_stack,
            "up": self._cmd_up,
            "down": self._cmd_down,
            "quit": self._cmd_quit,
        }

        handler = handlers.get(cmd_name)
        if handler:
            try:
                return handler(command)
            except Exception as e:
                return {"error": f"Command error: {e}", "traceback": traceback.format_exc()}
        else:
            return {"error": f"Unknown command: {cmd_name}"}

    # -------------------------------------------------------------------------
    # Command Handlers
    # -------------------------------------------------------------------------

    def _get_status_response(self) -> Dict:
        """Build the standard status response."""
        frame = self._get_current_frame()

        response = {
            "status": "paused",
            "stop_reason": self.stop_reason,
            "location": self._get_location(frame),
            "variables": {
                "locals": format_variables(frame.f_locals if frame else {}, max_depth=1)
            }
        }

        if self.exception_info:
            response["exception"] = {
                "type": self.exception_info[0],
                "message": self.exception_info[1],
                "traceback": self.exception_info[2]
            }

        return response

    def _get_location(self, frame) -> Dict:
        """Get location info for a frame."""
        if not frame:
            return {}

        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        funcname = frame.f_code.co_name

        # Try to get source line
        code_line = ""
        try:
            import linecache
            code_line = linecache.getline(filename, lineno).rstrip()
        except Exception:
            pass

        return {
            "file": filename,
            "line": lineno,
            "function": funcname,
            "code": code_line
        }

    def _get_current_frame(self):
        """Get the currently selected frame (considering up/down navigation)."""
        if self.current_frame_index < len(self.stack_frames):
            return self.stack_frames[self.current_frame_index][0]
        return self.current_frame

    def _cmd_status(self, command: Dict) -> Dict:
        """Return current debugger status."""
        return self._get_status_response()

    def _cmd_continue(self, command: Dict) -> Dict:
        """Continue execution until next breakpoint."""
        self.set_continue()
        self.exception_info = None
        return {"status": "running", "_continue": True}

    def _cmd_step(self, command: Dict) -> Dict:
        """Step into the next line."""
        self.set_step()
        self.exception_info = None
        return {"status": "stepping", "_continue": True}

    def _cmd_next(self, command: Dict) -> Dict:
        """Step over to the next line."""
        self.set_next(self.current_frame)
        self.exception_info = None
        return {"status": "stepping", "_continue": True}

    def _cmd_finish(self, command: Dict) -> Dict:
        """Run until the current function returns."""
        self.set_return(self.current_frame)
        self.exception_info = None
        return {"status": "running", "_continue": True}

    def _cmd_break(self, command: Dict) -> Dict:
        """Set a breakpoint."""
        filename = command.get("file")
        lineno = command.get("line")
        condition = command.get("condition")
        exception_type = command.get("exception")

        if exception_type:
            # Exception breakpoint
            self.break_on_exception = True
            if exception_type != "*":
                if exception_type not in self.exception_types:
                    self.exception_types.append(exception_type)
            return {
                "status": "ok",
                "message": f"Exception breakpoint set for {exception_type}"
            }

        if not filename or not lineno:
            return {"error": "Missing file or line number"}

        # Resolve filename to absolute path
        filename = os.path.abspath(filename)

        # Set breakpoint
        bp = self.set_break(filename, lineno)
        if bp:
            return {"error": str(bp)}

        # Set condition if provided
        if condition:
            # Find the breakpoint and set condition
            for bp_obj in bdb.Breakpoint.bpbynumber:
                if bp_obj and bp_obj.file == filename and bp_obj.line == lineno:
                    bp_obj.cond = condition
                    break

        return {
            "status": "ok",
            "message": f"Breakpoint set at {filename}:{lineno}" +
                      (f" with condition: {condition}" if condition else "")
        }

    def _cmd_delete(self, command: Dict) -> Dict:
        """Delete a breakpoint."""
        filename = command.get("file")
        lineno = command.get("line")
        bp_number = command.get("number")
        exception_type = command.get("exception")

        if exception_type:
            if exception_type == "*":
                self.break_on_exception = False
                self.exception_types.clear()
                return {"status": "ok", "message": "All exception breakpoints cleared"}
            elif exception_type in self.exception_types:
                self.exception_types.remove(exception_type)
                if not self.exception_types:
                    self.break_on_exception = False
                return {"status": "ok", "message": f"Exception breakpoint for {exception_type} removed"}
            else:
                return {"error": f"No exception breakpoint for {exception_type}"}

        if bp_number:
            err = self.clear_bpbynumber(bp_number)
            if err:
                return {"error": str(err)}
            return {"status": "ok", "message": f"Breakpoint {bp_number} deleted"}

        if filename and lineno:
            filename = os.path.abspath(filename)
            self.clear_break(filename, lineno)
            return {"status": "ok", "message": f"Breakpoint at {filename}:{lineno} deleted"}

        return {"error": "Must specify file/line or breakpoint number"}

    def _cmd_breakpoints(self, command: Dict) -> Dict:
        """List all breakpoints."""
        breakpoints = []

        for bp in bdb.Breakpoint.bpbynumber:
            if bp:
                breakpoints.append({
                    "number": bp.number,
                    "file": bp.file,
                    "line": bp.line,
                    "enabled": bp.enabled,
                    "condition": bp.cond,
                    "hits": bp.hits
                })

        exception_breakpoints = []
        if self.break_on_exception:
            if self.exception_types:
                exception_breakpoints = self.exception_types.copy()
            else:
                exception_breakpoints = ["*"]

        return {
            "status": "ok",
            "breakpoints": breakpoints,
            "exception_breakpoints": exception_breakpoints
        }

    def _cmd_locals(self, command: Dict) -> Dict:
        """Get local variables."""
        frame = self._get_current_frame()
        if not frame:
            return {"error": "No frame available"}

        max_depth = command.get("depth", 2)
        return {
            "status": "ok",
            "locals": format_variables(frame.f_locals, max_depth)
        }

    def _cmd_globals(self, command: Dict) -> Dict:
        """Get global variables."""
        frame = self._get_current_frame()
        if not frame:
            return {"error": "No frame available"}

        max_depth = command.get("depth", 2)
        return {
            "status": "ok",
            "globals": format_variables(frame.f_globals, max_depth)
        }

    def _cmd_eval(self, command: Dict) -> Dict:
        """Evaluate an expression."""
        expr = command.get("expression")
        if not expr:
            return {"error": "No expression provided"}

        frame = self._get_current_frame()
        if not frame:
            return {"error": "No frame available"}

        # Set up timeout
        def timeout_handler(signum, frame):
            raise TimeoutError("Expression evaluation timed out")

        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(EVAL_TIMEOUT)

        try:
            # Try eval first (expressions)
            try:
                result = eval(expr, frame.f_globals, frame.f_locals)
            except SyntaxError:
                # Try exec for statements
                exec(expr, frame.f_globals, frame.f_locals)
                result = None

            signal.alarm(0)

            return {
                "status": "ok",
                "expression": expr,
                "result": format_value(result, max_depth=3)
            }

        except TimeoutError:
            return {"error": "Expression evaluation timed out (5s limit)"}
        except Exception as e:
            signal.alarm(0)
            return {
                "error": f"{type(e).__name__}: {e}",
                "expression": expr
            }
        finally:
            signal.signal(signal.SIGALRM, old_handler)

    def _cmd_inspect(self, command: Dict) -> Dict:
        """Deep inspect a variable or expression."""
        expr = command.get("expression")
        if not expr:
            return {"error": "No expression provided"}

        frame = self._get_current_frame()
        if not frame:
            return {"error": "No frame available"}

        try:
            # First check locals, then globals
            if expr in frame.f_locals:
                obj = frame.f_locals[expr]
            elif expr in frame.f_globals:
                obj = frame.f_globals[expr]
            else:
                # Try to evaluate as expression
                obj = eval(expr, frame.f_globals, frame.f_locals)

            # Deep inspection
            max_depth = command.get("depth", 4)
            result = format_value(obj, max_depth=max_depth)

            # Add type-specific information
            type_info = {
                "type": type(obj).__name__,
                "module": type(obj).__module__,
            }

            # Add attributes for objects
            if hasattr(obj, "__dict__"):
                attrs = {}
                for name in dir(obj):
                    if not name.startswith("_"):
                        try:
                            val = getattr(obj, name)
                            if not callable(val):
                                attrs[name] = format_value(val, max_depth=1)
                        except Exception:
                            pass
                if attrs:
                    result["attributes"] = attrs

            # Add length for sequences
            if hasattr(obj, "__len__"):
                try:
                    type_info["length"] = len(obj)
                except Exception:
                    pass

            result["type_info"] = type_info
            return {"status": "ok", "inspection": result}

        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"}

    def _cmd_stack(self, command: Dict) -> Dict:
        """Get the call stack."""
        stack = []
        for i, (frame, lineno) in enumerate(self.stack_frames):
            stack.append({
                "index": i,
                "file": frame.f_code.co_filename,
                "line": lineno,
                "function": frame.f_code.co_name,
                "current": i == self.current_frame_index
            })

        return {"status": "ok", "stack": stack, "current_index": self.current_frame_index}

    def _cmd_up(self, command: Dict) -> Dict:
        """Move up the call stack."""
        if self.current_frame_index < len(self.stack_frames) - 1:
            self.current_frame_index += 1
            frame = self._get_current_frame()
            return {
                "status": "ok",
                "message": f"Moved to frame {self.current_frame_index}",
                "location": self._get_location(frame)
            }
        else:
            return {"error": "Already at oldest frame"}

    def _cmd_down(self, command: Dict) -> Dict:
        """Move down the call stack."""
        if self.current_frame_index > 0:
            self.current_frame_index -= 1
            frame = self._get_current_frame()
            return {
                "status": "ok",
                "message": f"Moved to frame {self.current_frame_index}",
                "location": self._get_location(frame)
            }
        else:
            return {"error": "Already at newest frame"}

    def _cmd_quit(self, command: Dict) -> Dict:
        """Quit the debugger."""
        self.should_quit = True
        self.set_quit()
        return {"status": "terminated", "_continue": True}


# =============================================================================
# CLI Interface
# =============================================================================

def send_command(session: SessionManager, command: Dict) -> Dict:
    """Send a command to an active debugger session."""
    client = DebuggerClient(session.socket_path)
    if not client.connect():
        return {"error": "Could not connect to debugger. Is it running?"}

    try:
        response = client.send_command(command)
        return response if response else {"error": "No response from debugger"}
    finally:
        client.close()


def cmd_start(args) -> int:
    """Start debugging a script."""
    script_path = os.path.abspath(args.script)

    if not os.path.exists(script_path):
        print(json.dumps({"error": f"Script not found: {script_path}"}))
        return 1

    # Check for existing session
    existing = SessionManager.find_active_session(script_path)
    if existing:
        print(json.dumps({
            "error": "Debugger already running for this script",
            "hint": "Use 'debugger.py status' or 'debugger.py quit' first"
        }))
        return 1

    # Create session manager
    session = SessionManager(script_path)

    # Fork subprocess
    pid = os.fork()

    if pid == 0:
        # Child process - run the debugger
        try:
            # Redirect stdout/stderr to prevent interfering with JSON output
            # In a real implementation, you might log to a file
            debugger = ClaudeDebugger(session)
            debugger.run_script(script_path, args.args)
        except Exception as e:
            session.update_session(status="error", error=str(e))
            sys.exit(1)
        sys.exit(0)
    else:
        # Parent process
        session.create_session(pid)

        # Wait for debugger to start
        time.sleep(0.5)

        # Try to get initial status
        client = DebuggerClient(session.socket_path)
        if client.connect(timeout=5.0):
            response = client.send_command({"command": "status"})
            client.close()
            print(json.dumps(response if response else {"status": "started", "pid": pid}))
        else:
            print(json.dumps({"status": "started", "pid": pid}))

        return 0


def cmd_status(args) -> int:
    """Get debugger status."""
    sessions = SessionManager.get_all_sessions()

    if not sessions:
        print(json.dumps({"status": "no_active_sessions"}))
        return 0

    # If script specified, find that session
    if args.script:
        session = SessionManager.find_active_session(args.script)
        if not session:
            print(json.dumps({"error": "No active session for this script"}))
            return 1
        response = send_command(session, {"command": "status"})
        print(json.dumps(response))
        return 0

    # Return all sessions
    print(json.dumps({"status": "ok", "sessions": sessions}))
    return 0


def cmd_break(args) -> int:
    """Set a breakpoint."""
    if not args.file and not args.exception:
        print(json.dumps({"error": "Must specify --file or --exception"}))
        return 1

    # Find session
    session = None
    if args.file:
        session = SessionManager.find_active_session(args.file)

    if not session:
        sessions = SessionManager.get_all_sessions()
        if sessions:
            session = SessionManager(sessions[0]["script"])
        else:
            print(json.dumps({"error": "No active debugger session"}))
            return 1

    command = {"command": "break"}

    if args.exception:
        command["exception"] = args.exception
    else:
        command["file"] = args.file
        command["line"] = args.line
        if args.condition:
            command["condition"] = args.condition

    response = send_command(session, command)
    print(json.dumps(response))
    return 0 if response.get("status") == "ok" else 1


def cmd_delete(args) -> int:
    """Delete a breakpoint."""
    sessions = SessionManager.get_all_sessions()
    if not sessions:
        print(json.dumps({"error": "No active debugger session"}))
        return 1

    session = SessionManager(sessions[0]["script"])

    command = {"command": "delete"}
    if args.exception:
        command["exception"] = args.exception
    elif args.number:
        command["number"] = args.number
    elif args.file and args.line:
        command["file"] = args.file
        command["line"] = args.line
    else:
        print(json.dumps({"error": "Must specify breakpoint to delete"}))
        return 1

    response = send_command(session, command)
    print(json.dumps(response))
    return 0 if response.get("status") == "ok" else 1


def cmd_breakpoints(args) -> int:
    """List all breakpoints."""
    sessions = SessionManager.get_all_sessions()
    if not sessions:
        print(json.dumps({"error": "No active debugger session"}))
        return 1

    session = SessionManager(sessions[0]["script"])
    response = send_command(session, {"command": "breakpoints"})
    print(json.dumps(response))
    return 0


def cmd_execution(args, command: str) -> int:
    """Handle execution commands (continue, step, next, finish)."""
    sessions = SessionManager.get_all_sessions()
    if not sessions:
        print(json.dumps({"error": "No active debugger session"}))
        return 1

    session = SessionManager(sessions[0]["script"])
    response = send_command(session, {"command": command})

    # Wait a moment for the debugger to hit next stop
    time.sleep(0.1)

    # Get updated status
    status_response = send_command(session, {"command": "status"})

    # Merge responses
    if status_response.get("status") == "paused":
        print(json.dumps(status_response))
    else:
        print(json.dumps(response))

    return 0


def cmd_locals(args) -> int:
    """Get local variables."""
    sessions = SessionManager.get_all_sessions()
    if not sessions:
        print(json.dumps({"error": "No active debugger session"}))
        return 1

    session = SessionManager(sessions[0]["script"])
    command = {"command": "locals"}
    if args.depth:
        command["depth"] = args.depth

    response = send_command(session, command)
    print(json.dumps(response))
    return 0


def cmd_globals(args) -> int:
    """Get global variables."""
    sessions = SessionManager.get_all_sessions()
    if not sessions:
        print(json.dumps({"error": "No active debugger session"}))
        return 1

    session = SessionManager(sessions[0]["script"])
    command = {"command": "globals"}
    if args.depth:
        command["depth"] = args.depth

    response = send_command(session, command)
    print(json.dumps(response))
    return 0


def cmd_eval(args) -> int:
    """Evaluate an expression."""
    sessions = SessionManager.get_all_sessions()
    if not sessions:
        print(json.dumps({"error": "No active debugger session"}))
        return 1

    session = SessionManager(sessions[0]["script"])
    response = send_command(session, {"command": "eval", "expression": args.expression})
    print(json.dumps(response))
    return 0


def cmd_inspect(args) -> int:
    """Deep inspect a variable."""
    sessions = SessionManager.get_all_sessions()
    if not sessions:
        print(json.dumps({"error": "No active debugger session"}))
        return 1

    session = SessionManager(sessions[0]["script"])
    command = {"command": "inspect", "expression": args.expression}
    if args.depth:
        command["depth"] = args.depth

    response = send_command(session, command)
    print(json.dumps(response))
    return 0


def cmd_stack(args) -> int:
    """Get call stack."""
    sessions = SessionManager.get_all_sessions()
    if not sessions:
        print(json.dumps({"error": "No active debugger session"}))
        return 1

    session = SessionManager(sessions[0]["script"])
    response = send_command(session, {"command": "stack"})
    print(json.dumps(response))
    return 0


def cmd_up(args) -> int:
    """Move up the call stack."""
    sessions = SessionManager.get_all_sessions()
    if not sessions:
        print(json.dumps({"error": "No active debugger session"}))
        return 1

    session = SessionManager(sessions[0]["script"])
    response = send_command(session, {"command": "up"})
    print(json.dumps(response))
    return 0


def cmd_down(args) -> int:
    """Move down the call stack."""
    sessions = SessionManager.get_all_sessions()
    if not sessions:
        print(json.dumps({"error": "No active debugger session"}))
        return 1

    session = SessionManager(sessions[0]["script"])
    response = send_command(session, {"command": "down"})
    print(json.dumps(response))
    return 0


def cmd_quit(args) -> int:
    """Quit the debugger."""
    sessions = SessionManager.get_all_sessions()
    if not sessions:
        print(json.dumps({"status": "no_active_sessions"}))
        return 0

    session = SessionManager(sessions[0]["script"])
    response = send_command(session, {"command": "quit"})

    # Clean up session
    session.delete_session()

    print(json.dumps(response))
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code Python Debugger",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # start
    start_parser = subparsers.add_parser("start", help="Start debugging a script")
    start_parser.add_argument("script", help="Python script to debug")
    start_parser.add_argument("args", nargs="*", help="Arguments to pass to the script")

    # status
    status_parser = subparsers.add_parser("status", help="Get debugger status")
    status_parser.add_argument("-s", "--script", help="Script to check status for")

    # break
    break_parser = subparsers.add_parser("break", help="Set a breakpoint")
    break_parser.add_argument("-f", "--file", help="File path")
    break_parser.add_argument("-l", "--line", type=int, help="Line number")
    break_parser.add_argument("-c", "--condition", help="Conditional expression")
    break_parser.add_argument("-e", "--exception", help="Exception type (use * for all)")

    # delete
    delete_parser = subparsers.add_parser("delete", help="Delete a breakpoint")
    delete_parser.add_argument("-f", "--file", help="File path")
    delete_parser.add_argument("-l", "--line", type=int, help="Line number")
    delete_parser.add_argument("-n", "--number", type=int, help="Breakpoint number")
    delete_parser.add_argument("-e", "--exception", help="Exception type")

    # breakpoints
    subparsers.add_parser("breakpoints", help="List all breakpoints")

    # Execution commands
    subparsers.add_parser("continue", help="Continue execution")
    subparsers.add_parser("step", help="Step into next line")
    subparsers.add_parser("next", help="Step over to next line")
    subparsers.add_parser("finish", help="Run until function returns")

    # locals
    locals_parser = subparsers.add_parser("locals", help="Get local variables")
    locals_parser.add_argument("-d", "--depth", type=int, default=2, help="Inspection depth")

    # globals
    globals_parser = subparsers.add_parser("globals", help="Get global variables")
    globals_parser.add_argument("-d", "--depth", type=int, default=2, help="Inspection depth")

    # eval
    eval_parser = subparsers.add_parser("eval", help="Evaluate an expression")
    eval_parser.add_argument("expression", help="Expression to evaluate")

    # inspect
    inspect_parser = subparsers.add_parser("inspect", help="Deep inspect a variable")
    inspect_parser.add_argument("expression", help="Variable or expression to inspect")
    inspect_parser.add_argument("-d", "--depth", type=int, default=4, help="Inspection depth")

    # stack
    subparsers.add_parser("stack", help="Get call stack")

    # up/down
    subparsers.add_parser("up", help="Move up the call stack")
    subparsers.add_parser("down", help="Move down the call stack")

    # quit
    subparsers.add_parser("quit", help="Quit the debugger")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    command_handlers = {
        "start": cmd_start,
        "status": cmd_status,
        "break": cmd_break,
        "delete": cmd_delete,
        "breakpoints": cmd_breakpoints,
        "continue": lambda a: cmd_execution(a, "continue"),
        "step": lambda a: cmd_execution(a, "step"),
        "next": lambda a: cmd_execution(a, "next"),
        "finish": lambda a: cmd_execution(a, "finish"),
        "locals": cmd_locals,
        "globals": cmd_globals,
        "eval": cmd_eval,
        "inspect": cmd_inspect,
        "stack": cmd_stack,
        "up": cmd_up,
        "down": cmd_down,
        "quit": cmd_quit,
    }

    handler = command_handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
