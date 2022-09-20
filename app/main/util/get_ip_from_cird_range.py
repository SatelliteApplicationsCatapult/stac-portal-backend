import ipaddress
from typing import List


def get_ip_from_cird_range(cird_range: str,
                           remove_unusable: bool = True) -> List[str]:
    ips = [str(ip) for ip in ipaddress.IPv4Network(cird_range)]
    if remove_unusable and len(ips) > 2:
        # only remove unusable if the flag is set and there are more than 2 ips (network and broadcast)
        ips = ips[1:-1]
    return ips
