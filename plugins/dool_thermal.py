### Author: Dag Wieers <dag@wieers.com>

# Syntax:
#    show only specific thermal zones (by the nick shown in the header):
#       DOOL_THERMAL_ZONES=tz0,tz2 dool --thermal

class dool_plugin(dool):
    def __init__(self):
        self.name = 'thermal'
        self.type = 'd'
        self.width = 3
        self.scale = 20

        if os.path.exists('/sys/devices/virtual/thermal/'):
            zones = []
            for zone in os.listdir('/sys/devices/virtual/thermal/'):
                zone_split = zone.split("thermal_zone")
                if len(zone_split) == 2:
                    zones.append(zone)

            # Sort numerically (thermal_zone0, thermal_zone1, ..., thermal_zone10)
            # rather than the arbitrary order os.listdir() returns.
            zones.sort(key=lambda z: int(z.split("thermal_zone")[1]))

            self.vars = []
            self.nick = []
            for zone in zones:
                name = "".join(["tz", zone.split("thermal_zone")[1]])
                self.vars.append(zone)
                self.nick.append(name)

        elif os.path.exists('/sys/bus/acpi/devices/LNXTHERM:01/thermal_zone/'):
            self.vars = sorted(os.listdir('/sys/bus/acpi/devices/LNXTHERM:01/thermal_zone/'))
            self.nick = []
            for name in self.vars:
                self.nick.append(name.lower())

        elif os.path.exists('/proc/acpi/ibm/thermal'):
            self.namelist = ['cpu', 'pci', 'hdd', 'cpu', 'ba0', 'unk', 'ba1', 'unk']
            self.nick = []
            for line in dopen('/proc/acpi/ibm/thermal'):
                l = line.split()
                for i, name in enumerate(self.namelist):
                    if int(l[i+1]) > 0:
                        self.nick.append(name)
            self.vars = self.nick

        elif os.path.exists('/proc/acpi/thermal_zone/'):
            self.vars = sorted(os.listdir('/proc/acpi/thermal_zone/'))
            self.nick = []
            for name in self.vars:
                self.nick.append(name.lower())

        else:
            raise Exception('Needs kernel thermal, ACPI or IBM-ACPI support')

        self.filter_zones()

    def check(self):
        if not os.path.exists('/proc/acpi/ibm/thermal') and \
           not os.path.exists('/proc/acpi/thermal_zone/') and \
           not os.path.exists('/sys/devices/virtual/thermal/') and \
           not os.path.exists('/sys/bus/acpi/devices/LNXTHERM:00/thermal_zone/'):
            raise Exception('Needs kernel thermal, ACPI or IBM-ACPI support')

    # Optionally restrict which zones are displayed via the
    # DOOL_THERMAL_ZONES env var, a comma separated list of nicks as
    # shown in the header (e.g. "tz0,tz2"). Unset/empty means show all.
    def filter_zones(self):
        filter_str = os.getenv('DOOL_THERMAL_ZONES', '').strip()
        if not filter_str:
            return

        wanted = [z.strip() for z in filter_str.split(',') if z.strip()]
        if not wanted:
            return

        filtered_vars = []
        filtered_nick = []
        for var, nick in zip(self.vars, self.nick):
            if nick in wanted or var in wanted:
                filtered_vars.append(var)
                filtered_nick.append(nick)

        missing = array_diff(wanted, self.nick + self.vars)
        for item in missing:
            msg = text_color(214, "Warning: unable to find thermal zone %s" % item)
            print(msg)

        if filtered_vars:
            self.vars = filtered_vars
            self.nick = filtered_nick

    def extract(self):
        if os.path.exists('/sys/devices/virtual/thermal/'):
            for zone in self.vars:
                for line in dopen('/sys/devices/virtual/thermal/'+zone+'/temp').readlines():
                    l = line.split()
                    self.val[zone] = int(l[0])
        elif os.path.exists('/sys/bus/acpi/devices/LNXTHERM:01/thermal_zone/'):
            for zone in self.vars:
                if os.path.isdir('/sys/bus/acpi/devices/LNXTHERM:01/thermal_zone/'+zone) == False:
                    for line in dopen('/sys/bus/acpi/devices/LNXTHERM:01/thermal_zone/'+zone).readlines():
                        l = line.split()
                        if l[0].isdigit() == True:
                            self.val[zone] = int(l[0])
                        else:
                            self.val[zone] = 0
        elif os.path.exists('/proc/acpi/ibm/thermal'):
            for line in dopen('/proc/acpi/ibm/thermal'):
                l = line.split()
                for i, name in enumerate(self.namelist):
                    if int(l[i+1]) > 0:
                        self.val[name] = int(l[i+1])
        elif os.path.exists('/proc/acpi/thermal_zone/'):
            for zone in self.vars:
                for line in dopen('/proc/acpi/thermal_zone/'+zone+'/temperature').readlines():
                    l = line.split()
                    self.val[zone] = int(l[1])

# vim:ts=4:sw=4:et
