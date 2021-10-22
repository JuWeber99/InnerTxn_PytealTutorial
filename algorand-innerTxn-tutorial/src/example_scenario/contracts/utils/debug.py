from algosdk import algod_client
# dryrun_debug returns a response with disassembly, logic-sig-messages w PASS/REJECT and sig-trace
# dryrun source if provided, else dryrun compiled
def dryrun_debug(lstx, mysource):
    sources = []
    if (mysource != None):
        # source
        sources = [DryrunSource(field_name="lsig", source=mysource, txn_index=0)]
    drr = DryrunRequest(txns=[lstx], sources=sources)
    dryrun_response = algod_client.dryrun(drr)
    return dryrun_response