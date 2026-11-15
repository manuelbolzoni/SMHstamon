from Nagstamon.Servers.Generic import GenericServer
import requests
import sys
import datetime as dt
from Nagstamon.Objects import (GenericHost,
                               GenericService,
                               Result)

def _calc_duration(agtlastcheck,agtlastok):
        agtfaultS = (agtlastcheck - agtlastok).total_seconds()
        # If the SMHUB agent has not received the data (agent offline)
        if agtfaultS == 0:
            agtlastcheck = dt.datetime.now()
            agtfaultS = (agtlastcheck - agtlastok).total_seconds()
        agtfaultM, agtfaultS = divmod(agtfaultS, 60)
        agtfaultH, agtfaultM = divmod(agtfaultM, 60)
        agtfaultD, agtfaultH = divmod(agtfaultH, 24)
        agtfaultW, agtfaultD = divmod(agtfaultD, 7)
        agtduration = str(round(agtfaultW)) + "w " + str(round(agtfaultD)) + "d " + str(round(agtfaultH)) + "h " + str(round(agtfaultM)) + "m " + str(round(agtfaultS)) + "s"
        return agtduration
class SMHubServer(GenericServer):
    """
	SMHUB (SAP Monitor Hub)
Powerful modular and secure monitoring tool ideal for systems that deliver SAP applications: local and/or remote agents monitor the system, using owned schedulers, communicating anomalies   via non permanent connections and/or remote monitoring.
 All communications to SMHUB are via HTTP/ HTTPS protocol, allowing a controlled traffic management from small to large companies. No sensitive data is sent/stored.
No authentication required.
    """

    TYPE = u'SMHUB'
    SERVICE_SEVERITY_CODE_TEXT_MAP = dict()
    MENU_ACTIONS = []
    BROWSER_URLS = {'monitor': '$MONITOR$',
                        'hosts': '$MONITOR$', \
                    'services': '$MONITOR$', \
                    'history': '$MONITOR$'}


    def __init__(self, **kwds):
        GenericServer.__init__(self, **kwds)
        self.username = 'nouser'
        self.password = 'nouser'
        self.STATES_MAPPING = {
            'operating': 'OK',
            'warning': 'WARNING',
            'critical': 'CRITICAL',
            'unknow': 'UNKNOWN',
            'unknown': 'UNKNOWN'
        }


    def _get_status(self):
        '''Get status from SMHUB SERVER'''
        # new_hosts dictionary
        self.new_hosts = dict()
        try:
            self.init_HTTP()
            result = self.session.get(url=self.monitor_url, timeout=self.timeout)
            result.raise_for_status()
            if(result.status_code==200):
                json_res = result.json()
                agents = {k:v for (k,v) in json_res['agents'].items() if v['status'] not in ['disabled','operating']}
                host_name = json_res['summary']['label'].upper()
                self.new_hosts[host_name] = GenericHost()
                self.new_hosts[host_name].name = host_name
                self.new_hosts[host_name].server = self.name
                self.new_hosts[host_name].status = 'UP'
                for agent in agents:
                    service_name = f"{agents[agent]['name'].upper()} ({agents[agent]['component'].upper()})"
                    service_status = agents[agent]["status"]
                    service_status_info = (agents[agent].get("notes") or "").upper()
                    last_check = dt.datetime.strptime(agents[agent]["lastcheck"], "%H:%M:%S %d/%m/%Y")
                    last_ok = dt.datetime.strptime(agents[agent]["lastok"], "%H:%M:%S %d/%m/%Y")
                    duration = _calc_duration(last_check,last_ok)
                    if not service_name in self.new_hosts[host_name].services:
                        self.new_hosts[host_name].services[service_name] = GenericService()
                        self.new_hosts[host_name].services[service_name].host = host_name
                        self.new_hosts[host_name].services[service_name].name = service_name
                        self.new_hosts[host_name].services[service_name].server = self.name
                        self.new_hosts[host_name].services[service_name].last_check = last_check.strftime('%Y-%m-%d %H:%M:%S')
                        self.new_hosts[host_name].services[service_name].status = self.STATES_MAPPING[service_status]
                        self.new_hosts[host_name].services[service_name].status_information = service_status_info
                        self.new_hosts[host_name].services[service_name].duration = duration
                        
            else:
                return Result(result='ERROR', error='Unexpected SMHUB HTTP status: {}'.format(result.status_code),
                              status_code=result.status_code)
            return Result()
                        


        except Exception:
            self.new_hosts.clear()

            # set checking flag back to False
            self.isChecking = False
            result, error = self.Error(sys.exc_info())
            return Result(result=result, error=error)
    

    def init_HTTP(self):
        # Reuse one session per server, including configured TLS and proxy settings.
        # SMHUB API URLs require no HTTP authentication.
        if self.session is None:
            self.session = self.create_session()
            self.session.auth = NoAuth()
        return True

class NoAuth(requests.auth.AuthBase):
    """
        Override to avoid auth headers
        Needed for LDAP login
    """

    def __call__(self, r):
        return r
