     cookies = {}
     if mfl_user_id:
         cookies["MFL_USER_ID"] = mfl_user_id
-        mfl_api_key = ""
+        # Only the assets endpoint rejects requests that carry both the
+        # cookie and the APIKEY at once. Every other endpoint needs the
+        # APIKEY present even when the cookie is set, so only clear it here.
+        if api_type == "assets":
+            mfl_api_key = ""

     url = f"https://{host}/{league_year}/export?TYPE={api_type}&L={league_id}&APIKEY={mfl_api_key}&JSON=1{extra_params}"
     response = requests.get(url, cookies=cookies, timeout=30)
     response.raise_for_status()
-    return response.json()
+    data = response.json()
+
+    # MFL can return a 200 with an error payload instead of real data
+    # (e.g. bad/missing auth). Without this check that error object gets
+    # silently loaded into BigQuery as if it were valid data.
+    if isinstance(data, dict) and "error" in data:
+        raise ValueError(f"MFL API error for TYPE={api_type}: {data['error']}")
+
+    return data
