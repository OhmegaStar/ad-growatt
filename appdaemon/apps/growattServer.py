name = "growattServer"

import datetime
from enum import IntEnum
import hashlib
import json
import requests
import warnings
from random import randint

def hash_password(password):
    """
    Normal MD5, except add c if a byte of the digest is less than 10.
    """
    password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest()
    for i in range(0, len(password_md5), 2):
        if password_md5[i] == '0':
            password_md5 = password_md5[0:i] + 'c' + password_md5[i + 1:]
    return password_md5

class Timespan(IntEnum):
    hour = 0
    day = 1
    month = 2

class GrowattApi:
    server_url = 'https://openapi.growatt.com/'
    agent_identifier = "Dalvik/2.1.0 (Linux; U; Android 12; https://github.com/indykoning/PyPi_GrowattServer)"

    def __init__(self, add_random_user_id=True, agent_identifier=None):
        if (agent_identifier != None):
            self.agent_identifier = agent_identifier

        #If a random user id is required, generate a 5 digit number and add it to the user agent
        if (add_random_user_id):
            random_number = ''.join(["{}".format(randint(0,9)) for num in range(0,50)])
            self.agent_identifier = random_number

        self.session = requests.Session()

        headers = {'User-Agent': self.agent_identifier}
        self.session.headers.update(headers)

    def __get_date_string(self, timespan=None, date=None):
        if timespan is not None:
            assert timespan in Timespan

        if date is None:
            date = datetime.datetime.now()

        date_str=""
        if timespan == Timespan.month:
            date_str = date.strftime('%Y-%m')
        else:
            date_str = date.strftime('%Y-%m-%d')

        return date_str

    def get_url(self, page):
        """
        Simple helper function to get the page url/
        """
        return self.server_url + page

    def login(self, username, password, is_password_hashed=False):
        """
        Log the user in.

        Returns
        'data' -- A List containing Objects containing the folowing
            'plantName' -- Friendly name of the plant
            'plantId'   -- The ID of the plant
        'service'
        'quality'
        'isOpenSmartFamily'
        'totalData' -- An Object
        'success'   -- True or False
        'msg'
        'app_code'
        'user' -- An Object containing a lot of user information
            'uid'
            'userLanguage'
            'inverterGroup' -- A List
            'timeZone' -- A Number
            'lat'
            'lng'
            'dataAcqList' -- A List
            'type'
            'accountName' -- The username
            'password' -- The password hash of the user
            'isValiPhone'
            'kind'
            'mailNotice' -- True or False
            'id'
            'lasLoginIp'
            'lastLoginTime'
            'userDeviceType'
            'phoneNum'
            'approved' -- True or False
            'area' -- Continent of the user
            'smsNotice' -- True or False
            'isAgent'
            'token'
            'nickName'
            'parentUserId'
            'customerCode'
            'country'
            'isPhoneNumReg'
            'createDate'
            'rightlevel'
            'appType'
            'serverUrl'
            'roleId'
            'enabled' -- True or False
            'agentCode'
            'inverterList' -- A list
            'email'
            'company'
            'activeName'
            'codeIndex'
            'appAlias'
            'isBigCustomer'
            'noticeType'
        """
        if not is_password_hashed:
            password = hash_password(password)

        response = self.session.post(self.get_url('newTwoLoginAPI.do'), data={
            'userName': username,
            'password': password
        })
#debugging
        if response.status_code == 403:
            data = {}
            data["msg"] = '403 Forbidden during Login / Session Creation'
            data['success'] = False
            data['response'] = response
            return data
#debugging

        data = json.loads(response.content.decode('utf-8'))['back']
        if data['success']:
            data.update({
                'userId': data['user']['id'],
                'userLevel': data['user']['rightlevel']
            })
        return data

    def plant_list(self, user_id):
        """
        Get a list of plants connected to this account.
        """
        response = self.session.get(self.get_url('PlantListAPI.do'),
                                    params={'userId': user_id},
                                    allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError("Request failed: %s", response)
        data = json.loads(response.content.decode('utf-8'))
        return data['back']

    def plant_detail(self, plant_id, timespan, date=None):
        """
        Get plant details for specified timespan.
        """
        date_str = self.__get_date_string(timespan, date)

        response = self.session.get(self.get_url('PlantDetailAPI.do'), params={
            'plantId': plant_id,
            'type': timespan.value,
            'date': date_str
        })
        data = json.loads(response.content.decode('utf-8'))
        return data['back']

    def inverter_data(self, inverter_id, date=None):
        """
        Get inverter data for specified date or today.
        """
        date_str = self.__get_date_string(date=date)
        response = self.session.get(self.get_url('newInverterAPI.do'), params={
            'op': 'getInverterData',
            'id': inverter_id,
            'type': 1,
            'date': date_str
        })
        data = json.loads(response.content.decode('utf-8'))
        return data

    def inverter_detail(self, inverter_id):
        """
        Get "All parameters" from PV inverter.
        """
        response = self.session.get(self.get_url('newInverterAPI.do'), params={
            'op': 'getInverterDetailData',
            'inverterId': inverter_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def inverter_detail_two(self, inverter_id):
        """
        Get "All parameters" from PV inverter.
        """
        response = self.session.get(self.get_url('newInverterAPI.do'), params={
            'op': 'getInverterDetailData_two',
            'inverterId': inverter_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def tlx_data(self, tlx_id, date=None):
        """
        Get inverter data for specified date or today.
        """
        date_str = self.__get_date_string(date=date)
        response = self.session.get(self.get_url('newTlxApi.do'), params={
            'op': 'getTlxData',
            'id': tlx_id,
            'type': 1,
            'date': date_str
        })
        data = json.loads(response.content.decode('utf-8'))
        return data

    def tlx_detail(self, tlx_id):
        """
        Get "All parameters" from PV inverter.
        """
        response = self.session.get(self.get_url('newTlxApi.do'), params={
            'op': 'getTlxDetailData',
            'id': tlx_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def mix_info(self, mix_id, plant_id = None):
        """
        Returns high level values from Mix device

        Keyword arguments:
        mix_id -- The serial number (device_sn) of the inverter
        plant_id -- The ID of the plant (the mobile app uses this but it does not appear to be necessary) (default None)

        Returns:
        'acChargeEnergyToday' -- ??? 2.7
        'acChargeEnergyTotal' -- ??? 25.3
        'acChargePower' -- ??? 0
        'capacity': '45' -- The current remaining capacity of the batteries (same as soc but without the % sign)
        'eBatChargeToday' -- Battery charged today in kWh
        'eBatChargeTotal' -- Battery charged total (all time) in kWh
        'eBatDisChargeToday' -- Battery discharged today in kWh
        'eBatDisChargeTotal' -- Battery discharged total (all time) in kWh
        'epvToday' -- Energy generated from PVs today in kWh
        'epvTotal' -- Energy generated from PVs total (all time) in kWh
        'isCharge'-- ??? 0 - Possible a 0/1 based on whether or not the battery is charging
        'pCharge1' -- ??? 0
        'pDischarge1' -- Battery discharging rate in W
        'soc' -- Statement of charge including % symbol
        'upsPac1' -- ??? 0
        'upsPac2' -- ??? 0
        'upsPac3' -- ??? 0
        'vbat' -- Battery Voltage
        'vbatdsp' -- ??? 51.8
        'vpv1' -- Voltage PV1
        'vpv2' -- Voltage PV2
        """
        request_params={
            'op': 'getMixInfo',
            'mixId': mix_id
        }

        if (plant_id):
            request_params['plantId'] = plant_id

        response = self.session.get(self.get_url('newMixApi.do'), params=request_params)

        data = json.loads(response.content.decode('utf-8'))
        return data['obj']

    def mix_totals(self, mix_id, plant_id):
        """
        Returns "Totals" values from Mix device

        Keyword arguments:
        mix_id -- The serial number (device_sn) of the inverter
        plant_id -- The ID of the plant

        Returns:
        'echargetoday' -- Battery charged today in kWh (same as eBatChargeToday from mix_info)
        'echargetotal' -- Battery charged total (all time) in kWh (same as eBatChargeTotal from mix_info)
        'edischarge1Today' -- Battery discharged today in kWh (same as eBatDisChargeToday from mix_info)
        'edischarge1Total' -- Battery discharged total (all time) in kWh (same as eBatDisChargeTotal from mix_info)
        'elocalLoadToday' -- Load consumption today in kWh
        'elocalLoadTotal' -- Load consumption total (all time) in kWh
        'epvToday' -- Energy generated from PVs today in kWh (same as epvToday from mix_info)
        'epvTotal' -- Energy generated from PVs total (all time) in kWh (same as epvTotal from mix_info)
        'etoGridToday' -- Energy exported to the grid today in kWh
        'etogridTotal' -- Energy exported to the grid total (all time) in kWh
        'photovoltaicRevenueToday' -- Revenue earned from PV today in 'unit' currency
        'photovoltaicRevenueTotal' -- Revenue earned from PV total (all time) in 'unit' currency
        'unit' -- Unit of currency for 'Revenue'
        """
        response = self.session.post(self.get_url('newMixApi.do'), params={
            'op': 'getEnergyOverview',
            'mixId': mix_id,
            'plantId': plant_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data['obj']

    def mix_system_status(self, mix_id, plant_id):
        """
        Returns current "Status" from Mix device

        Keyword arguments:
        mix_id -- The serial number (device_sn) of the inverter
        plant_id -- The ID of the plant

        Returns:
        'SOC' -- Statement of charge (remaining battery %)
        'chargePower' -- Battery charging rate in kw
        'fAc' -- Frequency (Hz)
        'lost' -- System status e.g. 'mix.status.normal'
        'pLocalLoad' -- Load conumption in kW
        'pPv1' -- PV1 Wattage in W
        'pPv2' -- PV2 Wattage in W
        'pactogrid' -- Export to grid rate in kW
        'pactouser' -- Import from grid rate in kW
        'pdisCharge1' -- Discharging batteries rate in kW
        'pmax' -- ??? 6 ??? PV Maximum kW ??
        'ppv' -- PV combined Wattage in kW
        'priorityChoose' -- Priority setting - 0=Local load
        'status' -- System statue - ENUM - Unknown values
        'unit' -- Unit of measurement e.g. 'kW'
        'upsFac' -- ??? 0
        'upsVac1' -- ??? 0
        'uwSysWorkMode' -- ??? 6
        'vAc1' -- Grid voltage in V
        'vBat' -- Battery voltage in V
        'vPv1' -- PV1 voltage in V
        'vPv2' -- PV2 voltage in V
        'vac1' -- Grid voltage in V (same as vAc1)
        'wBatteryType' -- ??? 1
        """
        response = self.session.post(self.get_url('newMixApi.do'), params={
            'op': 'getSystemStatus_KW',
            'mixId': mix_id,
            'plantId': plant_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data['obj']

    def mix_detail(self, mix_id, plant_id, timespan=Timespan.hour, date=None):
        """
        Get Mix details for specified timespan

        Keyword arguments:
        mix_id -- The serial number (device_sn) of the inverter
        plant_id -- The ID of the plant
        timespan -- The ENUM value conforming to the time window you want e.g. hours from today, days, or months (Default Timespan.hour)
        date -- The date you are interested in (Default datetime.datetime.now())

        Returns:
        A chartData object where each entry is for a specific 5 minute window e.g. 00:05 and 00:10 respectively (below)
        'chartData': {   '00:05': {   'pacToGrid' -- Export rate to grid in kW
                                      'pacToUser' -- Import rate from grid in kW
                                      'pdischarge' -- Battery discharge in kW
                                      'ppv' -- Solar generation in kW
                                      'sysOut' -- Load consumption in kW
                                  },
                         '00:10': {   'pacToGrid': '0',
                                      'pacToUser': '0.93',
                                      'pdischarge': '0',
                                      'ppv': '0',
                                      'sysOut': '0.93'},
                          ......
                     }
        'eAcCharge' -- Exported to grid in kWh
        'eCharge' -- System production in kWh = Self-consumption + Exported to Grid
        'eChargeToday' -- Load consumption from solar in kWh
        'eChargeToday1' -- Self-consumption in kWh
        'eChargeToday2' -- Self-consumption in kWh (eChargeToday + echarge1)
        'echarge1' -- Load consumption from battery in kWh
        'echargeToat' -- Total battery discharged (all time) in kWh
        'elocalLoad' -- Load consumption in kW (battery + solar + imported)
        'etouser' -- Load consumption imported from grid in kWh
        'photovoltaic' -- Load consumption from solar in kWh (same as eChargeToday)
        'ratio1' -- % of system production that is self-consumed
        'ratio2' -- % of system production that is exported
        'ratio3' -- % of Load consumption that is "self consumption"
        'ratio4' -- % of Load consumption that is "imported from grid"
        'ratio5' -- % of Self consumption that is directly from Solar
        'ratio6' -- % of Self consumption that is from batteries
        'unit' -- Unit of measurement e.g kWh
        'unit2' -- Unit of measurement e.g kW


        NOTE - It is possible to calculate the PV generation that went into charging the batteries by performing the following calculation:
        Solar to Battery = Solar Generation - Export to Grid - Load consumption from solar
                           epvToday (from mix_info) - eAcCharge - eChargeToday
        """
        date_str = self.__get_date_string(timespan, date)

        response = self.session.post(self.get_url('newMixApi.do'), params={
            'op': 'getEnergyProdAndCons_KW',
            'plantId': plant_id,
            'mixId': mix_id,
            'type': timespan.value,
            'date': date_str
        })
        data = json.loads(response.content.decode('utf-8'))

        return data['obj']

    def dashboard_data(self, plant_id, timespan=Timespan.hour, date=None):
        """
        Get 'dashboard' data for specified timespan
        NOTE - All numerical values returned by this api call include units e.g. kWh or %
             - Many of the 'total' values that are returned for a Mix system are inaccurate on the system this was tested against.
               However, the statistics that are correct are not available on any other interface, plus these values may be accurate for
               non-mix types of system. Where the values have been proven to be inaccurate they are commented below.

        Keyword arguments:
        plant_id -- The ID of the plant
        timespan -- The ENUM value conforming to the time window you want e.g. hours from today, days, or months (Default Timespan.hour)
        date -- The date you are interested in (Default datetime.datetime.now())

        Returns:
        A chartData object where each entry is for a specific 5 minute window e.g. 00:05 and 00:10 respectively (below)
        NOTE: The keys are interpreted differently, the examples below describe what they are used for in a 'Mix' system
        'chartData': {   '00:05': {   'pacToUser' -- Power from battery in kW
                                      'ppv' -- Solar generation in kW
                                      'sysOut' -- Load consumption in kW
                                      'userLoad' -- Export in kW
                                  },
                         '00:10': {   'pacToUser': '0',
                                      'ppv': '0',
                                      'sysOut': '0.7',
                                      'userLoad': '0'},
                          ......
                     }
        'chartDataUnit' -- Unit of measurement e.g. 'kW',
        'eAcCharge' -- Energy exported to the grid in kWh e.g. '20.5kWh' (not accurate for Mix systems)
        'eCharge' -- System production in kWh = Self-consumption + Exported to Grid e.g '23.1kWh' (not accurate for Mix systems - actually showing the total 'load consumption'
        'eChargeToday1' -- Self-consumption of PPV (possibly including excess diverted to batteries) in kWh e.g. '2.6kWh' (not accurate for Mix systems)
        'eChargeToday2' -- Total self-consumption (PPV consumption(eChargeToday2Echarge1) + Battery Consumption(echarge1)) e.g. '10.1kWh' (not accurate for Mix systems)
        'eChargeToday2Echarge1' -- Self-consumption of PPV only e.g. '0.8kWh' (not accurate for Mix systems)
        'echarge1' -- Self-consumption from Battery only e.g. '9.3kWh'
        'echargeToat' -- Not used on Dashboard view, likely to be total battery discharged e.g. '152.1kWh'
        'elocalLoad' -- Total load consumption (etouser + eChargeToday2) e.g. '20.3kWh', (not accurate for Mix systems)
        'etouser'-- Energy imported from grid today (includes both directly used by load and AC battery charging e.g. '10.2kWh'
        'keyNames' -- Keys to be used for the graph data e.g. ['Solar', 'Load Consumption', 'Export To Grid', 'From Battery']
        'photovoltaic' -- Same as eChargeToday2Echarge1 e.g. '0.8kWh'
        'ratio1' -- % of 'Solar production' that is self-consumed e.g. '11.3%' (not accurate for Mix systems)
        'ratio2' -- % of 'Solar production' that is exported e.g. '88.7%' (not accurate for Mix systems)
        'ratio3' -- % of 'Load consumption' that is self consumption e.g. '49.8%' (not accurate for Mix systems)
        'ratio4' -- % of 'Load consumption' that is imported from the grid e.g '50.2%' (not accurate for Mix systems)
        'ratio5' -- % of Self consumption that is from batteries e.g. '92.1%' (not accurate for Mix systems)
        'ratio6' -- % of Self consumption that is directly from Solar e.g. '7.9%' (not accurate for Mix systems)
        """
        date_str = self.__get_date_string(timespan, date)

        response = self.session.post(self.get_url('newPlantAPI.do'), params={
            'action': "getEnergyStorageData",
            'date': date_str,
            'type': timespan.value,
            'plantId': plant_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def storage_detail(self, storage_id):
        """
        Get "All parameters" from battery storage.
        """
        response = self.session.get(self.get_url('newStorageAPI.do'), params={
            'op': 'getStorageInfo_sacolar',
            'storageId': storage_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def storage_params(self, storage_id):
        """
        Get much more detail from battery storage.
        """
        response = self.session.get(self.get_url('newStorageAPI.do'), params={
            'op': 'getStorageParams_sacolar',
            'storageId': storage_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def storage_energy_overview(self, plant_id, storage_id):
        """
        Get some energy/generation overview data.
        """
        response = self.session.post(self.get_url('newStorageAPI.do?op=getEnergyOverviewData_sacolar'), params={
            'plantId': plant_id,
            'storageSn': storage_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data['obj']

    def inverter_list(self, plant_id):
        """
        Use device_list, it's more descriptive since the list contains more than inverters.
        """
        warnings.warn("This function may be deprecated in the future because naming is not correct, use device_list instead", DeprecationWarning)
        return self.device_list(plant_id)

    def device_list(self, plant_id):
        """
        Get a list of all devices connected to plant.
        """
        return self.plant_info(plant_id)['deviceList']

    def plant_info(self, plant_id):
        """
        Get basic plant information with device list.
        """
        response = self.session.get(self.get_url('newTwoPlantAPI.do'), params={
            'op': 'getAllDeviceList',
            'plantId': plant_id,
            'pageNum': 1,
            'pageSize': 1
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def get_plant_settings(self, plant_id):
        """
        Returns a dictionary containing the settings for the specified plant

        Keyword arguments:
        plant_id -- The id of the plant you want the settings of

        Returns:
        A python dictionary containing the settings for the specified plant
        """
        response = self.session.get(self.get_url('newPlantAPI.do'), params={
            'op': 'getPlant',
            'plantId': plant_id
        })
        data = json.loads(response.content.decode('utf-8'))
        return data

    def update_plant_settings(self, plant_id, changed_settings, current_settings = None):
        """
        Applies settings to the plant e.g. ID, Location, Timezone
        See README for all possible settings options

        Keyword arguments:
        plant_id -- The id of the plant you wish to update the settings for
        changed_settings -- A python dictionary containing the settings to be changed and their value
        current_settings -- A python dictionary containing the current settings of the plant (use the response from get_plant_settings), if None - fetched for you

        Returns:
        A response from the server stating whether the configuration was successful or not
        """
        #If no existing settings have been provided then get them from the growatt server
        if current_settings == None:
            current_settings = self.get_plant_settings(plant_id)

        #These are the parameters that the form requires, without these an error is thrown. Pre-populate their values with the current values
        form_settings = {
            'plantCoal': (None, str(current_settings['formulaCoal'])),
            'plantSo2': (None, str(current_settings['formulaSo2'])),
            'accountName': (None, str(current_settings['userAccount'])),
            'plantID': (None, str(current_settings['id'])),
            'plantFirm': (None, '0'), #Hardcoded to 0 as I can't work out what value it should have
            'plantCountry': (None, str(current_settings['country'])),
            'plantType': (None, str(current_settings['plantType'])),
            'plantIncome': (None, str(current_settings['formulaMoneyStr'])),
            'plantAddress': (None, str(current_settings['plantAddress'])),
            'plantTimezone': (None, str(current_settings['timezone'])),
            'plantLng': (None, str(current_settings['plant_lng'])),
            'plantCity': (None, str(current_settings['city'])),
            'plantCo2': (None, str(current_settings['formulaCo2'])),
            'plantMoney': (None, str(current_settings['formulaMoneyUnitId'])),
            'plantPower': (None, str(current_settings['nominalPower'])),
            'plantLat': (None, str(current_settings['plant_lat'])),
            'plantDate': (None, str(current_settings['createDateText'])),
            'plantName': (None, str(current_settings['plantName'])),
        }

        #Overwrite the current value of the setting with the new value
        for setting, value in changed_settings.items():
            form_settings[setting] = (None, str(value))

        response = self.session.post(self.get_url('newTwoPlantAPI.do?op=updatePlant'), files = form_settings)
        data = json.loads(response.content.decode('utf-8'))
        return data

    def update_mix_inverter_setting(self, serial_number, setting_type, parameters):
        """
        Applies settings for specified system based on serial number
        See README for known working settings

        Keyword arguments:
        serial_number -- The serial number (device_sn) of the inverter
        setting_type -- The setting to be configured (list of known working settings below)
        parameters -- A python dictionary of the parameters to be sent to the system based on the chosen setting_type, OR a python array which will be converted to a params dictionary

        Returns:
        A response from the server stating whether the configuration was successful or not
        """
        setting_parameters = parameters

        #If we've been passed an array then convert it into a dictionary
        if isinstance(parameters, list):
            setting_parameters = {}
            for index, param in enumerate(parameters, start=1):
                setting_parameters['param' + str(index)] = param

        default_params = {
            'op': 'mixSetApiNew',
            'serialNum': serial_number,
            'type': setting_type
        }
        settings_params = {**default_params, **setting_parameters}
        response = self.session.post(self.get_url('newTcpsetAPI.do'), params=settings_params)
        data = json.loads(response.content.decode('utf-8'))
        return data

    #Change - This is where the mechanism for setting parameters of charging parameters is done.
    #It's additional to the main growattServer project.
    def get_mix_inverter_settings(self, serial_number):

        """
        Gets the inverter settings related to grid first, battery first modes
        Keyword arguments:
        serial_number -- The serial number (device_sn) of the inverter
        Returns:
        A dictionary of settings
        Below values is from a SPH 10000TL3 BH-UP Inverter
        {
            'deviceType': 0,
            'msg': 'msg',
            'result': 1,    --1 = success 
            'dtc': 0,
            'haveMeter': 0,
            'obj': {
                'mixBean': {
                    'mix_ac_discharge_frequency': '0',
                    'communicationVersion': 'ZDAa-0089',
                    'singleExport': '0',
                    'dischargeTime3': None,
                    'bagingTestStep': '0',
                    'chargePowerCommand': '100',    --Battery First Charge Power Limit (0..100)
                    'uwLVRT2EE': '0.0',
                    'ccCurrent': '25.0',
                    'dischargeTime2': None,
                    'dischargeTime1': None,
                    'record': None,
                    'deviceType': '1',
                    'vbatStartforCharge': '1.45',
                    'uwHFRTTime2EE': '0',
                    'uwReconnectStartSlope': '0.0',
                    'outPower': '5.0',
                    'powerMaxText': '',
                    'backUpEn': '0',
                    'cvVoltage': '14.5',
                    'pv_pf_cmd_memory_state': '1',
                    'energyMonth': '0.0',
                    'acChargeEnable': '1',      --Battery First AC Charging 1 == Enabled, 0 == Disabled
                    'uwHFRTEE': '0.0',
                    'reactiveRate': '100',
                    'loadFirstStopSocSet': '98',    --Load First Battery SOC Stop Discharge limit (0..100)
                    'inPower': '20.0',
                    'powerMaxTime': None,
                    'vbatWarnClr': '5.0',
                    'forcedDischargeTimeStop2': '0:0',
                    'uwHFRT2EE': '0.0',
                    'forcedDischargeTimeStop3': '0:0',
                    'forcedDischargeTimeStop1': '0:0',
                    'forcedDischargeTimeStop6': '0:6',
                    'modbusVersion': '305',
                    'forcedDischargeTimeStop4': '0:0',
                    'buckUPSVoltSet': '0',
                    'forcedDischargeTimeStop5': '0:0',
                    'plantId': '0',
                    'exportLimit': '0',     --1 == Export LImitation Enabled, 0 == Disabled 
                    'energyMonthText': '0',
                    'vbatStopForCharge': '5.75',
                    'v1': '211.0',
                    'dataLogSn': 'ABCDE123456', -- a dataloggers alphanumeric serial number
                    'v2': '207.0',
                    'v3': '253.0',
                    'batteryType': '1',
                    'v4': '248.0',
                    'innerVersion': 'YBAA040489',
                    'groupId': '-1',
                    'pv_grid_voltage_high': '438.2',
                    'batFirstSwitch3': '0',
                    'forcedChargeTimeStop1': '2:0',     -- Battery First Time Slot 1 End (HH:MM)
                    'priorityChoose': '0',
                    'vbatStartForDischarge': '1.15',
                    'forcedChargeTimeStop2': '6:0',     -- Battery First Time Slot 2 End (HH:MM)
                    'forcedChargeTimeStop3': '0:0',     -- Battery First Time Slot 3 End (HH:MM)
                    'pv_active_p_rate': '100',
                    'batFirstSwitch2': '0',
                    'batFirstSwitch1': '0',
                    'countrySelected': '0',
                    'forcedChargeTimeStop4': '0:0',    -- Battery First 1 Time Slot 4 End (HH:MM)
                    'forcedChargeTimeStop5': '0:0',     -- Battery First 1 Time Slot 5 End (HH:MM)
                    'forcedChargeTimeStop6': '0:0',     -- Battery First 1 Time Slot 6 End (HH:MM)
                    'pvPfCmdMemoryState': '1',
                    'sgipEn': '0',
                    'epsFunEn': '0',    --1 == EPS (power when grid is missing mode) Enabled, 0 == Disabled
                    'uwLFRTTimeEE': '0',
                    'imgPath': './css/img/status_green.gif',
                    'region': '0',
                    'uwHVRT2EE': '0.0',
                    'lastUpdateTime': 'Wed Dec 20 06:09:18 CST 2023',
                    'pmax': '10000',
                    'uspFreqSet': '0',
                    'tcpServerIp': '47.91.95.95',
                    'wselectBaudrate': '0',
                    'uwLVRT3EE': '0.0',
                    'epsFreqSet': '1',
                    'activeRate': '100',
                    'batSysRateEnergy': '0.0',
                    'invVersion': '1',
                    'batTempLowerLimitC': '110.0',
                    'batTempLowerLimitD': '110.0',
                    'userName': None,
                    'comAddress': '1',
                    'pv_reactive_p_rate': '100',
                    'uwLVRTTimeEE': '0',
                    'uwHFRTTimeEE': '0',
                    'bctAdjust': '3',
                    'chargeTime3': None,
                    'chargeTime2': None,
                    'energyDay': '0.0',
                    'chargeTime1': None,
                    'statusText': 'mix.status.normal',
                    'forcedChargeTimeStart2': '4:0',    --Battery First Charge Time Slot 2 Start (HH:MM)
                    'forcedChargeTimeStart3': '0:0',    --Battery First Charge Time Slot 3 Start (HH:MM)
                    'batParallelNum': '0',
                    'location': '',
                    'forcedChargeTimeStart1': '1:0',    --Battery First Charge Time Slot 1 Start (HH:MM)
                    'vnormal': '360.0',
                    'forcedChargeTimeStart6': '0:0',    --Battery First 1 Charge Time Slot 6 Start (HH:MM)
                    'forcedChargeTimeStart4': '0:0',    --Battery First 1 Charge Time Slot 4 Start (HH:MM)
                    'forcedChargeTimeStart5': '0:0',    --Battery First 1 Charge Time Slot 5 Start (HH:MM)
                    'plantname': None,
                    'vbatWarning': '11.0',
                    'mcVersion': 'QBAa-8306',
                    'gridFirstSwitch1': '0',
                    'gridFirstSwitch2': '0',
                    'bctMode': '3',
                    'gridFirstSwitch3': '0',
                    'lcdLanguage': '1',
                    'pv_reactive_p_rate_two': 'over',
                    'children': None,
                    'lost': 'false',
                    'safety': '1b',
                    'model': '28547293900000',
                    'id': '0',
                    'uwHVRTTimeEE': '0',
                    'buckUpsFunEn': '0',
                    'voltageLowLimit': '338.6',
                    'serialNum': 'ABC12345',      --Inverter Serial Number
                    'uwLVRTTime2EE': '0',
                    'disChargePowerCommand': '100',
                    'powerMax': None,
                    'forcedDischargeStopSwitch2': '0',      --Grid First Time Slot 2, 1 == Enabled, 0 == Disabled
                    'forcedDischargeStopSwitch1': '0',      --Grid First Time Slot 1, 1 == Enabled, 0 == Disabled
                    'forcedDischargeStopSwitch6': '0',      --Grid First 1 Time Slot 6, 1 == Enabled, 0 == Disabled
                    'loadFirstControl': '0',                --?? Maybe controls forcing Load First Behaviour???
                    'uwHVRTEE': '0.0',
                    'forcedDischargeStopSwitch5': '2',      --Grid First 1 Time Slot 5, 1 == Enabled, 0 == Disabled
                    'forcedDischargeStopSwitch4': '0',      --Grid First 1 Time Slot 4, 1 == Enabled, 0 == Disabled
                    'forcedDischargeStopSwitch3': '0',      --Grid First Time Slot 3, 1 == Enabled, 0 == Disabled
                    'status': '6',
                    'pv_power_factor': '0.0',
                    'reactiveDelay': '3.0',
                    'parentID': 'LIST_XGD6CBD0A2_96',
                    'manufacturer': '   New Energy   ',
                    'treeID': 'ST_ABCD12345',      --Contains the Inverter Serial NUmber, Prefixed by ST ??
                    'sysTime': '2023-12-19 21:11:58',
                    'uwLFRTEE': '0.0',
                    'onOff': '1',       --Inverter On / Off, 1 == On, 0 == Off
                    'forcedDischargeTimeStart1': '0:0',     --Grid First Time Slot 1 Start Time (HH:MM)
                    'mix_off_grid_enable': '0',
                    'forcedDischargeTimeStart3': '0:0',     --Grid First Time Slot 3 Start Time (HH:MM)
                    'forcedDischargeTimeStart2': '0:0',     --Grid First Time Slot 2 Start Time (HH:MM)
                    'forcedDischargeTimeStart5': '0:0',     --Grid First 1 Time Slot 45 Start Time (HH:MM)
                    'forcedDischargeTimeStart4': '0:0',     --Grid First 1 Time Slot 4 Start Time (HH:MM)
                    'batSerialNum': None,
                    'exportLimitPowerRate': '0.0',          --Related to exportLimit
                    'forcedDischargeTimeStart6': '0:0',     --Grid First 1 Time Slot 6 Start Time (HH:MM)
                    'oldErrorFlag': '170',
                    'floatChargeCurrentLimit': '2.5',
                    'newSwVersionFlag': '0',
                    'uwLFRTTime2EE': '0',
                    'uwNominalGridVolt': '0.0',
                    'mix_ac_discharge_voltage': '0',
                    'forcedChargeStopSwitch2': '1',     --Battery First Time Slot 2, 1 == Enabled, 0 == Disabled 
                    'forcedChargeStopSwitch1': '0',     --Battery First Time Slot 1, 1 == Enabled, 0 == Disabled 
                    'uwLVRTEE': '0.0',
                    'forcedChargeStopSwitch6': '0',     --Battery First 1 Time Slot 6, 1 == Enabled, 0 == Disabled
                    'forcedChargeStopSwitch5': '0',     --Battery First 1 Time Slot 5, 1 == Enabled, 0 == Disabled 
                    'forcedChargeStopSwitch4': '0',     --Battery First 1 Time Slot 4, 1 == Enabled, 0 == Disabled 
                    'forcedChargeStopSwitch3': '0',     --Battery First Time Slot 3, 1 == Enabled, 0 == Disabled 
                    'updating': 'false',
                    'batSeriesNum': '12',
                    'lastUpdateTimeText': '2023-12-20 06:09:18',
                    'vbatStopForDischarge': '4.7',
                    'wdisChargeSOCLowLimit2': '10',     --Grid First Battery Discharge Stop SOC (0..100)
                    'wdisChargeSOCLowLimit1': '100',    --Gridt First Battery Dischatrge Effect Limit (0..100)
                    'wchargeSOCLowLimit1': '100',
                    'wchargeSOCLowLimit2': '100',       --Battery First Charge SOC Limit (0..100)
                    'epsVoltSet': '0',
                    'level': '4',
                    'uwGridWattDelay': '0',
                    'pCharge': '0.0',
                    'batTempUpperLimitC': '60.0',
                    'pv_on_off': '1',
                    'uwHVRTTime2EE': '0',
                    'batTempUpperLimitD': '70.0',
                    'pv_grid_voltage_low': '338.6',
                    'powerFactor': '0.0',
                    'sysTimeText': '2023-12-19 21:11:58',
                    'underExcited': '0',
                    'timezone': '8.0',
                    'voltageHighLimit': '438.2',
                    'portName': 'port_name',
                    'modelText': 'A1B1D0T3PFU8MASB',
                    'dtc': '3601',
                    'treeName': 'ABCD12345',   --seems to be same value as the serial of the inverter
                    'monitorVersion': 'ZEAa-8204',
                    'alias': 'ABCD12345',  --default is the serial of the inverter, alternatively the alias set for the inverter
                    'fwVersion': 'YA1.0',
                    'addr': '1',
                    'pDischarge': '0.0',
                    'uwLFRT2EE': '0.0',
                    'failsafe': '1',
                    'uwLVRTTime3EE': '0',
                    'lvVoltage': '11.5',
                    'vppOpen': '160',
                    'reactivePowerLimit': '43.0',
                    'pf_sys_year': '2023-12-19 21:11:58',   --inverters system date & time
                    'backflow_setting': '0'
                }
            },
            'normalPower': 0,
            'model': ''
        }


        """

        default_params = {
            'op': 'getMixSetParams',
            'serialNum': serial_number,
            'kind': 0
        }
        settings_params = {**default_params}
        response = self.session.get(self.get_url('newMixApi.do'), params=default_params)
        data = json.loads(response.content.decode('utf-8'))
        return data