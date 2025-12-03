# Officials Tracker - Streamlit Cloud Ready

Track government officials, positions, and media mentions.

## Quick Deploy to Streamlit Cloud

### 1. GitHub Desktop
- File > Add local repository
- Choose this folder
- Create repository (if needed)
- Publish repository (can be private)

### 2. Streamlit Cloud
- https://share.streamlit.io/
- Sign in with GitHub
- New app > Select your repository
- Main file: app.py
- Deploy

### 3. Share URL
Send app URL to your team: https://your-username-officials-tracker.streamlit.app

## Local Development

### Windows
```
START.bat
```

### Mac/Linux
```
chmod +x START.sh
./START.sh
```

Opens at: http://localhost:8501

## Import Data from CSV

```
python scripts/import_from_csv.py your_file.csv
```

Creates departments, subdepartments, positions, and persons automatically.

## Update Data

After importing new CSV:

GitHub Desktop:
1. Commit changes
2. Push origin

Streamlit auto-updates in 2-3 minutes.

## Optional: Password Protection

Add to top of app.py (after imports):
```python
import streamlit as st

def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("Incorrect password")
        return False
    else:
        return True

if not check_password():
    st.stop()
```

Then in Streamlit Cloud > Settings > Secrets:
```
password = "your_password"
```

## Structure

```
data/
├── departments.json       # Departments
├── subdepartments.json    # Subdepartments
├── positions/             # Positions
├── persons/               # People
└── mentions/              # Media mentions
```

## Requirements

- Python 3.8+
- Streamlit 1.30.0+
- See requirements.txt for full list
