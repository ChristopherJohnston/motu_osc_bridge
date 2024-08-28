import asyncio
import logging
from typing import Optional, Any, cast
from motu_osc_bridge.datastore_client import DatastoreClient
from zeroconf import IPVersion, Zeroconf, ServiceStateChange
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo, AsyncZeroconf
from pythonosc import udp_client


logger: logging.Logger = logging.getLogger(__name__)


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("motu_osc_bridge.log"), logging.StreamHandler()],
)

_PENDING_TASKS: set[asyncio.Task] = set()


class MotuOscBridge:
    """
    Listens for datastore udpates on the AVB server and passes them on as
    OSC messages to the OSC server.
    """
    def __init__(self, osc_service_name: str, avb_server_uri: str) -> None:
        self.osc_service_name: str = osc_service_name
        self.client_id: int = DatastoreClient.generate_client_id()
        self.datastore_client: DatastoreClient = DatastoreClient(avb_server_uri, self.client_id)
        self.osc_client: Optional[udp_client.SimpleUDPClient] = None

    def async_on_service_state_change(
        self, 
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange
    ) -> None:
        """
        ZeroConf callback when a service is Added, Updated or Deleted. React to these events accordingly.
        """
        logger.info(f"Service {name} of type {service_type} state changed: {state_change}")

        if name != self.osc_service_name:
            logger.info(f"Service '{name}' not expected, continuing to wait for '{self.osc_service_name}...")
            return
        
        state_change_fn_map = {
            ServiceStateChange.Added: self._service_added,
            ServiceStateChange.Updated: self._service_updated,
            ServiceStateChange.Removed: self._service_removed
        }

        task = asyncio.ensure_future(state_change_fn_map[state_change](zeroconf, service_type, name))
        _PENDING_TASKS.add(task)
        task.add_done_callback(_PENDING_TASKS.discard)

    def _message_callback(self, message: dict[str, Any]):
        """
        Callback for when an AVB Datastore update is received.

        Iterate through the items and send as OSC messages to the OSC Server.
        """
        for k, v in message.items():
            logger.info(f"Sending {k}: {v}")
            osc_client = cast(udp_client.SimpleUDPClient, self.osc_client)
            osc_client.send_message(k, v)

    async def _connect_osc_server(self, ip_address: str, port: Optional[int]=9000) -> None:
        """
        Connect to the OSC Server at the provided ip and port.
        """
        logger.info(f"Connecting to UDP OSC Server at {ip_address}:{port}")
        self.osc_client = udp_client.SimpleUDPClient(ip_address, port)

    async def _get_ip_and_port(self, zeroconf: Zeroconf, service_type: str, name: str) -> tuple:
        """
        Find the IP address and port for the service.
        """
        info = AsyncServiceInfo(service_type, name)
        await info.async_request(zeroconf, 3000)
        logger.info(f"service info: {info}")
        ip = info.parsed_addresses(IPVersion.V4Only)[0]
        return ip, info.port    

    async def _service_added(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        """
        When the OSC Server is added, connect to it and start listening for AVB Datastore updates.
        """
        ip, port = await self._get_ip_and_port(zeroconf, service_type, name)
        logger.info(f"Service {name} added.")
        await self._connect_osc_server(ip, port)
        await self.datastore_client.run(self._message_callback)

    async def _service_updated(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        """
        When the OSC Server is updated, re-connect to it.
        """
        ip, port = await self._get_ip_and_port(zeroconf, service_type, name)
        logger.info(f"Service {name} updated.")
        await self._connect_osc_server(ip, port)

    async def _service_removed(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        """
        When the OSC server goes away, stop the datastore client.
        """
        logger.info(f"Service {name} removed.")
        self.osc_client = None
        self.datastore_client.stop()


class AsyncRunner:
    """
    Async Runner for ZeroConf. Listens for ZeroConf services of the provided
    service_types and passes Add, Update, Remove events to the provided OscBridge.
    """
    def __init__(self, service_types: list[str], bridge: MotuOscBridge) -> None:
        self.service_types: list[str] = service_types
        self.aiobrowser: Optional[AsyncServiceBrowser] = None
        self.aiozc: Optional[AsyncZeroconf] = None
        self.bridge: MotuOscBridge = bridge

    async def async_run(self) -> None:
        """
        Run the browser loop, checking for service changes.
        """
        self.aiozc = AsyncZeroconf(ip_version=IPVersion.V4Only)
        await self.aiozc.zeroconf.async_wait_for_start()

        self.aiobrowser = AsyncServiceBrowser(
            self.aiozc.zeroconf,
            self.service_types,
            handlers=[self.bridge.async_on_service_state_change]
        )

        while True:
            await asyncio.sleep(1)

    async def async_close(self) -> None:
        """
        Closes the ZeroConf connections.
        """
        assert self.aiozc is not None
        assert self.aiobrowser is not None
        await self.aiobrowser.async_cancel()
        await self.aiozc.async_close()


def main(service_name: str, avb_server_uri: str) -> None:
    """
    Create the OSC Bridge Service.
    """
    loop = asyncio.get_event_loop()

    # Listen for OSC UDP Services on ZeroConf.
    service_type_osc = "_osc._udp.local."
    
    # Instantiate the OSC Bridge which will start listening for
    # datastore updates on the AVB server when the target OSC server is found.
    bridge = MotuOscBridge(
        osc_service_name=f"{service_name}.{service_type_osc}",
        avb_server_uri=avb_server_uri
    )

    # Instantiate the AsyncRunner to listen for services.
    runner = AsyncRunner([service_type_osc], bridge)

    # Exit on ctrl+c
    try:
        loop.run_until_complete(runner.async_run())
    except KeyboardInterrupt:
        loop.run_until_complete(runner.async_close())


if __name__ == "__main__":
    service_name = "iPhone" # "iPhone [iPhone] (TouchOSC)"
    main(service_name=service_name, avb_server_uri="http://localhost:8888")