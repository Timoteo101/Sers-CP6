class ResultadoDimensionamento:

    def __init__(
        self,
        consumo_referencia=0.0,
        percentual_atendimento=0.0,
        energia_fv=0.0,
        hsp=0.0,
        origem_hsp="",
        dias_periodo=30,
        eficiencia_sistema=0.0,
        potencia_fv=0.0,
        potencia_instalada=0.0,
        painel=None,
        quantidade_paineis=0,
        inversor=None,
        possui_bateria=False,
        autonomia_horas=0.0,
        capacidade_bateria_necessaria=0.0,
        baterias=None,
        quantidade_baterias=0,
        capacidade_bateria_instalada=0.0,
        geracao_estimada=0.0,
        custo_paineis=0.0,
        custo_inversor=0.0,
        custo_baterias=0.0,
        custos_adicionais=0.0,
        custo_total=0.0,
        compatibilidade=None,
    ):



        self.consumo_referencia = consumo_referencia
        self.percentual_atendimento = percentual_atendimento
        self.energia_fv = energia_fv

        self.hsp = hsp
        self.origem_hsp = origem_hsp

        self.dias_periodo = dias_periodo
        self.eficiencia_sistema = eficiencia_sistema
        self.potencia_fv = potencia_fv

        self.potencia_instalada = potencia_instalada
        self.painel = painel
        self.quantidade_paineis = quantidade_paineis

        self.inversor = inversor

        self.possui_bateria = possui_bateria
        self.autonomia_horas = autonomia_horas
        self.capacidade_bateria_necessaria = (
            capacidade_bateria_necessaria
        )

        self.baterias = baterias
        self.quantidade_baterias = quantidade_baterias

        self.capacidade_bateria_instalada = (
            capacidade_bateria_instalada
        )

        self.geracao_estimada = geracao_estimada

        self.custo_paineis = custo_paineis
        self.custo_inversor = custo_inversor
        self.custo_baterias = custo_baterias
        self.custos_adicionais = custos_adicionais
        self.custo_total = custo_total

        self.compatibilidade = compatibilidade

    def para_dict(self):

        return {
            "consumo_referencia": self.consumo_referencia,
            "percentual_atendimento": (
                self.percentual_atendimento
            ),
            "energia_fv": self.energia_fv,

            "hsp": self.hsp,
            "origem_hsp": self.origem_hsp,

            "dias_periodo": self.dias_periodo,
            "eficiencia_sistema": (
                self.eficiencia_sistema
            ),
            "potencia_fv": self.potencia_fv,

            "potencia_instalada": (
                self.potencia_instalada
            ),
            "painel": self.painel,
            "quantidade_paineis": (
                self.quantidade_paineis
            ),

            "inversor": self.inversor,

            "possui_bateria": self.possui_bateria,
            "autonomia_horas": self.autonomia_horas,

            "capacidade_bateria_necessaria": (
                self.capacidade_bateria_necessaria
            ),

            "baterias": self.baterias,
            "quantidade_baterias": (
                self.quantidade_baterias
            ),

            "capacidade_bateria_instalada": (
                self.capacidade_bateria_instalada
            ),

            "geracao_estimada": (
                self.geracao_estimada
            ),

            "custo_paineis": self.custo_paineis,
            "custo_inversor": self.custo_inversor,
            "custo_baterias": self.custo_baterias,
            "custos_adicionais": (
                self.custos_adicionais
            ),
            "custo_total": self.custo_total,

            "compatibilidade": self.compatibilidade,
        }

    @classmethod
    def de_dict(cls, dados):

        return cls(
            consumo_referencia=dados.get(
                "consumo_referencia",
                0.0,
            ),

            percentual_atendimento=dados.get(
                "percentual_atendimento",
                0.0,
            ),

            energia_fv=dados.get(
                "energia_fv",
                0.0,
            ),

            hsp=dados.get(
                "hsp",
                0.0,
            ),

            origem_hsp=dados.get(
                "origem_hsp",
                "",
            ),

            dias_periodo=dados.get(
                "dias_periodo",
                30,
            ),

            eficiencia_sistema=dados.get(
                "eficiencia_sistema",
                0.0,
            ),

            potencia_fv=dados.get(
                "potencia_fv",
                0.0,
            ),

            potencia_instalada=dados.get(
                "potencia_instalada",
                0.0,
            ),

            painel=dados.get(
                "painel",
            ),

            quantidade_paineis=dados.get(
                "quantidade_paineis",
                0,
            ),

            inversor=dados.get(
                "inversor",
            ),

            possui_bateria=dados.get(
                "possui_bateria",
                False,
            ),

            autonomia_horas=dados.get(
                "autonomia_horas",
                0.0,
            ),

            capacidade_bateria_necessaria=dados.get(
                "capacidade_bateria_necessaria",
                0.0,
            ),

            baterias=dados.get(
                "baterias",
            ),

            quantidade_baterias=dados.get(
                "quantidade_baterias",
                0,
            ),

            capacidade_bateria_instalada=dados.get(
                "capacidade_bateria_instalada",
                0.0,
            ),

            geracao_estimada=dados.get(
                "geracao_estimada",
                0.0,
            ),

            custo_paineis=dados.get(
                "custo_paineis",
                0.0,
            ),

            custo_inversor=dados.get(
                "custo_inversor",
                0.0,
            ),

            custo_baterias=dados.get(
                "custo_baterias",
                0.0,
            ),

            custos_adicionais=dados.get(
                "custos_adicionais",
                0.0,
            ),

            custo_total=dados.get(
                "custo_total",
                0.0,
            ),

            compatibilidade=dados.get(
                "compatibilidade",
            ),
        )