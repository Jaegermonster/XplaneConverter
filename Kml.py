class KML:
    def __init__(self, trackname):
        self.filename = trackname + '.kml'
        self.out = open(self.filename, 'w')

    def write_header(self):
        self.out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.out.write('<kml xmlns="http://www.opengis.net/kml/2.2" ' \
                'xmlns:gx="http://www.google.com/kml/ext/2.2" ' \
                'xmlns:kml="http://www.opengis.net/kml/2.2" ' \
                'xmlns:atom="http://www.w3.org/2005/Atom">\n')
        self.out.write('<Document>\n')
        self.out.write(f'    <name>{self.filename}</name>\n')
        self.out.write('    <StyleMap id="routeStyle">\n')
        self.out.write('        <Pair>\n')
        self.out.write('            <key>normal</key>\n')
        self.out.write('            <styleUrl>#routeStyle0</styleUrl>\n')
        self.out.write('        </Pair>\n')
        self.out.write('        <Pair>\n')
        self.out.write('            <key>highlight</key>\n')
        self.out.write('            <styleUrl>#routeStyle1</styleUrl>\n')
        self.out.write('        </Pair>\n')
        self.out.write('    </StyleMap>\n')
        self.out.write('    <Style id="routeStyle0">\n')
        self.out.write('        <LineStyle>\n')
        self.out.write('            <color>7fff0055</color>\n')
        self.out.write('            <width>3</width>\n')
        self.out.write('        </LineStyle>\n')
        self.out.write('    </Style>\n')
        self.out.write('    <Style id="routeStyle1">\n')
        self.out.write('        <LineStyle>\n')
        self.out.write('            <color>7fff0055</color>\n')
        self.out.write('            <width>3</width>\n')
        self.out.write('        </LineStyle>\n')
        self.out.write('    </Style>\n')
        self.out.write('    <Placemark>\n')
        self.out.write('        <styleUrl>#routeStyle</styleUrl>\n')
        self.out.write('        <MultiGeometry>\n')
        self.out.write('            <extrude>1</extrude>\n')
        self.out.write('            <altitudeMode>absolute</altitudeMode>\n')
        self.out.write('            <LineString>\n')
        self.out.write('                <extrude>1</extrude>\n')
        self.out.write('                <altitudeMode>absolute</altitudeMode>\n')
        self.out.write('                <coordinates>\n')

    def write_point(self, lat, lon, alt):
        self.out.write(f'                    {lon:.7f},{lat:.7f},{alt:.1f}\n')

    def write_footer(self):
        self.out.write('                </coordinates>\n')
        self.out.write('            </LineString>\n')
        self.out.write('        </MultiGeometry>\n')
        self.out.write('    </Placemark>\n')
        self.out.write('</Document>\n')
        self.out.write('</kml>\n')
