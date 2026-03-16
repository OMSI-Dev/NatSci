# Configuration Integration Guide

This guide shows how to quickly integrate the configuration and constants systems into your existing SOS Control System.

## Quick Integration Steps

### Step 1: Create Your Configuration File

```bash
cd main\config
copy settings.json.example settings.json
```

Edit `settings.json` with your network settings:

```json
{
  "sos": {
    "ip": "10.0.0.16",
    "port": 2468,
    "user": "sos"
  },
  "pi": {
    "ip": "10.10.51.111",
    "port": 4096,
    "enabled": false
  },
  "paths": {
    "base_share": "\\\\sos2\\AuxShare"
  }
}
```

### Step 2: Modified Files

The following files have been updated to use the configuration system:

#### Updated: `sdc.py`
- Now loads configuration from `config/settings.json`
- Uses configured IP addresses and ports
- Validates configuration on startup
- Prints configuration summary

#### Updated: `engine.py`
- Uses configuration for SOS and Pi connections
- Uses constants for timeouts
- More maintainable with centralized settings

#### Updated: `audio_init.py`
- Reads paths from configuration
- Uses configured SOS server settings

#### Updated: `pp_init.py`
- Uses configured presentation paths
- More flexible for different environments

### Step 3: Running with Configuration

Simply run the system as before:

```bash
cd main
python sdc.py
```

The system will:
1. Load `config/settings.json`
2. Print configuration summary
3. Validate settings
4. Run normally with your configured values

### Configuration Benefits

✅ **Single File** - All network settings in one place  
✅ **Easy Deployment** - Copy config file to new environment  
✅ **Clear Values** - No hunting through code for IP addresses  
✅ **Validation** - Checks settings before starting  

## Customization

### Using Environment Variables

You can override settings with environment variables:

```powershell
$env:SOS_IP = "192.168.1.10"
$env:PI_ENABLED = "true"
python sdc.py
```

### Adding New Settings

To add new configuration values:

1. **Add to `config/settings.json.example`**:
   ```json
   "my_feature": {
     "enabled": true,
     "value": 100
   }
   ```

2. **Access in your code**:
   ```python
   from config import get_config
   config = get_config()
   
   if config.get('my_feature.enabled'):
       value = config.get('my_feature.value', 100)
   ```

## Troubleshooting

### Config file not found

**Error**: `No such file: config/settings.json`

**Solution**: Copy the example file:
```bash
copy config\settings.json.example config\settings.json
```

### Invalid configuration

**Error**: `Config error: Base share not accessible`

**Solution**: Check that network paths are correct and accessible from your PC.

### Using old hardcoded values

If you want to keep using hardcoded values in specific files, that's fine! The configuration system is backward compatible. Files that aren't updated will continue using their default values.

## Next Steps

Once you're comfortable with the configuration:

1. Configure for your specific environment
2. Deploy to other machines by copying `settings.json`
3. Customize overlay settings in the config file
4. Add your own configuration sections as needed

The system is now more maintainable and easier to deploy to different environments!
