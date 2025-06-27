# Xert Home Assistant Integration Installation Guide

## Prerequisites

1. Home Assistant installed and running
2. Xert Online account with valid credentials
3. HACS (Home Assistant Community Store) installed (recommended)

## Installation Methods

### Method 1: HACS Installation (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the "+" button
4. Search for "Xert Online"
5. Click "Download"
6. Restart Home Assistant

### Method 2: Manual Installation

1. Download the `xert` folder from this repository
2. Copy it to your `custom_components` directory in your Home Assistant config folder
3. Ensure the structure looks like: `config/custom_components/xert/`
4. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services**
2. Click **"Add Integration"** in the bottom right
3. Search for **"Xert Online"**
4. Enter your Xert Online username and password
5. Click **Submit**

The integration will:
- Authenticate with Xert Online
- Set up 5 main sensor entities
- Begin polling for data every 15 minutes

## Entity Overview

After setup, you'll have these entities:

| Entity | Purpose | Primary State | Key Attributes |
|--------|---------|---------------|----------------|
| `sensor.xert_fitness_status` | Current fitness metrics | Training Load | Threshold Power, Peak Power, Training Status |
| `sensor.xert_training_progress` | Training progression | Daily XSS | Weekly/Monthly XSS, Focus, Progression |
| `sensor.xert_workout_manager` | Workout recommendations | Available Workouts | Recommended workout details |
| `sensor.xert_recent_activity` | Latest activity data | Activity Name | Duration, XSS, Breakthrough status |
| `sensor.xert_token_status` | API connection status | Token Validity | Expiry, refresh status |

## Using the Entities

### In Automations
```yaml
# Example: Alert on training status change
automation:
  - alias: "Training Status Alert"
    trigger:
      platform: state
      entity_id: sensor.xert_fitness_status
      attribute: training_status
    action:
      service: notify.mobile_app
      data:
        message: "Training status changed to {{ trigger.to_state.attributes.training_status }}"
```

### In Templates
```yaml
# Example: Power-to-weight ratio
template:
  sensor:
    - name: "Power to Weight Ratio"
      state: >
        {% set tp = state_attr('sensor.xert_fitness_status', 'threshold_power') | float(0) %}
        {{ (tp / 70) | round(2) }}  # Replace 70 with your weight
      unit_of_measurement: "W/kg"
```

### In Dashboards
```yaml
# Example: Entity card
type: entities
entities:
  - sensor.xert_fitness_status
  - sensor.xert_training_progress
  - sensor.xert_workout_manager
```

## Troubleshooting

### Common Issues

1. **"Cannot Connect" Error**
   - Check your internet connection
   - Verify Xert Online is accessible
   - Check Home Assistant logs for details

2. **"Invalid Auth" Error**
   - Verify your Xert username and password
   - Try logging into Xert Online manually to confirm credentials

3. **"Token Expired" Status**
   - The integration will automatically refresh tokens
   - If issues persist, remove and re-add the integration

4. **No Data in Entities**
   - Check `sensor.xert_token_status` for API issues
   - Verify you have recent activities in your Xert account
   - Check Home Assistant logs for API errors

### Log Information

Enable debug logging by adding to `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.xert: debug
```

## Data Privacy

- The integration stores only OAuth tokens locally
- No training data is stored in Home Assistant beyond current values
- All communication uses HTTPS
- Tokens are automatically refreshed to maintain security

## Support

For issues specific to this integration:
- Check the Home Assistant logs
- Verify your Xert account is active and accessible
- Ensure you have recent training data in Xert

For Xert-specific issues:
- Contact Xert support at support@xertonline.com
- Check Xert's API status and documentation