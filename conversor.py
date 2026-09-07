import json
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree


BASE_DIR = Path(__file__).resolve().parent
JSON_DIR = BASE_DIR / "json"
OUTPUT_DIR = BASE_DIR / "saida"

OUTPUT_DIR.mkdir(exist_ok=True)


def carregar_json(arquivo):
    with open(arquivo, "r", encoding="utf-8") as f:
        return json.load(f)


def extrair_coordenadas(obj):
    resultado = []

    if isinstance(obj, dict):

        if "latitude" in obj and "longitude" in obj:

            try:
                latitude = float(obj["latitude"])
                longitude = float(obj["longitude"])

                if -90 <= latitude <= 90 and -180 <= longitude <= 180:

                    resultado.append({
                        "latitude": latitude,
                        "longitude": longitude,
                        "ordem": obj.get("ordem")
                    })

            except (ValueError, TypeError):
                pass

        for valor in obj.values():
            resultado.extend(
                extrair_coordenadas(valor)
            )

    elif isinstance(obj, list):

        for item in obj:
            resultado.extend(
                extrair_coordenadas(item)
            )

    return resultado


def extrair_pontos(obj):
    resultado = []

    if isinstance(obj, dict):

        possui_coordenadas = (
            "latitude" in obj
            and "longitude" in obj
        )

        possui_identificacao = (
            "idPontoControle" in obj
            or "idPontoControleItinerario" in obj
            or "descricao" in obj
        )

        if possui_coordenadas and possui_identificacao:

            try:
                latitude = float(obj["latitude"])
                longitude = float(obj["longitude"])

                resultado.append({
                    "latitude": latitude,
                    "longitude": longitude,
                    "ordem": obj.get("ordem"),
                    "descricao": obj.get(
                        "descricao",
                        "Ponto de controle"
                    ),
                    "id": obj.get(
                        "idPontoControle"
                    ),
                    "id_itinerario": obj.get(
                        "idPontoControleItinerario"
                    ),
                    "tipo": obj.get(
                        "tipoPontoControleItinerario"
                    ),
                    "distancia": obj.get(
                        "distanciaInicioItinerarioEmKm"
                    )
                })

            except (ValueError, TypeError):
                pass

        for valor in obj.values():
            resultado.extend(
                extrair_pontos(valor)
            )

    elif isinstance(obj, list):

        for item in obj:
            resultado.extend(
                extrair_pontos(item)
            )

    return resultado


def remover_duplicados_percurso(pontos):

    resultado = []
    vistos = set()

    for ponto in pontos:

        chave = (
            ponto["latitude"],
            ponto["longitude"],
            ponto.get("ordem")
        )

        if chave not in vistos:

            vistos.add(chave)
            resultado.append(ponto)

    return resultado


def remover_duplicados_pontos(pontos):

    resultado = []
    vistos = set()

    for ponto in pontos:

        chave = (
            ponto["latitude"],
            ponto["longitude"],
            ponto.get("id"),
            ponto.get("id_itinerario")
        )

        if chave not in vistos:

            vistos.add(chave)
            resultado.append(ponto)

    return resultado


def ordenar_percurso(pontos):

    com_ordem = []
    sem_ordem = []

    for ponto in pontos:

        if ponto.get("ordem") is None:
            sem_ordem.append(ponto)
        else:
            com_ordem.append(ponto)

    try:

        com_ordem.sort(
            key=lambda p: float(p["ordem"])
        )

    except (ValueError, TypeError):

        pass

    return com_ordem + sem_ordem


def ordenar_pontos(pontos):

    try:

        return sorted(
            pontos,
            key=lambda p: (
                float(p["ordem"])
                if p.get("ordem") is not None
                else float("inf")
            )
        )

    except (ValueError, TypeError):

        return pontos


def criar_kml(nome, percurso, pontos, arquivo):

    kml = Element(
        "kml",
        {
            "xmlns": "http://www.opengis.net/kml/2.2"
        }
    )

    document = SubElement(
        kml,
        "Document"
    )

    SubElement(
        document,
        "name"
    ).text = nome

    estilo = SubElement(
        document,
        "Style",
        {
            "id": "trajeto"
        }
    )

    linha = SubElement(
        estilo,
        "LineStyle"
    )

    SubElement(
        linha,
        "color"
    ).text = "ff0000ff"

    SubElement(
        linha,
        "width"
    ).text = "5"

    placemark = SubElement(
        document,
        "Placemark"
    )

    SubElement(
        placemark,
        "name"
    ).text = "Trajeto"

    SubElement(
        placemark,
        "styleUrl"
    ).text = "#trajeto"

    line_string = SubElement(
        placemark,
        "LineString"
    )

    SubElement(
        line_string,
        "tessellate"
    ).text = "1"

    SubElement(
        line_string,
        "coordinates"
    ).text = "\n".join(
        f'{p["longitude"]:.6f},'
        f'{p["latitude"]:.6f},0'
        for p in percurso
    )

    for ponto in pontos:

        placemark = SubElement(
            document,
            "Placemark"
        )

        ordem = ponto.get("ordem")
        descricao = (
            ponto.get("descricao")
            or "Ponto de controle"
        )

        if ordem is not None:

            nome_ponto = (
                f"{ordem} - {descricao}"
            )

        else:

            nome_ponto = descricao

        SubElement(
            placemark,
            "name"
        ).text = nome_ponto

        descricao_kml = (
            f'ID: {ponto.get("id") or ""}<br/>'
            f'Tipo: {ponto.get("tipo") or ""}<br/>'
            f'Distância: '
            f'{ponto.get("distancia") or ""} km'
        )

        SubElement(
            placemark,
            "description"
        ).text = descricao_kml

        point = SubElement(
            placemark,
            "Point"
        )

        SubElement(
            point,
            "coordinates"
        ).text = (
            f'{ponto["longitude"]:.6f},'
            f'{ponto["latitude"]:.6f},0'
        )

    ElementTree(kml).write(
        arquivo,
        encoding="utf-8",
        xml_declaration=True
    )


def criar_gpx(nome, percurso, pontos, arquivo):

    gpx = Element(
        "gpx",
        {
            "version": "1.1",
            "creator": "Conversor",
            "xmlns": "http://www.topografix.com/GPX/1/1",
            "xmlns:xsi":
                "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:schemaLocation":
                "http://www.topografix.com/GPX/1/1 "
                "http://www.topografix.com/GPX/1/1/gpx.xsd"
        }
    )

    metadata = SubElement(
        gpx,
        "metadata"
    )

    SubElement(
        metadata,
        "name"
    ).text = nome

    track = SubElement(
        gpx,
        "trk"
    )

    SubElement(
        track,
        "name"
    ).text = nome

    segment = SubElement(
        track,
        "trkseg"
    )

    for ponto in percurso:

        SubElement(
            segment,
            "trkpt",
            {
                "lat":
                    f'{ponto["latitude"]:.6f}',
                "lon":
                    f'{ponto["longitude"]:.6f}'
            }
        )

    for ponto in pontos:

        waypoint = SubElement(
            gpx,
            "wpt",
            {
                "lat":
                    f'{ponto["latitude"]:.6f}',
                "lon":
                    f'{ponto["longitude"]:.6f}'
            }
        )

        ordem = ponto.get("ordem")
        descricao = (
            ponto.get("descricao")
            or "Ponto de controle"
        )

        if ordem is not None:

            nome_ponto = (
                f"{ordem} - {descricao}"
            )

        else:

            nome_ponto = descricao

        SubElement(
            waypoint,
            "name"
        ).text = nome_ponto

        SubElement(
            waypoint,
            "desc"
        ).text = (
            f'ID: {ponto.get("id") or ""}; '
            f'Tipo: {ponto.get("tipo") or ""}; '
            f'Distância: '
            f'{ponto.get("distancia") or ""} km'
        )

    ElementTree(gpx).write(
        arquivo,
        encoding="utf-8",
        xml_declaration=True
    )


def processar_linha(pasta):

    arquivo_percurso = (
        pasta / "percurso.json"
    )

    arquivo_pontos = (
        pasta / "pontos.json"
    )

    if not arquivo_percurso.exists():

        print(
            f"[ERRO] {pasta.name}: "
            "percurso.json não encontrado"
        )

        return

    if not arquivo_pontos.exists():

        print(
            f"[ERRO] {pasta.name}: "
            "pontos.json não encontrado"
        )

        return

    percurso_json = carregar_json(
        arquivo_percurso
    )

    pontos_json = carregar_json(
        arquivo_pontos
    )

    percurso = extrair_coordenadas(
        percurso_json
    )

    pontos = extrair_pontos(
        pontos_json
    )

    percurso = remover_duplicados_percurso(
        percurso
    )

    pontos = remover_duplicados_pontos(
        pontos
    )

    percurso = ordenar_percurso(
        percurso
    )

    pontos = ordenar_pontos(
        pontos
    )

    if not percurso:

        print(
            f"[ERRO] {pasta.name}: "
            "nenhum ponto de percurso encontrado"
        )

        return

    nome = pasta.name

    arquivo_kml = (
        OUTPUT_DIR /
        f"{nome}.kml"
    )

    arquivo_gpx = (
        OUTPUT_DIR /
        f"{nome}.gpx"
    )

    criar_kml(
        nome,
        percurso,
        pontos,
        arquivo_kml
    )

    criar_gpx(
        nome,
        percurso,
        pontos,
        arquivo_gpx
    )

    print(
        f"[OK] {nome} | "
        f"Percurso: {len(percurso)} pontos | "
        f"Pontos: {len(pontos)}"
    )


def main():

    pastas = [
        pasta
        for pasta in JSON_DIR.iterdir()
        if pasta.is_dir()
    ]

    if not pastas:

        print(
            "Nenhuma pasta de linha encontrada."
        )

        return

    for pasta in sorted(pastas):

        try:

            processar_linha(pasta)

        except Exception as erro:

            print(
                f"[ERRO] {pasta.name}: "
                f"{erro}"
            )


if __name__ == "__main__":
    main()