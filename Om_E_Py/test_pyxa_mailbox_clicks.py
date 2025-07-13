import sys
import time
from ome.controllers.mail.mail_controller import MailController
from ome.utils.uiNav.navBigDaDDy import navBigDaDDy

if len(sys.argv) < 2:
    print("Usage: python test_pyxa_mailbox_clicks.py <account_name>")
    sys.exit(1)

account_name = sys.argv[1]

start_script = time.time()
# Initialize MailController and navBigDaDDy
controller = MailController()
nav = navBigDaDDy(controller.BUNDLE_ID, app=controller.app)

# Get all mailboxes for the account using PyXA
mailboxes = controller.get_mailboxes(account_name)
mailbox_names = [mb.name for mb in mailboxes]
mailbox_names_lower = [name.lower() for name in mailbox_names]

print(f"Found {len(mailbox_names)} mailboxes for account '{account_name}':")
for name in mailbox_names:
    print(f"  - {name}")

# Helper to map mailbox names using controller's mapping
map_mailbox_name = controller._map_mailbox_name if hasattr(controller, '_map_mailbox_name') else (lambda x: x)

# Iterate over nav data (UI order) for this account
nav_items = controller.get_hierarchical_nav()
clicked_count = 0
for item in nav_items:
    path = item.get("path")
    if path and len(path) == 3 and path[0] == "accounts" and path[1].lower() == account_name.lower() and "omeClick" in item:
        nav_mailbox = path[2]
        mapped_nav_mailbox = map_mailbox_name(nav_mailbox)
        # Try to find a matching PyXA mailbox (case-insensitive)
        match = None
        for i, pyxa_name in enumerate(mailbox_names):
            if pyxa_name == nav_mailbox or pyxa_name.lower() == nav_mailbox.lower() or pyxa_name.lower() == mapped_nav_mailbox.lower():
                match = pyxa_name
                break
        if not match:
            # Try mapping PyXA names to nav_mailbox
            for i, pyxa_name in enumerate(mailbox_names):
                mapped_pyxa = map_mailbox_name(pyxa_name)
                if mapped_pyxa == nav_mailbox or mapped_pyxa.lower() == nav_mailbox.lower():
                    match = pyxa_name
                    break
        print(f"Clicking UI mailbox: {nav_mailbox} (nav path) | PyXA match: {match if match else 'None'}")
        omeClick = item["omeClick"]
        t0 = time.time()
        result = nav.click_at_coordinates(omeClick[0], omeClick[1], f"mailbox {nav_mailbox}")
        t1 = time.time()
        print(f"  Click result: {result} | Time: {t1-t0:.3f}s")
        clicked_count += 1

end_script = time.time()
print(f"Total mailboxes clicked in UI order: {clicked_count}")
print(f"Total elapsed time: {end_script - start_script:.2f} seconds.") 