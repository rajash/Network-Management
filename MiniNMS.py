from pysnmp.hlapi import *
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp, udp6
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from asyncClass import *
from datetime import datetime
import pandas as pd

class MiniNMS:
    
    def __init__(self, SNMP_HOST, SNMP_PORT, SNMP_COMMUNITY = 'public'):
        self.cmdGen = cmdgen.CommandGenerator()
        self.SNMP_HOST = SNMP_HOST
        self.SNMP_PORT = SNMP_PORT
        self.SNMP_COMMUNITY = SNMP_COMMUNITY
        self.errors = dict()
        self.responses = dict()
        self.responses['get'] = []
        self.errors['err-get'] = []
        self.responses['get-next'] = []
        self.errors['err-get-next'] = []
        print('done')
        
    def getResponse(self,*OID):
        errorIndication, errorStatus, errorIndex, varBinds = self.cmdGen.getCmd(
                cmdgen.CommunityData(self.SNMP_COMMUNITY),
                cmdgen.UdpTransportTarget((self.SNMP_HOST, self.SNMP_PORT)),
                *OID
            )
    
        if errorIndication:
            self.errors['err-get'].append({'time':datetime.now(),'error':errorIndication,'type':'get'})
            print(1)
        else:
            if errorStatus:
                self.errors['err-get'].append({'time':datetime.now(),'error':'%s at %s' % (
                  errorStatus.prettyPrint(),
                  errorIndex and varBinds[int(errorIndex)-1] or '?'
                  ),'type':'get'
                }
            )
                print(2)
            else:
                for varBind in varBinds:
                    if 'SNMPv2-MIB' in varBind[0].prettyPrint():
                        self.responses['get'].append({'time':datetime.now(),'OID':varBind[0].prettyPrint().replace('SNMPv2-MIB::',''),
                                                    'Response': ' '.join([x.prettyPrint() for x in varBind[1:]])
                                                     ,'type':'get'})
        return {'Errors':self.errors['err-get'], 'Responses':self.responses['get']}
    
    def getNextResponse(self, OID, max_rows=1):
        for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                                SnmpEngine(),
                                cmdgen.CommunityData(self.SNMP_COMMUNITY),
                                cmdgen.UdpTransportTarget((self.SNMP_HOST, self.SNMP_PORT)),
                                ContextData(),
                                ObjectType(ObjectIdentity(OID)),
                                maxRows=max_rows
                            ):
            if errorIndication:
                self.errors['err-get-next'].append({'time':datetime.now(),'error':errorIndication,'type':'get next'})
            else:
                if errorStatus:
                    self.errors['err-get-next'].append({'time':datetime.now(),'error':'%s at %s' % (
                      errorStatus.prettyPrint(),
                      errorIndex and varBinds[int(errorIndex)-1] or '?'
                      ),'type':'get next'
                    }
                )
                else:
                    for varBind in varBinds:
                        if 'SNMPv2-MIB' in varBind[0].prettyPrint():
                            self.responses['get-next'].append({'time':datetime.now(),'OID':varBind[0].prettyPrint().replace('SNMPv2-MIB::',''),
                                                    'Response': ' '.join([x.prettyPrint() for x in varBind[1:]])
                                                              ,'type':'get next'})
        return {'Errors':self.errors['err-get-next'], 'Responses': self.responses['get-next']}
        
    def listenForTraps(self):
        asyncF = asyncFunc()
        transportDispatcher = AsyncoreDispatcher()

        transportDispatcher.registerRecvCbFun(asyncF.cbFun)

        transportDispatcher.registerTransport(
            udp.domainName, udp.UdpSocketTransport().openServerMode((self.SNMP_HOST, self.SNMP_PORT))
        )

        transportDispatcher.jobStarted(1)

        try:
            # Dispatcher will never finish as job#1 never reaches zero
            transportDispatcher.runDispatcher()

        finally:
            transportDispatcher.closeDispatcher()
            
    def saveLogs(self):
        getResponses = pd.DataFrame(self.responses['get'])
        getResponses = pd.concat([getResponses, pd.DataFrame(self.responses['get-next'])])
        getResponses_file = 'Get Responses %s.csv'% datetime.now()
        getResponses.to_csv(getResponses_file)
               
        self.responses['get-next'] = dict()
        getResponsesErrors = pd.DataFrame(self.errors['err-get'])
        getResponsesErrors = pd.concat([getResponsesErrors, pd.DataFrame(self.errors['err-get-next'])])
        getResponsesErrors_file = 'Get Responses Errors %s.csv'% datetime.now()
        getResponsesErrors.to_csv(getResponsesErrors_file)
        
        return {'Responses filename':getResponses_file, 'Errors filename':getResponsesErrors_file}