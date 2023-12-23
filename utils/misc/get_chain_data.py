import web3.auto


async def get_chain_id(provider: web3.auto.Web3) -> int:
    while True:
        try:
            return await provider.eth.chain_id

        except Exception:
            pass


async def get_nonce(provider: web3.auto.Web3,
                    address: str) -> int:
    while True:
        try:
            return await provider.eth.get_transaction_count(account=address)

        except Exception:
            pass


async def get_gwei(provider: web3.auto.Web3) -> int:
    while True:
        try:
            return await provider.eth.gas_price

        except Exception:
            pass
