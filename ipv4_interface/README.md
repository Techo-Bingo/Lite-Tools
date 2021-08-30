# CentOS IPv4 操作库

> test case
```
ipv4 = IPv4Address()
dev = 'ens33'
print(ipv4.mask_str_to_bit('255.255.255.0'))
print(ipv4.mask_bit_to_str(24))
print(ipv4.get_range_by_ip_mask('192.168.1.1', '255.255.255.0'))
print(ipv4.get_range_by_ip_bit('192.168.1.1', 24))
print(ipv4.query_device_ip_list(dev))
print(ipv4.query_all_ip_dict())

print(ipv4.append_ip_by_ip_bit(dev, '192.168.1.100', 24))
print(ipv4.append_ip_by_ip_mask(dev, '192.168.1.200', '255.255.255.0'))
print(ipv4.modify_ip_by_ip_bit(dev, '192.168.1.100', 24, '192.168.1.101', 24))
print(ipv4.modify_ip_by_ip_mask(dev, '192.168.1.200', '255.255.255.0', '192.168.1.201', '255.255.255.0'))
print(ipv4.remove_ip_by_ip_bit(dev, '192.168.1.101', 24))
print(ipv4.remove_ip_by_ip_mask(dev, '192.168.1.201', '255.255.255.0'))

print(ipv4.device_down(dev))
print(ipv4.device_up(dev))
print(ipv4.device_restart(dev))
print(ipv4.network_on())
print(ipv4.network_off())
print(ipv4.network_restart())
```