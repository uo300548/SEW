import os
import xml.etree.ElementTree as ET


class XmlToKml:
    """Genera un fichero KML a partir de un XML de etapa."""

    def __init__(self, xml_path="etapaEsquema.xml", kml_path="etapa.kml"):
        self.xml_path = xml_path
        self.kml_path = kml_path
        self.namespace = {'ns': 'http://www.uniovi.es'}
        self.arbol = None
        self.raiz = None
        self.kml = None
        self.document = None

    def cargar_xml(self):
        """Carga el árbol XML en memoria."""
        self.arbol = ET.parse(self.xml_path)
        self.raiz = self.arbol.getroot()

    def obtener_primero(self, xpath):
        """Devuelve el primer nodo que coincide con la expresión XPath."""
        if self.raiz is None:
            return None
        return self.raiz.find(xpath, self.namespace)

    def obtener_nodos(self, xpath):
        """Devuelve todos los nodos coincidentes con la expresión XPath."""
        if self.raiz is None:
            return []
        return self.raiz.findall(xpath, self.namespace)

    def obtener_texto(self, nodo, xpath):
        """Obtiene el texto de un nodo XPath."""
        if nodo is None:
            return ""
        elemento = nodo.find(xpath, self.namespace)
        if elemento is None or elemento.text is None:
            return ""
        return elemento.text.strip()

    def obtener_coordenada(self, nodo):
        """Extrae longitud, latitud y altitud desde un nodo lugar o punto."""
        if nodo is None:
            return None
        coord = nodo.find('./ns:coordenadas', self.namespace)
        if coord is None:
            return None

        lon = coord.find('./ns:coord_longitud', self.namespace)
        lat = coord.find('./ns:coord_latitud', self.namespace)
        alt = coord.find('./ns:coord_altitud', self.namespace)

        if lon is None or lat is None or alt is None:
            return None

        try:
            return (float(lon.text), float(lat.text), float(alt.text))
        except (TypeError, ValueError):
            return None

    def obtener_nombre_etapa(self):
        """Obtiene el nombre de la etapa."""
        nombre = self.obtener_primero('./ns:nombre')
        if nombre is None or nombre.text is None:
            return 'Etapa'
        return nombre.text.strip()

    def obtener_numero_etapa(self):
        """Obtiene el número de la etapa."""
        numero = self.obtener_primero('./ns:numero')
        if numero is None or numero.text is None:
            return ''
        return numero.text.strip()

    def extraer_salida(self):
        """Obtiene la salida de la etapa."""
        nodo = self.obtener_primero('./ns:salida/ns:lugar')
        nombre = self.obtener_texto(nodo, './ns:nombre_lugar')
        coords = self.obtener_coordenada(nodo)
        return {'nombre': nombre, 'coordenadas': coords}

    def extraer_llegada(self):
        """Obtiene la llegada de la etapa."""
        nodo = self.obtener_primero('./ns:llegada/ns:lugar')
        nombre = self.obtener_texto(nodo, './ns:nombre_lugar')
        coords = self.obtener_coordenada(nodo)
        return {'nombre': nombre, 'coordenadas': coords}

    def extraer_puntos_anonimos(self):
        """Extrae puntos anónimos usando XPath."""
        puntos = []
        for punto in self.obtener_nodos('./ns:puntos_anonimos/ns:punto'):
            nombre = punto.get('nombre', 'Punto anónimo')
            coords = self.obtener_coordenada(punto)
            distancia = punto.find('./ns:distancia_km', self.namespace)
            distancia_texto = distancia.text.strip() if distancia is not None and distancia.text is not None else ''
            puntos.append({
                'nombre': nombre,
                'coordenadas': coords,
                'distancia': distancia_texto
            })
        return puntos

    def extraer_puertos(self):
        """Extrae los puertos de montaña."""
        puertos = []
        h = self.obtener_primero('./ns:hitos')
        if h is None:
            return puertos
        for puerto in h.findall('./ns:puertos/ns:puerto', self.namespace):
            nombre = self.obtener_texto(puerto, './ns:nombre_puerto')
            categoria = puerto.get('categoria', 'sin categoria')
            coords = self.obtener_coordenada(puerto)
            puertos.append({'nombre': nombre, 'categoria': categoria, 'coordenadas': coords})
        return puertos

    def extraer_sprints(self):
        """Extrae los sprints intermedios."""
        sprints = []
        h = self.obtener_primero('./ns:hitos')
        if h is None:
            return sprints
        for sprint in h.findall('./ns:sprints/ns:sprint', self.namespace):
            nombre = self.obtener_texto(sprint, './ns:nombre_sprint')
            tipo = sprint.get('tipo', 'sin tipo')
            coords = self.obtener_coordenada(sprint)
            sprints.append({'nombre': nombre, 'tipo': tipo, 'coordenadas': coords})
        return sprints

    def crear_kml(self):
        """Crea el árbol KML con puntos y recorridos."""
        self.kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
        self.document = ET.SubElement(self.kml, 'Document')

        nombre_etapa = self.obtener_nombre_etapa()
        numero_etapa = self.obtener_numero_etapa()
        ET.SubElement(self.document, 'name').text = f'Etapa {numero_etapa}: {nombre_etapa}'

        salida = self.extraer_salida()
        llegada = self.extraer_llegada()
        puntos_anonimos = self.extraer_puntos_anonimos()
        puertos = self.extraer_puertos()
        sprints = self.extraer_sprints()

        def add_placemark_point(nombre, descripcion, longitud, latitud, altitud, color):
            placemark = ET.SubElement(self.document, 'Placemark')
            ET.SubElement(placemark, 'name').text = nombre
            ET.SubElement(placemark, 'description').text = descripcion
            point = ET.SubElement(placemark, 'Point')
            ET.SubElement(point, 'coordinates').text = f'{longitud},{latitud},{altitud}'
            style = ET.SubElement(placemark, 'Style')
            icon_style = ET.SubElement(style, 'IconStyle')
            ET.SubElement(icon_style, 'color').text = color
            ET.SubElement(icon_style, 'scale').text = '1.2'
            ET.SubElement(icon_style, 'Icon')

        if salida['coordenadas'] is not None:
            lon, lat, alt = salida['coordenadas']
            add_placemark_point('Salida', salida['nombre'], lon, lat, alt, 'ff0000ff')

        if llegada['coordenadas'] is not None:
            lon, lat, alt = llegada['coordenadas']
            add_placemark_point('Meta', llegada['nombre'], lon, lat, alt, 'ff0000ff')

        for puerto in puertos:
            if puerto['coordenadas'] is not None:
                lon, lat, alt = puerto['coordenadas']
                add_placemark_point(f'Puerto: {puerto["nombre"]}', f'Categoría {puerto["categoria"]}', lon, lat, alt, 'ff00ff00')

        for sprint in sprints:
            if sprint['coordenadas'] is not None:
                lon, lat, alt = sprint['coordenadas']
                add_placemark_point(f'Sprint: {sprint["nombre"]}', sprint['tipo'], lon, lat, alt, 'ffff0000')

        for punto in puntos_anonimos:
            if punto['coordenadas'] is not None:
                lon, lat, alt = punto['coordenadas']
                add_placemark_point(f'{punto["nombre"]}', f'Distancia {punto["distancia"]} km', lon, lat, alt, 'ff00ffff')

        route = []
        for punto in puntos_anonimos:
            if punto['coordenadas'] is not None:
                lon, lat, alt = punto['coordenadas']
                route.append(f'{lon},{lat},{alt}')

        if salida['coordenadas'] is not None:
            lon, lat, alt = salida['coordenadas']
            route.insert(0, f'{lon},{lat},{alt}')

        if llegada['coordenadas'] is not None:
            lon, lat, alt = llegada['coordenadas']
            route.append(f'{lon},{lat},{alt}')

        if len(route) >= 2:
            placemark = ET.SubElement(self.document, 'Placemark')
            ET.SubElement(placemark, 'name').text = 'Recorrido de la etapa'
            line_string = ET.SubElement(placemark, 'LineString')
            ET.SubElement(line_string, 'extrude').text = '1'
            ET.SubElement(line_string, 'tessellate').text = '1'
            ET.SubElement(line_string, 'coordinates').text = '\n'.join(route)
            style = ET.SubElement(placemark, 'Style')
            line_style = ET.SubElement(style, 'LineStyle')
            ET.SubElement(line_style, 'color').text = 'ffffffff'
            ET.SubElement(line_style, 'width').text = '4'

    def escribir_kml(self):
        """Escribe el fichero KML."""
        if self.kml is None:
            self.crear_kml()
        arbol = ET.ElementTree(self.kml)
        ET.indent(arbol, space='  ')
        arbol.write(self.kml_path, encoding='utf-8', xml_declaration=True)

    def ejecutar(self):
        """Ejecuta la generación del KML."""
        self.cargar_xml()
        self.crear_kml()
        self.escribir_kml()
        print(f'KML creado: {self.kml_path}')


if __name__ == '__main__':
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    xml_path = os.path.join(ruta_base, 'etapaEsquema.xml')
    kml_path = os.path.join(ruta_base, 'etapa.kml')
    XmlToKml(xml_path=xml_path, kml_path=kml_path).ejecutar()
