# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.2] - 2024-11-12

### 🐛 Bug Fixes

- **Fixed device registry access error** - Integration now sets up correctly
- Fixed AttributeError when creating device
- Use correct async_get_device_registry import

**Impact:** Device grouping feature now works without errors!

---

## [2.0.1] - 2024-11-12

### ✨ Improvements

#### Device Grouping
- **All sensors now grouped under a single device** in Home Assistant
- Cleaner UI with all entities visible in one place
- Device shows:
  - Device name: "Xert Online - [username]"
  - Manufacturer: Xert Online
  - Model: API Client
  - Software version: Integration version
  - Configuration URL: Link to Xert Online

**Impact:** Much easier to view and manage all Xert entities!

---

## [2.0.0] - 2025-11-12

### 🎉 Major Features

#### Re-authentication Flow
- **Added seamless re-authentication** when tokens expire or become invalid
- No more need to delete and re-add the integration!
- Home Assistant will automatically prompt you to re-enter your password
- Fixes the critical "Token refresh failed: 400" error

#### Token Persistence
- **Tokens now persist across Home Assistant restarts**
- Refreshed tokens are automatically saved to config entry
- Token expiry timestamps are stored and tracked
- Proactive token refresh 1 hour before expiry

### ✨ New Features

#### Services
- **`xert.refresh_data`** - Manually trigger data refresh for all or specific integration
- **`xert.download_workout`** - Download workout files in ZWO or ERG format
  - Useful for syncing workouts to Zwift, TrainerRoad, etc.

#### Diagnostics
- **Added diagnostics platform** for easier troubleshooting
- View integration health, token status, and data state
- Access via Settings → Devices & Services → Xert → Download Diagnostics

### 🔧 Improvements

#### Enhanced Error Handling
- Proper distinction between authentication errors and network errors
- `ConfigEntryAuthFailed` exception triggers reauth flow automatically
- Better error messages and logging
- Detailed HTTP response logging for debugging

#### Token Management
- **Thread-safe token refresh** with asyncio locks
- Prevents concurrent refresh attempts
- Proactive refresh 1 hour before token expiry
- Handles clock skew and edge cases

#### Code Quality
- Complete type annotations
- Improved error handling throughout
- Better logging with debug/info/error levels
- More robust API request handling

### 🐛 Bug Fixes
- Fixed token refresh failures causing permanent integration breakage
- Fixed tokens not persisting after refresh
- Fixed race conditions in concurrent API calls
- Fixed token expiry calculation issues

### 📝 Documentation
- Added comprehensive troubleshooting guide
- Updated README with new features
- Added service documentation
- Added CHANGELOG for version tracking

---

## [1.0.5] - Previous Release
- Fixed HACS icon display issues
- Updated icon and logo files

## [1.0.2] - Previous Release
- Add recommended workout and details to workout_manager sensor
- Entity IDs now use username prefix

## [1.0.1] - Previous Release
- Bugfixes
- Entity_id prefix improvements
- Improved documentation
- Dashboard example

## [1.0.0] - Initial Release
- Initial release with basic sensor entities
- OAuth2 authentication
- 6 sensor entities (Fitness Status, Training Progress, Workout Manager, Recent Activity, Token Status, WOTD)
- Automatic token refresh
- Data updates every 15 minutes

---

## Upgrade Notes

### From 1.x to 2.0.0

**No action required!** The upgrade is seamless:

1. Update the integration via HACS or manually
2. Restart Home Assistant
3. Your existing tokens will continue to work
4. If tokens expire, you'll be prompted to re-authenticate (no need to delete integration)

**New Features Available:**
- Check out the new services in Developer Tools → Services
- Download diagnostics if you encounter any issues
- Enjoy worry-free token management!

---

## Future Roadmap

### Planned Features (Phase 3+)
- Binary sensors for training status alerts
- Adaptive update intervals based on training schedule
- Smart notifications for WOTD changes
- Training insights and visualization
- Calendar integration for scheduled workouts
- Workout automation capabilities

### Contributions Welcome!
Feel free to open issues or pull requests on [GitHub](https://github.com/salihinsaealal/xert-homeassistant).
