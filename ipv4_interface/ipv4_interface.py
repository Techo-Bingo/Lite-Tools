# -*- coding: utf-8 -*-
# EulerOS 网络操作接口
# Bingo

import sys
import json
import traceback
import subprocess

class Utils:

    @classmethod
    def execute_command(cls, cmd):
        def stream_2_str(in_ss):
            out_ss = in_ss if sys.version_info[0] == 2 else str(in_ss, encoding='GBK', errors='ignore')
            return out_ss

        p = subprocess.Popen([cmd],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=True)
        out, err = p.communicate()
        ret = False if p.returncode else True
        return ret, stream_2_str(out).strip(), stream_2_str(err).strip()

    @classmethod
    def execute_stdout(cls, cmd):
        return cls.execute_command(cmd)[1]

    @classmethod
    def execute_result(cls, cmd):
        return cls.execute_command(cmd)[0]

class IPv4Address(object):

    def _bin_to_ip_str(self, ip_bin):
        """Binary convert to IP string.
        in: 11000000101010000000000000000001
        out: 192.168.0.1
        """
        start, out = 0, []
        while len(ip_bin) >= start + 8:
            end = start + 8
            a = ip_bin[start:end]
            start += 8
            b = int(a, 2)
            out.append(str(b))
        return '.'.join(out)


    def _ip_str_to_bin(self, ip_str):
        """IP string convert to binary.
        in: 192.168.0.1
        out: 11000000101010000000000000000001
        """
        out = []
        for i in ip_str.split('.'):
            out.append(bin(int(i)).replace('0b', '').rjust(8, '0'))
        return ''.join(out)

    def mask_bit_to_str(self, bit):
        """Netmask prefix bit convert to netmask string.
        in: 24
        out: 255.255.255.0
        """
        if not isinstance(bit, int) or not  (0 < bit < 32):
            return ''
        bin_data = '1' * bit + '0' * (32 - bit)
        start, end = 0, 8
        bin_list = []
        while len(bin_data) >= end:
            a = bin_data[start:end]
            start +=8
            end += 8
            b = int(a, 2)
            bin_list.append(str(b))
        return '.'.join(bin_list)

    def mask_str_to_bit(self, mask_str):
        """Netmask string convert to netmask prefix bit.
        in: 255.255.255.0
        out: 24
        """
        return sum([bin(int(s)).count('1') for s in mask_str.split('.')])

    def get_range_by_ip_mask(self, ip_str, mask_str):
        """Get IP segment by IP and netmask string.
        in: 192.168.0.1, 255.255.255.0
        out: ['192.168.0.0', '192.168.0.255']
        """
        ip_bin = self._ip_str_to_bin(ip_str)
        mask_bin = self._ip_str_to_bin(mask_str)
        one_index = mask_bin.find('0')
        mask_bin = mask_bin[0:one_index]
        ip_bin = ip_bin[0:one_index]
        net_int_addr = int(mask_bin, 2) & int(ip_bin, 2)
        with_bin_net = bin(net_int_addr).replace('0b', '').rjust(one_index, '0')
        net_bin_addr = self._bin_to_ip_str(with_bin_net.ljust(32, '0'))
        broad_bin_addr = self._bin_to_ip_str(with_bin_net.ljust(32, '1'))
        return [net_bin_addr, broad_bin_addr]

    def get_range_by_ip_bit(self, ip_str, mask_bit):
        """Get IP segment by IP and netmask prefix bit.
        in: 192.168.0.1, 24
        out: ['192.168.0.1', '192.168.0.255']
        """
        return self.get_range_by_ip_mask(ip_str, self.mask_bit_to_str(mask_bit))

    def append_ip_by_ip_bit(self, device, ip_str, mask_bit):
        """Add an IP address by IP and netmask prefix bit for device.
        in: ens33, 192.168.1.100, 24
        out: True | False
        """
        cmd = """
        nmcli con mod {0} +ipv4.addresses {1}/{2} || exit 1
        nmcli con up {0}
        """.format(device, ip_str, mask_bit)
        return Utils.execute_result(cmd)

    def append_ip_by_ip_mask(self, device, ip_str, mask_str):
        """Add an IP address by IP and netmask string for device.
        in: ens33, 192.168.1.100, 255.255.255.0
        out: True | False
        """
        return self.append_ip_by_ip_bit(device, ip_str, self.mask_str_to_bit(mask_str))

    def remove_ip_by_ip_bit(self, device, ip_str, mask_bit):
        """Remove an IP address by IP and netmask prefix bit for device.
        if IP is not exist, return True.
        in: ens33, 192.168.1.100, 24
        out: True | False
        """
        cmd = """
        nmcli dev show {0} | grep -w '{1}/{2}' >/dev/null || exit 0
        nmcli con mod {0} -ipv4.addresses {1}/{2} || exit 1
        nmcli con up {0}
        """.format(device, ip_str, mask_bit)
        return Utils.execute_result(cmd)

    def remove_ip_by_ip_mask(self, device, ip_str, mask_str):
        """Remove an IP address by IP and netmask string for device.
        in: ens33, 192.168.1.100, 255.255.255.0
        out: True | False
        """
        return self.remove_ip_by_ip_bit(device, ip_str, self.mask_str_to_bit(mask_str))

    def modify_ip_by_ip_bit(self, device, old_ip, old_bit, new_ip, new_bit):
        """Modify an IP address, set old_ip to new_ip by IP and netmask prefix bit.
        in: ens33, 192.168.1.100, 24, 192.168.1.200, 24
        out: True | False
        """
        return all([self.remove_ip_by_ip_bit(device, old_ip, old_bit),
                    self.append_ip_by_ip_bit(device, new_ip, new_bit)])

    def modify_ip_by_ip_mask(self, device, old_ip, old_mask, new_ip, new_mask):
        """Modify an IP address, set old_ip to new_ip by IP and netmask string.
        in: ens33, 192.168.1.100, 24, 192.168.1.200, 24
        out: True | False
        """
        old_bit = self.mask_str_to_bit(old_mask)
        new_bit = self.mask_str_to_bit(new_mask)
        return self.modify_ip_by_ip_bit(device, old_ip, old_bit, new_ip, new_bit)

    def query_device_ip_list(self, device):
        """Query IP list on device
        in: ens33
        out: ['192.168.1.100/24', ...]
        """
        cmd = "nmcli dev show {0} | grep -w 'IP4.ADDRESS' | awk '{{print $2}}'".format(device)
        ip_str = Utils.execute_stdout(cmd)
        return ip_str.split('\n') if ip_str else []

    def query_all_ip_dict(self):
        """Query all IP list of each device
        in: None
        out: {
                 'lo': ['127.0.0.1/8'],
                 'ens33': ['192.168.1.100/24', ...]
                 ...
             }
        """
        cmd = """
        devices=$(nmcli dev status | grep -vw 'DEVICE' | awk '{{print $1}}')
        for dev in $devices
        do
            ips=$(nmcli dev show $dev | grep -w 'IP4.ADDRESS' | awk '{{print $2}}' | tr '\n' ';')
            echo "$dev $ips"
        done
        """
        out_dict = {}
        for dev_ips in Utils.execute_stdout(cmd).split('\n'):
            dev, ips = dev_ips.split(' ')
            ips = ips.strip(';')
            ip_list = [] if not ips else ips.split(';')
            out_dict[dev] = ip_list
        return out_dict

    def device_up(self, net_card):
        """Activate device network connection.
        in: ens33
        out: True | False
        """
        cmd = "nmcli con up {0}".format(net_card)
        return Utils.execute_result(cmd)

    def device_down(self, net_card):
        """Deactivate device network connection.
        in: ens33
        out: True | False
        """
        cmd = "nmcli con down {0}".format(net_card)
        return Utils.execute_result(cmd)

    def device_restart(self, net_card):
        """restart device network connection.
        in: ens33
        out: True | False
        """
        # return all([self.device_down(net_card), self.device_up(net_card)])
        self.device_down(net_card)
        return self.self.device_up(net_card)

    def network_on(self):
        """Activate all network connection.
        in: None
        out: True | False
        """
        cmd = "nmcli net on"
        return Utils.execute_result(cmd)

    def network_off(self):
        """Deactivate all network connection.
        in: None
        out: True | False
        """
        cmd = "nmcli net off"
        return Utils.execute_result(cmd)

    def network_restart(self):
        """Restart all network connection.
        in: None
        out: True | False
        """
        return all([self.network_off(), self.network_on()])


if __name__ == '__main__':
    """
    # test case
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
    """

    try:
        operate = sys.argv[1]
        ret = True
        if operate == 'network_on':
            ret = IPv4Address().network_on()
        elif operate == 'network_off':
            ret = IPv4Address().network_off()
        elif operate == 'network_restart':
            ret = IPv4Address().network_restart()
        elif operate == 'device_down':
            ret = IPv4Address().device_down(sys.argv[2])
        elif operate == 'device_up':
            ret = IPv4Address().device_up(sys.argv[2])
        elif operate == 'device_restart':
            ret = IPv4Address().device_restart(sys.argv[2])
        elif operate == 'append_ip_by_ip_bit':
            ret = IPv4Address().append_ip_by_ip_bit(sys.argv[2], sys.argv[3], sys.argv[4])
        elif operate == 'append_ip_by_ip_mask':
            ret = IPv4Address().append_ip_by_ip_mask(sys.argv[2], sys.argv[3], sys.argv[4])
        elif operate == 'remove_ip_by_ip_bit':
            ret = IPv4Address().remove_ip_by_ip_bit(sys.argv[2], sys.argv[3], sys.argv[4])
        elif operate == 'remove_ip_by_ip_mask':
            ret = IPv4Address().remove_ip_by_ip_mask(sys.argv[2], sys.argv[3], sys.argv[4])
        elif operate == 'modify_ip_by_ip_bit':
            ret = IPv4Address().modify_ip_by_ip_bit(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
        elif operate == 'modify_ip_by_ip_mask':
            ret = IPv4Address().modify_ip_by_ip_mask(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
        elif operate == 'mask_bit_to_str':
            print(IPv4Address().mask_bit_to_str(int(sys.argv[2])))
        elif operate == 'mask_str_to_bit':
            print(IPv4Address().mask_str_to_bit(sys.argv[2]))
        elif operate == 'get_range_by_ip_mask':
            print(json.dumps(IPv4Address().get_range_by_ip_mask(sys.argv[2], sys.argv[3]), indent=4))
        elif operate == 'get_range_by_ip_bit':
            print(json.dumps(IPv4Address().get_range_by_ip_bit(sys.argv[2], sys.argv[3]), indent=4))
        elif operate == 'query_device_ip_list':
            print(json.dumps(IPv4Address().query_device_ip_list(sys.argv[2]), indent=4))
        elif operate == 'query_all_ip_dict':
            print(json.dumps(IPv4Address().query_all_ip_dict(), indent=4))

        ret = 0 if ret else 1
    except:
        sys.stderr.write(traceback.format_exc())
        ret = 2
    sys.exit(ret)

