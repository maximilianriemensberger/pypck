"""Heartbeat tests."""
from datetime import datetime

import pytest
from pypck.lcn_addr import LcnAddr


@pytest.mark.asyncio
async def test_no_heartbeat_alive_last_seen(pchk_server, pypck_client):
    """Test heartbeat alive and last seen fields while not activated."""
    await pypck_client.async_connect()
    mod = pypck_client.get_address_conn(LcnAddr(0, 10, False))

    start = datetime.now()

    assert not mod.alive
    assert mod.last_seen < start

    assert await pchk_server.received(">M000010.SN")
    message = "=M000010.SN1AB20A123401FW190B11HW015"
    await pchk_server.send_message(message)
    assert await pypck_client.received(message)

    assert mod.alive
    assert mod.last_seen >= start


@pytest.mark.asyncio
async def test_heartbeat_lost_and_alive(pchk_server, pypck_client):
    """Test heartbeat signal loss and recovery."""
    pypck_client.settings["HEARTBEAT_INTERVAL_MSEC"] = 10
    pypck_client.settings["HEARTBEAT_MAX_LOST"] = 3
    pypck_client.settings["DEFAULT_TIMEOUT_MSEC"] = 10
    pypck_client.settings["NUM_TRIES"] = 1

    await pypck_client.async_connect()

    mod = pypck_client.get_address_conn(LcnAddr(0, 10, False))

    assert await pchk_server.received(">M000010.SN")
    message = "=M000010.SN1AB20A123401FW190B11HW015"
    await pchk_server.send_message(message)
    assert await pypck_client.received(message)

    start = datetime.now()
    mod.activate_heartbeat()

    assert await pchk_server.received(">M000010!LEER")
    assert await pchk_server.received(">M000010!LEER")
    assert await pchk_server.received(">M000010!LEER")
    assert await pchk_server.received(">M000010!LEER")

    assert not mod.alive
    assert mod.last_seen <= start
    await mod.wait_for_heartbeat_lost()

    start = datetime.now()

    message = "-M000010!"
    await pchk_server.send_message(message)
    assert await pypck_client.received(message)

    assert mod.alive
    assert mod.last_seen >= start
    await mod.wait_for_heartbeat_alive()
