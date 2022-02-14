from algosdk import *
from pyteal import *
from algosdk.v2client.algod import AlgodClient
import dex
from dotenv import dotenv_values

config = dotenv_values(".env")
# Create Account
secret_poetry = config["SECRET_POETRY"]
try:
    pk = mnemonic.to_public_key(secret_poetry)  # Public Key
    sk = mnemonic.to_private_key(secret_poetry)  # Secret Key
except error.WrongMnemonicLengthError:
    quit(f"Invalid mnemonic. Please update your mnemonic before running.")

algod_token = config["ALGOD_TOKEN"]  # Algod API Key
algod_address = "https://testnet-algorand.api.purestake.io/ps2"  # Algod Node Address
algod_header = {"X-API-Key": algod_token}
algod_client = AlgodClient(algod_token, algod_address, algod_header)


try:
    algod_client.status()
except error.AlgodHTTPError:
    quit(f"algod node connection failure\n Check if the Host and API key are correct")

# compile the pyteal contract
approval_teal = compileTeal(dex.approval(), Mode.Application, version=5)
clearstate_teal = compileTeal(dex.clear(), Mode.Application, version=5)

# convert TEAL to bytecode (gets encoded in base64)
approval_b64 = algod_client.compile(approval_teal)["result"]
clearstate_b64 = algod_client.compile(clearstate_teal)["result"]

# Decode the encoded TEAL
approval_prog = encoding.base64.b64decode(approval_b64)
clearstate_prog = encoding.base64.b64decode(clearstate_b64)

# txn params
sp = algod_client.suggested_params()
sp.flat_fee = True
sp.fee = 2_000

# deploy contract
appTxn = future.transaction.ApplicationCreateTxn(
    pk,
    sp,
    future.transaction.OnComplete.NoOpOC,
    approval_prog,
    clearstate_prog,
    future.transaction.StateSchema(5, 10),
    future.transaction.StateSchema(5, 10),
)

sAppTxn = appTxn.sign(sk)
txid = algod_client.send_transaction(sAppTxn)
future.transaction.wait_for_confirmation(algod_client, txid)
print("\x1b[32mApp deployed successfully\x1b[0m")
print("========================================")
print(f"https://testnet.algoexplorer.io/tx/{txid}")
