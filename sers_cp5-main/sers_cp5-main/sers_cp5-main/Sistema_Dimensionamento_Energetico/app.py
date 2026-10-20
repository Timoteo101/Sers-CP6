import streamlit as st
from datetime import date
from models.usuario import Usuario
from models.imovel import Imovel

from services.autenticacao import carregar_dados, salvar_dados

from services.imoveis import (
    listar_imoveis,
    obter_usuario_dados,
    gerar_id_imovel,
    calcular_consumo_medio,
    calcular_consumo_maximo,
    obter_mes_maior_consumo,
)

from services import dimensionamento as servico_dimensionamento


st.set_page_config(
    page_title="Sistema de Dimensionamento Energético",
    page_icon="⚡",
    layout="wide",
)


EQUIPAMENTOS_PADRAO = {
    "Geladeira": {"potencia_w": 150, "horas_dia": 8},
    "Chuveiro Elétrico": {"potencia_w": 5500, "horas_dia": 0.5},
    "TV": {"potencia_w": 100, "horas_dia": 5},
    "Ar-condicionado": {"potencia_w": 900, "horas_dia": 8},
    "Computador": {"potencia_w": 200, "horas_dia": 6},
    "Lâmpada LED": {"potencia_w": 9, "horas_dia": 5},
    "Máquina de Lavar": {"potencia_w": 500, "horas_dia": 1},
    "Micro-ondas": {"potencia_w": 1200, "horas_dia": 0.3},
}


def calcular_consumo_equipamentos(equipamentos):
    return round(sum(
        float(item.get("potencia_w", 0)) * int(item.get("quantidade", 0))
        * float(item.get("horas_dia", 0)) * 30 / 1000
        for item in equipamentos
    ), 2)


def salvar_equipamentos_imovel(usuario, id_imovel, equipamentos):
    dados = carregar_dados()
    usuario_dados = obter_usuario_dados(dados, usuario.email)
    if usuario_dados is None:
        return False, "Usuário não encontrado."
    imovel = next((item for item in usuario_dados.get("imoveis", [])
                   if str(item.get("id_imovel")) == str(id_imovel)), None)
    if imovel is None:
        return False, "Imóvel não encontrado."

    imovel["equipamentos"] = equipamentos
    hoje = date.today()
    consumos = imovel.setdefault("consumos", [])
    registro = next((c for c in consumos
                     if int(c.get("mes", 0)) == hoje.month
                     and int(c.get("ano", 0)) == hoje.year), None)
    consumo = calcular_consumo_equipamentos(equipamentos)
    if registro is None:
        consumos.append({"mes": hoje.month, "ano": hoje.year,
                         "consumo_kwh": consumo,
                         "origem": "estimativa_por_equipamentos"})
    else:
        registro["consumo_kwh"] = consumo
        registro["origem"] = "estimativa_por_equipamentos"
    salvar_dados(dados)
    return True, f"Equipamentos salvos. Consumo mensal estimado: {consumo:.2f} kWh."


def cadastrar(nome, email, senha):
    dados = carregar_dados()

    nome = nome.strip()
    email = email.strip().lower()

    if not nome or not email or not senha:
        return False, "Preencha todos os campos."

    if any(
        u.get("email", "").lower() == email
        for u in dados.get("usuarios", [])
    ):
        return False, "Este e-mail já está cadastrado."

    usuario = Usuario(
        nome=nome,
        email=email,
        senha=senha,
        imoveis=[],
    )

    dados.setdefault("usuarios", []).append(
        usuario.para_dict()
    )

    salvar_dados(dados)

    return True, "Cadastro realizado com sucesso!"


def autenticar(email, senha):
    dados = carregar_dados()
    email = email.strip().lower()

    for item in dados.get("usuarios", []):
        if (
            item.get("email", "").lower() == email
            and item.get("senha", "") == senha
        ):
            return Usuario.de_dict(item)

    return None

def criar_imovel(
    usuario,
    nome,
    tipo,
    endereco,
    cidade,
    estado,
):
    dados = carregar_dados()

    usuario_dados = obter_usuario_dados(
        dados,
        usuario.email,
    )

    if usuario_dados is None:
        return False, "Usuário não encontrado."

    campos = [
        nome,
        tipo,
        endereco,
        cidade,
        estado,
    ]

    if any(not campo.strip() for campo in campos):
        return False, "Preencha todos os campos."

    imoveis = usuario_dados.setdefault(
        "imoveis",
        [],
    )

    novo_id = gerar_id_imovel(imoveis)

    novo_imovel = Imovel(
        id_imovel=novo_id,
        nome=nome.strip(),
        tipo=tipo.strip(),
        endereco=endereco.strip(),
        cidade=cidade.strip(),
        estado=estado.strip(),
        consumos=[],
        dimensionamentos=[],
    )

    imoveis.append(novo_imovel.para_dict())

    salvar_dados(dados)

    return True, "Imóvel cadastrado com sucesso!"


def registrar_consumo(
    usuario,
    id_imovel,
    mes,
    ano,
    kwh,
):
    if kwh <= 0:
        return False, "O consumo deve ser maior que zero."

    dados = carregar_dados()

    usuario_dados = obter_usuario_dados(
        dados,
        usuario.email,
    )

    if usuario_dados is None:
        return False, "Usuário não encontrado."

    for imovel in usuario_dados.get("imoveis", []):
        if str(imovel.get("id_imovel")) == str(id_imovel):
            consumos = imovel.setdefault("consumos", [])

            if any(
                c.get("mes") == mes
                and c.get("ano") == ano
                for c in consumos
            ):
                return (
                    False,
                    "Já existe consumo para esse mês e ano.",
                )

            consumos.append({
                "mes": int(mes),
                "ano": int(ano),
                "consumo_kwh": float(kwh),
            })

            salvar_dados(dados)

            return True, "Consumo registrado com sucesso!"

    return False, "Imóvel não encontrado."

def executar_dimensionamento(
    imovel,
    percentual,
    possui_bateria,
    autonomia,
):

    consumos = imovel.obter_consumos()

    if not consumos:
        st.warning(
            "Registre pelo menos um consumo mensal "
            "antes de dimensionar o sistema."
        )
        return

    try:
        # PB01: consumo de referência.
        consumo_referencia = (
            servico_dimensionamento.calcular_consumo_referencia(
                consumos
            )
        )

        # PB02: obtenção da HSP pela localização.
        dados_hsp = (
            servico_dimensionamento.obter_hsp_imovel(
                imovel
            )
        )

        if not dados_hsp:
            st.error(
                "Não foi possível obter a HSP para "
                "a cidade e o estado informados. "
                "Confira os dados e o dataset solar."
            )
            return

        if isinstance(dados_hsp, dict):
            hsp = float(dados_hsp["hsp"])
            origem_hsp = dados_hsp.get("origem", "")
        else:
            hsp = float(dados_hsp)
            origem_hsp = ""

        if hsp <= 0:
            st.error("A HSP deve ser maior que zero.")
            return

        # PB03 e PB04: energia e potência necessárias.
        resultado = (
            servico_dimensionamento.criar_resultado_base(
                consumos=consumos,
                percentual_atendimento=percentual,
                hsp=hsp,
                origem_hsp=origem_hsp,
            )
        )

        # PB05: seleção e dimensionamento dos painéis.
        resultado = servico_dimensionamento.executar_pb05(
            resultado
        )

        if resultado is None:
            st.warning(
                "Nenhum painel compatível foi encontrado "
                "no dataset de equipamentos."
            )
            return

        # PB06: seleção do inversor.
        resultado = servico_dimensionamento.executar_pb06(
            resultado
        )

        if resultado is None:
            st.warning(
                "Nenhum inversor compatível foi encontrado."
            )
            return

        # PB08 e PB09: armazenamento opcional.
        if possui_bateria:
            resultado = (
                servico_dimensionamento.executar_armazenamento(
                    resultado,
                    autonomia_horas=autonomia,
                )
            )

            if resultado.baterias is None:
                st.warning(
                    "Não foi encontrada bateria adequada "
                    "no dataset. Confira os equipamentos."
                )

        # PB10: compatibilidade.
        resultado = servico_dimensionamento.executar_pb10(
            resultado
        )

        # Estimativa de geração.
        resultado.geracao_estimada = (
            servico_dimensionamento.calcular_geracao_estimada(
                potencia_instalada=resultado.potencia_instalada,
                hsp=resultado.hsp,
                dias_periodo=resultado.dias_periodo,
                eficiencia=resultado.eficiencia_sistema,
            )
        )

        # Orçamento.
        resultado.custos_adicionais = 0.0

        resultado = servico_dimensionamento.calcular_custos(
            resultado
        )

        # PB12: relatório.
        relatorio = (
            servico_dimensionamento.gerar_resumo_final(
                resultado
            )
        )

        st.session_state.relatorio_dimensionamento = relatorio
        st.session_state.resultado_dimensionamento = resultado

    except (ValueError, KeyError, TypeError, AttributeError) as erro:
        st.error(
            f"Não foi possível concluir o dimensionamento: {erro}"
        )
        st.caption(
            "Confira os campos do modelo ResultadoDimensionamento "
            "e as funções dos serviços de equipamentos, baterias "
            "e compatibilidade."
        )

    except Exception as erro:
        st.error(
            f"Ocorreu um erro durante o dimensionamento: {erro}"
        )


def exibir_dimensionamento(imoveis):
    st.subheader("Dimensionamento fotovoltaico")

    if not imoveis:
        st.warning(
            "Cadastre um imóvel antes de realizar o dimensionamento."
        )
        return

    mapa = {
        f"{i.nome} — {i.cidade}/{i.estado} (ID {i.id_imovel})": i
        for i in imoveis
    }

    with st.form("form_dimensionamento"):
        selecionado = st.selectbox(
            "Selecione o imóvel",
            list(mapa.keys()),
        )

        percentual = st.slider(
            "Percentual de atendimento do consumo",
            min_value=1,
            max_value=100,
            value=100,
            step=1,
            format="%d%%",
        )

        st.write("**Armazenamento de energia**")

        possui_bateria = st.checkbox(
            "Incluir baterias no sistema",
            value=False,
        )

        autonomia = st.number_input(
            "Autonomia desejada (horas)",
            min_value=1.0,
            max_value=24.0,
            value=4.0,
            step=1.0,
            disabled=not possui_bateria,
        )

        calcular = st.form_submit_button(
            "Calcular dimensionamento",
            type="primary",
            use_container_width=True,
        )

    if calcular:
        imovel = mapa[selecionado]

        st.session_state.pop(
            "relatorio_dimensionamento",
            None,
        )
        st.session_state.pop(
            "resultado_dimensionamento",
            None,
        )

        executar_dimensionamento(
            imovel=imovel,
            percentual=percentual,
            possui_bateria=possui_bateria,
            autonomia=autonomia,
        )

    relatorio = st.session_state.get(
        "relatorio_dimensionamento"
    )

    if relatorio:
        st.divider()

        st.subheader("Resultado do dimensionamento")

        d = relatorio.get("dimensionamento", {})
        painel = relatorio.get("painel") or {}
        inversor = relatorio.get("inversor") or {}
        bateria = relatorio.get("bateria", {})
        orcamento = relatorio.get("orcamento", {})

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Consumo médio",
            f"{d.get('consumo_referencia', 0):.2f} kWh/mês",
        )

        c2.metric(
            "Potência necessária",
            f"{d.get('potencia_fv', 0):.2f} kW",
        )

        c3.metric(
            "Potência instalada",
            f"{d.get('potencia_instalada', 0):.2f} kW",
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Quantidade de painéis",
            d.get("quantidade_paineis", 0),
        )

        c2.metric(
            "Geração estimada",
            f"{d.get('geracao_estimada', 0):.2f} kWh/mês",
        )

        c3.metric(
            "HSP",
            f"{d.get('hsp', 0):.2f} h",
        )

        st.caption(
            f"Origem da HSP: {d.get('origem_hsp') or 'Não informada'}"
        )

        st.divider()
        st.subheader("Equipamentos selecionados")

        with st.container(border=True):
            st.write("**Painel fotovoltaico**")

            if painel:
                st.write(
                    f"Fabricante: {painel.get('fabricante', 'Não informado')}"
                )
                st.write(
                    f"Modelo: {painel.get('modelo', 'Não informado')}"
                )
                st.write(
                    f"Potência: {painel.get('potencia_wp', 'Não informada')} Wp"
                )
                st.write(
                    f"Quantidade: {d.get('quantidade_paineis', 0)}"
                )
            else:
                st.info("Nenhum painel selecionado.")

        with st.container(border=True):
            st.write("**Inversor**")

            if inversor:
                st.write(
                    f"Fabricante: {inversor.get('fabricante', 'Não informado')}"
                )
                st.write(
                    f"Modelo: {inversor.get('modelo', 'Não informado')}"
                )
                st.write(
                    f"Potência nominal: {inversor.get('potencia_nominal_kw', 'Não informada')} kW"
                )
            else:
                st.info("Nenhum inversor selecionado.")

        with st.container(border=True):
            st.write("**Armazenamento**")

            if bateria.get("possui_bateria"):
                equipamento = bateria.get("equipamento")

                if equipamento:
                    st.write(
                        f"Fabricante: {equipamento.get('fabricante', 'Não informado')}"
                    )
                    st.write(
                        f"Modelo: {equipamento.get('modelo', 'Não informado')}"
                    )
                    st.write(
                        f"Quantidade: {bateria.get('quantidade', 0)}"
                    )
                    st.write(
                        f"Capacidade instalada: {bateria.get('capacidade_instalada', 0):.2f} kWh"
                    )
                else:
                    st.warning(
                        "O sistema solicitou baterias, mas "
                        "nenhum equipamento foi selecionado."
                    )
            else:
                st.write("Sistema sem baterias.")

        st.divider()
        st.subheader("Compatibilidade")

        compatibilidade = relatorio.get("compatibilidade")

        if compatibilidade is None:
            st.warning("Compatibilidade não calculada.")
        elif compatibilidade.get("compativel", False):
            st.success("Os equipamentos foram considerados compatíveis.")
        else:
            st.error("Foram encontrados problemas de compatibilidade.")

            for problema in compatibilidade.get("problemas", []):
                st.write(f"- {problema}")

        st.divider()
        st.subheader("Orçamento estimado")

        def moeda(valor):
            try:
                valor = float(valor or 0)
                texto = f"{valor:,.2f}"
                texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
                return f"R$ {texto}"
            except (TypeError, ValueError):
                return "Não informado"

        c1, c2 = st.columns(2)

        c1.metric(
            "Painéis",
            moeda(orcamento.get("custo_paineis")),
        )

        c2.metric(
            "Inversor",
            moeda(orcamento.get("custo_inversor")),
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Baterias",
            moeda(orcamento.get("custo_baterias")),
        )

        c2.metric(
            "Custos adicionais",
            moeda(orcamento.get("custos_adicionais")),
        )

        st.metric(
            "Custo total estimado",
            moeda(orcamento.get("custo_total")),
        )

        faltantes = relatorio.get("precos_nao_informados", [])

        if faltantes:
            st.warning(
                "Não há preços válidos cadastrados para: "
                + ", ".join(faltantes)
                + ". O orçamento pode estar incompleto."
            )

        with st.expander("Ver relatório técnico completo"):
            st.json(relatorio)

            if st.button(
                "Exibir relatório detalhado no terminal"
            ):
                servico_dimensionamento.exibir_resumo_final(
                    relatorio
                )


if "usuario" not in st.session_state:
    st.session_state.usuario = None

st.title("Sistema de Dimensionamento Energético")
st.caption(
    "Gerencie seus imóveis, acompanhe o consumo "
    "e dimensione sistemas fotovoltaicos."
)

usuario = st.session_state.usuario


if usuario is None:
    entrar, cadastrar_tab = st.tabs(
        ["Entrar", "Criar conta"]
    )

    with entrar:
        with st.form("form_login"):
            email = st.text_input("E-mail")
            senha = st.text_input(
                "Senha",
                type="password",
            )

            enviar = st.form_submit_button(
                "Entrar",
                type="primary",
                use_container_width=True,
            )

        if enviar:
            usuario = autenticar(email, senha)

            if usuario:
                st.session_state.usuario = usuario
                st.rerun()
            else:
                st.error("E-mail ou senha incorretos.")

    with cadastrar_tab:
        with st.form("form_cadastro"):
            nome = st.text_input("Nome completo")
            novo_email = st.text_input("E-mail para cadastro")
            nova_senha = st.text_input(
                "Senha",
                type="password",
            )

            confirmar = st.form_submit_button(
                "Criar conta",
                type="primary",
                use_container_width=True,
            )

        if confirmar:
            ok, mensagem = cadastrar(
                nome,
                novo_email,
                nova_senha,
            )

            if ok:
                st.success(mensagem)
            else:
                st.error(mensagem)


else:
    with st.sidebar:
        st.subheader("Menu")
        st.write(f"Olá, **{usuario.nome}**!")

        pagina = st.radio(
            "Navegação",
            [
                "Visão geral",
                "Meus imóveis",
                "Registrar consumo",
                "Histórico de consumo",
                "Dimensionamento",
            ],
        )

        if st.button(
            "Sair",
            use_container_width=True,
        ):
            st.session_state.usuario = None
            st.session_state.pop(
                "relatorio_dimensionamento",
                None,
            )
            st.session_state.pop(
                "resultado_dimensionamento",
                None,
            )
            st.rerun()

    imoveis = listar_imoveis(usuario)

    if pagina == "Visão geral":
        st.subheader("Visão geral")

        total_consumos = sum(
            len(imovel.obter_consumos())
            for imovel in imoveis
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Imóveis cadastrados",
            len(imoveis),
        )

        c2.metric(
            "Registros de consumo",
            total_consumos,
        )

        st.write("Bem-vindo ao seu painel de controle.")

        if not imoveis:
            st.info(
                "Cadastre um imóvel e registre seu consumo "
                "mensal para começar."
            )
        else:
            st.subheader("Seus imóveis")

            for imovel in imoveis:
                with st.container(border=True):
                    st.write(f"**{imovel.nome}**")
                    st.caption(
                        f"{imovel.cidade}/{imovel.estado} · "
                        f"{imovel.tipo}"
                    )

    elif pagina == "Meus imóveis":
        st.subheader("Meus imóveis")

        with st.expander(
            "Cadastrar novo imóvel",
            expanded=not imoveis,
        ):
            st.write("**Dados do imóvel**")
            nome_imovel = st.text_input(
                "Nome do imóvel",
                key="cadastro_nome_imovel",
            )

            tipo = st.selectbox(
                "Tipo de imóvel",
                [
                    "Residencial",
                    "Comercial",
                    "Industrial",
                    "Rural",
                    "Outro",
                ],
                key="cadastro_tipo_imovel",
            )

            endereco = st.text_input("Endereço", key="cadastro_endereco")
            cidade = st.text_input("Cidade", key="cadastro_cidade")
            estado = st.text_input("Estado/UF", key="cadastro_estado")

            st.divider()
            st.write("**2. Como deseja informar o consumo?**")
            modo_consumo = st.radio(
                "Escolha uma opção",
                ["Por equipamentos", "Informar apenas o consumo mensal"],
                horizontal=True,
                key="modo_consumo_cadastro_imovel",
            )

            consumo_manual = 0.0
            equipamentos_cadastro = []
            if modo_consumo == "Informar apenas o consumo mensal":
                st.caption("Informe o consumo total que aparece na conta de energia, sem precisar cadastrar equipamentos.")
                consumo_manual = st.number_input(
                    "Consumo mensal (kWh/mês)", min_value=0.0,
                    value=0.0, step=10.0, key="consumo_manual_cadastro_imovel"
                )
            else:
                st.write("**2. Equipamentos**")
                st.caption("Selecione um equipamento, informe a quantidade e as horas de uso por dia.")

            if modo_consumo == "Por equipamentos":
                if "equipamento_em_edicao" not in st.session_state:
                    st.session_state.equipamento_em_edicao = "Geladeira"
                if "equipamentos_cadastro_lista" not in st.session_state:
                    st.session_state.equipamentos_cadastro_lista = []

                nomes = list(EQUIPAMENTOS_PADRAO.keys())
                grade = st.columns(5)
                for indice, nome_eq in enumerate(nomes):
                    with grade[indice % 5]:
                        selecionado = nome_eq == st.session_state.equipamento_em_edicao
                        texto = f"{'✓ ' if selecionado else ''}{nome_eq}\n\n{EQUIPAMENTOS_PADRAO[nome_eq]['potencia_w']} W"
                        if st.button(texto, key=f"card_eq_{nome_eq}",
                                     use_container_width=True,
                                     type="primary" if selecionado else "secondary"):
                            st.session_state.equipamento_em_edicao = nome_eq
                            st.rerun()

                atual = st.session_state.equipamento_em_edicao
                padrao = EQUIPAMENTOS_PADRAO[atual]
                col_qtd, col_horas, col_add = st.columns([1, 1, 0.24])
                quantidade = col_qtd.number_input(
                    "Quantidade", min_value=1, max_value=100, value=1, step=1,
                    key=f"qtd_eq_{atual}",
                )
                horas = col_horas.number_input(
                    "Horas de uso por dia", min_value=0.0, max_value=24.0,
                    value=float(padrao["horas_dia"]), step=0.5,
                    key=f"horas_eq_{atual}",
                )
                if col_add.button("Adicionar", type="primary", key="adicionar_eq"):
                    lista = st.session_state.equipamentos_cadastro_lista
                    item = {"nome": atual, "quantidade": int(quantidade),
                            "potencia_w": float(padrao["potencia_w"]),
                            "horas_dia": float(horas)}
                    existente = next((x for x in lista if x["nome"] == atual), None)
                    if existente:
                        existente.update(item)
                    else:
                        lista.append(item)
                    st.session_state.equipamentos_cadastro_lista = lista
                    st.rerun()

                st.write("**Equipamentos cadastrados**")
                equipamentos_cadastro = st.session_state.equipamentos_cadastro_lista
                if equipamentos_cadastro:
                    linhas = [{
                        "Equipamento": item["nome"],
                        "Qtd.": item["quantidade"],
                        "Horas/dia": item["horas_dia"],
                        "Consumo (kWh/mês)": round(
                            item["potencia_w"] * item["quantidade"] * item["horas_dia"] * 30 / 1000, 2
                        ),
                    } for item in equipamentos_cadastro]
                    st.dataframe(linhas, use_container_width=True, hide_index=True)
                    remover = st.multiselect(
                        "Equipamentos para remover",
                        [item["nome"] for item in equipamentos_cadastro],
                        key="remover_eq_cadastro",
                    )
                    if st.button("Remover selecionados", key="remover_eq_btn"):
                        st.session_state.equipamentos_cadastro_lista = [
                            item for item in equipamentos_cadastro if item["nome"] not in remover
                        ]
                        st.rerun()
                else:
                    st.info("Nenhum equipamento cadastrado ainda.")

                consumo_previsto = calcular_consumo_equipamentos(equipamentos_cadastro)
                st.metric("Consumo mensal estimado", f"{consumo_previsto:.2f} kWh/mês")

            if st.button("Cadastrar imóvel e equipamentos", type="primary",
                         key="salvar_imovel_e_equipamentos"):
                if modo_consumo == "Por equipamentos" and not equipamentos_cadastro:
                    st.warning("Adicione pelo menos um equipamento antes de cadastrar o imóvel.")
                elif modo_consumo == "Informar apenas o consumo mensal" and consumo_manual <= 0:
                    st.warning("Informe um consumo mensal maior que zero.")
                else:
                    ok, mensagem = criar_imovel(usuario, nome_imovel, tipo, endereco, cidade, estado)
                    if ok:
                        dados_atualizados = carregar_dados()
                        usuario_dados = obter_usuario_dados(dados_atualizados, usuario.email)
                        novo_imovel = None
                        if usuario_dados is not None:
                            novo_imovel = next((
                                item for item in usuario_dados.get("imoveis", [])
                                if item.get("nome") == nome_imovel.strip()
                                and item.get("cidade") == cidade.strip()
                                and item.get("endereco") == endereco.strip()
                            ), None)
                        if novo_imovel is not None:
                            if modo_consumo == "Por equipamentos":
                                ok_consumo, mensagem_consumo = salvar_equipamentos_imovel(
                                    usuario, novo_imovel.get("id_imovel"), equipamentos_cadastro
                                )
                            else:
                                hoje = date.today()
                                ok_consumo, mensagem_consumo = registrar_consumo(
                                    usuario, novo_imovel.get("id_imovel"),
                                    hoje.month, hoje.year, consumo_manual
                                )
                            if ok_consumo:
                                st.success(
                                    mensagem_consumo if modo_consumo == "Por equipamentos"
                                    else "Imóvel cadastrado e consumo mensal registrado com sucesso!"
                                )
                                st.session_state.equipamentos_cadastro_lista = []
                                st.rerun()
                            else:
                                st.error(mensagem_consumo)
                        else:
                            st.error("Imóvel cadastrado, mas não foi possível localizar seu registro.")
                    else:
                        st.error(mensagem)

        if imoveis:
            for imovel in imoveis:
                with st.container(border=True):
                    st.write(f"### {imovel.nome}")

                    a, b = st.columns(2)

                    a.write(f"**ID:** {imovel.id_imovel}")
                    a.write(f"**Tipo:** {imovel.tipo}")

                    b.write(f"**Cidade:** {imovel.cidade}")
                    b.write(f"**Estado:** {imovel.estado}")

                    st.write(
                        f"**Endereço:** {imovel.endereco}"
                    )
        else:
            st.info("Você ainda não cadastrou imóveis.")

    elif pagina == "Registrar consumo":
        st.subheader("Registrar consumo")
        st.write(
            "Selecione um imóvel já cadastrado para adicionar um registro "
            "mensal de consumo, sem precisar cadastrar o imóvel novamente."
        )

        if not imoveis:
            st.warning("Cadastre um imóvel antes de registrar o consumo.")
        else:
            mapa_imoveis = {
                f"{i.nome} — {i.cidade}/{i.estado} (ID {i.id_imovel})": i
                for i in imoveis
            }

            with st.form("form_registrar_consumo_existente"):
                selecionado = st.selectbox(
                    "Imóvel já cadastrado",
                    list(mapa_imoveis.keys()),
                )
                col1, col2 = st.columns(2)
                mes = col1.selectbox(
                    "Mês", options=list(range(1, 13)),
                    format_func=lambda m: f"{m:02d}",
                )
                ano = col2.number_input(
                    "Ano", min_value=2000, max_value=2100,
                    value=date.today().year, step=1,
                )
                consumo_kwh = st.number_input(
                    "Consumo mensal (kWh)", min_value=0.1,
                    value=100.0, step=10.0,
                )
                salvar_consumo = st.form_submit_button(
                    "Adicionar consumo", type="primary",
                )

            if salvar_consumo:
                imovel_selecionado = mapa_imoveis[selecionado]
                ok, mensagem = registrar_consumo(
                    usuario,
                    imovel_selecionado.id_imovel,
                    int(mes),
                    int(ano),
                    float(consumo_kwh),
                )
                if ok:
                    st.success(mensagem)
                    st.rerun()
                else:
                    st.error(mensagem)

    elif pagina == "Histórico de consumo":
        st.subheader("Histórico de consumo")
        st.caption(
            "Os valores são calculados a partir dos equipamentos cadastrados "
            "em cada imóvel. Para atualizar a estimativa, edite o cadastro "
            "dos equipamentos do imóvel."
        )

        encontrou_consumos = False
        for imovel in imoveis:
            consumos = imovel.obter_consumos()
            if consumos:
                encontrou_consumos = True
                st.write(f"**{imovel.nome}**")
                st.dataframe(
                    [
                        {
                            "Mês": f"{c['mes']:02d}/{c['ano']}",
                            "Consumo (kWh)": c["consumo_kwh"],
                        }
                        for c in sorted(
                            consumos,
                            key=lambda c: (c["ano"], c["mes"]),
                            reverse=True,
                        )
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
                media = calcular_consumo_medio(usuario, imovel.id_imovel)
                maximo = calcular_consumo_maximo(usuario, imovel.id_imovel)
                c1, c2 = st.columns(2)
                c1.metric("Consumo médio", f"{media:.2f} kWh/mês")
                c2.metric("Consumo máximo", f"{maximo:.2f} kWh/mês")

                maior = obter_mes_maior_consumo(usuario, imovel.id_imovel)
                if maior:
                    st.caption(
                        f"Mês de maior consumo: {maior['mes']:02d}/{maior['ano']}"
                    )

        if not encontrou_consumos:
            st.info(
                "Nenhum consumo calculado ainda. Cadastre um imóvel com "
                "seus equipamentos para gerar a primeira estimativa."
            )


    elif pagina == "Dimensionamento":
        exibir_dimensionamento(imoveis)


st.divider()
st.caption(
    "Sistema local · Dados armazenados no arquivo do projeto"
)

