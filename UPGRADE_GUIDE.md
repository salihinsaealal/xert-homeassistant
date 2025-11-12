# Upgrade Guide: v1.x → v2.0.0

## 🎉 Welcome to v2.0.0!

This major update brings **seamless re-authentication** and many quality-of-life improvements. No more deleting and re-adding the integration when tokens expire!

---

## ⚡ Quick Upgrade (TL;DR)

1. **Update** the integration via HACS or manually
2. **Restart** Home Assistant
3. **Done!** Everything works automatically

**No configuration changes needed. No data loss. No manual steps.**

---

## 📋 What's New in v2.0.0

### 🔐 Seamless Re-authentication
- **Before:** Token expires → Integration breaks → Delete & re-add
- **After:** Token expires → Notification appears → Enter password → Fixed!

### 💾 Token Persistence
- Tokens now survive Home Assistant restarts
- Refreshed tokens are automatically saved
- No more "lost sessions" after reboot

### 🛠️ New Services
- `xert.refresh_data` - Manually refresh data
- `xert.download_workout` - Download workout files

### 🔍 Diagnostics
- Download integration diagnostics for troubleshooting
- Access via Settings → Devices & Services → Xert → ⋮ → Download diagnostics

### 🎯 Better Error Handling
- Clear error messages
- Automatic recovery from network issues
- Proactive token refresh (1 hour before expiry)

---

## 🔄 Upgrade Process

### Via HACS (Recommended)

1. **Open HACS**
   - Go to HACS in your Home Assistant sidebar

2. **Update Integration**
   - Find "Xert Online" in your installed integrations
   - Click "Update" if available
   - Or go to the repository and click "Redownload"

3. **Restart Home Assistant**
   - Settings → System → Restart

4. **Verify**
   - Go to Settings → Devices & Services
   - Check that Xert integration shows "Configured"
   - Verify sensors are updating

### Manual Installation

1. **Backup Current Installation** (optional but recommended)
   ```bash
   cp -r custom_components/xert custom_components/xert.backup
   ```

2. **Download v2.0.0**
   - Download from GitHub releases
   - Or clone the repository

3. **Replace Files**
   ```bash
   cp -r xert-homeassistant/custom_components/xert custom_components/
   ```

4. **Restart Home Assistant**

5. **Verify Installation**
   - Check that version shows 2.0.0
   - Verify sensors are working

---

## ✅ Post-Upgrade Checklist

After upgrading, verify these items:

- [ ] All 6 sensors are present and updating
- [ ] Token status sensor shows "Valid"
- [ ] No errors in Home Assistant logs
- [ ] Dashboard cards display correctly
- [ ] Entity IDs remain the same (no breaking changes)

---

## 🆕 Using New Features

### Re-authentication (When Needed)

If your tokens expire or become invalid:

1. **You'll see a notification** in Home Assistant
2. **Go to Settings → Devices & Services**
3. **Look for Xert integration** with a "Configure" button
4. **Click Configure** and enter your password
5. **Done!** Integration recovers automatically

### Manual Data Refresh

Use the new service to refresh data on demand:

```yaml
service: xert.refresh_data
```

Or in an automation:
```yaml
automation:
  - alias: "Refresh Xert Data"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: xert.refresh_data
```

### Download Workouts

Download your WOTD or any workout:

```yaml
service: xert.download_workout
data:
  workout_id: "vovdxww5i7fzqbun"  # Get from sensor.username_wotd
  format: "zwo"  # or "erg"
```

### Diagnostics

If you encounter issues:

1. Go to **Settings → Devices & Services**
2. Click on **Xert** integration
3. Click **⋮** (three dots)
4. Select **Download diagnostics**
5. Share the file when reporting issues

---

## 🔧 Troubleshooting

### Issue: Integration Shows "Failed to Setup"

**Solution:**
1. Check Home Assistant logs for specific error
2. Enable debug logging:
   ```yaml
   logger:
     logs:
       custom_components.xert: debug
   ```
3. Restart Home Assistant
4. Check logs again for detailed error

### Issue: Sensors Show "Unavailable"

**Solution:**
1. Check `sensor.[username]_token_status`
2. If token is expired, reauth flow should trigger
3. If not, manually trigger reauth:
   - Settings → Devices & Services → Xert → Configure

### Issue: "Token Refresh Failed: 400"

**Solution:**
This is the exact issue v2.0.0 fixes! The reauth flow should trigger automatically.

1. Look for notification in Home Assistant
2. Go to Settings → Devices & Services
3. Click "Configure" on Xert integration
4. Enter your password
5. Integration recovers

### Issue: Old Tokens Not Working After Upgrade

**Solution:**
If your tokens were already expired before upgrade:

1. The integration will detect this on first update
2. Reauth flow will trigger automatically
3. Enter your password when prompted
4. Fresh tokens will be generated

---

## 🔄 Rollback (If Needed)

If you need to rollback to v1.x:

1. **Restore Backup** (if you made one)
   ```bash
   rm -rf custom_components/xert
   mv custom_components/xert.backup custom_components/xert
   ```

2. **Or Reinstall v1.x**
   - Download v1.0.5 from GitHub releases
   - Replace files in `custom_components/xert/`

3. **Restart Home Assistant**

**Note:** v2.0.0 is backward compatible. Rollback should only be needed in rare cases.

---

## 📊 Comparison: v1.x vs v2.0.0

| Feature | v1.x | v2.0.0 |
|---------|------|--------|
| Token Refresh | ✅ Yes | ✅ Yes |
| Token Persistence | ❌ No | ✅ Yes |
| Re-authentication | ❌ Manual (delete/re-add) | ✅ Automatic |
| Proactive Refresh | ❌ No | ✅ Yes (1hr before expiry) |
| Services | ❌ No | ✅ 2 services |
| Diagnostics | ❌ No | ✅ Yes |
| Error Handling | ⚠️ Basic | ✅ Enhanced |
| Thread Safety | ⚠️ Basic | ✅ Lock-protected |
| Documentation | ⚠️ Basic | ✅ Comprehensive |

---

## 🎓 What Changed Under the Hood

### For Developers

**Config Entry Structure:**
```python
# v1.x
{
    "username": "user",
    "access_token": "token",
    "refresh_token": "refresh",
    "expires_in": 604800
}

# v2.0.0 (backward compatible)
{
    "username": "user",
    "access_token": "token",
    "refresh_token": "refresh",
    "expires_in": 604800,
    "token_expires_at": "2024-11-19T12:00:00+00:00"  # NEW
}
```

**Error Handling:**
```python
# v1.x
raise UpdateFailed("Token refresh failed")

# v2.0.0
raise ConfigEntryAuthFailed("Token refresh failed")  # Triggers reauth
```

**Token Refresh:**
```python
# v1.x
if token_expired:
    refresh()  # At expiry

# v2.0.0
if token_expires_in_1_hour:
    refresh()  # Proactive
```

---

## 🆘 Getting Help

### Before Reporting Issues

1. **Check logs** with debug logging enabled
2. **Download diagnostics** from the integration
3. **Try reauth** if it's a token issue
4. **Check GitHub issues** for similar problems

### Reporting Issues

Include:
- Home Assistant version
- Integration version (should be 2.0.0)
- Error logs (with debug enabled)
- Diagnostics file (redact sensitive info)
- Steps to reproduce

**GitHub Issues:** https://github.com/salihinsaealal/xert-homeassistant/issues

---

## 🎉 Enjoy v2.0.0!

This update represents a major improvement in reliability and user experience. You should never need to delete and re-add the integration again!

**Questions?** Open a discussion on GitHub!

**Found a bug?** Open an issue with details!

**Love the update?** Consider [buying me a coffee](https://coff.ee/salihin) ☕

---

**Happy Training! 💪**
