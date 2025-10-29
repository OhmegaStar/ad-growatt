import hassapi as hass
import growattServer
import time

class AD_Growatt(hass.Hass):
    #ohm: 20240107 added api instance & session instance
    _instance = None
    _session = None

    def get_instance(self):
        self.log ('get_instance() begin')
        if self._instance is None:
            self.log ('get_instance() Create Instance')
            self._instance = growattServer.GrowattApi()
        return self._instance

    def get_session(self):
        self.log ('get_session() begin')
        if self._session is None:
            self.log ('get_session() Create Session')
            un = self.args["growatt_username"]
            pwd = self.args["growatt_password"]
            self._session = self.get_instance().login(un, pwd)
            if self._session['success']:
                self.log ('get_session() Session Created')
                self.set_state("sensor.template_adgw_api_state", state="Session Initialized")
                return self._session
            else:
                self.log ('get_session() Session Creation Error, session:')
                self.log (self._session)
                if self._session["msg"] == "507":
                    self.set_state("sensor.template_adgw_api_state", state="Locked " + self._session["lockDuration"] + " hours")
                else:
                    self.set_state("sensor.template_adgw_api_state", state="Error Msg " + self._session["msg"])
                return False
        else:
            self.log ('get_session() Return Cached Session')
            self.set_state("sensor.template_adgw_api_state", state="Cached Session Initialized")
            return self._session

    def initialize(self):
        self._instance = None
        self._session = None
        self.listen_state(self.get_mix_system_status_handler, "input_button.adgw_get_mix_system_status_button")
        self.listen_state(self.get_charge_settings_cached, "input_button.adgw_get_charge_settings_button_cache")
        self.listen_state(self.get_charge_settings, "input_button.adgw_get_charge_settings_button")
        self.listen_state(self.set_charge_settings_export_handler, "input_button.adgw_set_charge_settings_button_export")
        self.listen_state(self.set_charge_settings_battery_handler, "input_button.adgw_set_charge_settings_button_battery_first")
        self.listen_state(self.set_charge_settings_battery1_handler, "input_button.adgw_set_charge_settings_button_battery_first1")
        self.listen_state(self.set_charge_settings_grid_handler, "input_button.adgw_set_charge_settings_button_grid_first")
        self.listen_state(self.set_charge_settings_grid1_handler, "input_button.adgw_set_charge_settings_button_grid_first1")
        #ohm:20231225 added inverter settings handler
        self.listen_state(self.set_inverter_settings_handler, "input_button.adgw_set_inverter_settings_button")
        #ohm:20231225 added inverter EPS settings handler
        self.listen_state(self.set_inverter_eps_settings_handler, "input_button.adgw_set_inverter_eps_settings_button")

        #ohm:20231219 added load handler
        self.listen_state(self.set_charge_settings_load_handler, "input_button.adgw_set_charge_settings_button_load_first")
        #call get_charge_settings by pressing Get charge settings button
        self.call_service("input_button/press", entity_id="input_button.adgw_get_charge_settings_button")


##################################################
# get_charge_settings_cached() begin
# Return all Charge Settings (Grid First, Battery First etc. as well as general Inverter Settings)
# Uses session & API instance caching to reduce number of calls to the login method at the growatt server.
##################################################
    def get_charge_settings_cached(self, entity, attribute, old, new, kwargs):
        self.log ('get_charge_settings_cached() begin')
        device_sn = self.args["growatt_device"]
        api = self.get_instance()
        session = self.get_session()  # Ensure session creation
        if session != False:
            response = api.get_mix_inverter_settings(device_sn)
            if response['result'] == 1:
                self.set_state("sensor.template_adgw_api_state", state="Cached API & Session Get Success")
            else:
                self.set_state("sensor.template_adgw_api_state", state="Cached API & Session Get Error")
                self.log ('get_charge_settings_cached() response error: ')
                self.log (response)
                #destroy Session & Instance, so the next call will create a new session & instance
                self._session = None
                self._Instance = None
                return False
        else:
            #failed to establish session - return false
            #destroy Session & Instance, so the next call will create a new session & instance
            self._session = None
            self._Instance = None
            return False

        #Got a result process the mixbean properties

        #Debug Logging
        self.log ('----------------response object start-----------------------')
        self.log (response)
        self.log ('----------------response object end-----------------------')

        #List all key pairs from response to log. Comment out before going into production
#        for key, value in response['obj']['mixBean'].items():
#            self.log(f"{key}: {value}")

        # Populate Inverter Settings
        if (response['obj']['mixBean']['onOff']) == "1":
            self.set_state ("input_boolean.adgw_inverter_on", state = "on")
        else:
            self.set_state ("input_boolean.adgw_inverter_on", state = "off")

        #Populate EPS Enabled or not
        if (response['obj']['mixBean']['epsFunEn']) == "1":
            self.set_state ("input_boolean.adgw_inverter_eps_on", state = "on")
        else:
            self.set_state ("input_boolean.adgw_inverter_eps_on", state = "off")


        # Populate Export
        if (response['obj']['mixBean']['exportLimit']) == "1":
            self.set_state ("input_boolean.adgw_export_limit_on", state = "on")
        else:
            self.set_state ("input_boolean.adgw_export_limit_on", state = "off")

        # Populate Battery First
        self.set_state("input_select.adgw_battery_charge_max_soc", state = response['obj']['mixBean']['wchargeSOCLowLimit2'])
        self.set_state("input_select.adgw_grid_charge_power", state = response['obj']['mixBean']['chargePowerCommand'])
        
        if (response['obj']['mixBean']['acChargeEnable']) == "1":
            self.set_state ("input_boolean.adgw_ac_charge_on", state = "on")
        else:
            self.set_state ("input_boolean.adgw_ac_charge_on", state = "off")
        self.set_state("input_datetime.adgw_battery_first_time_slot_1_start", state = response['obj']['mixBean']['forcedChargeTimeStart1'])
        self.set_state("input_datetime.adgw_battery_first_time_slot_1_end", state = response['obj']['mixBean']['forcedChargeTimeStop1'])
        if (response['obj']['mixBean']['forcedChargeStopSwitch1']) == "1":
            self.set_state ("input_boolean.adgw_battery_first_time_slot_1_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_battery_first_time_slot_1_enabled", state = "off")

        self.set_state("input_datetime.adgw_battery_first_time_slot_2_start", state = response['obj']['mixBean']['forcedChargeTimeStart2'])
        self.set_state("input_datetime.adgw_battery_first_time_slot_2_end", state = response['obj']['mixBean']['forcedChargeTimeStop2'])
        if (response['obj']['mixBean']['forcedChargeStopSwitch2']) == "1":
            self.set_state ("input_boolean.adgw_battery_first_time_slot_2_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_battery_first_time_slot_2_enabled", state = "off")

        self.set_state("input_datetime.adgw_battery_first_time_slot_3_start", state = response['obj']['mixBean']['forcedChargeTimeStart3'])
        self.set_state("input_datetime.adgw_battery_first_time_slot_3_end", state = response['obj']['mixBean']['forcedChargeTimeStop3'])
        if (response['obj']['mixBean']['forcedChargeStopSwitch3']) == "1":
            self.set_state ("input_boolean.adgw_battery_first_time_slot_3_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_battery_first_time_slot_3_enabled", state = "off")

        # Populate Battery First1
        self.set_state("input_datetime.adgw_battery_first1_time_slot_4_start", state = response['obj']['mixBean']['forcedChargeTimeStart4'])
        self.set_state("input_datetime.adgw_battery_first1_time_slot_4_end", state = response['obj']['mixBean']['forcedChargeTimeStop4'])
        if (response['obj']['mixBean']['forcedChargeStopSwitch4']) == "1":
            self.set_state ("input_boolean.adgw_battery_first1_time_slot_4_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_battery_first1_time_slot_4_enabled", state = "off")

        self.set_state("input_datetime.adgw_battery_first1_time_slot_3_start", state = response['obj']['mixBean']['forcedChargeTimeStart5'])
        self.set_state("input_datetime.adgw_battery_first1_time_slot_3_end", state = response['obj']['mixBean']['forcedChargeTimeStop5'])
        if (response['obj']['mixBean']['forcedChargeStopSwitch5']) == "1":
            self.set_state ("input_boolean.adgw_battery_first1_time_slot_5_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_battery_first1_time_slot_5_enabled", state = "off")

        self.set_state("input_datetime.adgw_battery_first1_time_slot_6_start", state = response['obj']['mixBean']['forcedChargeTimeStart6'])
        self.set_state("input_datetime.adgw_battery_first1_time_slot_6_end", state = response['obj']['mixBean']['forcedChargeTimeStop6'])
        if (response['obj']['mixBean']['forcedChargeStopSwitch6']) == "1":
            self.set_state ("input_boolean.adgw_battery_first1_time_slot_6_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_battery_first1_time_slot_6_enabled", state = "off")

        # Populate Grid First
        self.set_state("input_select.adgw_grid_discharge_stopped_soc", state = response['obj']['mixBean']['wdisChargeSOCLowLimit2'])
        self.set_state("input_select.adgw_grid_discharge_power", state = response['obj']['mixBean']['wdisChargeSOCLowLimit1'])
        self.set_state("input_datetime.adgw_grid_first_time_slot_1_start", state = response['obj']['mixBean']['forcedDischargeTimeStart1'])
        self.set_state("input_datetime.adgw_grid_first_time_slot_1_end", state = response['obj']['mixBean']['forcedDischargeTimeStop1'])
        if (response['obj']['mixBean']['forcedDischargeStopSwitch1']) == "1":
            self.set_state ("input_boolean.adgw_grid_first_time_slot_1_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_grid_first_time_slot_1_enabled", state = "off")

        self.set_state("input_datetime.adgw_grid_first_time_slot_2_start", state = response['obj']['mixBean']['forcedDischargeTimeStart2'])
        self.set_state("input_datetime.adgw_grid_first_time_slot_2_end", state = response['obj']['mixBean']['forcedDischargeTimeStop2'])
        if (response['obj']['mixBean']['forcedDischargeStopSwitch2']) == "1":
            self.set_state ("input_boolean.adgw_grid_first_time_slot_2_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_grid_first_time_slot_2_enabled", state = "off")

        self.set_state("input_datetime.adgw_grid_first_time_slot_3_start", state = response['obj']['mixBean']['forcedDischargeTimeStart3'])
        self.set_state("input_datetime.adgw_grid_first_time_slot_3_end", state = response['obj']['mixBean']['forcedDischargeTimeStop3'])
        if (response['obj']['mixBean']['forcedDischargeStopSwitch3']) == "1":
            self.set_state ("input_boolean.adgw_grid_first_time_slot_3_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_grid_first_time_slot_3_enabled", state = "off")

        # Populate Grid First1

        self.set_state("input_datetime.adgw_grid_first1_time_slot_4_start", state = response['obj']['mixBean']['forcedDischargeTimeStart4'])
        self.set_state("input_datetime.adgw_grid_first1_time_slot_4_end", state = response['obj']['mixBean']['forcedDischargeTimeStop4'])
        if (response['obj']['mixBean']['forcedDischargeStopSwitch4']) == "1":
            self.set_state ("input_boolean.adgw_grid_first1_time_slot_4_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_grid_first1_time_slot_4_enabled", state = "off")

        self.set_state("input_datetime.adgw_grid_first1_time_slot_5_start", state = response['obj']['mixBean']['forcedDischargeTimeStart5'])
        self.set_state("input_datetime.adgw_grid_first1_time_slot_5_end", state = response['obj']['mixBean']['forcedDischargeTimeStop5'])
        if (response['obj']['mixBean']['forcedDischargeStopSwitch5']) == "1":
            self.set_state ("input_boolean.adgw_grid_first1_time_slot_5_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_grid_first1_time_slot_5_enabled", state = "off")

        self.set_state("input_datetime.adgw_grid_first1_time_slot_6_start", state = response['obj']['mixBean']['forcedDischargeTimeStart6'])
        self.set_state("input_datetime.adgw_grid_first1_time_slot_6_end", state = response['obj']['mixBean']['forcedDischargeTimeStop6'])
        if (response['obj']['mixBean']['forcedDischargeStopSwitch6']) == "1":
            self.set_state ("input_boolean.adgw_grid_first1_time_slot_6_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_grid_first1_time_slot_6_enabled", state = "off")



        #ohm 20231219 added load first battery discharge stop setting (should be between 10-100)
        # Populate Load First
        self.set_state("input_select.adgw_load_bat_discharge_stop_soc", state = response['obj']['mixBean']['loadFirstStopSocSet'])


##################################################
# get_charge_settings_cached() end
##################################################




##################################################
# get_mix_system_status() begin
# Return all Current Statistics for a Mix Ingerter
# Uses session & API instance caching to reduce number of calls to the login method at the growatt server.
##################################################
    def get_mix_system_status(self):
        self.log ('get_mix_system_status() begin')
        device_sn = self.args["growatt_device"]
        api = self.get_instance()
        session = self.get_session()  # Ensure session creation
        if session != False:
            response = api.mix_system_status(device_sn, 0)  # Secoond arg is plant Id but seems to be not used / ignored.
            if response['result'] == 1:
                self.set_state("sensor.template_adgw_api_state", state="Cached API & Session Get Success")
            else:
                self.set_state("sensor.template_adgw_api_state", state="Cached API & Session Get Error")
                self.log ('get_mix_system_status() response error: ')
                self.log (response)
                #destroy Session & Instance, so the next call will create a new session & instance
                self._session = None
                self._Instance = None
                return False
        else:
            #failed to establish session - return false
            #destroy Session & Instance, so the next call will create a new session & instance
            self._session = None
            self._Instance = None
            return False

        #Got a result process the mixbean properties

        #Debug Logging
        self.log ('----------------response object start-----------------------')
        self.log (response)
        self.log ('----------------response object end-----------------------')

        #List all key pairs from response to log. Comment out before going into production
#        for key, value in response['obj']['mixBean'].items():
#            self.log(f"{key}: {value}")


##################################################
# get_mix_system_status() end
##################################################

##################################################
# get_mix_system_status_handler() begin
# Orchestrates up to 5 attempts to get mix system stastus
##################################################
    def get_mix_system_status_handler(self, entity, attribute, old, new, kwargs):
        for attempt in range(5):
            if self.get_mix_system_status() == True:
                break

##################################################
# get_mix_system_status_handler() end
##################################################



    def get_charge_settings(self, entity, attribute, old, new, kwargs):
        #It's good practice to have those values stored in the secrets file
        un = self.args["growatt_username"]
        pwd = self.args["growatt_password"]
        device_sn = self.args["growatt_device"]
        #Query the server using the api
        api = growattServer.GrowattApi() #get an instance of the api, using a random string as the ID
        session = api.login(un, pwd) #login and return a session

        if session['success'] == True: #Handle error message
            self.set_state("sensor.template_adgw_api_state", state = "Initialized")
        else:
            if session["msg"] == "507":
                self.set_state("sensor.template_adgw_api_state", state = "Locked " + session["lockDuration"] + " hours")
            else:
                self.set_state("sensor.template_adgw_api_state", state = "Error Msg " + session["msg"])
            return False
        response = api.get_mix_inverter_settings(device_sn)

        #Debug Logging
#        self.log ('\n----------------response object start-----------------------\n')
#        self.log (response)
#        self.log ('\n----------------response object end-----------------------\n')

        #List all key pairs from response to log. Comment out before going into production
#        for key, value in response['obj']['mixBean'].items():
#            self.log(f"{key}: {value}")

        # Populate Inverter Settings
#        if (response['obj']['mixBean']['NOT_DEFINED_VALUE']) == "1":
#            self.set_state ("input_boolean.adgw_inverter_on", state = "on")
#        else:
#            self.set_state ("input_boolean.adgw_inverter_on", state = "off")
        #parameter for Inverter On / Off is unknown at this time, just set to on
        self.set_state ("input_boolean.adgw_inverter_on", state = "on")

        if (response['obj']['mixBean']['epsFunEn']) == "1":
            self.set_state ("input_boolean.adgw_inverter_eps_on", state = "on")
        else:
            self.set_state ("input_boolean.adgw_inverter_eps_on", state = "off")


        # Populate Export
        if (response['obj']['mixBean']['exportLimit']) == "1":
            self.set_state ("input_boolean.adgw_export_limit_on", state = "on")
        else:
            self.set_state ("input_boolean.adgw_export_limit_on", state = "off")

        # Populate Battery First
        self.set_state("input_select.adgw_battery_charge_max_soc", state = response['obj']['mixBean']['wchargeSOCLowLimit2'])
        self.set_state("input_select.adgw_grid_charge_power", state = response['obj']['mixBean']['chargePowerCommand'])
        
        if (response['obj']['mixBean']['acChargeEnable']) == "1":
            self.set_state ("input_boolean.adgw_ac_charge_on", state = "on")
        else:
            self.set_state ("input_boolean.adgw_ac_charge_on", state = "off")
        self.set_state("input_datetime.adgw_battery_first_time_slot_1_start", state = response['obj']['mixBean']['forcedChargeTimeStart1'])
        self.set_state("input_datetime.adgw_battery_first_time_slot_1_end", state = response['obj']['mixBean']['forcedChargeTimeStop1'])
        if (response['obj']['mixBean']['forcedChargeStopSwitch1']) == "1":
            self.set_state ("input_boolean.adgw_battery_first_time_slot_1_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_battery_first_time_slot_1_enabled", state = "off")

        self.set_state("input_datetime.adgw_battery_first_time_slot_2_start", state = response['obj']['mixBean']['forcedChargeTimeStart2'])
        self.set_state("input_datetime.adgw_battery_first_time_slot_2_end", state = response['obj']['mixBean']['forcedChargeTimeStop2'])
        if (response['obj']['mixBean']['forcedChargeStopSwitch2']) == "1":
            self.set_state ("input_boolean.adgw_battery_first_time_slot_2_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_battery_first_time_slot_2_enabled", state = "off")

        self.set_state("input_datetime.adgw_battery_first_time_slot_3_start", state = response['obj']['mixBean']['forcedChargeTimeStart3'])
        self.set_state("input_datetime.adgw_battery_first_time_slot_3_end", state = response['obj']['mixBean']['forcedChargeTimeStop3'])
        if (response['obj']['mixBean']['forcedChargeStopSwitch3']) == "1":
            self.set_state ("input_boolean.adgw_battery_first_time_slot_3_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_battery_first_time_slot_3_enabled", state = "off")

        # Populate Battery First1

        self.set_state("input_datetime.adgw_battery_first1_time_slot_4_start", state = response['obj']['mixBean']['forcedChargeTimeStart4'])
        self.set_state("input_datetime.adgw_battery_first1_time_slot_4_end", state = response['obj']['mixBean']['forcedChargeTimeStop4'])
        if (response['obj']['mixBean']['forcedChargeStopSwitch4']) == "1":
            self.set_state ("input_boolean.adgw_battery_first1_time_slot_4_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_battery_first1_time_slot_4_enabled", state = "off")

        self.set_state("input_datetime.adgw_battery_first1_time_slot_3_start", state = response['obj']['mixBean']['forcedChargeTimeStart5'])
        self.set_state("input_datetime.adgw_battery_first1_time_slot_3_end", state = response['obj']['mixBean']['forcedChargeTimeStop5'])
        if (response['obj']['mixBean']['forcedChargeStopSwitch5']) == "1":
            self.set_state ("input_boolean.adgw_battery_first1_time_slot_5_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_battery_first1_time_slot_5_enabled", state = "off")

        self.set_state("input_datetime.adgw_battery_first1_time_slot_6_start", state = response['obj']['mixBean']['forcedChargeTimeStart6'])
        self.set_state("input_datetime.adgw_battery_first1_time_slot_6_end", state = response['obj']['mixBean']['forcedChargeTimeStop6'])
        if (response['obj']['mixBean']['forcedChargeStopSwitch6']) == "1":
            self.set_state ("input_boolean.adgw_battery_first1_time_slot_6_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_battery_first1_time_slot_6_enabled", state = "off")

        # Populate Grid First
        self.set_state("input_select.adgw_grid_discharge_stopped_soc", state = response['obj']['mixBean']['wdisChargeSOCLowLimit2'])
        self.set_state("input_select.adgw_grid_discharge_power", state = response['obj']['mixBean']['wdisChargeSOCLowLimit1'])
        self.set_state("input_datetime.adgw_grid_first_time_slot_1_start", state = response['obj']['mixBean']['forcedDischargeTimeStart1'])
        self.set_state("input_datetime.adgw_grid_first_time_slot_1_end", state = response['obj']['mixBean']['forcedDischargeTimeStop1'])
        if (response['obj']['mixBean']['forcedDischargeStopSwitch1']) == "1":
            self.set_state ("input_boolean.adgw_grid_first_time_slot_1_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_grid_first_time_slot_1_enabled", state = "off")

        self.set_state("input_datetime.adgw_grid_first_time_slot_2_start", state = response['obj']['mixBean']['forcedDischargeTimeStart2'])
        self.set_state("input_datetime.adgw_grid_first_time_slot_2_end", state = response['obj']['mixBean']['forcedDischargeTimeStop2'])
        if (response['obj']['mixBean']['forcedDischargeStopSwitch2']) == "1":
            self.set_state ("input_boolean.adgw_grid_first_time_slot_2_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_grid_first_time_slot_2_enabled", state = "off")

        self.set_state("input_datetime.adgw_grid_first_time_slot_3_start", state = response['obj']['mixBean']['forcedDischargeTimeStart3'])
        self.set_state("input_datetime.adgw_grid_first_time_slot_3_end", state = response['obj']['mixBean']['forcedDischargeTimeStop3'])
        if (response['obj']['mixBean']['forcedDischargeStopSwitch3']) == "1":
            self.set_state ("input_boolean.adgw_grid_first_time_slot_3_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_grid_first_time_slot_3_enabled", state = "off")

        # Populate Grid First1

        self.set_state("input_datetime.adgw_grid_first1_time_slot_4_start", state = response['obj']['mixBean']['forcedDischargeTimeStart4'])
        self.set_state("input_datetime.adgw_grid_first1_time_slot_4_end", state = response['obj']['mixBean']['forcedDischargeTimeStop4'])
        if (response['obj']['mixBean']['forcedDischargeStopSwitch4']) == "1":
            self.set_state ("input_boolean.adgw_grid_first1_time_slot_4_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_grid_first1_time_slot_4_enabled", state = "off")

        self.set_state("input_datetime.adgw_grid_first1_time_slot_5_start", state = response['obj']['mixBean']['forcedDischargeTimeStart5'])
        self.set_state("input_datetime.adgw_grid_first1_time_slot_5_end", state = response['obj']['mixBean']['forcedDischargeTimeStop5'])
        if (response['obj']['mixBean']['forcedDischargeStopSwitch5']) == "1":
            self.set_state ("input_boolean.adgw_grid_first1_time_slot_5_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_grid_first1_time_slot_5_enabled", state = "off")

        self.set_state("input_datetime.adgw_grid_first1_time_slot_6_start", state = response['obj']['mixBean']['forcedDischargeTimeStart6'])
        self.set_state("input_datetime.adgw_grid_first1_time_slot_6_end", state = response['obj']['mixBean']['forcedDischargeTimeStop6'])
        if (response['obj']['mixBean']['forcedDischargeStopSwitch6']) == "1":
            self.set_state ("input_boolean.adgw_grid_first1_time_slot_6_enabled", state = "on")
        else:
            self.set_state ("input_boolean.adgw_grid_first1_time_slot_6_enabled", state = "off")



        #ohm 20231219 added load first battery discharge stop setting (should be between 10-100)
        # Populate Load First
        self.set_state("input_select.adgw_load_bat_discharge_stop_soc", state = response['obj']['mixBean']['loadFirstStopSocSet'])

        #List all key pairs from response to log. Comment out before going into production
        #for key, value in response['obj']['mixBean'].items():
        #    self.log(f"{key}: {value}")
        #self.log (response)

        if (response['result']) == 1: # Set status in UI
            self.set_state("sensor.template_adgw_api_state", state = "Get success")
        else:
            self.set_state("sensor.template_adgw_api_state", state = "Error getting")

    def set_charge_settings_export(self):
        #It's good practice to have those values stored in the secrets file
        un = self.args["growatt_username"]
        pwd = self.args["growatt_password"]
        device_sn = self.args["growatt_device"]
        #Query the server using the api
        api = growattServer.GrowattApi() #get an instance of the api, using a random string as the ID
        session = api.login(un, pwd) #login and return a session
        if session['success'] == True: #Handle error message
            self.set_state("sensor.template_adgw_api_state", state = "Initialized")
        else:
            if session["msg"] == "507":
                self.set_state("sensor.template_adgw_api_state", state = "Locked " + session["lockDuration"] + " hours")
            else:
                self.set_state("sensor.template_adgw_api_state", state = "Error Msg " + session["msg"])
            return False
        # Export limit save
        export_limit_on = convert_on_off(self.get_state("input_boolean.adgw_export_limit_on"))
        schedule_settings = [export_limit_on,   #Export limit - Eabled/Disabled (0/1)
                                "0"] #0% export limit means all export is stopped
        response = api.update_mix_inverter_setting(device_sn, 'backflow_setting', schedule_settings)
        if response['success'] == True:
            self.set_state("sensor.template_adgw_api_state", state = "Export saved")
            return True
        else:
            self.set_state("sensor.template_adgw_api_state", state = "Error saving Export limit: "  + response['msg'])
            return False

    def set_charge_settings_export_handler(self, entity, attribute, old, new, kwargs):
        for attempt in range(5):
            if self.set_charge_settings_export() == True:
                break

    def set_charge_settings_battery(self):
        #It's good practice to have those values stored in the secrets file
        un = self.args["growatt_username"]
        pwd = self.args["growatt_password"]
        device_sn = self.args["growatt_device"]
        #Query the server using the api
        api = growattServer.GrowattApi() #get an instance of the api, using a random string as the ID
        session = api.login(un, pwd) #login and return a session
        if session['success'] == True: #Handle error message
            self.set_state("sensor.template_adgw_api_state", state = "Initialized")
        else:
            if session["msg"] == "507":
                self.set_state("sensor.template_adgw_api_state", state = "Locked " + session["lockDuration"] + " hours")
            else:
                self.set_state("sensor.template_adgw_api_state", state = "Error Msg " + session["msg"])
            return False
        #Battery first save
        strings = self.get_state("input_datetime.adgw_battery_first_time_slot_1_start").split(":")
        start_time = [s.zfill(2) for s in strings]
        strings = self.get_state("input_datetime.adgw_battery_first_time_slot_1_end").split(":")
        end_time = [s.zfill(2) for s in strings]
        charge_final_soc = self.get_state("input_select.adgw_battery_charge_max_soc")
        ac_charge_on = convert_on_off(self.get_state("input_boolean.adgw_ac_charge_on"))
        charge_power = self.get_state("input_select.adgw_grid_charge_power")
        time_slot_1_enabled = convert_on_off(self.get_state("input_boolean.adgw_battery_first_time_slot_1_enabled"))

        strings = self.get_state("input_datetime.adgw_battery_first_time_slot_2_start").split(":")
        start_time2 = [s.zfill(2) for s in strings]
        strings = self.get_state("input_datetime.adgw_battery_first_time_slot_2_end").split(":")
        end_time2 = [s.zfill(2) for s in strings]
        time_slot_2_enabled = convert_on_off(self.get_state("input_boolean.adgw_battery_first_time_slot_2_enabled"))

        strings = self.get_state("input_datetime.adgw_battery_first_time_slot_3_start").split(":")
        start_time3 = [s.zfill(2) for s in strings]
        strings = self.get_state("input_datetime.adgw_battery_first_time_slot_3_end").split(":")
        end_time3 = [s.zfill(2) for s in strings]
        time_slot_3_enabled = convert_on_off(self.get_state("input_boolean.adgw_battery_first_time_slot_3_enabled"))

        # Create dictionary of settings to apply through the api call. The order of these elements is important.
        schedule_settings = [charge_power, #Charging power %
                                charge_final_soc.replace("%", ""), #Stop charging SoC %
                                ac_charge_on,   #Allow AC charging (1 = Enabled)
                                start_time[0], start_time[1], #Schedule 1 - Start time "00","00"
                                end_time[0], end_time[1], #Schedule 1 - End time "00","00"
                                time_slot_1_enabled,        #Schedule 1 - Enabled/Disabled (0 = Disabled, 1 Enabled)
                                start_time2[0], start_time2[1], #Schedule 2 - Start time "00","00"
                                end_time2[0], end_time2[1], #Schedule 2 - End time "00","00"
                                time_slot_2_enabled,        #Schedule 2 - Enabled/Disabled (0 = Disabled, 1 Enabled)
                                start_time3[0], start_time3[1], #Schedule 3 - Start time "00","00"
                                end_time3[0], end_time3[1], #Schedule 3 - End time "00","00"
                                time_slot_3_enabled]        #Schedule 3 - Enabled/Disabled (0 = Disabled, 1 Enabled)
        # The api call - specifically for the mix inverter. Some other op will need to be applied if you dont have a mix inverter (replace 'mix_ac_charge_time_period')
        response = api.update_mix_inverter_setting(device_sn, 'mix_ac_charge_time_period', schedule_settings)
        if response['success'] == True:
            self.set_state("sensor.template_adgw_api_state", state = "Battery first saved")
            return True
        else:
            self.set_state("sensor.template_adgw_api_state", state = "Error saving Battery first: "  + response['msg'])
            return False

    def set_charge_settings_battery_handler(self, entity, attribute, old, new, kwargs):
        for attempt in range(5):
            if self.set_charge_settings_battery() == True:
                break



    def set_charge_settings_battery1(self):

        self.set_state("sensor.template_adgw_api_state", state = "Battery first 1 save - Not Implemented")
        return True

        #It's good practice to have those values stored in the secrets file
        un = self.args["growatt_username"]
        pwd = self.args["growatt_password"]
        device_sn = self.args["growatt_device"]
        #Query the server using the api
        api = growattServer.GrowattApi() #get an instance of the api, using a random string as the ID
        session = api.login(un, pwd) #login and return a session
        if session['success'] == True: #Handle error message
            self.set_state("sensor.template_adgw_api_state", state = "Initialized")
        else:
            if session["msg"] == "507":
                self.set_state("sensor.template_adgw_api_state", state = "Locked " + session["lockDuration"] + " hours")
            else:
                self.set_state("sensor.template_adgw_api_state", state = "Error Msg " + session["msg"])
            return False
        #Battery first save
        strings = self.get_state("input_datetime.adgw_battery_first_time_slot_1_start").split(":")
        start_time = [s.zfill(2) for s in strings]
        strings = self.get_state("input_datetime.adgw_battery_first_time_slot_1_end").split(":")
        end_time = [s.zfill(2) for s in strings]
        charge_final_soc = self.get_state("input_select.adgw_battery_charge_max_soc")
        ac_charge_on = convert_on_off(self.get_state("input_boolean.adgw_ac_charge_on"))
        charge_power = self.get_state("input_select.adgw_grid_charge_power")
        time_slot_1_enabled = convert_on_off(self.get_state("input_boolean.adgw_battery_first_time_slot_1_enabled"))

        strings = self.get_state("input_datetime.adgw_battery_first_time_slot_2_start").split(":")
        start_time2 = [s.zfill(2) for s in strings]
        strings = self.get_state("input_datetime.adgw_battery_first_time_slot_2_end").split(":")
        end_time2 = [s.zfill(2) for s in strings]
        time_slot_2_enabled = convert_on_off(self.get_state("input_boolean.adgw_battery_first_time_slot_2_enabled"))

        strings = self.get_state("input_datetime.adgw_battery_first_time_slot_3_start").split(":")
        start_time3 = [s.zfill(2) for s in strings]
        strings = self.get_state("input_datetime.adgw_battery_first_time_slot_3_end").split(":")
        end_time3 = [s.zfill(2) for s in strings]
        time_slot_3_enabled = convert_on_off(self.get_state("input_boolean.adgw_battery_first_time_slot_3_enabled"))

        # Create dictionary of settings to apply through the api call. The order of these elements is important.
        schedule_settings = [charge_power, #Charging power %
                                charge_final_soc.replace("%", ""), #Stop charging SoC %
                                ac_charge_on,   #Allow AC charging (1 = Enabled)
                                start_time[0], start_time[1], #Schedule 1 - Start time "00","00"
                                end_time[0], end_time[1], #Schedule 1 - End time "00","00"
                                time_slot_1_enabled,        #Schedule 1 - Enabled/Disabled (0 = Disabled, 1 Enabled)
                                start_time2[0], start_time2[1], #Schedule 2 - Start time "00","00"
                                end_time2[0], end_time2[1], #Schedule 2 - End time "00","00"
                                time_slot_2_enabled,        #Schedule 2 - Enabled/Disabled (0 = Disabled, 1 Enabled)
                                start_time3[0], start_time3[1], #Schedule 3 - Start time "00","00"
                                end_time3[0], end_time3[1], #Schedule 3 - End time "00","00"
                                time_slot_3_enabled]        #Schedule 3 - Enabled/Disabled (0 = Disabled, 1 Enabled)
        # The api call - specifically for the mix inverter. Some other op will need to be applied if you dont have a mix inverter (replace 'mix_ac_charge_time_period')
        response = api.update_mix_inverter_setting(device_sn, 'mix_ac_charge_time_period', schedule_settings)
        if response['success'] == True:
            self.set_state("sensor.template_adgw_api_state", state = "Battery first 1 saved")
            return True
        else:
            self.set_state("sensor.template_adgw_api_state", state = "Error saving Battery first 1: "  + response['msg'])
            return False

    def set_charge_settings_battery1_handler(self, entity, attribute, old, new, kwargs):
        for attempt in range(5):
            if self.set_charge_settings_battery1() == True:
                break











    def set_charge_settings_grid(self):
        #It's good practice to have those values stored in the secrets file
        un = self.args["growatt_username"]
        pwd = self.args["growatt_password"]
        device_sn = self.args["growatt_device"]
        #Query the server using the api
        api = growattServer.GrowattApi() #get an instance of the api, using a random string as the ID
        session = api.login(un, pwd) #login and return a session
        if session['success'] == True: #Handle error message
            self.set_state("sensor.template_adgw_api_state", state = "Initialized")
        else:
            if session["msg"] == "507":
                self.set_state("sensor.template_adgw_api_state", state = "Locked " + session["lockDuration"] + " hours")
            else:
                self.set_state("sensor.template_adgw_api_state", state = "Error Msg " + session["msg"])
            return False

        #Grid first save
        strings = self.get_state("input_datetime.adgw_grid_first_time_slot_1_start").split(":")
        start_time = [s.zfill(2) for s in strings]
        strings = self.get_state("input_datetime.adgw_grid_first_time_slot_1_end").split(":")
        end_time = [s.zfill(2) for s in strings]
        discharge_stopped_soc = self.get_state("input_select.adgw_grid_discharge_stopped_soc")
        discharge_power = self.get_state("input_select.adgw_grid_discharge_power")
        time_slot_1_enabled = convert_on_off(self.get_state("input_boolean.adgw_grid_first_time_slot_1_enabled"))

        strings = self.get_state("input_datetime.adgw_grid_first_time_slot_2_start").split(":")
        start_time2 = [s.zfill(2) for s in strings]
        strings = self.get_state("input_datetime.adgw_grid_first_time_slot_2_end").split(":")
        end_time2 = [s.zfill(2) for s in strings]
        time_slot_2_enabled = convert_on_off(self.get_state("input_boolean.adgw_grid_first_time_slot_2_enabled"))

        strings = self.get_state("input_datetime.adgw_grid_first_time_slot_3_start").split(":")
        start_time3 = [s.zfill(2) for s in strings]
        strings = self.get_state("input_datetime.adgw_grid_first_time_slot_3_end").split(":")
        end_time3 = [s.zfill(2) for s in strings]
        time_slot_3_enabled = convert_on_off(self.get_state("input_boolean.adgw_grid_first_time_slot_3_enabled"))

        # Create dictionary of settings to apply through the api call. The order of these elements is important.
        schedule_settings = [discharge_power, #Discharging power %
                                discharge_stopped_soc, #Stop charging SoC %
                                start_time[0], start_time[1], #Schedule 1 - Start time "00","00"
                                end_time[0], end_time[1], #Schedule 1 - End time "00","00"
                                time_slot_1_enabled,        #Schedule 1 - Enabled/Disabled (0 = Disabled, 1 Enabled)
                                start_time2[0], start_time2[1], #Schedule 2 - Start time "00","00"
                                end_time2[0], end_time2[1], #Schedule 2 - End time "00","00"
                                time_slot_2_enabled,        #Schedule 2 - Enabled/Disabled (0 = Disabled, 1 Enabled)
                                start_time3[0], start_time3[1], #Schedule 3 - Start time "00","00"
                                end_time3[0], end_time3[1], #Schedule 3 - End time "00","00"
                                time_slot_3_enabled]        #Schedule 3 - Enabled/Disabled (0 = Disabled, 1 Enabled)
        # The api call - specifically for the mix inverter. Some other op will need to be applied if you dont have a mix inverter (replace 'mix_ac_charge_time_period')
        response = api.update_mix_inverter_setting(device_sn, 'mix_ac_discharge_time_period', schedule_settings)
        if response['success'] == True:
            self.set_state("sensor.template_adgw_api_state", state = "Grid first saved")
            return True
        else:
            self.set_state("sensor.template_adgw_api_state", state = "Error saving Grid first: " + response['msg'])
            return False

    def set_charge_settings_grid_handler(self, entity, attribute, old, new, kwargs):
        for attempt in range(5):
            if self.set_charge_settings_grid() == True:
                break




    def set_charge_settings_grid1(self):

        self.set_state("sensor.template_adgw_api_state", state = "Grid first 1 save - Not Implemented")
        return True

        #It's good practice to have those values stored in the secrets file
        un = self.args["growatt_username"]
        pwd = self.args["growatt_password"]
        device_sn = self.args["growatt_device"]
        #Query the server using the api
        api = growattServer.GrowattApi() #get an instance of the api, using a random string as the ID
        session = api.login(un, pwd) #login and return a session
        if session['success'] == True: #Handle error message
            self.set_state("sensor.template_adgw_api_state", state = "Initialized")
        else:
            if session["msg"] == "507":
                self.set_state("sensor.template_adgw_api_state", state = "Locked " + session["lockDuration"] + " hours")
            else:
                self.set_state("sensor.template_adgw_api_state", state = "Error Msg " + session["msg"])
            return False

        #Grid first save
        strings = self.get_state("input_datetime.adgw_grid_first_time_slot_1_start").split(":")
        start_time = [s.zfill(2) for s in strings]
        strings = self.get_state("input_datetime.adgw_grid_first_time_slot_1_end").split(":")
        end_time = [s.zfill(2) for s in strings]
        discharge_stopped_soc = self.get_state("input_select.adgw_grid_discharge_stopped_soc")
        discharge_power = self.get_state("input_select.adgw_grid_discharge_power")
        time_slot_1_enabled = convert_on_off(self.get_state("input_boolean.adgw_grid_first_time_slot_1_enabled"))

        strings = self.get_state("input_datetime.adgw_grid_first_time_slot_2_start").split(":")
        start_time2 = [s.zfill(2) for s in strings]
        strings = self.get_state("input_datetime.adgw_grid_first_time_slot_2_end").split(":")
        end_time2 = [s.zfill(2) for s in strings]
        time_slot_2_enabled = convert_on_off(self.get_state("input_boolean.adgw_grid_first_time_slot_2_enabled"))

        strings = self.get_state("input_datetime.adgw_grid_first_time_slot_3_start").split(":")
        start_time3 = [s.zfill(2) for s in strings]
        strings = self.get_state("input_datetime.adgw_grid_first_time_slot_3_end").split(":")
        end_time3 = [s.zfill(2) for s in strings]
        time_slot_3_enabled = convert_on_off(self.get_state("input_boolean.adgw_grid_first_time_slot_3_enabled"))

        # Create dictionary of settings to apply through the api call. The order of these elements is important.
        schedule_settings = [discharge_power, #Discharging power %
                                discharge_stopped_soc, #Stop charging SoC %
                                start_time[0], start_time[1], #Schedule 1 - Start time "00","00"
                                end_time[0], end_time[1], #Schedule 1 - End time "00","00"
                                time_slot_1_enabled,        #Schedule 1 - Enabled/Disabled (0 = Disabled, 1 Enabled)
                                start_time2[0], start_time2[1], #Schedule 2 - Start time "00","00"
                                end_time2[0], end_time2[1], #Schedule 2 - End time "00","00"
                                time_slot_2_enabled,        #Schedule 2 - Enabled/Disabled (0 = Disabled, 1 Enabled)
                                start_time3[0], start_time3[1], #Schedule 3 - Start time "00","00"
                                end_time3[0], end_time3[1], #Schedule 3 - End time "00","00"
                                time_slot_3_enabled]        #Schedule 3 - Enabled/Disabled (0 = Disabled, 1 Enabled)
        # The api call - specifically for the mix inverter. Some other op will need to be applied if you dont have a mix inverter (replace 'mix_ac_charge_time_period')
        response = api.update_mix_inverter_setting(device_sn, 'mix_ac_discharge_time_period', schedule_settings)
        if response['success'] == True:
            self.set_state("sensor.template_adgw_api_state", state = "Grid first saved")
            return True
        else:
            self.set_state("sensor.template_adgw_api_state", state = "Error saving Grid first: " + response['msg'])
            return False

    def set_charge_settings_grid1_handler(self, entity, attribute, old, new, kwargs):
        for attempt in range(5):
            if self.set_charge_settings_grid1() == True:
                break


    #ohm: 20231219 added load first
    def set_charge_settings_load(self):

        #It's good practice to have those values stored in the secrets file
        un = self.args["growatt_username"]
        pwd = self.args["growatt_password"]
        device_sn = self.args["growatt_device"]
        #Query the server using the api
        api = growattServer.GrowattApi() #get an instance of the api, using a random string as the ID
        session = api.login(un, pwd) #login and return a session
        if session['success'] == True: #Handle error message
            self.set_state("sensor.template_adgw_api_state", state = "Initialized")
        else:
            if session["msg"] == "507":
                self.set_state("sensor.template_adgw_api_state", state = "Locked " + session["lockDuration"] + " hours")
            else:
                self.set_state("sensor.template_adgw_api_state", state = "Error Msg " + session["msg"])
            return False

        #load first save
        discharge_stopped_soc = self.get_state("input_select.adgw_load_bat_discharge_stop_soc")

        parameter_settings = []        
        # Create dictionary of settings to apply through the api call. The order of these elements is important.
        parameter_settings = [discharge_stopped_soc]        #Load First Battery Discharge Stop soc (numeric 0-100)

        # The api call - specifically for the mix inverter. Some other op will need to be applied if you dont have a mix inverter
        response = api.update_mix_inverter_setting(device_sn, 'mix_load_flast_value_multi', parameter_settings)
        if response['success'] == True:
            self.set_state("sensor.template_adgw_api_state", state = "Load first saved")
            return True
        else:
            self.set_state("sensor.template_adgw_api_state", state = "Error saving Load first: " + response['msg'])
            return False

    def set_charge_settings_load_handler(self, entity, attribute, old, new, kwargs):
        for attempt in range(5):
            if self.set_charge_settings_load() == True:
                break


    #ohm: 20231225 added inverter settings
    def set_inverter_settings(self):

        #It's good practice to have those values stored in the secrets file
        un = self.args["growatt_username"]
        pwd = self.args["growatt_password"]
        device_sn = self.args["growatt_device"]
        #Query the server using the api
        api = growattServer.GrowattApi() #get an instance of the api, using a random string as the ID
        session = api.login(un, pwd) #login and return a session
        if session['success'] == True: #Handle error message
            self.set_state("sensor.template_adgw_api_state", state = "Initialized")
        else:
            if session["msg"] == "507":
                self.set_state("sensor.template_adgw_api_state", state = "Locked " + session["lockDuration"] + " hours")
            else:
                self.set_state("sensor.template_adgw_api_state", state = "Error Msg " + session["msg"])
            return False

        #Inverter On / Off Setting
        inverter_on_off = convert_on_off(self.get_state("input_boolean.adgw_inverter_on"))

        # Create dictionary of settings to apply through the api call. The order of these elements is important.
        parameter_settings = []
        parameter_settings = [inverter_on_off]
        # The api call - specifically for the mix inverter. Some other op will need to be applied if you dont have a mix inverter (replace 'mix_ac_charge_time_period')
        response = api.update_mix_inverter_setting(device_sn, 'pv_on_off', parameter_settings)
        if response['success'] == True:
            self.set_state("sensor.template_adgw_api_state", state = "Inverter setting saved")
            return True
        else:
            self.set_state("sensor.template_adgw_api_state", state = "Error saving Inverter setting: " + response['msg'])
            return False

    def set_inverter_settings_handler(self, entity, attribute, old, new, kwargs):
        for attempt in range(5):
            if self.set_inverter_settings() == True:
                break

    #ohm: 20231225 added inverter eps settings
    def set_inverter_eps_settings(self):

        #It's good practice to have those values stored in the secrets file
        un = self.args["growatt_username"]
        pwd = self.args["growatt_password"]
        device_sn = self.args["growatt_device"]
        #Query the server using the api
        api = growattServer.GrowattApi() #get an instance of the api, using a random string as the ID
        session = api.login(un, pwd) #login and return a session
        if session['success'] == True: #Handle error message
            self.set_state("sensor.template_adgw_api_state", state = "Initialized")
        else:
            if session["msg"] == "507":
                self.set_state("sensor.template_adgw_api_state", state = "Locked " + session["lockDuration"] + " hours")
            else:
                self.set_state("sensor.template_adgw_api_state", state = "Error Msg " + session["msg"])
            return False

        #load EPS State
        inverter_eps_enabled = convert_on_off(self.get_state("input_boolean.adgw_inverter_eps_enabled"))

        parameter_settings = []        
        # Create dictionary of settings to apply through the api call. The order of these elements is important.
        parameter_settings = [inverter_eps_enabled]        #Inverter EPS Setting - Enabled/Disabled (0 = Disabled, 1 Enabled)

        # The api call - specifically for the mix inverter. Some other op will need to be applied if you dont have a mix inverter (replace 'mix_ac_charge_time_period')
        response = api.update_mix_inverter_setting(device_sn, 'mix_off_grid_enable', parameter_settings)
        if response['success'] == True:
            self.set_state("sensor.template_adgw_api_state", state = "EPS Settings saved")
            return True
        else:
            self.set_state("sensor.template_adgw_api_state", state = "Error saving EPS Settings: " + response['msg'])
            return False

    def set_inverter_eps_settings_handler(self, entity, attribute, old, new, kwargs):
        for attempt in range(5):
            if self.set_inverter_eps_settings() == True:
                break

    #ohm: 20231225 added inverter date & time settings
    def set_inverter_time_settings(self):

        self.set_state("sensor.template_adgw_api_state", state = "Inverter Date & Time Settings save - Not Implemented")
        return True

        #It's good practice to have those values stored in the secrets file
        un = self.args["growatt_username"]
        pwd = self.args["growatt_password"]
        device_sn = self.args["growatt_device"]
        #Query the server using the api
        api = growattServer.GrowattApi() #get an instance of the api, using a random string as the ID
        session = api.login(un, pwd) #login and return a session
        if session['success'] == True: #Handle error message
            self.set_state("sensor.template_adgw_api_state", state = "Initialized")
        else:
            if session["msg"] == "507":
                self.set_state("sensor.template_adgw_api_state", state = "Locked " + session["lockDuration"] + " hours")
            else:
                self.set_state("sensor.template_adgw_api_state", state = "Error Msg " + session["msg"])
            return False

        #load New Date & Time & format to YYYY-MM-DD HH24:MI:SS
        inverter_eps_enabled = convert_on_off(self.get_state("input_boolean.adgw_inverter_eps_enabled"))

        parameter_settings = []
        # Create dictionary of settings to apply through the api call. The order of these elements is important.
        parameter_settings = [inverter_eps_enabled]        #Inverter Date & Time Setting - YYYY-MM-DD HH24:MI:SS

        # The api call - specifically for the mix inverter. Some other op will need to be applied if you dont have a mix inverter (replace 'mix_ac_charge_time_period')
        response = api.update_mix_inverter_setting(device_sn, 'pf_sys_year', parameter_settings)
        if response['success'] == True:
            self.set_state("sensor.template_adgw_api_state", state = "Inverter Date & Time Settings saved")
            return True
        else:
            self.set_state("sensor.template_adgw_api_state", state = "Error saving Inverter Date & Time Settings: " + response['msg'])
            return False

    def set_inverter_time_settings_handler(self, entity, attribute, old, new, kwargs):
        for attempt in range(5):
            if self.set_inverter_time_settings() == True:
                break



def convert_on_off(value):
    # Function to convert on/off to 1/0
    if value == "on":
        return "1"
    else:
        return "0"