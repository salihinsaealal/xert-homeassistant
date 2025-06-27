# Xert Online Home Assistant Integration

Integrate your [Xert Online](https://www.xertonline.com/) fitness and training data directly into [Home Assistant](https://www.home-assistant.io/).

## Features
- OAuth2 authentication with Xert Online
- 5 sensor entities:
  - Fitness Status
  - Training Progress
  - Workout Manager
  - Recent Activity
  - Token Status
- Automatic token refresh
- Data updates every 15 minutes
- Dashboard-ready entities

## Installation

### HACS (Recommended)
1. Add this repository to HACS as a custom integration.
2. Search for "Xert Online" in HACS > Integrations.
3. Install and restart Home Assistant.

### Manual
1. Copy the `xert` folder to your `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration
1. Go to **Settings > Devices & Services** in Home Assistant.
2. Click **Add Integration** and search for **Xert Online**.
3. Enter your Xert Online username and password.
4. Complete the setup.

## Entities
| Entity                        | Description                        |
|-------------------------------|------------------------------------|
| `sensor.xert_fitness_status`  | Current fitness metrics            |
| `sensor.xert_training_progress`| Training progression               |
| `sensor.xert_workout_manager` | Workout recommendations            |
| `sensor.xert_recent_activity` | Latest activity data               |
| `sensor.xert_token_status`    | API connection status              |

## Example Dashboard YAML
```yaml
# Add to your dashboard
- type: entities
  entities:
    - sensor.xert_fitness_status
    - sensor.xert_training_progress
    - sensor.xert_workout_manager
    - sensor.xert_recent_activity
    - sensor.xert_token_status
```

## Troubleshooting
- Check `sensor.xert_token_status` for API/auth issues.
- Enable debug logging in `configuration.yaml`:
  ```yaml
  logger:
    default: warning
    logs:
      custom_components.xert: debug
  ```
- For Xert account issues, contact [Xert support](mailto:support@xertonline.com).

## Privacy
- OAuth tokens are stored locally and refreshed automatically.
- No training data is stored beyond current values.

## License
MIT 