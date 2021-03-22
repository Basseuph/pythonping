import sys
from . import network, executor, payload_provider
from .utils import random_text
from random import randint


# this needs to be available across all thread usages and will hold ints
SEED_IDs = []


def ping(target,
         timeout=2,
         count=4,
         size=1,
         payload=None,
         sweep_start=None,
         sweep_end=None,
         df=False,
         verbose=False,
         out=sys.stdout,
         match=False,
         overall_timeout=float("inf")
    ):
    """Pings a remote host and handles the responses

    :param target: The remote hostname or IP address to ping
    :type target: str
    :param timeout: Time in seconds before considering each non-arrived reply permanently lost.
    :type timeout: Union[int, float]
    :param count: How many times to attempt the ping, set to None for infinite loop (or overall_timeout based control)
    :type count: int
    :param size: Size of the entire packet to send
    :type size: int
    :param payload: Payload content, leave None if size is set to use random text
    :type payload: Union[str, bytes]
    :param sweep_start: If size is not set, initial size in a sweep of sizes
    :type sweep_start: int
    :param sweep_end: If size is not set, final size in a sweep of sizes
    :type sweep_end: int
    :param df: Don't Fragment flag value for IP Header
    :type df: bool
    :param verbose: Print output while performing operations
    :type verbose: bool
    :param out: Stream to which redirect the verbose output
    :type out: stream
    :param match: Do payload matching between request and reply (default behaviour follows that of Windows which is
    by packet identifier only, Linux behaviour counts a non equivalent payload in reply as fail, such as when pinging
    8.8.8.8 with 1000 bytes and reply is truncated to only the first 74 of request payload with packet identifiers
    the same in request and reply)
    :type match: bool
    :param overall_timeout: the overall time the ping should be executed, default postitive infinity is chosen as per Linux default behavior of ping command
    :type overall_timeout: float
    :return: List with the result of each ping
    :rtype: executor.ResponseList"""
    provider = payload_provider.Repeat(b'', 0)
    if sweep_start and sweep_end and sweep_end >= sweep_start:
        if not payload:
            payload = random_text(sweep_start)
        provider = payload_provider.Sweep(payload, sweep_start, sweep_end)
    elif size and size > 0:
        if not payload:
            payload = random_text(size)
        provider = payload_provider.Repeat(payload, count)
    options = ()
    if df:
        options = network.Socket.DONT_FRAGMENT

    # Fix to allow for pythonping multithreaded usage;
    # no need to protect this loop as no one will ever surpass 0xFFFF amount of threads
    while True:
        # seed_id needs to be less than or equal to 65535 (as original code was seed_id = getpid() & 0xFFFF)
        seed_id = randint(0x1, 0xFFFF)
        if seed_id not in SEED_IDs:
            SEED_IDs.append(seed_id)
            break

    comm = executor.Communicator(target, provider, timeout,
                                 socket_options=options, verbose=verbose,
                                 output=out, seed_id=seed_id,
                                 overall_timeout=overall_timeout
                                )
    comm.run(match_payloads=match)

    SEED_IDs.remove(seed_id)

    return comm.responses
