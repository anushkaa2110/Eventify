import copy
import csv
import json
from datetime import datetime, date
from pathlib import Path
from tkinter import messagebox, filedialog

import customtkinter as ctk

# ---------------- THEME ----------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG = "#111111"
SIDEBAR = "#181818"
CARD = "#222222"
CARD2 = "#2B2B2B"
GOLD = "#D6AA60"
GOLD_HOVER = "#B98C45"
WHITE = "#F5F0E7"
MUTED = "#AAA49A"
GREEN = "#62B58A"
RED = "#D47777"

RSVP_OPTIONS = ["Registered", "Confirmed", "Maybe", "Cancelled"]
RSVP_COLORS = {"Registered": GOLD, "Confirmed": GREEN, "Maybe": MUTED, "Cancelled": RED}

# ---------------- DATA (saved to a JSON file next to this script) ----------------
DATA_FILE = Path(__file__).resolve().with_name("eventify_data.json")

DEMO_EVENTS = [
    {"id": 1, "name": "TechNova Summit", "date": "2026-12-15",
     "venue": "Main Auditorium", "description": "A day of technology and innovation.",
     "budget": 45000.0},
    {"id": 2, "name": "Golden Hour Gala", "date": "2026-12-20",
     "venue": "Grand Ballroom", "description": "An evening celebration.",
     "budget": 65000.0},
    {"id": 3, "name": "Creative Minds Workshop", "date": "2027-01-08",
     "venue": "Seminar Hall 2", "description": "A hands-on creative workshop.",
     "budget": 18000.0},
]

DEMO_GUESTS = [
    {"id": 1, "name": "Aarav Sharma", "email": "aarav@example.com",
     "phone": "9876543210", "event_id": 1, "rsvp": "Confirmed", "attended": True},
    {"id": 2, "name": "Diya Patel", "email": "diya@example.com",
     "phone": "9876543211", "event_id": 2, "rsvp": "Registered", "attended": False},
    {"id": 3, "name": "Rohan Mehta", "email": "rohan@example.com",
     "phone": "9876543212", "event_id": 1, "rsvp": "Confirmed", "attended": True},
    {"id": 4, "name": "Sneha Kapoor", "email": "sneha@example.com",
     "phone": "9876543213", "event_id": 3, "rsvp": "Maybe", "attended": False},
]


def load_data():
    """Load saved data, or fall back to demo data on first run / bad file."""
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data["events"], data["guests"]
    except (OSError, ValueError, KeyError):
        return copy.deepcopy(DEMO_EVENTS), copy.deepcopy(DEMO_GUESTS)


events, guests = load_data()


def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"events": events, "guests": guests}, f, indent=2)
    except OSError as err:
        print("Could not save data:", err)


def next_id(items):
    return max((i["id"] for i in items), default=0) + 1


# ---------------- DATE HELPERS ----------------
def days_until(date_str):
    return (datetime.strptime(date_str, "%Y-%m-%d").date() - date.today()).days


def when_text(date_str):
    """Friendly countdown text and its colour."""
    n = days_until(date_str)
    if n == 0:
        return "Today", GOLD
    if n == 1:
        return "Tomorrow", GREEN
    if n > 1:
        return f"In {n} days", GREEN
    if n == -1:
        return "Yesterday", MUTED
    return f"{-n} days ago", MUTED


# ---------------- WIDGET HELPERS ----------------
def button(parent, text, command, primary=False, width=110):
    return ctk.CTkButton(
        parent, text=text, command=command, width=width, height=36,
        corner_radius=9, font=ctk.CTkFont(size=12, weight="bold"),
        fg_color=GOLD if primary else CARD2,
        hover_color=GOLD_HOVER if primary else "#3A3A3A",
        text_color="#17130D" if primary else WHITE
    )


def label(parent, text, size=13, color=WHITE, bold=False):
    return ctk.CTkLabel(
        parent, text=text, text_color=color,
        font=ctk.CTkFont(size=size, weight="bold" if bold else "normal")
    )


def entry(parent, placeholder, width=250):
    return ctk.CTkEntry(
        parent, width=width, height=38, corner_radius=9,
        placeholder_text=placeholder, fg_color=CARD2,
        border_color="#454039", text_color=WHITE,
        placeholder_text_color=MUTED
    )


def option_menu(parent, values, width=150, command=None):
    return ctk.CTkOptionMenu(
        parent, values=values, width=width, height=36, command=command,
        fg_color=CARD2, button_color=GOLD, button_hover_color=GOLD_HOVER,
        text_color=WHITE, dropdown_fg_color=CARD2
    )


def clear(frame):
    for widget in frame.winfo_children():
        widget.destroy()


def open_modal(app, title, size):
    """Create a centered modal window. Esc closes it."""
    win = ctk.CTkToplevel(app)
    win.title(title)
    win.geometry(size)
    win.resizable(False, False)
    win.configure(fg_color=BG)
    win.transient(app)
    win.bind("<Escape>", lambda e: win.destroy())
    win.after(150, win.grab_set)  # delayed grab avoids a macOS focus glitch
    win.after(150, win.focus)
    return win


class Eventify(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Eventify | Event Management")
        self.geometry("1200x760")
        self.minsize(980, 640)
        self.configure(fg_color=BG)
        self.current_page = "Dashboard"
        self.visible_guests = []

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.pack(side="right", fill="both", expand=True)

        self.build_sidebar()
        self.show_page("Dashboard")

    def build_sidebar(self):
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=22, pady=(30, 38))
        label(brand, "✦ EVENTIFY", 24, GOLD, True).pack(anchor="w")
        label(brand, "PLAN  •  ORGANIZE  •  CELEBRATE", 9, MUTED).pack(anchor="w", pady=(6, 0))

        self.nav = {}
        for page, symbol in [
            ("Dashboard", "⌂"), ("Events", "▦"),
            ("Guests", "♙"), ("Analytics", "▥")
        ]:
            b = ctk.CTkButton(
                self.sidebar, text=f"   {symbol}     {page}",
                command=lambda p=page: self.show_page(p),
                height=45, corner_radius=10, anchor="w",
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent", hover_color="#30291D",
                text_color=MUTED
            )
            b.pack(fill="x", padx=14, pady=5)
            self.nav[page] = b

        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=22, pady=25)
        label(footer, "AUTO-SAVED", 10, GOLD, True).pack(anchor="w")
        label(footer, "Eventify  •  Version 1.1", 10, MUTED).pack(anchor="w", pady=(6, 0))

    def show_page(self, page):
        self.current_page = page
        for name, b in self.nav.items():
            b.configure(
                fg_color=GOLD if name == page else "transparent",
                text_color="#17130D" if name == page else MUTED
            )
        clear(self.main)
        {
            "Dashboard": self.dashboard,
            "Events": self.events_page,
            "Guests": self.guests_page,
            "Analytics": self.analytics_page
        }[page]()

    def refresh(self):
        self.show_page(self.current_page)

    def header(self, title, subtitle, add_text=None, add_command=None):
        top = ctk.CTkFrame(self.main, fg_color="transparent")
        top.pack(fill="x", padx=30, pady=(28, 20))
        left = ctk.CTkFrame(top, fg_color="transparent")
        left.pack(side="left")
        label(left, title, 27, WHITE, True).pack(anchor="w")
        label(left, subtitle, 12, MUTED).pack(anchor="w", pady=(5, 0))
        if add_text:
            button(top, add_text, add_command, True, 125).pack(side="right", pady=4)
        return top

    def stat_card(self, parent, title, value, foot):
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=14,
                            border_width=1, border_color="#393126")
        card.pack(side="left", fill="both", expand=True, padx=6)
        label(card, title.upper(), 10, MUTED, True).pack(anchor="w", padx=17, pady=(16, 5))
        label(card, str(value), 27, GOLD, True).pack(anchor="w", padx=17)
        label(card, foot, 10, MUTED).pack(anchor="w", padx=17, pady=(3, 15))

    def event_name(self, event_id):
        for e in events:
            if e["id"] == event_id:
                return e["name"]
        return "Unknown event"

    # ---------------- DASHBOARD ----------------
    def dashboard(self):
        self.header("Welcome back, Admin", "Here's what's happening with your events.")
        today = date.today().isoformat()
        upcoming = [e for e in events if e["date"] >= today]
        checked = sum(g["attended"] for g in guests)
        rate = round(checked / len(guests) * 100) if guests else 0

        stats = ctk.CTkFrame(self.main, fg_color="transparent")
        stats.pack(fill="x", padx=24, pady=(0, 20))
        self.stat_card(stats, "Total events", len(events), "Events created")
        self.stat_card(stats, "Total guests", len(guests), "Registered attendees")
        self.stat_card(stats, "Upcoming", len(upcoming), "Today and future")
        self.stat_card(stats, "Attendance", f"{rate}%", "Guests checked in")

        lower = ctk.CTkFrame(self.main, fg_color="transparent")
        lower.pack(fill="both", expand=True, padx=30, pady=(0, 25))

        panel = ctk.CTkFrame(lower, fg_color=CARD, corner_radius=14)
        panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
        label(panel, "UPCOMING EVENTS", 13, GOLD, True).pack(anchor="w", padx=18, pady=18)

        if not upcoming:
            label(panel, "No upcoming events. Create your first event.", 12, MUTED).pack(pady=25)
        else:
            for e in sorted(upcoming, key=lambda x: x["date"])[:6]:
                row = ctk.CTkFrame(panel, fg_color=CARD2, corner_radius=10)
                row.pack(fill="x", padx=13, pady=5)
                info = ctk.CTkFrame(row, fg_color="transparent")
                info.pack(side="left", fill="x", expand=True, padx=12, pady=10)
                label(info, e["name"], 13, WHITE, True).pack(anchor="w")
                label(info, f'{e["date"]}  •  {e["venue"]}', 10, MUTED).pack(anchor="w", pady=(4, 0))
                count = sum(g["event_id"] == e["id"] for g in guests)
                text, color = when_text(e["date"])
                right = ctk.CTkFrame(row, fg_color="transparent")
                right.pack(side="right", padx=14)
                label(right, text, 11, color, True).pack(anchor="e")
                label(right, f"{count} guests", 10, GOLD).pack(anchor="e")

        quick = ctk.CTkFrame(lower, width=230, fg_color=CARD, corner_radius=14)
        quick.pack(side="right", fill="y", padx=(8, 0))
        quick.pack_propagate(False)
        label(quick, "QUICK ACTIONS", 13, GOLD, True).pack(anchor="w", padx=18, pady=18)
        button(quick, "+  Create event", self.open_event_form, True, 190).pack(padx=18, pady=7)
        button(quick, "+  Add guest", self.open_guest_form, False, 190).pack(padx=18, pady=7)
        button(quick, "View events", lambda: self.show_page("Events"), False, 190).pack(padx=18, pady=7)
        label(quick, "ATTENDANCE RATE", 10, MUTED, True).pack(anchor="w", padx=18, pady=(35, 8))
        bar = ctk.CTkProgressBar(quick, progress_color=GOLD, fg_color=CARD2)
        bar.pack(fill="x", padx=18)
        bar.set(rate / 100)
        label(quick, f"{rate}% checked in", 11, WHITE).pack(anchor="w", padx=18, pady=8)

    # ---------------- EVENTS ----------------
    def events_page(self):
        self.header("Events", "Create, organize and manage your events.",
                    "+  Add Event", self.open_event_form)
        tools = ctk.CTkFrame(self.main, fg_color="transparent")
        tools.pack(fill="x", padx=30, pady=(0, 12))
        self.event_query = entry(tools, "Search events or venues...", 300)
        self.event_query.pack(side="left")
        self.event_query.bind("<KeyRelease>", lambda e: self.load_events())  # live search
        self.event_filter = option_menu(tools, ["All", "Upcoming", "Past"], 120,
                                        lambda _: self.load_events())
        self.event_filter.pack(side="left", padx=8)
        button(tools, "Clear", self.clear_event_search, False, 80).pack(side="left")

        self.event_list = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        self.event_list.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        self.load_events()

    def clear_event_search(self):
        self.event_query.delete(0, "end")
        self.event_filter.set("All")
        self.load_events()

    def load_events(self):
        clear(self.event_list)
        q = self.event_query.get().lower().strip()
        mode = self.event_filter.get()
        today = date.today().isoformat()
        matches = [
            e for e in events
            if (q in e["name"].lower() or q in e["venue"].lower())
            and (mode == "All"
                 or (mode == "Upcoming" and e["date"] >= today)
                 or (mode == "Past" and e["date"] < today))
        ]
        matches.sort(key=lambda e: e["date"])
        if not matches:
            label(self.event_list, "No events found.", 13, MUTED).pack(pady=35)
            return
        for e in matches:
            card = ctk.CTkFrame(self.event_list, fg_color=CARD, corner_radius=13,
                                border_width=1, border_color="#393126")
            card.pack(fill="x", padx=5, pady=7)
            ctk.CTkFrame(card, fg_color=GOLD, width=5, corner_radius=3).pack(
                side="left", fill="y", padx=(0, 14), pady=12)
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=13)
            label(info, e["name"], 16, WHITE, True).pack(anchor="w")
            label(info, f'{e["date"]}   •   {e["venue"]}', 11, MUTED).pack(anchor="w", pady=4)
            if e["description"]:
                label(info, e["description"], 10, MUTED).pack(anchor="w")
            count = sum(g["event_id"] == e["id"] for g in guests)
            label(info, f'{count} guests   •   Budget: ₹{e["budget"]:,.0f}', 10, GOLD).pack(anchor="w", pady=(5, 0))

            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.pack(side="right", padx=14)
            text, color = when_text(e["date"])
            label(actions, text, 11, color, True).pack(pady=(0, 4))
            button(actions, "Edit", lambda item=e: self.open_event_form(item), False, 65).pack(pady=3)
            button(actions, "Delete", lambda item=e: self.delete_event(item), False, 65).pack(pady=3)

    def open_event_form(self, event=None):
        win = open_modal(self, "Event details", "460x555")
        label(win, "EDIT EVENT" if event else "CREATE AN EVENT", 21, GOLD, True).pack(anchor="w", padx=28, pady=(24, 5))
        label(win, "Fill in the details below.", 11, MUTED).pack(anchor="w", padx=28, pady=(0, 15))

        fields = {}
        specs = [
            ("Name", "Event name"),
            ("Date", "YYYY-MM-DD"),
            ("Venue", "Event venue"),
            ("Description", "Short description"),
            ("Budget", "Budget in ₹")
        ]
        for key, hint in specs:
            label(win, key, 11, MUTED, True).pack(anchor="w", padx=30, pady=(7, 4))
            fields[key] = entry(win, hint, 395)
            fields[key].pack(padx=30)
        if event:
            vals = [event["name"], event["date"], event["venue"],
                    event["description"], str(event["budget"])]
            for (key, _), val in zip(specs, vals):
                fields[key].insert(0, val)

        def save():
            name = fields["Name"].get().strip()
            d = fields["Date"].get().strip()
            venue = fields["Venue"].get().strip()
            if not name or not venue:
                messagebox.showwarning("Missing details", "Event name and venue are required.", parent=win)
                return
            try:
                datetime.strptime(d, "%Y-%m-%d")
                budget = float(fields["Budget"].get().replace(",", "") or 0)
                if budget < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid details",
                                     "Use a valid date (YYYY-MM-DD) and a non-negative budget.", parent=win)
                return
            desc = fields["Description"].get().strip()
            if event:
                event.update(name=name, date=d, venue=venue, description=desc, budget=budget)
            else:
                events.append({"id": next_id(events), "name": name, "date": d,
                               "venue": venue, "description": desc, "budget": budget})
            save_data()
            win.destroy()
            self.refresh()

        button(win, "Save Event", save, True, 395).pack(padx=30, pady=20)

    def delete_event(self, event):
        n = sum(g["event_id"] == event["id"] for g in guests)
        if messagebox.askyesno("Delete event",
                               f'Delete "{event["name"]}" and its {n} guest registration(s)?'):
            events[:] = [e for e in events if e["id"] != event["id"]]
            guests[:] = [g for g in guests if g["event_id"] != event["id"]]
            save_data()
            self.refresh()

    # ---------------- GUESTS ----------------
    def guests_page(self):
        self.header("Guests", "Manage registrations, RSVP and attendance.",
                    "+  Add Guest", self.open_guest_form)
        tools = ctk.CTkFrame(self.main, fg_color="transparent")
        tools.pack(fill="x", padx=30, pady=(0, 12))
        self.guest_query = entry(tools, "Search guests or events...", 300)
        self.guest_query.pack(side="left")
        self.guest_query.bind("<KeyRelease>", lambda e: self.load_guests())  # live search
        self.guest_filter = option_menu(tools, ["All statuses"] + RSVP_OPTIONS, 150,
                                        lambda _: self.load_guests())
        self.guest_filter.pack(side="left", padx=8)
        button(tools, "Clear", self.clear_guest_search, False, 80).pack(side="left")
        button(tools, "Export CSV", self.export_guests, False, 110).pack(side="right")

        self.guest_summary = label(self.main, "", 11, MUTED)
        self.guest_summary.pack(anchor="w", padx=34, pady=(0, 6))
        self.guest_list = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        self.guest_list.pack(fill="both", expand=True, padx=25, pady=(0, 10))
        self.load_guests()

    def clear_guest_search(self):
        self.guest_query.delete(0, "end")
        self.guest_filter.set("All statuses")
        self.load_guests()

    def load_guests(self):
        clear(self.guest_list)
        q = self.guest_query.get().lower().strip()
        status = self.guest_filter.get()
        self.visible_guests = [
            g for g in guests
            if (q in g["name"].lower() or q in g["email"].lower()
                or q in self.event_name(g["event_id"]).lower())
            and (status == "All statuses" or g["rsvp"] == status)
        ]
        checked = sum(g["attended"] for g in self.visible_guests)
        self.guest_summary.configure(
            text=f"Showing {len(self.visible_guests)} of {len(guests)} guests  •  {checked} checked in")

        if not self.visible_guests:
            label(self.guest_list, "No guests found.", 13, MUTED).pack(pady=35)
            return
        for g in self.visible_guests:
            card = ctk.CTkFrame(self.guest_list, fg_color=CARD, corner_radius=12)
            card.pack(fill="x", padx=5, pady=6)
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=15, pady=12)
            label(info, g["name"], 14, WHITE, True).pack(anchor="w")
            label(info, f'{g["email"] or "No email"}   •   {g["phone"] or "No phone"}', 10, MUTED).pack(anchor="w", pady=3)
            line = ctk.CTkFrame(info, fg_color="transparent")
            line.pack(anchor="w")
            label(line, f'{self.event_name(g["event_id"])}   •   ', 10, GOLD).pack(side="left")
            label(line, g["rsvp"], 10, RSVP_COLORS.get(g["rsvp"], MUTED), True).pack(side="left")
            label(card, "CHECKED IN" if g["attended"] else "NOT CHECKED IN", 10,
                  GREEN if g["attended"] else MUTED, True).pack(side="left", padx=12)

            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.pack(side="right", padx=12)
            button(actions, "Undo" if g["attended"] else "Check in",
                   lambda item=g: self.toggle_check_in(item),
                   not g["attended"], 85).pack(pady=3)
            row = ctk.CTkFrame(actions, fg_color="transparent")
            row.pack(pady=3)
            button(row, "Edit", lambda item=g: self.open_guest_form(item), False, 55).pack(side="left", padx=(0, 4))
            button(row, "Delete", lambda item=g: self.delete_guest(item), False, 62).pack(side="left")

    def open_guest_form(self, guest=None):
        if not events:
            messagebox.showinfo("No events", "Create an event before adding guests.")
            return
        win = open_modal(self, "Guest details", "440x480")
        label(win, "EDIT GUEST" if guest else "REGISTER A GUEST", 21, GOLD, True).pack(anchor="w", padx=28, pady=(25, 5))
        label(win, "Add attendee details and choose an event.", 11, MUTED).pack(anchor="w", padx=28, pady=(0, 15))

        fields = {}
        for key, hint in [("Name", "Full name"), ("Email", "Email address"), ("Phone", "Phone number")]:
            label(win, key, 11, MUTED, True).pack(anchor="w", padx=30, pady=(8, 4))
            fields[key] = entry(win, hint, 380)
            fields[key].pack(padx=30)

        label(win, "Event", 11, MUTED, True).pack(anchor="w", padx=30, pady=(13, 4))
        choices = {f'{e["name"]}  ({e["date"]})': e["id"] for e in events}
        event_choice = option_menu(win, list(choices.keys()), 380)
        event_choice.pack(padx=30)

        label(win, "RSVP status", 11, MUTED, True).pack(anchor="w", padx=30, pady=(12, 4))
        rsvp = option_menu(win, RSVP_OPTIONS, 380)
        rsvp.pack(padx=30)

        if guest:
            fields["Name"].insert(0, guest["name"])
            fields["Email"].insert(0, guest["email"])
            fields["Phone"].insert(0, guest["phone"])
            for text, eid in choices.items():
                if eid == guest["event_id"]:
                    event_choice.set(text)
            rsvp.set(guest["rsvp"])

        def save():
            name = fields["Name"].get().strip()
            email = fields["Email"].get().strip()
            phone = fields["Phone"].get().strip()
            if not name:
                messagebox.showwarning("Missing name", "Guest name is required.", parent=win)
                return
            if email and ("@" not in email or "." not in email.split("@")[-1]):
                messagebox.showerror("Invalid email", "Please enter a valid email address.", parent=win)
                return
            if phone and not phone.replace("+", "").replace(" ", "").replace("-", "").isdigit():
                messagebox.showerror("Invalid phone", "Phone number can only contain digits, spaces, + and -.", parent=win)
                return
            data = {"name": name, "email": email, "phone": phone,
                    "event_id": choices[event_choice.get()], "rsvp": rsvp.get()}
            if guest:
                guest.update(data)
            else:
                guests.append({"id": next_id(guests), **data, "attended": False})
            save_data()
            win.destroy()
            self.refresh()

        button(win, "Save Guest", save, True, 380).pack(padx=30, pady=20)

    def toggle_check_in(self, guest):
        guest["attended"] = not guest["attended"]
        save_data()
        self.load_guests()

    def delete_guest(self, guest):
        if messagebox.askyesno("Delete guest", f'Remove {guest["name"]} from the guest list?'):
            guests.remove(guest)
            save_data()
            self.load_guests()

    def export_guests(self):
        if not self.visible_guests:
            messagebox.showinfo("Nothing to export", "There are no guests in the current view.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile="eventify_guests.csv",
            filetypes=[("CSV file", "*.csv")])
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Name", "Email", "Phone", "Event", "RSVP", "Checked in"])
                for g in self.visible_guests:
                    w.writerow([g["name"], g["email"], g["phone"],
                                self.event_name(g["event_id"]), g["rsvp"],
                                "Yes" if g["attended"] else "No"])
            messagebox.showinfo("Exported", f"Saved {len(self.visible_guests)} guests to:\n{path}")
        except OSError as err:
            messagebox.showerror("Export failed", str(err))

    # ---------------- ANALYTICS ----------------
    def analytics_page(self):
        self.header("Analytics", "A snapshot of event registrations and attendance.")
        total = len(guests)
        attended = sum(g["attended"] for g in guests)
        confirmed = sum(g["rsvp"] == "Confirmed" for g in guests)
        budget = sum(e["budget"] for e in events)
        rate = round(attended / total * 100) if total else 0

        body = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=(0, 15))

        stats = ctk.CTkFrame(body, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 16))
        self.stat_card(stats, "Events created", len(events), "All events")
        self.stat_card(stats, "Registered guests", total, "Across all events")
        self.stat_card(stats, "Confirmed RSVPs", confirmed, "Confirmed attendees")
        self.stat_card(stats, "Total budget", f"₹{budget:,.0f}", "Combined event budgets")

        attendance = ctk.CTkFrame(body, fg_color=CARD, corner_radius=14)
        attendance.pack(fill="x", padx=6, pady=(0, 14))
        label(attendance, "ATTENDANCE OVERVIEW", 13, GOLD, True).pack(anchor="w", padx=20, pady=(18, 8))
        label(attendance, f"{attended} of {total} guests checked in  •  {rate}%", 13, WHITE).pack(anchor="w", padx=20, pady=(0, 12))
        bar = ctk.CTkProgressBar(attendance, progress_color=GOLD, fg_color=CARD2, height=13)
        bar.pack(fill="x", padx=20, pady=(0, 20))
        bar.set(rate / 100)

        rsvp_panel = ctk.CTkFrame(body, fg_color=CARD, corner_radius=14)
        rsvp_panel.pack(fill="x", padx=6, pady=(0, 14))
        label(rsvp_panel, "RSVP BREAKDOWN", 13, GOLD, True).pack(anchor="w", padx=20, pady=(18, 8))
        for status in RSVP_OPTIONS:
            count = sum(g["rsvp"] == status for g in guests)
            row = ctk.CTkFrame(rsvp_panel, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=5)
            label(row, status, 12, WHITE, True).pack(side="left")
            label(row, str(count), 12, RSVP_COLORS[status], True).pack(side="right")
            b = ctk.CTkProgressBar(rsvp_panel, progress_color=RSVP_COLORS[status], fg_color=CARD2, height=8)
            b.pack(fill="x", padx=20, pady=(0, 6))
            b.set(count / total if total else 0)
        ctk.CTkFrame(rsvp_panel, fg_color="transparent", height=8).pack()

        breakdown = ctk.CTkFrame(body, fg_color=CARD, corner_radius=14)
        breakdown.pack(fill="x", padx=6, pady=(0, 10))
        label(breakdown, "EVENT BUDGET BREAKDOWN", 13, GOLD, True).pack(anchor="w", padx=20, pady=18)
        if not events:
            label(breakdown, "Create events to see budget insights.", 12, MUTED).pack(anchor="w", padx=20, pady=(0, 18))
        for e in sorted(events, key=lambda x: x["budget"], reverse=True):
            n = sum(g["event_id"] == e["id"] for g in guests)
            checked = sum(g["event_id"] == e["id"] and g["attended"] for g in guests)
            share = e["budget"] / budget if budget else 0
            row = ctk.CTkFrame(breakdown, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=(8, 2))
            label(row, e["name"], 12, WHITE, True).pack(side="left")
            label(row, f'₹{e["budget"]:,.0f}  ({share:.0%})', 12, GOLD).pack(side="right")
            b = ctk.CTkProgressBar(breakdown, progress_color=GOLD, fg_color=CARD2, height=8)
            b.pack(fill="x", padx=20, pady=(0, 2))
            b.set(share)
            per_guest = f"₹{e['budget'] / n:,.0f} per guest" if n else "No guests yet"
            label(breakdown, f"{n} guests  •  {checked} checked in  •  {per_guest}", 10, MUTED).pack(anchor="w", padx=20, pady=(0, 8))
        ctk.CTkFrame(breakdown, fg_color="transparent", height=8).pack()


if __name__ == "__main__":
    app = Eventify()
    app.mainloop()