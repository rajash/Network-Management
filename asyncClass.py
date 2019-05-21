class asyncClass:
    def __init__(self):
        pass
    
    def cbFun(self, transportDispatcher, transportDomain, transportAddress, wholeMsg):
        while wholeMsg:
            msgVer = int(api.decodeMessageVersion(wholeMsg))

            if msgVer in api.protoModules:
                pMod = api.protoModules[msgVer]    
            else:
                print('Unsupported SNMP version %s' % msgVer)
                return

            reqMsg, wholeMsg = decoder.decode(
                wholeMsg, asn1Spec=pMod.Message()
            )

            print('Notification message from %s:%s: ' % (transportDomain,
                                                         transportAddress))

            reqPDU = pMod.apiMessage.getPDU(reqMsg)
            if reqPDU.isSameTypeWith(pMod.TrapPDU()):
                if msgVer == api.protoVersion1:
                    print('Enterprise: %s' % (pMod.apiTrapPDU.getEnterprise(reqPDU).prettyPrint()))
                    print('Agent Address: %s' % (pMod.apiTrapPDU.getAgentAddr(reqPDU).prettyPrint()))
                    print('Generic Trap: %s' % (pMod.apiTrapPDU.getGenericTrap(reqPDU).prettyPrint()))
                    print('Specific Trap: %s' % (pMod.apiTrapPDU.getSpecificTrap(reqPDU).prettyPrint()))
                    print('Uptime: %s' % (pMod.apiTrapPDU.getTimeStamp(reqPDU).prettyPrint()))
                    varBinds = pMod.apiTrapPDU.getVarBinds(reqPDU)

                else:
                    varBinds = pMod.apiPDU.getVarBinds(reqPDU)

                print('Var-binds:')

                for oid, val in varBinds:
                    print('%s = %s' % (oid.prettyPrint(), val.prettyPrint()))

        return wholeMsg