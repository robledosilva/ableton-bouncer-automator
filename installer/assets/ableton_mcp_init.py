# AbletonMCP/init.py
from __future__ import absolute_import, print_function, unicode_literals

from _Framework.ControlSurface import ControlSurface
import socket
import json
import threading
import time
import traceback

# Change queue import for Python 2
try:
    import Queue as queue  # Python 2
except ImportError:
    import queue  # Python 3

# Constants for socket communication
DEFAULT_PORT = 9877
HOST = "localhost"

def create_instance(c_instance):
    """Create and return the AbletonMCP script instance"""
    return AbletonMCP(c_instance)

class AbletonMCP(ControlSurface):
    """AbletonMCP Remote Script for Ableton Live"""

    def __init__(self, c_instance):
        """Initialize the control surface"""
        ControlSurface.__init__(self, c_instance)
        self.log_message("AbletonMCP Remote Script initializing...")

        # Socket server for communication
        self.server = None
        self.client_threads = []
        self.server_thread = None
        self.running = False

        # Cache the song reference for easier access
        self._song = self.song()

        # Start the socket server
        self.start_server()

        self.log_message("AbletonMCP initialized")

        # Show a message in Ableton
        self.show_message("AbletonMCP: Listening for commands on port " + str(DEFAULT_PORT))

    def disconnect(self):
        """Called when Ableton closes or the control surface is removed"""
        self.log_message("AbletonMCP disconnecting...")
        self.running = False

        if self.server:
            try:
                self.server.close()
            except:
                pass

        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(1.0)

        for client_thread in self.client_threads[:]:
            if client_thread.is_alive():
                self.log_message("Client thread still alive during disconnect")

        ControlSurface.disconnect(self)
        self.log_message("AbletonMCP disconnected")

    def start_server(self):
        """Start the socket server in a separate thread"""
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((HOST, DEFAULT_PORT))
            self.server.listen(5)

            self.running = True
            self.server_thread = threading.Thread(target=self._server_thread)
            self.server_thread.daemon = True
            self.server_thread.start()

            self.log_message("Server started on port " + str(DEFAULT_PORT))
        except Exception as e:
            self.log_message("Error starting server: " + str(e))
            self.show_message("AbletonMCP: Error starting server - " + str(e))

    def _server_thread(self):
        """Server thread implementation"""
        try:
            self.log_message("Server thread started")
            self.server.settimeout(1.0)

            while self.running:
                try:
                    client, address = self.server.accept()
                    self.log_message("Connection accepted from " + str(address))
                    self.show_message("AbletonMCP: Client connected")

                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client,)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                    self.client_threads.append(client_thread)
                    self.client_threads = [t for t in self.client_threads if t.is_alive()]

                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.log_message("Server accept error: " + str(e))
                    time.sleep(0.5)

            self.log_message("Server thread stopped")
        except Exception as e:
            self.log_message("Server thread error: " + str(e))

    def _handle_client(self, client):
        """Handle communication with a connected client"""
        self.log_message("Client handler started")
        client.settimeout(None)
        buffer = ''

        try:
            while self.running:
                try:
                    data = client.recv(8192)

                    if not data:
                        self.log_message("Client disconnected")
                        break

                    try:
                        buffer += data.decode('utf-8')
                    except AttributeError:
                        buffer += data

                    try:
                        command = json.loads(buffer)
                        buffer = ''

                        self.log_message("Received command: " + str(command.get("type", "unknown")))
                        response = self._process_command(command)

                        try:
                            client.sendall(json.dumps(response).encode('utf-8'))
                        except AttributeError:
                            client.sendall(json.dumps(response))
                    except ValueError:
                        continue

                except Exception as e:
                    self.log_message("Error handling client data: " + str(e))
                    self.log_message(traceback.format_exc())

                    error_response = {"status": "error", "message": str(e)}
                    try:
                        client.sendall(json.dumps(error_response).encode('utf-8'))
                    except:
                        break

                    if not isinstance(e, ValueError):
                        break
        except Exception as e:
            self.log_message("Error in client handler: " + str(e))
        finally:
            try:
                client.close()
            except:
                pass
            self.log_message("Client handler stopped")

    def _process_command(self, command):
        """Process a command and return a response"""
        command_type = command.get("type", "")
        params = command.get("params", {})

        response = {"status": "success", "result": {}}

        try:
            if command_type == "get_session_info":
                response["result"] = self._get_session_info()
            elif command_type == "get_track_info":
                response["result"] = self._get_track_info(params.get("track_index", 0))
            elif command_type in ["create_midi_track", "set_track_name",
                                  "create_clip", "add_notes_to_clip", "set_clip_name",
                                  "set_tempo", "fire_clip", "stop_clip",
                                  "start_playback", "stop_playback", "load_browser_item"]:
                response_queue = queue.Queue()

                def main_thread_task():
                    try:
                        result = None
                        if command_type == "create_midi_track":
                            result = self._create_midi_track(params.get("index", -1))
                        elif command_type == "set_track_name":
                            result = self._set_track_name(params.get("track_index", 0), params.get("name", ""))
                        elif command_type == "create_clip":
                            result = self._create_clip(params.get("track_index", 0), params.get("clip_index", 0), params.get("length", 4.0))
                        elif command_type == "add_notes_to_clip":
                            result = self._add_notes_to_clip(params.get("track_index", 0), params.get("clip_index", 0), params.get("notes", []))
                        elif command_type == "set_clip_name":
                            result = self._set_clip_name(params.get("track_index", 0), params.get("clip_index", 0), params.get("name", ""))
                        elif command_type == "set_tempo":
                            result = self._set_tempo(params.get("tempo", 120.0))
                        elif command_type == "fire_clip":
                            result = self._fire_clip(params.get("track_index", 0), params.get("clip_index", 0))
                        elif command_type == "stop_clip":
                            result = self._stop_clip(params.get("track_index", 0), params.get("clip_index", 0))
                        elif command_type == "start_playback":
                            result = self._start_playback()
                        elif command_type == "stop_playback":
                            result = self._stop_playback()
                        elif command_type == "load_browser_item":
                            result = self._load_browser_item(params.get("track_index", 0), params.get("item_uri", ""))
                        response_queue.put({"status": "success", "result": result})
                    except Exception as e:
                        self.log_message("Error in main thread task: " + str(e))
                        response_queue.put({"status": "error", "message": str(e)})

                try:
                    self.schedule_message(0, main_thread_task)
                except AssertionError:
                    main_thread_task()

                try:
                    task_response = response_queue.get(timeout=10.0)
                    if task_response.get("status") == "error":
                        response["status"] = "error"
                        response["message"] = task_response.get("message", "Unknown error")
                    else:
                        response["result"] = task_response.get("result", {})
                except queue.Empty:
                    response["status"] = "error"
                    response["message"] = "Timeout waiting for operation to complete"
            elif command_type == "get_browser_tree":
                response["result"] = self.get_browser_tree(params.get("category_type", "all"))
            elif command_type == "get_browser_items_at_path":
                response["result"] = self.get_browser_items_at_path(params.get("path", ""))
            else:
                response["status"] = "error"
                response["message"] = "Unknown command: " + command_type
        except Exception as e:
            self.log_message("Error processing command: " + str(e))
            response["status"] = "error"
            response["message"] = str(e)

        return response

    def _get_session_info(self):
        try:
            return {
                "tempo": self._song.tempo,
                "signature_numerator": self._song.signature_numerator,
                "signature_denominator": self._song.signature_denominator,
                "track_count": len(self._song.tracks),
                "return_track_count": len(self._song.return_tracks),
                "master_track": {
                    "name": "Master",
                    "volume": self._song.master_track.mixer_device.volume.value,
                    "panning": self._song.master_track.mixer_device.panning.value
                }
            }
        except Exception as e:
            self.log_message("Error getting session info: " + str(e))
            raise

    def _get_track_info(self, track_index):
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            track = self._song.tracks[track_index]
            clip_slots = []
            for slot_index, slot in enumerate(track.clip_slots):
                clip_info = None
                if slot.has_clip:
                    clip = slot.clip
                    clip_info = {"name": clip.name, "length": clip.length,
                                 "is_playing": clip.is_playing, "is_recording": clip.is_recording}
                clip_slots.append({"index": slot_index, "has_clip": slot.has_clip, "clip": clip_info})
            devices = []
            for i, device in enumerate(track.devices):
                devices.append({"index": i, "name": device.name,
                                 "class_name": device.class_name, "type": self._get_device_type(device)})
            return {
                "index": track_index, "name": track.name,
                "is_audio_track": track.has_audio_input, "is_midi_track": track.has_midi_input,
                "mute": track.mute, "solo": track.solo, "arm": track.arm,
                "volume": track.mixer_device.volume.value, "panning": track.mixer_device.panning.value,
                "clip_slots": clip_slots, "devices": devices
            }
        except Exception as e:
            self.log_message("Error getting track info: " + str(e))
            raise

    def _create_midi_track(self, index):
        self._song.create_midi_track(index)
        new_index = len(self._song.tracks) - 1 if index == -1 else index
        track = self._song.tracks[new_index]
        return {"index": new_index, "name": track.name}

    def _set_track_name(self, track_index, name):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        self._song.tracks[track_index].name = name
        return {"name": self._song.tracks[track_index].name}

    def _create_clip(self, track_index, clip_index, length):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            raise IndexError("Clip index out of range")
        slot = track.clip_slots[clip_index]
        if slot.has_clip:
            raise Exception("Clip slot already has a clip")
        slot.create_clip(length)
        return {"name": slot.clip.name, "length": slot.clip.length}

    def _add_notes_to_clip(self, track_index, clip_index, notes):
        track = self._song.tracks[track_index]
        slot = track.clip_slots[clip_index]
        if not slot.has_clip:
            raise Exception("No clip in slot")
        live_notes = [(n.get("pitch",60), n.get("start_time",0.0),
                       n.get("duration",0.25), n.get("velocity",100), n.get("mute",False))
                      for n in notes]
        slot.clip.set_notes(tuple(live_notes))
        return {"note_count": len(notes)}

    def _set_clip_name(self, track_index, clip_index, name):
        slot = self._song.tracks[track_index].clip_slots[clip_index]
        if not slot.has_clip:
            raise Exception("No clip in slot")
        slot.clip.name = name
        return {"name": slot.clip.name}

    def _set_tempo(self, tempo):
        self._song.tempo = tempo
        return {"tempo": self._song.tempo}

    def _fire_clip(self, track_index, clip_index):
        slot = self._song.tracks[track_index].clip_slots[clip_index]
        if not slot.has_clip:
            raise Exception("No clip in slot")
        slot.fire()
        return {"fired": True}

    def _stop_clip(self, track_index, clip_index):
        self._song.tracks[track_index].clip_slots[clip_index].stop()
        return {"stopped": True}

    def _start_playback(self):
        self._song.start_playing()
        return {"playing": self._song.is_playing}

    def _stop_playback(self):
        self._song.stop_playing()
        return {"playing": self._song.is_playing}

    def _load_browser_item(self, track_index, item_uri):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        app = self.application()
        item = self._find_browser_item_by_uri(app.browser, item_uri)
        if not item:
            raise ValueError("Browser item not found: " + item_uri)
        self._song.view.selected_track = track
        app.browser.load_item(item)
        return {"loaded": True, "item_name": item.name, "track_name": track.name}

    def _find_browser_item_by_uri(self, node, uri, max_depth=10, depth=0):
        if hasattr(node, 'uri') and node.uri == uri:
            return node
        if depth >= max_depth:
            return None
        if hasattr(node, 'instruments'):
            for cat in [node.instruments, node.sounds, node.drums, node.audio_effects, node.midi_effects]:
                r = self._find_browser_item_by_uri(cat, uri, max_depth, depth+1)
                if r: return r
            return None
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                r = self._find_browser_item_by_uri(child, uri, max_depth, depth+1)
                if r: return r
        return None

    def _get_device_type(self, device):
        try:
            if device.can_have_drum_pads: return "drum_machine"
            if device.can_have_chains: return "rack"
            if "instrument" in device.class_display_name.lower(): return "instrument"
            if "audio_effect" in device.class_name.lower(): return "audio_effect"
            if "midi_effect" in device.class_name.lower(): return "midi_effect"
            return "unknown"
        except:
            return "unknown"

    def get_browser_tree(self, category_type="all"):
        try:
            app = self.application()
            if not app: raise RuntimeError("Could not access Live application")
            result = {"type": category_type, "categories": []}
            def process_item(item):
                if not item: return None
                return {"name": getattr(item, 'name', 'Unknown'),
                        "is_folder": hasattr(item, 'children') and bool(item.children),
                        "is_device": getattr(item, 'is_device', False),
                        "is_loadable": getattr(item, 'is_loadable', False),
                        "uri": getattr(item, 'uri', None), "children": []}
            for attr, label in [("instruments","Instruments"),("sounds","Sounds"),
                                 ("drums","Drums"),("audio_effects","Audio Effects"),
                                 ("midi_effects","MIDI Effects")]:
                if (category_type in ("all", attr)) and hasattr(app.browser, attr):
                    item = process_item(getattr(app.browser, attr))
                    if item:
                        item["name"] = label
                        result["categories"].append(item)
            return result
        except Exception as e:
            self.log_message("Error getting browser tree: " + str(e))
            raise

    def get_browser_items_at_path(self, path):
        try:
            app = self.application()
            if not app: raise RuntimeError("Could not access Live application")
            parts = path.split("/")
            root = parts[0].lower()
            cats = {"instruments": "instruments", "sounds": "sounds", "drums": "drums",
                    "audio_effects": "audio_effects", "midi_effects": "midi_effects"}
            if root not in cats or not hasattr(app.browser, cats[root]):
                return {"path": path, "error": "Unknown category: " + root, "items": []}
            current = getattr(app.browser, cats[root])
            for part in parts[1:]:
                if not part: continue
                found = False
                for child in (current.children if hasattr(current, 'children') else []):
                    if getattr(child, 'name', '').lower() == part.lower():
                        current = child; found = True; break
                if not found:
                    return {"path": path, "error": "Not found: " + part, "items": []}
            items = [{"name": c.name, "is_folder": hasattr(c,'children') and bool(c.children),
                      "is_device": getattr(c,'is_device',False),
                      "is_loadable": getattr(c,'is_loadable',False),
                      "uri": getattr(c,'uri',None)}
                     for c in (current.children if hasattr(current,'children') else [])]
            return {"path": path, "name": getattr(current,'name',''), "items": items}
        except Exception as e:
            self.log_message("Error getting browser items: " + str(e))
            raise
