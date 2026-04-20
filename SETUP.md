# ndMAX Orbit — GitHub Setup

## Step 1: Install Git (one time)

Download and install from: https://git-scm.com/download/win  
Accept all defaults during install.

---

## Step 2: Initialize this folder as the GitHub repo

Open **Command Prompt** or **PowerShell** and run these commands exactly:

```
cd "C:\Users\Stephanie.Klahre\Documents\PROJECT MANAGEMENT SYSTEM"

git init
git remote add origin https://github.com/stephanieklahrenetdocs/projectmanagement.git
git add .
git commit -m "initial commit: Orbit Client Hub"
git branch -M main
git push -u origin main
```

When it asks for credentials, sign in with your GitHub account.

---

## Step 3: Enable GitHub Pages

1. Go to: https://github.com/stephanieklahrenetdocs/projectmanagement/settings/pages
2. Under **Source**, select: **GitHub Actions**
3. Click **Save**

The first deploy will trigger automatically from the push in Step 2.  
Your live URL will be: **https://stephanieklahrenetdocs.github.io/projectmanagement/**

---

## Step 4: Add your CSV data

Copy your latest combined CSV export into the `data/` folder:

```
copy "C:\Users\Stephanie.Klahre\Downloads\combined_20260414.csv" "C:\Users\Stephanie.Klahre\Documents\PROJECT MANAGEMENT SYSTEM\data\combined.csv"
```

Then push it:

```
cd "C:\Users\Stephanie.Klahre\Documents\PROJECT MANAGEMENT SYSTEM"
git add data/combined.csv
git commit -m "data: add client CSV"
git push
```

The live dashboard at your GitHub Pages URL will now show all client data.

---

## Daily workflow (after setup)

### When you get a new CSV export:
```
copy "C:\Users\...\Downloads\combined_YYYYMMDD.csv" "...\PROJECT MANAGEMENT SYSTEM\data\combined.csv"
cd "C:\Users\Stephanie.Klahre\Documents\PROJECT MANAGEMENT SYSTEM"
git add data/combined.csv
git commit -m "data: refresh [date]"
git push
```

### Staircase health data (automatic):
The daily Claude Code scheduled task runs at 8am weekdays, pulls from Staircase AI,
and writes `data/snapshot.json`. When git is set up, it also pushes automatically.

---

## Repo structure

```
/
├── index.html                  ← Live dashboard (GitHub Pages entry point)
├── orbit_hub.html              ← Local copy (same file)
├── data/
│   ├── combined.csv           ← Latest CSV export (push when you get a new one)
│   └── snapshot.json          ← Daily Staircase data (auto-pushed by scheduled task)
├── .github/
│   └── workflows/
│       └── pages.yml          ← Auto-deploys to GitHub Pages on every push
├── scripts/
│   ├── 01_create_custom_fields.py
│   ├── 02_migrate_gcx.py
│   └── refresh_hub.py
├── skills/
│   └── ...
└── orbit-config.json
```

---

## Your live URL once set up:
**https://stephanieklahrenetdocs.github.io/projectmanagement/**
