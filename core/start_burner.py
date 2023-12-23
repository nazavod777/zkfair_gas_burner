import asyncio

from eth_abi import encode
from eth_account import Account
from eth_account.account import LocalAccount
from loguru import logger
from web3 import Web3
from web3.auto import w3
from web3.eth import AsyncEth

from data import config, constants
from utils.misc import get_nonce


class Burner:
    def __init__(self,
                 private_key: str,
                 proxy: str):
        self.private_key: str = private_key
        self.proxy: str = proxy
        self.account: LocalAccount = Account.from_key(private_key=private_key)

    @staticmethod
    async def get_tx_deadline_timestamp(provider):
        block = await provider.eth.get_block('latest')
        return block['timestamp'] + 600

    def get_data(self,
                 deadline_timestamp: int):
        return '0x7ff36ab5' + encode(types=constants.abi_types,
                                     args=(8, (constants.usdc_address, constants.usdt_address),
                                           self.account.address.lower(), deadline_timestamp)).hex()

    async def send_transaction(self,
                               provider,
                               nonce: int,
                               tx_data: str) -> str:
        gwei: float = w3.to_wei(number=config.GWEI,
                                unit='gwei')

        transaction_data: dict = {
            'nonce': nonce,
            'to': constants.swap_address,
            'value': w3.to_wei(number=0.00001,
                               unit='ether'),
            'gas': config.GAS_LIMIT,
            'gasPrice': gwei,
            'data': tx_data
        }

        signed_transaction = provider.eth.account.sign_transaction(transaction_dict=transaction_data,
                                                                   private_key=self.account.key)

        await provider.eth.send_raw_transaction(signed_transaction.rawTransaction)

        transaction_hash: str = w3.to_hex(w3.keccak(signed_transaction.rawTransaction))

        return transaction_hash

    async def start_burner(self) -> None:
        provider = Web3(Web3.AsyncHTTPProvider(endpoint_uri=config.RPC_URL,
                                               request_kwargs={
                                                   'proxy': self.proxy
                                               }),
                        modules={'eth': (AsyncEth,)},
                        middlewares=[])

        while True:
            try:
                nonce: int = await get_nonce(provider=provider,
                                             address=self.account.address)
                deadline_timestamp: int = await self.get_tx_deadline_timestamp(provider=provider)
                tx_data: str = self.get_data(deadline_timestamp=deadline_timestamp)

            except Exception as error:
                logger.error(f'{self.account.address} | Неизвестная ошибка при получении данных кошелька: {error}')

            else:
                break

        for i in range(5):
            while True:
                try:
                    tx_hash: str = await self.send_transaction(provider=provider,
                                                               nonce=nonce,
                                                               tx_data=tx_data)

                except Exception as error:
                    if "'insufficient funds for gas * price + value'" in str(error):
                        logger.error(f'{self.account.address} | Low Balance')
                        return

                    if "'already known'" in str(error):
                        logger.info(f'{self.account.address} | Already Known')
                        nonce += 1
                        continue

                    if "'nonce too high'" in str(error):
                        logger.info(f'{self.account.address} | Nonce Too High')
                        nonce -= 1
                        continue

                    if "'nonce too low'" in str(error):
                        logger.info(f'{self.account.address} | Nonce Too Low')
                        nonce += 1
                        continue

                    logger.error(f'{self.account.address} | Неизвестная ошибка при отправке транзакции: {error}')

                else:
                    logger.success(f'{self.account.address} | {self.account.key.hex()} - {tx_hash} | [{i + 1}/5]')
                    nonce += 1
                    break


async def start_burner(private_key: str,
                       proxy: str,
                       semaphore: asyncio.Semaphore) -> None:
    async with semaphore:
        try:
            await Burner(private_key=private_key,
                         proxy=proxy).start_burner()

        except Exception as error:
            from traceback import format_exc
            print(format_exc())
            logger.error(f'{private_key} | Unexpected Error: {error}')
