# ✦ Eventify – Event Management System

Eventify is a desktop application for planning events and managing guests,
built with Python and CustomTkinter. It has a modern dark theme with gold
accents and a sidebar for moving between pages.

## Features
- **Dashboard:** summary cards, upcoming events with countdowns, quick actions
- **Events:** create, edit, delete, search and filter (All / Upcoming / Past)
- **Guests:** register and edit guests, track RSVP status, check in or undo,
  search and filter, export the list to CSV
- **Analytics:** attendance rate, RSVP breakdown, budget share per event
  and cost per guest
- **Validation:** checks date format, budget, email and phone before saving
- **Auto-save:** data is stored in a local `eventify_data.json` file

## Tech stack
Python 3.13, CustomTkinter, tkinter, json, csv, datetime

## Run it
    pip install customtkinter
    python eventify.py

Requires Python with Tk 8.6 (the installer from python.org includes it).

## Screenshots
Add your screenshots here, for example: `![Dashboard](screenshots/dashboard.png)`
