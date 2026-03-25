# Run Charts Generator — same page checklist

Use these exact steps so we're using the same files and server.

## 1. Open the project folder

In File Explorer, go to:

```
C:\Users\DP\OneDrive\Desktop\charts generator
```

You must run the app from this folder (or its `backend` subfolder). If your project lives somewhere else, tell me the exact path.

## 2. Start the backend

1. Open **PowerShell** or **Command Prompt**.
2. Go to the backend folder:
   ```powershell
   cd "C:\Users\DP\OneDrive\Desktop\charts generator\backend"
   ```
3. Start the server:
   ```powershell
   python app.py
   ```

You should see something like:

```
============================================================
Charts Generator — Backend
============================================================
Serving frontend from this file:
   C:\Users\DP\OneDrive\Desktop\charts generator\frontend\index.html
...
Open in browser:   http://localhost:5000
You should see a green bar at the top: 'App version: 2025-02-fresh'
============================================================
 * Running on http://127.0.0.1:5000
```

**Check:** The path under "Serving frontend from this file" must be the same as your real project path. If it shows a different drive or folder, you're running from another copy of the project.

## 3. Open the app in the browser

1. Open: **http://localhost:5000**
2. Do a **hard refresh** so the browser doesn’t use cache: **Ctrl + F5** (or Ctrl + Shift + R).

## 4. Confirm you’re on the latest file

At the **very top** of the page you should see a **dark green bar** with white text:

**"App version: 2025-02-fresh — if you see this, you are loading the correct file."**

- **If you see that bar** → You’re loading the right `index.html`. We’re on the same page.
- **If you don’t see it** → You’re either seeing a cached page or a different project copy. Try:
  - Hard refresh again (Ctrl + F5)
  - Or close the tab and open http://localhost:5000 again
  - Or try an incognito/private window: http://localhost:5000

## 5. Test with the dummy dataset

1. In **Step 1**, open the dropdown and choose **"Dummy (test data)"**.
2. In **Step 2**, choose **Pie Chart**.
3. In **Step 3**, choose **Category**.
4. You should get a chart (and maybe a category filter step). That confirms the flow works.

---

**If anything doesn’t match** (different path in the terminal, no green version bar, or no Dummy option), tell me exactly:

- The full path shown in the terminal under "Serving frontend from this file"
- Whether you see the green "App version: 2025-02-fresh" bar
- What you see in the Step 1 dropdown (e.g. "Choose a dataset...", "Dummy (test data)", or something else)

Then we can fix the path or copy so everything uses the same project.
