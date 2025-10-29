# ad-growatt

An AppDaemon App Example for controlling Growatt Inverters via HomeAssistant.

This is a further development of the original code by mjdyson. The following are the main changes:
- Ability to control Grid First, Battery First and Export Limit
- UI now consists of one Lovelace card
- Improved error handling, eg. handling the lock-out by displaying a message
- Can only handle one inverter, specify Device Serial Number in secrets together with username and password for inverter

!! Growatt API was updated during September 2023. That update pretty much broke all Growatt integrations. Growatt is not offering any solutions, they focus on blocking enthusiast trying to make Growatt products work with home automation. Currently this code (AD Growatt) is not working due to Growatt servers blocking access. It might work again some time in the future and everyone are very welcome to try to use my code for future versions.
Personally I gave up on Growatt servers and will be using Solar Assistant going forward. So Long, and Thanks for All the Fish :)

# Versions
v0.1 July 13. 2023: initial release

v0.2 August 8. 2023: Seperates the save functions to avoid timeouts and API overload. Update config.yaml and growatt_app.py files + Lovelace card. Automations have to be changed to conform with new save

v.03 August 14. 2023: Control of "Grid first, discharge power" implemented together with other improvements, eg. more robustnness when saving; now retrying 5 times, if theres's a problem with Growatt server. Remember to update the Lovelace card with the code below.

v.04 September 19. 2023: Charge power setting added, thanks to Jasperwolsing (added getting charge power on top of the Jasperwolsing change). Services adgw_battery_first_on and adgw_battery_first_off added to control the battery first state on/off from scripts. 

v.041 September 26. 2023: Changed initialization to more correctly show if there's a 50x error.

2023-December -> 2024, Lots of updates to fix what was broken, add some missing functions it now works pretty OK.
  Tested with a Growatt SPH 10k TL3 BH-UP (Hybrid) with Batteries

# Lovelace card
```
type: entities
entities:
  - entity: input_boolean.adgw_inverter_on
  - entity: input_button.adgw_set_inverter_settings_button
  - type: divider
  - entity: input_boolean.adgw_inverter_eps_on
  - entity: input_button.adgw_set_inverter_eps_settings_button
  - type: divider
  - entity: input_boolean.adgw_export_limit_on
  - entity: input_button.adgw_set_charge_settings_button_export
  - type: divider
  - entity: input_select.adgw_battery_charge_max_soc
  - entity: input_select.adgw_grid_charge_power
  - entity: input_boolean.adgw_ac_charge_on
  - entity: input_datetime.adgw_battery_first_time_slot_1_start
  - entity: input_datetime.adgw_battery_first_time_slot_1_end
  - entity: input_boolean.adgw_battery_first_time_slot_1_enabled
  - entity: input_datetime.adgw_battery_first_time_slot_2_start
  - entity: input_datetime.adgw_battery_first_time_slot_2_end
  - entity: input_boolean.adgw_battery_first_time_slot_2_enabled
  - entity: input_datetime.adgw_battery_first_time_slot_3_start
  - entity: input_datetime.adgw_battery_first_time_slot_3_end
  - entity: input_boolean.adgw_battery_first_time_slot_3_enabled
  - entity: input_button.adgw_set_charge_settings_button_battery_first
  - type: divider
  - entity: input_datetime.adgw_battery_first1_time_slot_4_start
  - entity: input_datetime.adgw_battery_first1_time_slot_4_end
  - entity: input_boolean.adgw_battery_first1_time_slot_4_enabled
  - entity: input_datetime.adgw_battery_first1_time_slot_5_start
  - entity: input_datetime.adgw_battery_first1_time_slot_5_end
  - entity: input_boolean.adgw_battery_first1_time_slot_5_enabled
  - entity: input_datetime.adgw_battery_first1_time_slot_6_start
  - entity: input_datetime.adgw_battery_first1_time_slot_6_end
  - entity: input_boolean.adgw_battery_first1_time_slot_6_enabled
  - entity: input_button.adgw_set_charge_settings_button_battery_first1
  - type: divider
  - entity: input_select.adgw_grid_discharge_stopped_soc
  - entity: input_select.adgw_grid_discharge_power
  - entity: input_datetime.adgw_grid_first_time_slot_1_start
  - entity: input_datetime.adgw_grid_first_time_slot_1_end
  - entity: input_boolean.adgw_grid_first_time_slot_1_enabled
  - entity: input_datetime.adgw_grid_first_time_slot_2_start
  - entity: input_datetime.adgw_grid_first_time_slot_2_end
  - entity: input_boolean.adgw_grid_first_time_slot_2_enabled
  - entity: input_datetime.adgw_grid_first_time_slot_3_start
  - entity: input_datetime.adgw_grid_first_time_slot_3_end
  - entity: input_boolean.adgw_grid_first_time_slot_3_enabled
  - entity: input_button.adgw_set_charge_settings_button_grid_first
  - type: divider
  - entity: input_datetime.adgw_grid_first1_time_slot_4_start
  - entity: input_datetime.adgw_grid_first1_time_slot_4_end
  - entity: input_boolean.adgw_grid_first1_time_slot_4_enabled
  - entity: input_datetime.adgw_grid_first1_time_slot_5_start
  - entity: input_datetime.adgw_grid_first1_time_slot_5_end
  - entity: input_boolean.adgw_grid_first1_time_slot_5_enabled
  - entity: input_datetime.adgw_grid_first1_time_slot_6_start
  - entity: input_datetime.adgw_grid_first1_time_slot_6_end
  - entity: input_boolean.adgw_grid_first1_time_slot_6_enabled
  - entity: input_button.adgw_set_charge_settings_button_grid_first1
  - type: divider
  - entity: input_select.adgw_load_bat_discharge_stop_soc
  - entity: input_button.adgw_set_charge_settings_button_load_first
  - type: divider
  - entity: input_button.adgw_get_charge_settings_button
  - entity: sensor.template_adgw_api_state
title: Full Inverter settings
show_header_toggle: false
```
![image](https://github.com/KasperHolchKragelund/ad-growatt/assets/127233863/884fef5f-f24a-4b08-b74e-34e9420f763d)

# Installation
The steps to set up is:

1. If you have the old Growatt integration installed, remove it, as it might trigger the server block on Growatt servers. For monitoring, use Grott https://github.com/johanmeijer/grott. This step is optional but will improve stability greatly.

2. Install AppDaemon from Add-ons in HA

3. Copy files from ad-growatt on Github to your config directory (/config on my HA Yellow, will use this path going foroward, but it might be different on your installation)

4. Modify /config/configuration.yaml to include
```
homeassistant:
  packages: !include_dir_named packages
```

5. Modify /config/secrets.yaml (or the /addon_configs/randomchars_appdaemon/secrets.yaml) to include:
```
growatt_username: X
growatt_password: X
growatt_device: X
```
Replacing X’s with login, password and Device Serial Number (found on main page of Growatt Server: Login Page https://server.growatt.com/)

6. Restart HA, or just reload HA configuration and restart AppDaemon

7. Create the Lovelace card, see code above

Enjoy controlling your Growatt inverter directly from HA !!


# Example of automation templates for automations.yaml
Automations can set the values on the Lovelace card and then push the button to Get or Save. Eg. the below example calls the script to turn on export limit under certain condition, eg. price low:
```
- id: 'XX'
  alias: Export Limit On
  description: When something happens, turn off export
  trigger:
    define your own trigger, eg. price from Nordpool
  action:
  - service: script.adgw_set_export_limit_on
    data: {}
  mode: single
```
And this example turns off export limit
```
- id: 'XX'
  alias: Export Limit Off
  description: When something happens, turn off export
  trigger:
    define your own trigger, eg. price from Nordpool
  action:
  - service: script.adgw_set_export_limit_off
    data: {}
  mode: single
```

# Disclaimer

The developers & maintainers of this library accept no responsibility for any damage, problems or issues that arise with your Growatt systems as a result of its use.

The library contains functions that allow you to modify the configuration of your plant & inverter which carries the ability to set values outside of normal operating parameters, therefore, settings should only be modified if you understand the consequences.

To the best of our knowledge only the settings functions perform modifications to your system and all other operations are read only. Regardless of the operation:

The library is used entirely at your own risk.

# Credit

Credit to the original authors at  
https://github.com/KasperHolchKragelund/ad-growatt
https://github.com/mjdyson/ad-growatt
https://github.com/indykoning/PyPi_GrowattServer/
https://github.com/muppet3000/PyPi_GrowattServer/
