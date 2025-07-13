import atomac
import json
from pathlib import Path
from datetime import datetime
from atomac.AXClasses import BaseAXUIElement

CLICKMAP_DATA_DIR = Path("ome/data/clickmaps")
CLICKMAP_DATA_DIR.mkdir(parents=True, exist_ok=True)

class AppClickmapGenerator:
    def __init__(self, app_name_or_bundle_id: str):
        self.app_name_or_bundle_id = app_name_or_bundle_id
        self.app_ref = None
        self.bundle_id = None
        self.app_name = None
        self._find_and_set_app_details()

    def _robust_get_attr(self, element, attr_name, default_value="dunna"):
        try:
            value = getattr(element, attr_name, None)
            if value is None: return default_value
            if isinstance(value, (tuple, list)) and len(value) == 2 and isinstance(value[0], (int, float)) and isinstance(value[1], (int, float)):
                return list(value) # Convert tuples of coords/size to lists
            if isinstance(value, str) and not value.strip(): return default_value
            return value
        except Exception:
            return f"[Error getting {attr_name}]"

    def _get_role_path(self, element):
        path_parts = []
        current = element
        try:
            for _ in range(10): # Limit depth
                if not current or not hasattr(current, 'AXRole'): break
                role = self._robust_get_attr(current, 'AXRole', 'UnknownRole')
                parent = getattr(current, 'AXParent', None)
                if parent and hasattr(parent, 'AXChildren'):
                    children = parent.AXChildren
                    try: index = children.index(current) if current in children else -1
                    except (ValueError, AttributeError, TypeError): index = -1
                    path_parts.append(f"{role}[{index if index != -1 else '?'}]")
                else:
                    path_parts.append(f"{role}[-]")
                if self._robust_get_attr(current, 'AXRole') == 'AXWindow' or not parent: break
                current = parent
        except Exception: return "[Error building role path]"
        return "/".join(reversed(path_parts))

    def _find_and_set_app_details(self):
        try:
            # Try as bundle ID first
            if '.' in self.app_name_or_bundle_id:
                self.app_ref = atomac.getAppRefByBundleId(self.app_name_or_bundle_id)
                if self.app_ref:
                    self.bundle_id = self.app_name_or_bundle_id
                    self.app_name = self._robust_get_attr(self.app_ref, "AXTitle", self.app_name_or_bundle_id.split('.')[-1])
                    print(f"✅ App found by bundle ID: {self.app_name} ({self.bundle_id})")
                    return

            # Fallback to searching by name
            apps = BaseAXUIElement._getRunningApps()
            for app_info in apps:
                name_from_list = ""
                bundle_id_from_list = ""
                try: 
                    name_from_list = app_info['name']
                    bundle_id_from_list = app_info['bundle_id']
                except TypeError: 
                    name_from_list = app_info.localizedName()
                    bundle_id_from_list = app_info.bundleIdentifier()
                
                if name_from_list == self.app_name_or_bundle_id:
                    self.app_ref = atomac.getAppRefByBundleId(bundle_id_from_list)
                    if self.app_ref:
                        self.app_name = name_from_list
                        self.bundle_id = bundle_id_from_list
                        print(f"✅ App found by name: {self.app_name} ({self.bundle_id})")
                        return
            print(f"⛔ App not found: {self.app_name_or_bundle_id}")
            self.app_ref = None # Ensure it's None if not found
        except Exception as e:
            print(f"⛔ Error finding app {self.app_name_or_bundle_id}: {e}")
            self.app_ref = None

    def get_elements_for_labeling(self, window_index=0):
        if not self.app_ref:
            print(f"⛔ App reference not available for {self.app_name_or_bundle_id}. Cannot get elements.")
            return []
        
        try:
            windows = self.app_ref.windows()
            if not windows or window_index >= len(windows):
                print(f"⛔ Window {window_index} not found for {self.app_name}.")
                return []
            window = windows[window_index]
            print(f"✅ Processing window: {self._robust_get_attr(window, 'AXTitle', 'Untitled Window')}")

            all_elements_in_window = window.findAllR()
            print(f"🔍 Found {len(all_elements_in_window)} total elements in the window.")

            elements_for_labeling = []
            for i, el in enumerate(all_elements_in_window):
                pos_val = self._robust_get_attr(el, "AXPosition", None)
                size_val = self._robust_get_attr(el, "AXSize", None)

                is_pos_list_of_2 = isinstance(pos_val, list) and len(pos_val) == 2
                is_size_list_of_2 = isinstance(size_val, list) and len(size_val) == 2
                is_size_non_zero = is_size_list_of_2 and (size_val[0] != 0.0 or size_val[1] != 0.0)

                if not (is_pos_list_of_2 and is_size_list_of_2 and is_size_non_zero):
                    continue # Skip elements without valid coordinates

                title = self._robust_get_attr(el, "AXTitle")
                role = self._robust_get_attr(el, "AXRole", "UnknownRole")
                subrole = self._robust_get_attr(el, "AXSubrole")
                ax_identifier = self._robust_get_attr(el, "AXIdentifier")
                ax_role_path = self._get_role_path(el)
                
                extra_info = {}
                for attr in ["AXHelp", "AXDescription", "AXValue", "AXPlaceholderValue"]:
                    val = self._robust_get_attr(el, attr)
                    if val != "dunna" and not (isinstance(val, str) and val.startswith("[Error")):
                        if attr == "AXValue" and hasattr(val, 'AXRole'):
                            extra_info["AXValue_role"] = self._robust_get_attr(val, "AXRole")
                            extra_info["AXValue_title"] = self._robust_get_attr(val, "AXTitle")
                        else: extra_info[attr] = val
                if ax_identifier != "dunna" and not (isinstance(ax_identifier, str) and ax_identifier.startswith("[Error")):
                     extra_info["AXIdentifier"] = ax_identifier
                if ax_role_path != "dunna" and not (isinstance(ax_role_path, str) and ax_role_path.startswith("[Error")):
                    extra_info["AXRolePath"] = ax_role_path
                
                el_type = "unknown"; confidence = 0.3
                if isinstance(role, str):
                    if role == "AXButton": el_type = "control"; confidence = 0.6
                    elif role in ["AXTextField", "AXTextArea", "AXSearchField"]: el_type = "input"; confidence = 0.8
                    elif role == "AXStaticText": el_type = "text"; confidence = 0.4
                    elif role == "AXLink": el_type = "link"; confidence = 0.7

                element_data = {
                    "id": f"el_{i}", "title": title, "role": role, "subrole": subrole,
                    "position": pos_val, "size": size_val,
                    "click": [pos_val[0] + size_val[0] / 2, pos_val[1] + size_val[1] / 2],
                    "auto_type": el_type, "action_hint": "click", "confidence": confidence,
                    "extra_info": extra_info,
                    "type": "",           # AI-friendly classification field
                    "description": "",    # AI-friendly description field  
                    "hints": []           # AI-friendly hints for future use
                }
                elements_for_labeling.append(element_data)
            
            print(f"✅ Extracted {len(elements_for_labeling)} elements with valid coordinates for labeling.")
            return elements_for_labeling

        except Exception as e:
            print(f"⛔ Error getting elements for {self.app_name}: {e}")
            return []

    def save_elements_for_labeling(self, elements_data, filename_suffix="for_labeling"):
        if not self.app_name or not self.bundle_id:
            print("⛔ App details not set, cannot save file with standard name.")
            base_name = "unknown_app"
        else:
            base_name = self.app_name.replace(' ', '_')

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file_name = f"{base_name}_{filename_suffix}_{timestamp}.json"
        out_file_path = CLICKMAP_DATA_DIR / out_file_name

        output_json = {
            "app_name": self.app_name,
            "bundle_id": self.bundle_id,
            "generated_at": timestamp,
            "elements": elements_data
        }
        with open(out_file_path, "w") as f:
            json.dump(output_json, f, indent=2, default=str)
        print(f"💾 Elements for labeling saved to: {out_file_path}")
        return out_file_path

# Example usage (would be in a separate script like notes_button_clickmap_S1_S2.py):
# if __name__ == "__main__":
#     notes_generator = AppClickmapGenerator("Notes") # Or use "com.apple.Notes"
#     if notes_generator.app_ref: # Check if app was found
#         elements_to_label = notes_generator.get_elements_for_labeling()
#         if elements_to_label:
#             notes_generator.save_elements_for_labeling(elements_to_label) 