from abc import get_cache_token
import base64
from enum import Enum
from os import read
from algosdk.v2client import algod
from algosdk.future import transaction as algo_txn
from typing import List, Any, Optional
from algosdk import account as algo_acc
from algosdk import transaction
from pyteal import Bytes


class ChainGlobals(Enum):
    tealVersion = 5
    applicationWalletAddress = Bytes("here is the dev address")


class AuctionAppNotes(Enum):
    biddingNote = Bytes("innerTxn tut pyteal - juw99")
    creationNote = Bytes("innerTxn tut pyteal - juw99")
    closingNote = Bytes("innerTxn tut pyteal - juw99")


algod_address = "http://172.18.0.4:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
algod_client = algod.AlgodClient(algod_token, algod_address)
user1 = "CTVACV76YEM424JPHBH6CRR7R4AIBZ37A3CZNI3DZASWIRUC6CTA6DHBTY"
user2 = "NCJEBHZNYU2WV5QAKYRMSEKDYMYE2AURPQ45CWDZCR5BHS4K3FORLQR3EY"
user3 = "PNUHNACMXFAIMEBG5DVMJ3JFKCSKWNXMCGRGTGG4MRNCRKED65AEBBQH2Y"

sender = user1

params = algod_client.suggested_params()
# comment out the next two (2) lines to use suggested fees
params.flat_fee = True
params.fee = 1000


funding_txn = 
