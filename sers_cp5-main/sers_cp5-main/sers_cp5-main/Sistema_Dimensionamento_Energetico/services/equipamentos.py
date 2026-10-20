from math import ceil
from utils.arquivos import carregar_csv
from utils.constantes import (
    ARQUIVO_HSP,
    ARQUIVO_PAINEIS,
    ARQUIVO_INVERSORES,
    ARQUIVO_BATERIAS,
)

def carregar_hsp():

    return carregar_csv(
        ARQUIVO_HSP
    )


def buscar_hsp_por_localizacao(
    cidade,
    estado
):


    if not cidade or not estado:
        return None

    registros = carregar_hsp()

    cidade_busca = str(cidade).strip().lower()
    estado_busca = str(estado).strip().lower()

    for registro in registros:

        cidade_registro = str(
            registro.get(
                "cidade",
                ""
            )
        ).strip().lower()

        uf_registro = str(
            registro.get(
                "uf",
                ""
            )
        ).strip().lower()

        if (
            cidade_registro == cidade_busca
            and
            uf_registro == estado_busca
        ):

            valor_hsp = registro.get(
                "hsp_kwh_m2_dia"
            )

            fonte = registro.get(
                "fonte",
                ""
            )

            try:
                valor_hsp = float(
                    str(valor_hsp).replace(
                        ",",
                        "."
                    )
                )

            except (TypeError, ValueError):
                return None

            if valor_hsp <= 0:
                return None

            return {
                "hsp": valor_hsp,
                "origem": fonte,
            }

    return None

def carregar_paineis():

    return carregar_csv(
        ARQUIVO_PAINEIS
    )

def carregar_inversores():

    return carregar_csv(
        ARQUIVO_INVERSORES
    )

def carregar_baterias():

    return carregar_csv(
        ARQUIVO_BATERIAS
    )

def verificar_dataset(registros, nome_dataset):

    if not registros:
        print(
            f"\nDataset '{nome_dataset}' está vazio."
        )
        return False

    return True


def obter_hsp(cidade, estado):

    resultado = buscar_hsp_por_localizacao(
        cidade,
        estado
    )

    if resultado is None:

        print(
            "\nNão foi encontrada HSP para "
            f"{cidade}/{estado}."
        )

        return None

    return resultado

def validar_painel(painel):

    if painel is None:
        raise ValueError(
            "Nenhum painel foi informado."
        )

    campos_obrigatorios = [
        "fabricante",
        "modelo",
        "potencia_wp",
    ]

    for campo in campos_obrigatorios:

        if campo not in painel:
            raise ValueError(
                f"O painel não possui o campo '{campo}'."
            )

    try:
        potencia_wp = float(
            str(
                painel["potencia_wp"]
            ).replace(",", ".")
        )

    except (TypeError, ValueError):
        raise ValueError(
            "A potência do painel deve ser numérica."
        )

    if potencia_wp <= 0:
        raise ValueError(
            "A potência do painel deve ser maior que zero."
        )

    return True


def calcular_quantidade_paineis(
    potencia_fv,
    potencia_painel_wp,
):

    # Calcula a quantidade necessária de painéis.
    #
    # Fórmula:
    #
    #     N = teto(P_FV / P_painel)
    #
    # P_FV:
    #     potência FV necessária em kW.
    #
    # P_painel:
    #     potência nominal do painel em Wp.


    try:
        potencia_fv = float(
            potencia_fv
        )

        potencia_painel_wp = float(
            potencia_painel_wp
        )

    except (TypeError, ValueError):
        raise ValueError(
            "As potências devem ser numéricas."
        )

    if potencia_fv <= 0:
        raise ValueError(
            "A potência FV deve ser maior que zero."
        )

    if potencia_painel_wp <= 0:
        raise ValueError(
            "A potência do painel deve ser maior que zero."
        )

    # Conversão de Wp para kWp.
    potencia_painel_kw = (
        potencia_painel_wp / 1000
    )

    quantidade = ceil(
        potencia_fv / potencia_painel_kw
    )

    return quantidade


def calcular_potencia_instalada(
    quantidade_paineis,
    potencia_painel_wp,
):

    try:
        quantidade_paineis = int(
            quantidade_paineis
        )

        potencia_painel_wp = float(
            potencia_painel_wp
        )

    except (TypeError, ValueError):
        raise ValueError(
            "Quantidade e potência do painel "
            "devem ser numéricas."
        )

    if quantidade_paineis <= 0:
        raise ValueError(
            "A quantidade de painéis deve ser maior que zero."
        )

    if potencia_painel_wp <= 0:
        raise ValueError(
            "A potência do painel deve ser maior que zero."
        )

    potencia_instalada = (
        quantidade_paineis
        * potencia_painel_wp
        / 1000
    )

    return potencia_instalada


def dimensionar_paineis(
    potencia_fv,
    painel,
):


    validar_painel(
        painel
    )

    potencia_painel_wp = float(
        str(
            painel["potencia_wp"]
        ).replace(",", ".")
    )

    quantidade = calcular_quantidade_paineis(
        potencia_fv=potencia_fv,
        potencia_painel_wp=potencia_painel_wp,
    )

    potencia_instalada = (
        calcular_potencia_instalada(
            quantidade_paineis=quantidade,
            potencia_painel_wp=potencia_painel_wp,
        )
    )

    return {
        "painel": painel,
        "quantidade_paineis": quantidade,
        "potencia_instalada": potencia_instalada,
    }

def selecionar_painel(
    potencia_fv,
    fabricante=None,
    modelo=None,
):

    paineis = carregar_paineis()

    if not verificar_dataset(
        paineis,
        "paineis.csv"
    ):
        return None

    for painel in paineis:

        try:
            validar_painel(painel)

        except ValueError:
            continue

        fabricante_painel = str(
            painel.get(
                "fabricante",
                ""
            )
        ).strip()

        modelo_painel = str(
            painel.get(
                "modelo",
                ""
            )
        ).strip()

        if fabricante is not None:

            if fabricante_painel.lower() != (
                str(fabricante).strip().lower()
            ):
                continue

        if modelo is not None:

            if modelo_painel.lower() != (
                str(modelo).strip().lower()
            ):
                continue

        return painel

    return None


def listar_paineis():

    registros = carregar_paineis()

    if not registros:
        return []

    paineis_validos = []

    for painel in registros:

        try:
            validar_painel(painel)
            paineis_validos.append(painel)

        except ValueError:
            continue

    return paineis_validos

def validar_inversor(inversor):

    if inversor is None:
        raise ValueError(
            "Nenhum inversor foi informado."
        )

    campos_obrigatorios = [
        "fabricante",
        "modelo",
        "potencia_nominal_kw",
        "potencia_fv_max_kw",
        "tensao_min_v",
        "tensao_max_v",
        "corrente_max_a",
    ]

    for campo in campos_obrigatorios:

        if campo not in inversor:
            raise ValueError(
                f"O inversor não possui o campo "
                f"'{campo}'."
            )

    try:
        potencia_nominal_kw = float(
            str(
                inversor["potencia_nominal_kw"]
            ).replace(",", ".")
        )

        potencia_fv_max_kw = float(
            str(
                inversor["potencia_fv_max_kw"]
            ).replace(",", ".")
        )

        tensao_min_v = float(
            str(
                inversor["tensao_min_v"]
            ).replace(",", ".")
        )

        tensao_max_v = float(
            str(
                inversor["tensao_max_v"]
            ).replace(",", ".")
        )

        corrente_max_a = float(
            str(
                inversor["corrente_max_a"]
            ).replace(",", ".")
        )

    except (TypeError, ValueError):
        raise ValueError(
            "Os dados elétricos do inversor "
            "devem ser numéricos."
        )

    if potencia_nominal_kw <= 0:
        raise ValueError(
            "A potência nominal do inversor "
            "deve ser maior que zero."
        )

    if potencia_fv_max_kw <= 0:
        raise ValueError(
            "A potência FV máxima do inversor "
            "deve ser maior que zero."
        )

    if tensao_min_v <= 0:
        raise ValueError(
            "A tensão mínima do inversor "
            "deve ser maior que zero."
        )

    if tensao_max_v <= tensao_min_v:
        raise ValueError(
            "A tensão máxima do inversor "
            "deve ser maior que a tensão mínima."
        )

    if corrente_max_a <= 0:
        raise ValueError(
            "A corrente máxima do inversor "
            "deve ser maior que zero."
        )

    return True


def listar_inversores():

    registros = carregar_inversores()

    if not registros:
        return []

    inversores_validos = []

    for inversor in registros:

        try:
            validar_inversor(
                inversor
            )

            inversores_validos.append(
                inversor
            )

        except ValueError:
            continue

    return inversores_validos


def selecionar_inversor(
    potencia_instalada,
    fabricante=None,
    modelo=None,
    possui_bateria=False,
):

    # Seleciona um inversor para o sistema fotovoltaico.
    #
    # Regras:
    #     - A potência FV instalada deve ser <= potência FV máxima
    #       suportada pelo inversor.
    #     - Se houver bateria, somente inversores explicitamente
    #       compatíveis com bateria podem ser selecionados.
    #     - Fabricante e modelo podem ser utilizados como filtros.
    #     - Entre os candidatos válidos, seleciona o menor inversor
    #       pela potência nominal.


    try:
        potencia_instalada = float(
            potencia_instalada
        )
    except (TypeError, ValueError):
        raise ValueError(
            "A potência instalada deve ser numérica."
        )

    if potencia_instalada <= 0:
        raise ValueError(
            "A potência instalada deve ser maior que zero."
        )


    inversores = listar_inversores()

    if not inversores:
        return None

    possui_bateria = bool(
        possui_bateria
    )

    candidatos = []

    for inversor in inversores:


        fabricante_inversor = str(
            inversor.get(
                "fabricante",
                ""
            )
        ).strip()

        if fabricante is not None:

            if fabricante_inversor.lower() != (
                str(fabricante)
                .strip()
                .lower()
            ):
                continue

        modelo_inversor = str(
            inversor.get(
                "modelo",
                ""
            )
        ).strip()

        if modelo is not None:

            if modelo_inversor.lower() != (
                str(modelo)
                .strip()
                .lower()
            ):
                continue

        try:

            potencia_nominal_kw = float(
                str(
                    inversor[
                        "potencia_nominal_kw"
                    ]
                ).replace(",", ".")
            )

            potencia_fv_max_kw = float(
                str(
                    inversor[
                        "potencia_fv_max_kw"
                    ]
                ).replace(",", ".")
            )

        except (
            TypeError,
            ValueError,
            KeyError,
        ):
            continue

        # O inversor precisa suportar a potência
        # FV instalada.

        if potencia_fv_max_kw < potencia_instalada:
            continue

        compatibilidade_bateria = str(
            inversor.get(
                "compatibilidade_bateria",
                ""
            )
        ).strip().lower()

        valores_compativeis = [
            "sim",
            "yes",
            "true",
            "1",
            "compatível",
            "compativel",
        ]

        bateria_compativel = (
            compatibilidade_bateria
            in valores_compativeis
        )

        if possui_bateria:

            # Só aceita inversor explicitamente
            # compatível com bateria.

            if not bateria_compativel:
                continue

        candidatos.append(
            (
                potencia_nominal_kw,
                potencia_fv_max_kw,
                inversor,
            )
        )

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    return candidatos[0][2]