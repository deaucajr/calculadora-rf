---
title: "PDF to Markdown"
source: "https://pdf2md.morethan.io/"
author:
published:
created: 2026-06-12
description: "Converts PDF files to Markdown."
tags:
  - "clippings"
---
## SUMÁRIO

- 1. GLOSSÁRIO
- 2. FUNCIONAMENTO DA FERRAMENTA CALC
- 2.1 Utilização da Ferramenta CALC
- 2.1.1 Acesso
- 2.2 Manutenção da Base da Ferramenta CALC
- 2.2.1 Cobertura
- 2.2.2 Inclusões
- 2.2.3 Alterações
- 2.2.4 Exclusões
- 2.3 Atualização do IPCA em dia de divulgação do índice pelo IBGE
- 2.4 Suporte à Ferramenta CALC
- 3. Metodologia de Cálculo
- 3.1 Metodologia de Cálculo para Debêntures
- 3.1.1 Debêntures Prefixadas
- 3.1.2 Debêntures Indexadas a um Percentual da Taxa DI
- 3.1.3 Debêntures Indexadas a Taxa DI mais Spread
- 3.1.4 Debêntures indexadas ao IPCA
- 3.1.4.1 VNA na data de aniversário do papel............................................................
- 3.1.4.1.1 VNA entre a data de divulgação do IPCA e o próximo aniversário
- 3.1.4.2 VNA entre as datas de aniversário e de divulgação do IPCA
- 3.1.4.3 Taxa Exponencial
- 3.1.5 Debêntures indexadas ao IGP-M
- 3.1.5.1 VNA na data de aniversário do papel............................................................
- 3.1.5.1.1 VNA entre a data de divulgação do IGP-M e data de aniversário
- 3.1.5.2 VNA entre as datas de aniversário e de divulgação do IGP-M
- 3.2 Metodologia de Cálculo para Títulos Públicos
- 3.2.1 LFT – Tesouro Selic
- 3.2.2 LTN – Tesouro Prefixado
- 3.2.3 NTN-F – Tesouro Prefixado com Juros Semestrais
- 3.2.4 NTN-B – Tesouro IPCA com Juros Semestrais
- 3.2.4.1 VNA no décimo quinto dia do mês
- 3.2.4.1.1 VNA entre a divulgação do IPCA pelo IBGE e o décimo quinto dia do mês
- IPCA pelo IBGE 3.2.4.1.2 VNA após o décimo quinto dia do mês e a próxima data de divulgação do
- 3.2.5 NTN-B Principal – Tesouro IPCA
- 3.2.5.1 VNA no décimo quinto dia do mês
- mês 3.2.5.1.1 VNA entre a divulgação do IPCA do mês anterior e o décimo quinto dia do
- 3.2.5.2 VNA após o décimo quinto dia do mês
- 3.2.6 NTN-C – Tesouro IGP-M com juros semestrais
- 3.2.6.1 VNA no primeiro dia do mês
- 3.2.6.2 VNA entre a divulgação do IGP-M e o primeiro dia do mês
- 3.2.6.3 VNA após o primeiro dia do mês
- 3.3 Metodologia de Cálculo para DI Acumulado e Índice DI
- 3.3.1 Metodologia de Cálculo Acumulado de DI
- 3.3.2 Metodologia de Cálculo do Índice DI
- 3.4 Metodologia de Cálculo para CRA’s e CRI’s
- 3.4.1 CRA’s e CRI’s Indexados a Taxa DI
- 3.4.2 CRA’s e CRI’s Indexados ao IPCA
- 3.4.2.1 VNA na data de aniversário do papel............................................................
- 3.4.2.1.1 VNA entre a data de divulgação do IPCA e o próximo aniversário
- 3.4.2.2 VNA entre as datas de aniversário e de divulgação do IPCA
- Anexo I – Interpolação
- Anexo II – Regras de arredondamento e truncamento

4

## 1\. GLOSSÁRIO

```
Taxa DI Taxa de Depósito Interfinanceiro divulgada
diariamente pela B
```
```
Duration Prazo médio ponderado dos fluxos de caixa a serem
pagos pelo título avaliado
```
```
IBGE Instituto Brasileiro de Geografia e Estatística
```
```
IGP-M Índice Geral de Preços – Mercado
```
```
IPCA Índice Nacional de Preços ao Consumidor – Amplo
```
```
PU Preço Unitário
```
```
PUPar Preço calculado considerando o valor nominal
atualizado e taxa de juros vigente do papel no
momento de sua precificação
```
```
PU Operação Preço calculado considerando o valor nominal
atualizado e taxa de desconto indicada para o papel
no momento de sua precificação
```
```
Financeiro PU Operação multiplicado pela quantidade negociada
```
```
SELIC Sistema Especial de Liquidação e de Custódia
```
```
SELIC Over Taxa média ponderada e ajustada das operações de
financiamento por um dia lastreadas em títulos
```

5

```
públicos federais e cursadas no SELIC, divulgada
diariamente pelo Banco Central do Brasil (BCB)
```
```
Spread Para as definições desse documento tomamos por
spread a sobretaxa aplicada a remuneração de um
título, ou simplesmente a taxa de juros de emissão do
papel
```
```
Valor Base Valor Base do título (de emissão ou atualizado
```
```
Remanescente monetariamente) descontado as amortizações e
demais eventos extraordinários que possam incorrer
sobre o papel entre a sua data de emissão e a sua
data de avaliação
```
```
VNA Valor Nominal Atualizado
```
```
VNE Valor Nominal de Emissão
```
```
VNR Valor Nominal Remanescente
```
```
VF Valor Futuro
```
```
VP Valor Presente
```

6

## 2\. FUNCIONAMENTO DA FERRAMENTA CALC

A CALC atende à demanda por uma ferramenta amigável para consulta de PUs  
em operações de títulos públicos,debêntures e CRA’s negociados na plataforma  
Cetip|Trader. Com essa ferramenta, a B3 oferece mais um serviço no mercado  
de debêntures,títulos públicos e CRA’s com o objetivo de viabilizar a liquidação  
de negócios de forma eficiente e transparente para o mercado de balcão.

Para as operações eletrônicas ou operações registradas no Cetip|Voice, a  
ferramenta traz a rentabilidade e permite o batimento e confirmação de PU e  
financeiro entre as partes, o que contribui para o processo operacional da  
instituição financeira que opera nesse mercado.

A CALC realiza cálculos de PU, Taxa, disponibiliza informações adicionais como  
projeções de fluxo de caixa (VP, VF), descrição do ativo, VNA e cálculo de  
duration. Além disso, a B3 oferece a possibilidade de integrar a CALC com os  
sistemas internos (boletadores, sistemas de risco, etc) de seus participantes.

A CALC permite ao usuário realizar simulações, armazenar na tela as consultas  
realizadas, acompanhar o preço da posição em carteira de debêntures e títulos  
públicos e calcular preços de liquidação para D0 e D+1.

## 2.1 Utilização da Ferramenta CALC

É possível utilizar a ferramenta CALC para obter preços referenciais com base  
em uma taxa inserida pelo usuário ou taxas referenciais de acordo com um preço  
inserido pelo mesmo.

Para selecionar o tipo de título desejado no website da ferramenta CALC, basta  
clicar nos botões indicados em ( 1 ). O título específico deve ser escolhido a partir  
da caixa de seleção ( 2 ). Também é possível escolher entre calcular o preço (PU)  
a partir da informação da taxa, ou a taxa a partir da informação do preço, através  
da seleção dos botões indicados em ( 3 ), sendo necessário inserir um valor para

7

a taxa (caso a intenção seja calcular o preço indicativo) ou para o preço (caso o  
objetivo seja calcular a taxa) no campo indicado ( 4 ).

Após clicar em calcular, o resultado será exibido conforme abaixo:

Na tela de resultados é possível verificar o fluxo de pagamentos do título, bem  
como os cálculos do preço indicativo (PU), taxa, descrição do ativo, valor nominal  
atualizado (VNA) e duration.

Importante: Os preços calculados pela ferramenta CALC são indicativos,  
ficando a critério do usuário considerá-lo para negociação do título em questão.

```
8
```
```
Qualquer dúvida com relação aos resultados exibidos pela ferramenta poderá
ser direcionada para o e-mail calculadorarendafixa@b3.com.br.
```

## 2.1.1 Acesso

```
Para usuários não cadastrados a CALC permite até 10 cálculos diários. Usuários
não cadastrados recebem uma mensagem de pop-up comunicando quantos
cálculos restam na data antes de receber o resultado do cálculo.
```
```
Para usuários que efetuarem o cadastro mas não realizarem a contração de um
plano serão disponibilizados, além dos cálculos realizados enquanto usuário não
cadastrado, 5 cálculos adicionais com a mesma precisão disponibilizada para
um usuário contratante de um plano.
```
```
Usuários PREMIUM, aqueles associados a um dos planos disponíveis, terão
limitações de acesso determinadas de acordo com as características de seu
plano. Informações acerca das características dos planos disponíveis e forma de
contração encontram-se disponíveis no site da ferramenta.
```

## 2.2 Manutenção da Base da Ferramenta CALC

## 2.2.1 Cobertura

```
A fim de ampliar a quantidade de títulos disponíveis na CALC, diariamente, a
equipe responsável pela manutenção da calculadora realiza inclusões de
debêntures emitidas ao mercado, desde que estejam com a documentação
```

9

disponível e possuam características calculadas pelos métodos de cálculo  
existentes na CALC.

Além disso, periodicamente, a base de títulos negociados na plataforma de  
negociação Cetip|Trader é comparada com os títulos cadastrados na CALC,  
avaliando-se a possibilidade de inclusão dos títulos que ainda não foram  
disponibilizados na ferramenta.

Abaixo a relação de títulos objeto de precificação pela ferramenta CALC:

Títulos Públicos: NTN-B, LFT, LTN e NTN-F.

Debentures

São objeto de cálculo pela ferramenta debentures que apresentarem as  
seguintes características:

Não são objeto de cálculo pela ferramenta debentures que não encontrem  
correspondência no quadro acima ou ainda que apresentem qualquer das  
características destacadas abaixo:  
i. Duas ou mais taxas de juros (spread ou sobretaxa) diferentes que  
remunerem o papel a qualquer momento;  
ii. Títulos objeto de amortização extraordinária sem que após a  
ocorrência do evento seja indicada a nova composição dos fluxos de  
amortização;

10

```
iii. Fluxo de amortização não apresente conjunto de datas e taxas
expressamente definidas;
iv. Clausula de conversibilidade ou permutabilidade;
v. Apresentem sucessivas falhas no pagamento de suas obrigações;
vi. Título em situação de inadimplência;
vii. Data de vencimento indefinida ou perpetuidade;
viii. Apresentem evento de amortização sem a ocorrência de evento
simultâneo de juros;
ix. Apresentem evento genérico;
```

Após o título ser incluído na CALC, prontamente ele poderá ser consultado por  
meio do website da ferramenta. O cálculo através da Plataforma de Negociação  
Cetip|Trader torna-se disponível ao usuário a partir do dia útil seguinte ao de  
sua inclusão no website.

Para debêntures que apresentam pagamento de prêmio, integrada à CALC, uma  
mensagem conforme no exemplo abaixo irá aparecer antes do resultado do  
cálculo informando acerca dos parâmetros considerados para geração dos  
valores exibidos:

11

Destacamos, porém, que para os títulos que apresentarem tais particularidades  
a realização do cálculo será possível somente no site. Não será possível realizar  
o seu cálculo de forma automática na plataforma de negociação Cetip|Trader,  
de tal forma que sua negociação será possível mediante a informação do PU  
(cujo valor poderá ser obtido através do site da calculadora).

CRA **’** s e CRI **’s**

São objeto de cálculo pela ferramenta CRA’s e CRI’s que apresentarem as  
seguintes características:

Não são objeto de cálculo pela ferramenta CRA’s e CRI’s que não encontrem  
correspondência no quadro acima ou ainda que apresentem qualquer das  
características destacadas abaixo:  
i. Duas ou mais taxas de juros (spread ou sobretaxa) diferentes que  
remunerem o papel a qualquer momento;  
ii. Títulos objeto de amortização extraordinária sem que após a  
ocorrência do evento seja indicada a nova composição dos fluxos de  
amortização;  
iii. Fluxo de amortização não apresente conjunto de datas e taxas  
expressamente definidas;  
iv. Clausula de conversibilidade ou permutabilidade;  
v. Apresentem sucessivas falhas no pagamento de suas obrigações;  
vi. Título em situação de inadimplência;  
vii. Data de vencimento indefinida ou perpetuidade;  
viii. Apresentem evento de amortização sem a ocorrência de evento  
simultâneo de juros;

12

```
ix. Apresentem evento genérico;
```

A metodologia de cálculo, bem como os indexadores atendidos pela calculadora,  
estão detalhados no item 3 deste manual (Metodologia de Cálculo).

## 2.2.2 Inclusões

Quando o usuário da CALC identificar um papel específico (tanto debêntures  
como títulos públicos) ainda não calculado pela ferramenta, existe a  
possibilidade do mesmo solicitar a inclusão para a B3, por meio do canal  
exclusivo de comunicação através do e-mail calculadorarendafixa@b3.com.br.

A equipe responsável pela manutenção da calculadora avaliará se as  
características do título estão contempladas pela metodologia de cálculo  
existente e se a documentação do ativo está disponível no site do agente  
fiduciário. Após análise será informado ao participante se a solicitação poderá  
ser atendida ou não.

Atenção: O prazo de resposta é de até 48 horas após a solicitação, tendo  
em vista que o horário de atendimento da calculadora é de Segunda a Sexta  
das 8 h30 às 18 h30, excluídas as datas em que se observar feriado nacional  
e os horários de funcionamento do final do ano.

Na possibilidade de inclusão do título solicitado, a consulta no website da  
ferramenta CALC é imediata, para a inclusões na Plataforma de Negociação do  
Cetip|Trader, o título em questão fica disponível somente após o encerramento  
do processamento noturno, podendo ser visualizada no dia útil seguinte.

## 2.2.3 Alterações

Debêntures podem sofrer alterações em suas características durante o período  
de vigência. Algumas dessas alterações impactam diretamente o cálculo do  
papel na CALC, tais como: alteração do vencimento, alteração nas taxas de juros

13

ou em outras características do fluxo do papel que impactem a determinação de  
seu preço.

Toda e qualquer alteração da debênture é realizada após a divulgação e  
disponibilização da respectiva documentação para a B3. Após análise desta  
documentação, a atualização no website é imediata, enquanto que a atualização  
na plataforma de Negociação do Cetip|Trader ocorre somente após o  
encerramento do processamento noturno e pode ser visualizada no dia útil  
seguinte.

Ao identificar que a alteração das características de um título impossibilita o seu  
cálculo na ferramenta, é feita a desativação imediata do cálculo do título no  
website da ferramenta CALC e na plataforma de negociação do Cetip|Trader.

## 2.2.4 Exclusões

As debêntures vencidas são retiradas da CALC 7 dias corridos após a ocorrência  
do evento. As debêntures canceladas ou que tiveram um resgate antecipado  
total, também serão retiradas 7 dias corridos após a divulgação e  
disponibilização da respectiva documentação para a B3.

## 2.3 Atualização do IPCA em dia de divulgação do índice pelo IBGE

A divulgação do IPCA é realizada pelo IBGE em caráter mensal, de acordo com  
o calendário disponibilizado em sua página na internet. A publicação ocorre pela  
manhã, geralmente por volta das 09:00hs. Após a publicação, as bases da CALC  
(tanto do site como no Cetip|Trader) são atualizadas e este valor passa a ser  
incorporado aos cálculos da ferramenta.

## 2.4 Suporte à Ferramenta CALC

A B3 disponibiliza equipe especializada no suporte à ferramenta CALC, cujo  
horário de atendimento é de segunda a sexta-feira, salvo datas em que se

14

observar feriado nacional, das 0 8 h30 às 1 8 h30 através do telefone (11) 3111 -  
1585 ou do endereço de e-mail calculadorarendafixa@b3.com.br. Quaisquer  
solicitações realizadas após o encerramento das atividades serão atendidas no  
dia útil seguinte.

Para dúvidas em relação ao produto ou solicitações de melhorias e  
desenvolvimentos, a equipe de Produtos – Sistemas de Front, Middle e Balcão  
deverá ser contatada pelo telefone (11) 2565 - 5922 ou pelo endereço de e-mail  
calc@b3.com.br.

## 3\. Metodologia de Cálculo

A CALC disponibiliza aos seus usuários preços referenciais para os Títulos  
Públicos Federais, Debêntures e CRA’s negociados em mercado.

São objeto de cálculo, desde que apresentem características que se enquadrem  
nas métricas disponíveis, títulos que sejam remunerados por taxas prefixadas,  
taxa DI, taxa SELIC, IPCA e IGP-M.

O acesso aos cálculos produzidos pode ser realizado pela rede mundial de  
computadores, no endereço https://calculadorarendafixa.com.br/, ou através da  
Plataforma de Negociação Cetip|Trader.

## 3.1 Metodologia de Cálculo para Debêntures

## 3.1.1 Debêntures Prefixadas

São objeto de cálculo os títulos emitidos com taxas prefixadas expressas em  
percentual ao ano na base 252 dias úteis.

15

O Valor Nominal de Emissão (VNE) desses papéis não sofre atualização  
monetária, sendo o seu Valor Nominal Atualizado (VNA) na data indicada para  
o cálculo determinado pela fórmula abaixo:

### 𝑽𝑵𝑨=𝑽𝑵𝑬− ∑𝑨𝒕𝒊

```
𝒏
```
```
𝒊=𝟏
```

Tal que:

𝑨𝒕𝒊 amortização que incide sobre o título na data 𝒕𝒊, tomando-se por 𝒕𝟏

```
a data de ocorrência da primeira amortização do papel e 𝒕𝒏 a data
de ocorrência de amortização imediatamente anterior à data de
realização do cálculo
```
```
𝑨𝒕𝒊=𝑽𝑵𝑬×𝑷𝒕𝒊
```

𝑷𝒕𝒊 valor percentual da amortização, indicado na escritura de emissão,

```
a ser realizada na data 𝒕𝒊
```

Nos casos particulares em que a data de cálculo precede a ocorrência da  
primeira amortização ou o papel não apresente amortizações então VNA = VNE.

O PU Par é determinado pelo VNA acrescido da remuneração acumulada dos  
juros desde a data de emissão do papel ou a data do último evento de pagamento  
de juros (o mais recente) até a data de cálculo, conforme a equação abaixo:

### 𝑷𝑼 𝑷𝒂𝒓=𝑽𝑵𝑨×(𝟏+𝒋𝒆𝒎𝒊)

```
𝟐𝟓𝟐𝒅𝒖
```

Tal que:

16

𝒋𝒆𝒎𝒊 taxa de juros de emissão do papel, expressa em percentual ao ano  
na base 252 dias úteis

𝒅𝒖 quantidade de dias úteis entre a data de emissão ou a data do  
último evento de pagamento de juros (o mais recente) e a data de  
cálculo

O PU Operação é dado pelo somatório dos eventos remanescentes que  
incidirão sobre a debênture avaliada, conforme a equação abaixo:

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐=
```

### ∑ 𝑱𝒕𝒊

```
𝒏
𝒊=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```

### 𝟐𝟓𝟐𝒅𝒖𝒊+^

### ∑ 𝑨𝒕𝒋

```
𝒏
𝒋=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```
```
𝒅𝒖𝒋
𝟐𝟓𝟐
```

Tal que:

𝑱𝒕𝒊 valor futuro dos juros a serem pagos pelo emissor na data 𝒕𝒊,

```
conforme definido adiante nesse documento, tomando-se por 𝒕𝟏 a
primeira data de pagamento de juros imediatamente posterior à
data de cálculo determinada e 𝒕𝒏 a última data de pagamento de
evento de juros
```

𝑨𝒕𝒋 valor da amortização a ser paga pelo emissor na data 𝒕𝒋, tomando-

```
se por 𝒕𝟏 a primeira data de pagamento de amortização
imediatamente posterior à data de cálculo determinada e 𝒕𝒏 a última
data de ocorrência de amortização
```

𝒋𝒏𝒆𝒈 taxa de juros indicada pelo usuário para a realização do negócio,

```
expressa em percentual ao ano na base 252 dias úteis
```

𝒅𝒖𝒊 quantidade de dias úteis entre a data de cálculo e a data do evento  
de juros considerado

17

𝒅𝒖𝒋 quantidade de dias úteis entre a data de cálculo e a data do evento

de amortização considerado  
Onde:

### 𝑱𝒕𝒊=𝑽𝑵𝑨𝒕𝒊× \[(𝟏+ 𝒋𝒆𝒎𝒊)

```
𝒅𝒖𝟐𝟓𝟐𝒕
−𝟏]
```

Tal que:

𝑽𝑵𝑨𝒕𝒊 Valor Nominal Atualizado da debênture na data 𝒕𝒊

𝒋𝒆𝒎𝒊 taxa de juros de emissão do papel, expressa em percentual ao ano  
na base 252 dias úteis

𝒅𝒖𝒕 quantidade de dias úteis entre a data do evento de juros  
considerado e a data do evento de juros imediatamente anterior a  
este. Caso o evento em questão seja o primeiro pagamento de  
juros, então considera-se a quantidade de dias úteis entre a data  
de início de rentabilidade do papel e a data de ocorrência do evento

Toma-se por Valor Financeiro da Operação (ou, simplesmente, Financeiro)  
conforme terminologia exibida na ferramenta, o seguinte:

```
𝑭𝒊𝒏𝒂𝒏𝒄𝒆𝒊𝒓𝒐=𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐×𝑸𝒖𝒂𝒏𝒕𝒊𝒅𝒂𝒅𝒆 𝒅𝒆 𝑻í𝒕𝒖𝒍𝒐𝒔 𝑵𝒆𝒈𝒐𝒄𝒊𝒂𝒅𝒐𝒔
```

A Duration do papel é calculada em anos e da seguinte maneira:

### 𝑫𝒖𝒓𝒂𝒕𝒊𝒐𝒏= \[

### ∑ 𝑱𝒕𝒊

```
𝒏
𝒊=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```

### 𝟐𝟓𝟐𝒅𝒖𝒊×𝒅𝒕𝒊+^

### ∑ 𝑨𝒕𝒋

```
𝒏
𝒋=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```
```
𝒅𝒖𝒋
𝟐𝟓𝟐
```

### ×𝒅𝒕𝒋

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐 ]
𝟐𝟓𝟐^
```

18

Tal que:

𝒅𝒕𝒊 quantidade de dias úteis entre a data de cálculo e a data de

```
ocorrência do evento 𝑱𝒕𝒊
```

𝒅𝒕𝒋 quantidade de dias úteis entre a data de cálculo e a data de

```
ocorrência do evento 𝑨𝒕𝒋
```

## 3.1.2 Debêntures Indexadas a um Percentual da Taxa DI

Título privado cujo fluxo de pagamentos de juros é indexado a um percentual da  
Taxa DI.

O Valor Nominal de Emissão (VNE) dessa categoria de títulos não sofre  
atualização monetária, tal que seu Valor Nominal Atualizado (VNA) na data  
indicada para o cálculo é dado por:

```
𝑽𝑵𝑨=𝑽𝑵𝑬− ∑𝑨𝒕𝒊
```
```
𝒏
```
```
𝒊=𝟏
```

Tal que:

𝑨𝒕𝒊 amortização que incide sobre o título na data 𝒕𝒊, tomando-se por 𝒕𝟏  
a data de ocorrência da primeira amortização do papel e 𝒕𝒏 a data  
de ocorrência de amortização imediatamente anterior à data de  
realização do cálculo

Nos casos particulares em que a data de cálculo precede a ocorrência da  
primeira amortização ou o papel não apresente amortizações então VNA = VNE.

O PU Par é calculado conforme equação abaixo:

19

### 𝑷𝑼 𝑷𝒂𝒓=𝑽𝑵𝑨 × ∏{\[(𝟏+𝑻𝒂𝒙𝒂 𝑫𝑰𝒊)

```
𝟐𝟓𝟐𝟏
−𝟏] × %𝑫𝑰𝒆𝒎𝒊+𝟏}
```
```
𝒅𝒖
```
```
𝒊=𝟏
```

Tal que:

𝑻𝒂𝒙𝒂 𝑫𝑰𝒊 Taxa DI, publicada diariamente pela B3, observada na data i,

%𝑫𝑰𝒆𝒎𝒊 percentual de remuneração da taxa DI indicada na emissão do  
titulo

𝒅𝒖 quantidade de dias úteis entre a data de emissão ou a data do  
último evento de pagamento de juros (o mais recente) até a data  
de cálculo

O PU Operação é determinado pelo somatório do valor presente dos eventos  
remanescentes do papel baseados no cálculo da taxa indicada pelo usuário para  
o negócio. É utilizada uma curva estimada para a Taxa DI construída com a  
própria Taxa DI e os contratos futuros DI1 da B 3. Destaca-se que são  
considerados os preços de fechamento desses contratos do dia útil  
imediatamente anterior à data de realização do cálculo para construção da curva  
de desconto dos títulos. A maneira como essa curva é interpolada está detalhada  
no Anexo I – INTERPOLAÇÃO.

O valor do PU Operação é dado pela equação abaixo e seus argumentos são  
definidos na sequência:

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐= ∑𝑭𝑫𝑽𝑭𝒊𝒊
```
```
𝒏
```

𝒊=𝟏  
Tal que:

20

𝒊 data de ocorrência do evento calculado

𝒏 data de ocorrência do último evento incidente sobre o título avaliado

O valor na data de sua ocorrência 𝒊, ou simplesmente valor futuro (𝑽𝑭𝒊), de cada  
evento será dado por:

### 𝑽𝑭𝒊=𝑽𝑵𝑨𝒊×\[∏{\[(𝟏+𝑫𝑰𝒕)

```
𝟐𝟓𝟐𝟏
−𝟏] × %𝑫𝑰𝒆𝒎𝒊+𝟏}
```
```
𝒅𝒖
```
```
𝒕=𝟏
```

### −𝟏\]+𝑨𝒊

Tal que:

𝒊 data de ocorrência do evento calculado

𝑽𝑵𝑨𝒊 Valor Nominal Atualizado do papel na data 𝒊

𝒅𝒖 quantidade de dias úteis entre a data do evento imediatamente  
anterior à data 𝒊 e o evento a ocorrer na data 𝒊

𝑨𝒊 amortização a ser realizada na data 𝒊

𝑫𝑰𝒕 a Taxa DI vigente ou projetada com base nos vértices dos contratos  
futuros de Taxa DI negociados em ambiente de bolsa, na data 𝒕, tal  
que tomamos por 𝒕=𝟏 o dia útil imediatamente posterior ao de  
ocorrência do evento imediatamente anterior à data 𝒊 e assim  
sucessivamente

%𝑫𝑰𝒆𝒎𝒊 percentual de remuneração da taxa DI indicada na emissão do  
título

21

O Fator de Desconto do evento a ocorrer na data 𝒊, ou simplesmente 𝑭𝑫𝒊, que  
traz a valor presente o fluxo projetado para a data 𝒊 é dado por:

### 𝑭𝑫𝒊= ∏{\[(𝟏+𝑷𝒓𝒐𝒋 𝑫𝑰𝒛)

```
𝟐𝟓𝟐𝟏
−𝟏] × %𝑫𝑰𝒏𝒆𝒈+𝟏}
```
```
𝒅𝒖
```
```
𝒛=𝟏
```
```
Tal que:
```

%𝑫𝑰𝒏𝒆𝒈 percentual de remuneração da taxa DI para o papel indicado pelo  
usuário para realização do negócio

𝑷𝒓𝒐𝒋 𝑫𝑰𝒛 a Taxa DI projetada com base nos vértices dos contratos futuros de  
Taxa DI negociados em ambiente de bolsa, na data 𝒕, tal que  
tomamos por 𝒕=𝟏 o dia útil imediatamente posterior ao de  
ocorrência do evento imediatamente anterior à data 𝒊, ou data de  
cálculo do título (o que for mais recente), e assim sucessivamente

A projeção da Taxa DI entre a data de cálculo e uma data futura qualquer  
expressa nas equações acima pelas variáveis 𝑫𝑰𝒕 e 𝑷𝒓𝒐𝒋 𝑫𝑰𝒛, denotada  
simplesmente 𝑷𝒓𝒐𝒋 𝑫𝑰𝒕 abaixo, é dada por:

### 𝑷𝒓𝒐𝒋 𝑫𝑰𝒕=

### {^

### \[(𝟏+𝑽𝒑)

```
𝒅𝒖𝒑
𝟐𝟓𝟐
(𝟏+𝑽𝒂)
```

### 𝒅𝒖𝟐𝟓𝟐𝒂\]

```
𝒅𝒖𝒅𝒖𝒕−𝒅𝒖𝒂
𝒑−𝒅𝒖𝒂
× (𝟏+𝑽𝒂)
```
```
𝒅𝒖𝟐𝟓𝟐𝒂
```
```
}^
```
```
𝟐𝟓𝟐𝒅𝒖
𝒕
− 𝟏
```
```
Tal que:
```

𝒕 data para a qual se deseja calcular a projeção acumulada da Taxa  
DI

22

𝑽𝒑 valor do vértice de contrato futuro de Taxa DI negociado em bolsa

```
posterior à data 𝒕, expresso em taxa anualizada na base 252 dias
úteis
```

𝑽𝒂 valor do vértice de contrato futuro de Taxa DI negociado em bolsa  
anterior à data 𝒕, expresso em taxa anualizada na base 252 dias  
úteis

𝒅𝒖𝒑 quantidade de dias úteis entre as datas de cálculo e de vencimento  
do vértice 𝑽𝒑

𝒅𝒖𝒂 quantidade de dias úteis entre as datas de cálculo e de vencimento  
do vértice 𝑽𝒂

𝒅𝒖𝒕 quantidade de dias úteis entre as datas de cálculo e a data 𝒕 para  
a qual se procura a projeção da Taxa DI

Toma-se por Valor Financeiro da Operação, ou simplesmente, Financeiro,  
conforme terminologia exibida na ferramenta, o seguinte:

```
𝑭𝒊𝒏𝒂𝒏𝒄𝒆𝒊𝒓𝒐=𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐×𝑸𝒖𝒂𝒏𝒕𝒊𝒅𝒂𝒅𝒆 𝒅𝒆 𝑻í𝒕𝒖𝒍𝒐𝒔 𝑵𝒆𝒈𝒐𝒄𝒊𝒂𝒅𝒐𝒔
```

A Duration do papel é calculada em anos e da seguinte maneira:

### 𝑫𝒖𝒓𝒂𝒕𝒊𝒐𝒏=

### \[∑

### 𝑽𝑭𝒊

### 𝑭𝑫𝒊

```
𝒏
𝒊=𝟏 ×𝒅𝒖𝒊
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐
```

### \]

### 𝟐𝟓𝟐^

Tal que:

𝑽𝑭𝒊 valor futuro do evento a ocorrer na data 𝒊

𝑭𝑫𝒊 fator de desconto a ser aplicado sobre o fluxo a ocorrer na data 𝒊

23

𝒅𝒖𝒊 quantidade de dias úteis entre a data de cálculo e a data de  
ocorrência do evento 𝒊

Para cálculos retroativos, a CALC não armazena os dados históricos,  
considerando sempre o divulgado e as projeções disponíveis na data de  
apuração.

## 3.1.3 Debêntures Indexadas a Taxa DI mais Spread

Título privado cujo fluxo de pagamentos de juros é indexado à Taxa DI ou à Taxa  
DI acrescida de um spread (taxa de juros indicada na escritura de emissão do  
título).

O Valor Nominal de Emissão (VNE) dessa categoria de títulos não sofre  
atualização monetária, tal que seu Valor Nominal Atualizado (VNA) na data  
indicada para o cálculo é dado por:

### 𝑽𝑵𝑨=𝑽𝑵𝑬− ∑𝑨𝒕𝒊

```
𝒏
```
```
𝒊=𝟏
```

Tal que:

𝑨𝒕𝒊 amortização que incide sobre o título na data 𝒕𝒊, tomando-se por 𝒕𝟏

```
a data de ocorrência da primeira amortização do papel e 𝒕𝒏 a data
de ocorrência de amortização imediatamente anterior à data de
realização do cálculo
```

Nos casos particulares em que a data de cálculo precede a ocorrência da  
primeira amortização ou o papel não apresente amortizações então VNA = VNE.

O PU Par é calculado conforme equação abaixo:

24

### 𝑷𝑼 𝑷𝒂𝒓=𝑽𝑵𝑨 × (𝟏+𝑻𝒂𝒙𝒂 𝑫𝑰𝒊)

```
𝟐𝟓𝟐𝒅𝒖
×(𝟏+𝒋𝒆𝒎𝒊)
𝟐𝟓𝟐𝒅𝒖
```

Tal que:

𝑻𝒂𝒙𝒂 𝑫𝑰𝒊 Taxa DI, publicada diariamente pela B3, observada na data i

𝒅𝒖 quantidade de dias úteis entre a data de emissão ou a data do  
último evento de pagamento de juros (o mais recente) até a data  
de cálculo

𝒋𝒆𝒎𝒊 taxa de juros de emissão do papel, expressa em percentual ao ano  
na base 252 dias úteis

O PU Operação é determinado pelo somatório do valor presente dos eventos  
remanescentes do papel baseados no cálculo da taxa indicada pelo usuário para  
o negócio. É utilizada uma curva estimada para a Taxa DI construída com a  
própria Taxa DI e os contratos futuros DI1 da B3. Destaca-se que são  
considerados os preços de fechamento desses vértices do dia útil imediatamente  
anterior a data de realização do cálculo para construção da curva de desconto  
dos títulos. A maneira como essa curva é interpolada está detalhada no Anexo I

- INTERPOLAÇÃO.

O valor do PU Operação é dado pela equação abaixo e seus argumentos são  
definidos na sequência:

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐= ∑𝑭𝑫𝑽𝑭𝒊𝒊
```
```
𝒏
```

𝒊=𝟏  
Tal que:

𝒊 data de ocorrência do evento calculado

25

𝒏 data de ocorrência do último evento incidente sobre o título avaliado

O valor na data de sua ocorrência 𝒊, ou simplesmente valor futuro (𝑽𝑭𝒊), de cada  
evento será dado por:

### 𝑽𝑭𝒊=𝑽𝑵𝑨𝒊×\[(𝟏+𝑫𝑰𝒕)

```
𝟐𝟓𝟐𝒅𝒖
×(𝟏+𝒋𝒆𝒎𝒊)
𝟐𝟓𝟐𝒅𝒖
−𝟏]+𝑨𝒊
```

Tal que:

𝒊 data de ocorrência do evento calculado

𝑽𝑵𝑨𝒊 Valor Nominal Atualizado do papel na data 𝒊

𝒅𝒖 quantidade de dias úteis entre a data do evento imediatamente  
anterior à data 𝒊 e o evento a ocorrer na data 𝒊

𝑨𝒊 amortização a ser realizada na data 𝒊

𝑫𝑰𝒕 a Taxa DI vigente ou projetada com base nos vértices dos contratos  
futuros de Taxa DI negociados em ambiente de bolsa, na data 𝒕, tal  
que tomamos por 𝒕=𝟏 o dia útil imediatamente posterior ao de  
ocorrência do evento imediatamente anterior à data 𝒊 e assim  
sucessivamente

𝒋𝒆𝒎𝒊 taxa de juros de emissão do papel, expressa em percentual ao ano  
na base 252 dias úteis

O Fator de Desconto do evento a ocorrer na data 𝒊, ou simplesmente 𝑭𝑫𝒊, que  
traz a valor presente o fluxo projetado para a data 𝒊 é dado por:

26

### 𝑭𝑫𝒊= (𝟏+𝑷𝒓𝒐𝒋 𝑫𝑰𝒛)

```
𝟐𝟓𝟐𝒅𝒖
×(𝟏+𝒋𝒏𝒆𝒈)
𝟐𝟓𝟐𝒅𝒖𝒛
```
```
Tal que:
```

𝒋𝒏𝒆𝒈 taxa de juros expressa em percentual ao ano na base 252 dias

```
úteis, para realização do negócio indicada pelo usuário
```

𝒅𝒖𝒛 quantidade de dias úteis entre a data de cálculo do título e o evento  
a ocorrer na data 𝒊

𝑷𝒓𝒐𝒋 𝑫𝑰𝒛 a Taxa DI projetada com base nos vértices dos contratos futuros de  
Taxa DI negociados em ambiente de bolsa, na data 𝒕, tal que  
tomamos por 𝒕=𝟏 o dia útil imediatamente posterior ao de  
ocorrência do evento imediatamente anterior à data 𝒊, ou data de  
cálculo do título (o que for mais recente), e assim sucessivamente

A projeção da Taxa DI entre a data de cálculo e uma data futura qualquer  
expressa nas equações acima pelas variáveis 𝑫𝑰𝒕 e 𝑷𝒓𝒐𝒋 𝑫𝑰𝒛, denotada  
simplesmente 𝑷𝒓𝒐𝒋 𝑫𝑰𝒕 abaixo, é dada por:

### 𝑷𝒓𝒐𝒋 𝑫𝑰𝒕=

### {^

### \[(𝟏+𝑽𝒑)

```
𝒅𝒖𝒑
𝟐𝟓𝟐
(𝟏+𝑽𝒂)𝒅𝒖𝟐𝟓𝟐𝒂
```

### \]

```
𝒅𝒖𝒅𝒖𝒕−𝒅𝒖𝒂
𝒑−𝒅𝒖𝒂
× (𝟏+𝑽𝒂)
```
```
𝒅𝒖𝟐𝟓𝟐𝒂
```
```
}^
```
```
𝟐𝟓𝟐𝒅𝒖
𝒕
− 𝟏
```
```
Tal que:
```

𝒕 data para a qual se deseja calcular a projeção acumulada da Taxa  
DI

27

𝑽𝒑 valor do vértice de contrato futuro de Taxa DI negociado em bolsa

```
posterior à data 𝒕, expresso em taxa anualizada na base 252 dias
úteis
```

𝑽𝒂 valor do vértice de contrato futuro de Taxa DI negociado em bolsa  
anterior à data 𝒕, expresso em taxa anualizada na base 252 dias  
úteis

𝒅𝒖𝒑 quantidade de dias úteis entre as datas de cálculo e de vencimento  
do vértice 𝑽𝒑

𝒅𝒖𝒂 quantidade de dias úteis entre as datas de cálculo e de vencimento  
do vértice 𝑽𝒂

𝒅𝒖𝒕 quantidade de dias úteis entre as datas de cálculo e a data 𝒕 para  
a qual se procura a projeção da Taxa DI

Toma-se por Valor Financeiro da Operação (ou, simplesmente, Financeiro)  
conforme terminologia exibida na ferramenta, o seguinte:

```
𝑭𝒊𝒏𝒂𝒏𝒄𝒆𝒊𝒓𝒐=𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐×𝑸𝒖𝒂𝒏𝒕𝒊𝒅𝒂𝒅𝒆 𝒅𝒆 𝑻í𝒕𝒖𝒍𝒐𝒔 𝑵𝒆𝒈𝒐𝒄𝒊𝒂𝒅𝒐𝒔
```

A Duration do papel é calculada em anos e da seguinte maneira:

### 𝑫𝒖𝒓𝒂𝒕𝒊𝒐𝒏=

### \[∑

### 𝑽𝑭𝒊

### 𝑭𝑫𝒊

```
𝒏
𝒊=𝟏 ×𝒅𝒖𝒊
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐
```

### \]

### 𝟐𝟓𝟐^

Tal que:

𝑽𝑭𝒊 valor futuro do evento a ocorrer na data 𝒊

𝑭𝑫𝒊 fator de desconto a ser aplicado sobre o fluxo a ocorrer na data 𝒊

28

𝒅𝒖𝒊 quantidade de dias úteis entre a data de cálculo e a data de  
ocorrência do evento 𝒊

Para cálculos retroativos, a CALC não armazena os dados históricos,  
considerando sempre o divulgado e as projeções disponíveis na data de  
apuração.

## 3.1.4 Debêntures indexadas ao IPCA

Título privado cujo fluxo de pagamentos de juros é corrigido pelo IPCA, índice de  
preços divulgado mensalmente pelo IBGE.

O Valor Nominal Atualizado (VNA) é o Valor Nominal de Emissão (VNE)  
atualizado pela variação mensal do IPCA e/ou das projeções. A atualização do  
VNA deve observar a data de aniversário da debênture, bem como as datas de  
divulgação do índice e projeção do IPCA, dessa forma segregando a  
determinação de seu VNA em três momentos:

## 3.1.4.1 VNA na data de aniversário do papel............................................................

Nessa data, o Valor Nominal Atualizado é calculado da seguinte maneira:

𝑽𝑵𝑨= (^) 𝑰𝑷𝑪𝑨𝑰𝑷𝑪𝑨𝒕  
𝒕𝟎

### .𝑽𝑵𝑬∙ (𝟏−∑𝑨𝒂𝒏𝒕)

Tal que:

𝑰𝑷𝑪𝑨𝒕 valor do número-índice do mês anterior ao mês de atualização

𝑰𝑷𝑪𝑨𝒕𝟎 valor do número-índice do mês anterior ao primeiro mês de  
rentabilidade do papel

𝑽𝑵𝑬 Valor Nominal de Emissão

29

∑𝑨𝒂𝒏𝒕 Soma dos percentuais de amortização que ocorreram antes da  
data de cálculo do papel

## 3.1.4.1.1 VNA entre a data de divulgação do IPCA e o próximo aniversário

Será dado pela equação abaixo:

### 𝑽𝑵𝑨= 𝑽𝑵𝑨𝒊× (𝑰𝑷𝑪𝑨𝑰𝑷𝑪𝑨𝒕−𝒕𝟏)

```
𝒅𝒖𝒅𝒖𝒊
𝒕∙ (𝟏−∑𝑨
𝒂𝒏𝒕)^
```

Tal que:

𝑽𝑵𝑨𝒊 Valor Nominal Atualizado do papel na última data de aniversário

𝑰𝑷𝑪𝑨𝒕 valor do IPCA divulgado para o mês anterior ao mês corrente

𝑰𝑷𝑪𝑨𝒕−𝟏 valor do IPCA divulgado imediatamente antes do valor de 𝑰𝑷𝑪𝑨𝒕

𝒅𝒖𝒊 quantidade de dias úteis entre a última data de aniversário e a data  
de cálculo do papel

𝒅𝒖𝒕 quantidade de dias úteis entre a última e a próxima data de  
aniversário do papel

∑𝑨𝒂𝒏𝒕 Soma dos percentuais de amortização que ocorreram antes da  
data de cálculo do papel

## 3.1.4.2 VNA entre as datas de aniversário e de divulgação do IPCA

Entre a data de aniversário do papel e a próxima divulgação do IPCA o VNA do  
papel será dado por:

```
𝑽𝑵𝑨= 𝑽𝑵𝑨𝒊× (𝟏+𝑰𝑷𝑪𝑨𝒑𝒓𝒐𝒋)
```
```
𝒅𝒖𝒅𝒖𝒊
𝒕∙ (𝟏−∑𝑨𝒂𝒏𝒕)
```

30

Tal que:

𝑽𝑵𝑨𝒊 Valor Nominal Atualizado do papel na última data de aniversário

𝑰𝑷𝑪𝑨𝒑𝒓𝒐𝒋 projeção corrente do IPCA divulgada pela ANBIMA em percentual  
(o usuário poderá indicar um valor para a projeção caso queira  
realizar os cálculos com um valor diferente daquele divulgado pela  
ANBIMA)

𝒅𝒖𝒊 quantidade de dias úteis entre a última data de aniversário e a data  
de cálculo do papel

𝒅𝒖𝒕 quantidade de dias úteis entre a última e a próxima data de  
aniversário do papel

∑𝑨𝒂𝒏𝒕 Soma dos percentuais de amortização que ocorreram antes da  
data de cálculo do papel

A CALC utiliza a projeção do IPCA divulgada pela ANBIMA sempre que o cálculo  
for realizado entre as datas de aniversário e de divulgação do IPCA pelo IBGE,  
mesmo que na escritura de emissão conste que o emissor utiliza, na ausência  
do IPCA mais atual, o último IPCA conhecido.

O PU Par é determinado pelo VNA na data de cálculo do papel acrescido da  
remuneração acumulada dos juros desde a data de emissão do papel ou a data  
do último evento de pagamento de juros (o mais recente) até a data de cálculo,  
conforme a equação abaixo:

### 𝑷𝑼 𝑷𝒂𝒓=𝑽𝑵𝑨×(𝟏+𝒋𝒆𝒎𝒊)

```
𝟐𝟓𝟐𝒅𝒖
```

Tal que:

𝒋𝒆𝒎𝒊 taxa de juros de emissão do papel, expressa em percentual ao ano  
na base 252 dias úteis

31

𝒅𝒖 quantidade de dias úteis entre a data de emissão ou a data do  
último evento de pagamento de juros (o mais recente) e a data de  
cálculo.

O PU Operação é dado pelo somatório dos eventos remanescentes do papel  
trazidos a valor presente pela taxa indicada pelo usuário (𝒋𝒏𝒆𝒈) no momento do

cálculo, conforme a equação abaixo:

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐=
```

### ∑ 𝑱𝒕𝒊

```
𝒏
𝒊=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```

### 𝟐𝟓𝟐𝒅𝒖𝒊+^

### ∑ 𝑨𝒕𝒋

```
𝒏
𝒋=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```
```
𝒅𝒖𝒋
𝟐𝟓𝟐
```

Tal que:

𝑱𝒕𝒊 valor futuro dos juros a serem pagos pelo emissor na data 𝒕𝒊,

```
conforme definido adiante nesse documento, tomando-se por 𝒕𝟏 a
primeira data de pagamento de juros imediatamente posterior à
data de cálculo determinada e 𝒕𝒏 a última data de pagamento de
evento de juros
```

𝑨𝒕𝒋 valor da amortização a ser paga pelo emissor na data 𝒕𝒋, tomando-

```
se por 𝒕𝟏 a primeira data de pagamento de amortização
imediatamente posterior à data de cálculo determinada e 𝒕𝒏 a última
data de ocorrência de amortização
```

𝒋𝒏𝒆𝒈 taxa de juros indicada pelo usuário para a realização do negócio,

```
em percentual ao ano na base 252 dias úteis
```

𝒅𝒖𝒊 quantidade de dias úteis entre a data de cálculo e a data do evento  
de juros considerado

32

𝒅𝒖𝒋 quantidade de dias úteis entre a data de cálculo e a data do evento

de amortização considerado  
Tal que:

### 𝑱𝒕𝒊=𝑽𝑵𝑨𝒕𝒊× \[(𝟏+ 𝒋𝒆𝒎𝒊)

```
𝒅𝒖𝟐𝟓𝟐𝒕
−𝟏]
```

Na qual:

𝑽𝑵𝑨𝒕𝒊 Valor Nominal Atualizado da debênture na data 𝒕𝒊

𝒋𝒆𝒎𝒊 taxa de juros de emissão do papel, expressa em percentual ao ano  
na base 252 dias úteis

𝒅𝒖𝒕 quantidade de dias úteis entre a data do evento de juros  
considerado e a data do evento de juros imediatamente anterior a  
este. Caso o evento em questão seja o primeiro pagamento de  
juros, então considera-se a quantidade de dias úteis entre a data  
de início de rentabilidade do papel e a data de ocorrência do evento  
E:

```
𝑨𝒕𝒋=𝑽𝑵𝑨𝒕𝒊×𝑷𝒕𝒊
```

Onde:

𝑷𝒕𝒊 percentual de amortização indicado para o evento de amortização  
que ocorre na data 𝒕𝒊

A amortização poderá incidir sobre o Valor Base de Emissão ou sobre o Valor  
Base Remanescente do Título.

Toma-se por Valor Financeiro da Operação (ou, simplesmente, Financeiro)  
conforme terminologia exibida na ferramenta, o seguinte:

33

```
𝑭𝒊𝒏𝒂𝒏𝒄𝒆𝒊𝒓𝒐=𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐×𝑸𝒖𝒂𝒏𝒕𝒊𝒅𝒂𝒅𝒆 𝒅𝒆 𝑻í𝒕𝒖𝒍𝒐𝒔 𝑵𝒆𝒈𝒐𝒄𝒊𝒂𝒅𝒐𝒔
```

A Duration do papel é calculada em anos e da seguinte maneira:

### 𝑫𝒖𝒓𝒂𝒕𝒊𝒐𝒏= \[

### ∑ 𝑱𝒕𝒊

```
𝒏
𝒊=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```

### 𝟐𝟓𝟐𝒅𝒖𝒊×𝒅𝒕𝒊+^

### ∑ 𝑨𝒕𝒋

```
𝒏
𝒋=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```
```
𝒅𝒖𝒋
𝟐𝟓𝟐
```

### ×𝒅𝒕𝒋

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐 ]
𝟐𝟓𝟐^
```

Tal que:

𝒅𝒕𝒊 quantidade de dias úteis entre a data de cálculo e a data de

```
ocorrência do evento 𝑱𝒕𝒊
```

𝒅𝒕𝒋 quantidade de dias úteis entre a data de cálculo e a data de

```
ocorrência do evento 𝑨𝒕𝒋
```

## 3.1.4.3 Taxa Exponencial

Debêntures indexadas ao IPCA com a taxa exponencial 360 dias corridos cujo  
fluxo de pagamentos é calculado considerando a quantidade de dias corridos  
entre datas.

## 3.1.5 Debêntures indexadas ao IGP-M

Título privado cujo fluxo de pagamentos de juros é corrigido pelo IGP-M, índice  
de preços divulgado mensalmente pelo IBGE.

O Valor Nominal Atualizado (VNA) é o Valor Nominal de Emissão (VNE)  
atualizado pela variação mensal do IGP-M e/ou das projeções. A atualização do  
VNA deve observar a data de aniversário da debênture, bem como as datas de

34

divulgação do índice e projeção do IGP-M, dessa forma segregando a  
determinação de seu VNA em três momentos:

## 3.1.5.1 VNA na data de aniversário do papel............................................................

Nessa data, o Valor Nominal Atualizado é calculado da seguinte maneira:

𝑽𝑵𝑨= (^) 𝑰𝑮𝑷𝑴𝑰𝑮𝑷𝑴𝒕−𝒕𝟏.𝑽𝑵𝑬∙ (𝟏−∑𝑨𝒂𝒏𝒕)  
Tal que:  
𝑰𝑮𝑷𝑴𝒕 valor do número-índice do mês anterior ao mês de atualização  
𝑰𝑮𝑷𝑴𝒕𝟎 valor do número-índice do mês anterior ao primeiro mês de  
rentabilidade do papel  
𝑽𝑵𝑬 Valor Nominal de Emissão  
∑𝑨𝒂𝒏𝒕 Soma dos percentuais de amortização que ocorreram antes da  
data de cálculo do papel

## 3.1.5.1.1 VNA entre a data de divulgação do IGP-M e data de aniversário

Será dado pela equação abaixo:

### 𝑽𝑵𝑨= 𝑽𝑵𝑨𝒊∙ (𝑰𝑮𝑷𝑴𝑰𝑮𝑷𝑴𝒕

```
𝒕−𝟏
```

### )

```
𝒅𝒖𝒅𝒖𝒊
𝒕∙ (𝟏−∑𝑨
𝒂𝒏𝒕)^
```

Tal que:

𝑽𝑵𝑨𝒊 Valor Nominal Atualizado do papel na última data de aniversário

𝑰𝑮𝑷𝑴𝒕 valor do IGP-M divulgado para o mês anterior ao mês  
corrente

35

𝑰𝑮𝑷𝑴𝒕−𝟏 valor do IGP-M divulgado imediatamente antes do valor de 𝑰𝑮𝑷𝑴𝒕

𝒅𝒖𝒊 quantidade de dias úteis entre a última data de aniversário e a data  
de cálculo do papel

𝒅𝒖𝒕 quantidade de dias úteis entre a última e a próxima data de  
aniversário do papel

∑𝑨𝒂𝒏𝒕 Soma dos percentuais de amortização que ocorreram antes da  
data de cálculo do papel

## 3.1.5.2 VNA entre as datas de aniversário e de divulgação do IGP-M

Entre as datas de aniversário do papel e a próxima divulgação do IGP-M o VNA  
do papel será dado por:

### 𝑽𝑵𝑨= 𝑽𝑵𝑨𝒊∙ (𝟏+𝑰𝑮𝑷𝑴𝒑𝒓𝒐𝒋)

```
𝒅𝒖𝒅𝒖𝒊
𝒕∙ (𝟏−∑𝑨𝒂𝒏𝒕)
```

Tal que:

𝑽𝑵𝑨𝒊 Valor Nominal Atualizado do papel na última data de aniversário

𝑰𝑮𝑷𝑴𝒑𝒓𝒐𝒋 projeção corrente do IGP-M divulgada pela ANBIMA em percentual  
(o usuário poderá indicar um valor para a projeção caso queira  
realizar os cálculos com um valor diferente daquele divulgado pela  
ANBIMA)

𝒅𝒖𝒊 quantidade de dias úteis entre a última data de aniversário e a data  
de cálculo do papel

𝒅𝒖𝒕 quantidade de dias úteis entre a última e a próxima data de  
aniversário do papel

∑𝑨𝒂𝒏𝒕 Soma dos percentuais de amortização que ocorreram antes da  
data de cálculo do papel

36

O PU Par é determinado pelo VNA na data de cálculo do papel acrescido da  
remuneração acumulada dos juros desde a data de emissão do papel ou a data  
do último evento de pagamento de juros (o mais recente) até a data de cálculo,  
conforme a equação abaixo:

```
𝑷𝑼 𝑷𝒂𝒓=𝑽𝑵𝑨×(𝟏+𝒋𝒆𝒎𝒊)
𝟐𝟓𝟐𝒅𝒖
```

Tal que:

𝒋𝒆𝒎𝒊 taxa de juros de emissão do papel, expressa em percentual ao ano  
na base 252 dias úteis

𝒅𝒖 quantidade de dias úteis entre a data de emissão ou a data do  
último evento de pagamento de juros (o mais recente) e a data de  
cálculo.

O PU Operação é dado pelo somatório dos eventos remanescentes do papel  
trazidos a valor presente pela taxa indicada pelo usuário (𝒋𝒏𝒆𝒈) no momento do  
cálculo:

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐=
```

### ∑ 𝑱𝒕𝒊

```
𝒏
𝒊=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```

### 𝟐𝟓𝟐𝒅𝒖𝒊+^

### ∑ 𝑨𝒕𝒋

```
𝒏
𝒋=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```
```
𝒅𝒖𝒋
𝟐𝟓𝟐
```

Tal que:

𝑱𝒕𝒊 valor futuro dos juros a serem pagos pelo emissor na data 𝒕𝒊,  
conforme definido adiante nesse documento, tomando-se por 𝒕𝟏 a  
primeira data de pagamento de juros imediatamente posterior à  
data de cálculo determinada e 𝒕𝒏 a última data de pagamento de  
evento de juros

37

𝑨𝒕𝒋 valor da amortização a ser paga pelo emissor na data 𝒕𝒋, tomando-

```
se por 𝒕𝟏 a primeira data de pagamento de amortização
imediatamente posterior à data de cálculo determinada e 𝒕𝒏 a última
data de ocorrência de amortização
```

𝒋𝒏𝒆𝒈 taxa de juros indicada pelo usuário para a realização do negócio,

```
em percentual ao ano na base 252 dias úteis
```

𝒅𝒖𝒊 quantidade de dias úteis entre a data de cálculo e a data do evento  
de juros considerado

𝒅𝒖𝒋 quantidade de dias úteis entre a data de cálculo e a data do evento

```
de amortização considerado
```

No qual:

### 𝑱𝒕𝒊=𝑽𝑵𝑨𝒕𝒊× \[(𝟏+ 𝒋𝒆𝒎𝒊)

```
𝒅𝒖𝟐𝟓𝟐𝒕
−𝟏]
```

Tal que:

𝑽𝑵𝑨𝒕𝒊 Valor Nominal Atualizado da debênture na data 𝒕𝒊

𝒋𝒆𝒎𝒊 taxa de juros de emissão do papel, expressa em percentual ao ano  
na base 252 dias úteis

𝒅𝒖𝒕 quantidade de dias úteis entre a data do evento de juros  
considerado e a data do evento de juros imediatamente anterior a  
este. Caso o evento em questão seja o primeiro pagamento de  
juros, então considera-se a quantidade de dias úteis entre a data  
de início de rentabilidade do papel e a data de ocorrência do evento  
E:

38

### 𝑨𝒕𝒋=𝑽𝑵𝑨𝒕𝒊×𝑷𝒕𝒊

Onde:

𝑷𝒕𝒊 percentual de Amortização indicado para o evento de amortização  
que ocorre na data 𝒕𝒊  
A amortização poderá incidir sobre o Valor Base de Emissão ou sobre o Valor  
Base Remanescente do Título.

Toma-se por Valor Financeiro da Operação (ou, simplesmente, Financeiro)  
conforme terminologia exibida na ferramenta, o seguinte:

```
𝑭𝒊𝒏𝒂𝒏𝒄𝒆𝒊𝒓𝒐=𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐×𝑸𝒖𝒂𝒏𝒕𝒊𝒅𝒂𝒅𝒆 𝒅𝒆 𝑻í𝒕𝒖𝒍𝒐𝒔 𝑵𝒆𝒈𝒐𝒄𝒊𝒂𝒅𝒐𝒔
```

A Duration do papel é calculada em anos e da seguinte maneira:

### 𝑫𝒖𝒓𝒂𝒕𝒊𝒐𝒏= \[

### ∑ 𝑱𝒕𝒊

```
𝒏
𝒊=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```

### 𝟐𝟓𝟐𝒅𝒖𝒊×𝒅𝒕𝒊+^

### ∑ 𝑨𝒕𝒋

```
𝒏
𝒋=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```
```
𝒅𝒖𝒋
𝟐𝟓𝟐
```

### ×𝒅𝒕𝒋

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐 ]
𝟐𝟓𝟐^
```

Tal que:

𝒅𝒕𝒊 quantidade de dias úteis entre a data de cálculo e a data de  
ocorrência do evento 𝑱𝒕𝒊

𝒅𝒕𝒋 quantidade de dias úteis entre a data de cálculo e a data de

```
ocorrência do evento 𝑨𝒕𝒋
```

39

## 3.2 Metodologia de Cálculo para Títulos Públicos

## 3.2.1 LFT – Tesouro Selic

Título Público Federal cujo fator de remuneração corresponde a 100% da  
variação da taxa SELIC Over divulgada pelo Banco Central do Brasil.

Possui Valor Nominal de Emissão (VNE) igual a R$ 1.000,00 a ser atualizado  
diariamente pelo fator de remuneração mencionado acima entre sua data de  
emissão e sua data de vencimento.

Apresenta um único fluxo de pagamento a ocorrer na sua data de vencimento.

O Valor Nominal Atualizado (VNA) e o PU Par desse título são equivalentes ao  
VNE corrigido pela valorização da Taxa Selic desde a data de emissão até a data  
de cálculo, obtido da seguinte maneira:

### 𝑽𝑵𝑨=𝑽𝑵𝑬×∏\[(𝟏+𝑻𝒂𝒙𝒂 𝑺𝒆𝒍𝒊𝒄𝒊)𝟏/𝟐𝟓𝟐−𝟏\]

```
𝒅𝒖
```
```
𝒊=𝟏
```

Tal que:

𝑻𝒂𝒙𝒂 𝑺𝒆𝒍𝒊𝒄𝒊 Taxa Selic que ocorreu no dia i

𝒅𝒖 número de dias úteis entre a data de emissão do título e a  
data de cálculo

O PU Operação é calculando da seguinte maneira:

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐= 𝟏
(𝑹+𝟏)𝟐𝟓𝟐𝒅𝒖
```

### ×𝑽𝑵𝑨

40

Tal que:

𝑹 taxa informada para o negócio a ser realizado expressa em percentual ao  
ano na base 252 dias uteis

𝒅𝒖 número de dias úteis entre a data de vencimento do título e data de cálculo

Toma-se por Valor Financeiro da Operação (ou, simplesmente, Financeiro)  
conforme terminologia exibida na ferramenta, o seguinte:

```
𝑭𝒊𝒏𝒂𝒏𝒄𝒆𝒊𝒓𝒐=𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐×𝑸𝒖𝒂𝒏𝒕𝒊𝒅𝒂𝒅𝒆 𝒅𝒆 𝑻í𝒕𝒖𝒍𝒐𝒔 𝑵𝒆𝒈𝒐𝒄𝒊𝒂𝒅𝒐𝒔
```

Por ser um título que apresenta um único fluxo de pagamentos a Duration, em  
anos, desse papel é simplesmente a quantidade de dias úteis remanescentes  
entre a data de cálculo e sua data de vencimento dividido por 252 (número de  
dias úteis correspondente a um ano).

No dia útil seguinte a divulgação da taxa de juros Selic pelo COPOM, a  
Calculadora contemplará a alteração da taxa para apuração dos preços em D+1  
para ativos indexados ao Selic pela manhã. O cadastro da alteração irá  
considerar a Selic Meta reduzida de 0,10 p.p.

## 3.2.2 LTN – Tesouro Prefixado

Título público com fluxo de caixa único igual a R$ 1.000 a ser pago na data de  
seu vencimento.

O PU Operação é o fluxo de caixa de R$ 1.000 trazido a valor presente por uma  
taxa indicada pelo usuário da Calculadora de Renda Fixa, calculado conforme a  
equação abaixo:

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐= 𝟏𝟎𝟎𝟎
(𝟏+𝒕𝒂𝒙𝒂)
```

### 𝟐𝟓𝟐𝒅𝒖^

41

Tal que:

𝒕𝒂𝒙𝒂 taxa indicada pelo usuário da Calculadora de Renda Fixa, expressa ao  
ano na base 252 dias uteis

𝒅𝒖 número de dias úteis entre a data de vencimento do título e data de cálculo

Toma-se por Valor Financeiro da Operação (ou, simplesmente, Financeiro)  
conforme terminologia exibida na ferramenta, o seguinte:

```
𝑭𝒊𝒏𝒂𝒏𝒄𝒆𝒊𝒓𝒐=𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐×𝑸𝒖𝒂𝒏𝒕𝒊𝒅𝒂𝒅𝒆 𝒅𝒆 𝑻í𝒕𝒖𝒍𝒐𝒔 𝑵𝒆𝒈𝒐𝒄𝒊𝒂𝒅𝒐𝒔
```

Por ser um título que apresenta um único fluxo de pagamentos a Duration, em  
anos, desse papel é simplesmente a quantidade de dias úteis remanescentes  
entre a data de cálculo e sua data de vencimento dividido por 252 (número de  
dias úteis correspondente a um ano).

## 3.2.3 NTN-F – Tesouro Prefixado com Juros Semestrais

Título Público Federal pré-fixado emitido com valor de face de R$ 1.000, cuja  
remuneração é paga semestralmente e sua amortização integral ocorre na data  
de vencimento do papel.

O PU Operação é o somatório de todos os fluxos de cupom e principal trazido a  
valor presente por uma taxa indicada pelo usuário da Calculadora de Renda Fixa,  
calculado conforme a equação abaixo:

42

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐=[∑(
```

### ((𝟏+𝒄𝒖𝒑𝒐𝒎)𝟏𝟐−𝟏)×𝟏𝟎𝟎𝟎

### (𝟏+𝒕𝒂𝒙𝒂)

### 𝒅𝒖𝟐𝟓𝟐𝒊 )

```
𝒏
```
```
𝒊=𝟏
```

### \]+ 𝟏𝟎𝟎𝟎

### (𝟏+𝒕𝒂𝒙𝒂)

### 𝟐𝟓𝟐𝒅𝒖^

Tal que:

𝒄𝒖𝒑𝒐𝒎 cupom do título definido em sua emissão

𝒏 número de fluxos de pagamentos remanescentes do título

𝒕𝒂𝒙𝒂 taxa indicada pelo usuário da Calculadora de Renda Fixa, expressa  
ao ano na base 252 dias úteis

𝒅𝒖𝒊 número de dias úteis entre a data de cálculo e a data de ocorrência  
do evento 𝒊

𝒅𝒖 número de dias úteis entre a data de cálculo e a data de vencimento  
do título

Toma-se por Valor Financeiro da Operação (ou, simplesmente, Financeiro)  
conforme terminologia exibida na ferramenta, o seguinte:

```
𝑭𝒊𝒏𝒂𝒏𝒄𝒆𝒊𝒓𝒐=𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐×𝑸𝒖𝒂𝒏𝒕𝒊𝒅𝒂𝒅𝒆 𝒅𝒆 𝑻í𝒕𝒖𝒍𝒐𝒔 𝑵𝒆𝒈𝒐𝒄𝒊𝒂𝒅𝒐𝒔
```

A Duration do título é dada por:

### 𝑫𝒖𝒓𝒂𝒕𝒊𝒐𝒏=

### \[∑ (((𝟏+𝒄𝒖𝒑𝒐𝒎)

```
𝟏𝟐
−𝟏)∙𝟏𝟎𝟎𝟎
(𝟏+𝒕𝒂𝒙𝒂)
```

### 𝒏𝒊=𝟏 𝟐𝟓𝟐𝒅𝒖𝒊 )\]∙𝒅𝒖𝒊+ 𝟏𝟎𝟎𝟎

### (𝟏+𝒕𝒂𝒙𝒂)

### 𝟐𝟓𝟐𝒅𝒖∙𝒅𝒖

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐
𝟐𝟓𝟐^
```

43

## 3.2.4 NTN-B – Tesouro IPCA com Juros Semestrais

Título público emitido com valor de face igual R$ 1.000, o qual remunera a juros  
semestrais e paga o principal na data de vencimento, tendo cada um de seus  
fluxos corrigidos pelo IPCA.

O Valor Nominal Atualizado (VNA) é o Valor de R$ 1.000 atualizado pela  
variação mensal do IPCA e/ou das projeções, desde a data de emissão do título  
até a data de cálculo. Segrega-se a determinação do VNA em três momentos  
distintos:

## 3.2.4.1 VNA no décimo quinto dia do mês

O Valor Nominal Atualizado (VNA), no décimo quinto dia do mês, é calculado da  
seguinte maneira:

### 𝑽𝑵𝑨=𝑰𝑷𝑪𝑨𝑰𝑷𝑪𝑨𝟎𝒕× 𝟏𝟎𝟎𝟎

Tal que:

𝑰𝑷𝑪𝑨𝒕 valor do número-índice do mês anterior ao mês de referência

𝑰𝑷𝑪𝑨𝟎 valor do número-índice do mês anterior a data de emissão do título

## 3.2.4.1.1 VNA entre a divulgação do IPCA pelo IBGE e o décimo quinto dia do mês

O Valor Nominal Atualizado (VNA) entre a divulgação do IPCA do mês anterior  
e o décimo quinto dia do mês, é calculado da seguinte maneira:

### 𝑽𝑵𝑨=\[𝑰𝑷𝑪𝑨𝑰𝑷𝑪𝑨𝒕𝒕−−𝟏𝟐\]

```
𝒅𝒖𝒅𝒖𝟏
𝟐× 𝑽𝑵𝑨
```

Tal que:

44

𝑰𝑷𝑪𝑨𝒕−𝟏 valor do número-índice divulgado pelo IBGE referente ao mês  
anterior ao mês de referência

𝑰𝑷𝑪𝑨𝒕−𝟐 valor do número-índice divulgado pelo IBGE referente a dois meses  
anteriores ao mês de referência

𝒅𝒖𝟏 número de dias úteis entre o dia 15 do mês anterior e a data de  
cálculo

𝒅𝒖𝟐 número de dias úteis total entre o dia 15 do mês anterior e a  
próximo dia 15

## IPCA pelo IBGE 3.2.4.1.2 VNA após o décimo quinto dia do mês e a próxima data de divulgação do

```
divulgação do IPCA pelo IBGE
```

O Valor Nominal Atualizado (VNA), após o décimo quinto dia do mês, é calculado  
da seguinte maneira:

### 𝑽𝑵𝑨=𝑽𝑵𝑨𝒕−𝟏 ×(𝟏+𝑰𝑷𝑪𝑨𝒑𝒓𝒐𝒋)

```
𝒅𝒖𝒅𝒖𝟏
𝟐
```

Tal que:

𝑽𝑵𝑨𝒕−𝟏 Valor Nominal Atualizado do mês anterior ao de referência

𝑰𝑷𝑪𝑨𝒑𝒓𝒐𝒋 projeção do IPCA, divulgada pela ANBIMA, para o mês de

```
referência (o usuário poderá indicar um valor para a projeção caso
queira realizar os cálculos com um valor diferente daquele
divulgado pela ANBIMA)
```

45

𝒅𝒖𝟏 número de dias úteis entre o dia 15 do mês de referência e a data  
de cálculo

𝒅𝒖𝟐 número de dias úteis entre os dias 15 do mês de referência e do  
próximo mês

O PU Par é o VNA multiplicado pela remuneração do cupom do título desde a  
data de emissão ou data do último evento (o mais recente) até a data de cálculo,  
conforme equação abaixo:

### 𝑷𝑼 𝑷𝒂𝒓=𝑽𝑵𝑨×\[(𝟏+𝒄𝒖𝒑𝒐𝒎)𝒅𝒖𝟐𝟓𝟐𝟏\]

Tal que:

𝒄𝒖𝒑𝒐𝒎 cupom do título definido em sua emissão

𝒅𝒖𝟏 número de dias úteis entre a data de cálculo e a data do último  
evento de juros pago pelo título

O PU Operação é o somatório dos cupons de cada evento acrescido do VNA. O  
fluxo de cada evento futuro é trazido a valor presente pela taxa indicada pelo  
usuário da CALC, conforme equação abaixo:

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐={[∑((𝟏+𝒄𝒖𝒑𝒐𝒎)
```
```
𝟏𝟐
−𝟏
(𝟏+𝒕𝒂𝒙𝒂)
```

### 𝟐𝟓𝒅𝒖𝟐𝒊 )

```
𝒏
```
```
𝒊=𝟏
```

### \]+ 𝟏

### (𝟏+𝒕𝒂𝒙𝒂)

### 𝟐𝟓𝟐𝒅𝒖}×𝑽𝑵𝑨^

46

Tal que:

𝒄𝒖𝒑𝒐𝒎 cupom do título definido em sua emissão

𝒕𝒂𝒙𝒂 taxa indicada pelo usuário da CALC expressa ao ano na base 252  
dias úteis

𝒅𝒖𝒊 número de dias úteis entre a data de cálculo e a data de vencimento  
do evento 𝒊

𝒅𝒖 número de dias úteis entre a data de cálculo e a data de vencimento  
do título

𝒏 número total de eventos remanescentes incidentes sobre o título

Toma-se por Valor Financeiro da Operação, (ou, simplesmente, Financeiro)  
conforme terminologia exibida na ferramenta, o seguinte:

```
𝑭𝒊𝒏𝒂𝒏𝒄𝒆𝒊𝒓𝒐=𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐×𝑸𝒖𝒂𝒏𝒕𝒊𝒅𝒂𝒅𝒆 𝒅𝒆 𝑻í𝒕𝒖𝒍𝒐𝒔 𝑵𝒆𝒈𝒐𝒄𝒊𝒂𝒅𝒐𝒔
```

A Duration do papel é calculada em anos e da seguinte maneira:

### 𝑫𝒖𝒓𝒂𝒕𝒊𝒐𝒏=

### {\[∑ ((𝟏+𝒄𝒖𝒑𝒐𝒎)

```
𝟏𝟐
−𝟏
(𝟏+𝒕𝒂𝒙𝒂)
```

### 𝒏𝒊=𝟏 𝟐𝟓𝟐𝒅𝒖𝒊 )\]∙𝒅𝒖𝒊+

### 𝟏

### (𝟏+𝒕𝒂𝒙𝒂)𝟐𝟓𝟐𝒅𝒖

### ∙ 𝒅𝒖}×𝑽𝑵𝑨

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐
𝟐𝟓𝟐^
```

Tal que:

𝒄𝒖𝒑𝒐𝒎 cupom do título definido em sua emissão

𝒕𝒂𝒙𝒂 taxa indicada pelo usuário da CALC

47

𝒅𝒖𝒊 número de dias úteis entre a data de cálculo e a data de ocorrência  
do evento 𝒊

𝒅𝒖 número de dias úteis entre a data de cálculo e a data de vencimento  
do título

## 3.2.5 NTN-B Principal – Tesouro IPCA

Título público emitido por R$ 1.000, com pagamento de juros e principal na data  
de vencimento, corrigidos por IPCA.

O Valor Nominal Atualizado (VNA) é o Valor de R$ 1.000 atualizado pela  
variação mensal do IPCA e/ou das projeções, desde a data de emissão do título  
até a data de cálculo.

## 3.2.5.1 VNA no décimo quinto dia do mês

O Valor Nominal Atualizado (VNA), no décimo quinto dia do mês, é calculado da  
seguinte maneira:

### 𝑽𝑵𝑨=𝑰𝑷𝑪𝑨𝑰𝑷𝑪𝑨𝒕

```
𝟎
```

### .×𝟏𝟎𝟎𝟎

Tal que:

𝑰𝑷𝑪𝑨𝒕 valor do número-índice do mês anterior ao mês de referência

𝑰𝑷𝑪𝑨𝟎 valor do número-índice do mês anterior à data de emissão do título

48

## mês 3.2.5.1.1 VNA entre a divulgação do IPCA do mês anterior e o décimo quinto dia do

```
quinto dia do mês
```

O Valor Nominal Atualizado (VNA) entre a divulgação do IPCA do mês anterior  
e o décimo quinto dia do mês, é calculado da seguinte maneira:

### 𝑽𝑵𝑨=\[𝑰𝑷𝑪𝑨𝑰𝑷𝑪𝑨𝒕𝒕−−𝟏𝟐\]

```
𝒅𝒄𝒅𝒄𝟏
𝟐× 𝑽𝑵𝑨𝒕−𝟏
```

Tal que:  
𝑰𝑷𝑪𝑨𝒕−𝟏 valor do número-índice do mês anterior ao mês de referência

𝑰𝑷𝑪𝑨𝒕−𝟐 valor do número-índice dois meses anteriores a data de cálculo

𝒅𝒄𝟏 número de dias corridos entre o dia 15 do mês anterior e a data de  
cálculo

𝒅𝒄𝟐 número de dias corridos total entre o dia 15 do mês anterior e a  
próximo dia 15

## 3.2.5.2 VNA após o décimo quinto dia do mês

O Valor Nominal Atualizado (VNA), após o décimo quinto dia do mês, é calculado  
da seguinte maneira:

### 𝑽𝑵𝑨=𝑽𝑵𝑨𝒕−𝟏×(𝟏+𝑰𝑷𝑪𝑨𝒑𝒓𝒐𝒋)

```
𝒅𝒄𝒅𝒄𝟏
𝟐
```

Tal que:

𝑽𝑵𝑨𝒕−𝟏 Valor Nominal Atualizado no dia 15 do mês anterior ao de  
referência;

49

𝑰𝑷𝑪𝑨𝒑𝒓𝒐𝒋 projeção do IPCA, divulgada pela ANBIMA, para o mês de

```
referência (pode ser indicada pelo usuário do Site da Calculadora
de Renda Fixa);
```

𝒅𝒄𝟏 número de dias corridos entre o dia 15 do mês de referência e a  
data de cálculo;

𝒅𝒄𝟐 número de dias corridos total entre o dia 15 do mês de referência e  
a próximo dia 15.

O PU Par ou VNA é o valor de R$ 1.000 corrigido pela inflação acumulada desde  
a data de emissão até a data de cálculo.

O PU Operação é o somatório dos cupons de cada evento acrescido do VNA. O  
fluxo de cada evento futuro é trazido a valor presente pela taxa indicada pelo  
usuário da CALC, obtido conforme equação abaixo:

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐= 𝑽𝑵𝑨
(𝟏+𝒕𝒂𝒙𝒂)
```

### 𝟐𝟓𝟐𝒅𝒖^

Tal que:

𝑽𝑵𝑨 Valor Nominal Atualizado da data do cálculo

𝒕𝒂𝒙𝒂 taxa indicada pelo usuário da CALC expressa ao ano na base 252  
dias úteis

𝒅𝒖 número de dias úteis entre a data de cálculo e a data de vencimento  
do título

50

Toma-se por Valor Financeiro da Operação (ou, simplesmente, Financeiro)  
conforme terminologia exibida na ferramenta, o seguinte:

```
𝑭𝒊𝒏𝒂𝒏𝒄𝒆𝒊𝒓𝒐=𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐×𝑸𝒖𝒂𝒏𝒕𝒊𝒅𝒂𝒅𝒆 𝒅𝒆 𝑻í𝒕𝒖𝒍𝒐𝒔 𝑵𝒆𝒈𝒐𝒄𝒊𝒂𝒅𝒐𝒔
```

A Duration desse título é representada pela quantidade de dias uteis entre a  
data de cálculo e o vencimento do papel dividido por 252.

## 3.2.6 NTN-C – Tesouro IGP-M com juros semestrais

Título público emitido com valor de face igual R$ 1.000, o qual remunera a juros  
semestrais e paga o principal na data de vencimento, tendo cada um de seus  
fluxos corrigidos pelo IGPM divulgado pela Fundação Getúlio Vargas.

O Valor Nominal Atualizado (VNA) é igual ao seu valor de emissão corrigido pela  
variação mensal do IGP-M e/ou das projeções, desde a data de emissão do título  
até a data de cálculo.

## 3.2.6.1 VNA no primeiro dia do mês

O Valor Nominal Atualizado (VNA), no primeiro dia do mês, é calculado da  
seguinte maneira:

### 𝑽𝑵𝑨=𝑰𝑮𝑷𝑴𝑰𝑮𝑷𝑴𝒕

```
𝟎
```

### ×𝟏𝟎𝟎𝟎

Tal que:

𝑰𝑮𝑷𝑴𝒕 valor do número-índice do mês de referência divulgado pela  
Fundação Getúlio Vargas

𝑰𝑮𝑷𝑴𝟎 valor do número-índice, divulgado pela Fundação Getúlio Vargas,  
do mês anterior à data de emissão do papel

51

## 3.2.6.2 VNA entre a divulgação do IGP-M e o primeiro dia do mês

O Valor Nominal Atualizado (VNA) entre a divulgação do IGP-M e o primeiro dia  
do mês, é calculado da seguinte maneira:

### 𝑽𝑵𝑨=\[𝑰𝑮𝑷𝑴𝑰𝑮𝑷𝑴𝒕

```
𝒕−𝟏
```

### \]

```
𝒅𝒖𝒅𝒖𝟏
𝟐 × 𝑽𝑵𝑨
𝒕−𝟏^
```

Tal que:

𝑰𝑮𝑷𝑴𝒕 valor do número-índice do mês de referência divulgado pela  
Fundação Getúlio Vargas

𝑰𝑮𝑷𝑴𝒕−𝟏 valor do número-índice do mês anterior ao de referência divulgado  
pela Fundação Getúlio Vargas

𝑽𝑵𝑨𝒕−𝟏 Valor Nominal Atualizado do mês anterior ao de referência

𝒅𝒖𝟏 número de dias úteis entre o dia 1° dia do mês de referência e a  
data de cálculo

𝒅𝒖𝟐 número de dias úteis total entre o dia 1° do mês anterior e o próximo  
dia 1°.

## 3.2.6.3 VNA após o primeiro dia do mês

Será calculado conforme a equação:

### 𝑽𝑵𝑨=𝑽𝑵𝑨𝒕−𝟏 × (𝟏+𝑰𝑮𝑷𝑴𝒑𝒓𝒐𝒋)

```
𝒅𝒖𝒅𝒖𝟏
𝟐
```

Tal que:

𝑽𝑵𝑨𝒕−𝟏 Valor Nominal Atualizado do mês anterior ao de referência

52

𝑰𝑮𝑷𝑴𝒑𝒓𝒐𝒋 projeção do IGP-M, divulgada pela ANBIMA, para o mês de

```
referência (podendo ser indicada pelo usuário do Site da
Calculadora de Renda Fixa caso não queira utilizar a oficial
considerada pelo sistema)
```

𝒅𝒖𝟏 número de dias úteis entre o dia 1º do mês de referência e a data  
de cálculo

𝒅𝒖𝟐 número de dias úteis total entre o dia 1º do mês de referência e a  
próximo dia 1º

O PU Par é o VNA multiplicado pela remuneração do cupom do título desde a  
data de emissão ou data do último evento (o mais recente) até a data de cálculo,  
obtido conforme equação abaixo:

### 𝑷𝑼 𝑷𝒂𝒓=𝑽𝑵𝑨.\[(𝟏+𝒄𝒖𝒑𝒐𝒎)𝒅𝒖𝟏⁄𝟐𝟓𝟐\]

Tal que:

𝒄𝒖𝒑𝒐𝒎 cupom do título definido em sua emissão

𝒅𝒖𝟏 número de dias úteis entre a data de cálculo e a data do último  
evento de juros pago pelo título

O PU Operação é o somatório dos cupons de cada evento acrescido do VNA. O  
fluxo de cada evento futuro é trazido a valor presente pela taxa indicada pelo  
usuário da Calculadora de Renda Fixa, obtido conforme equação abaixo:

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐={[∑((𝟏+𝒄𝒖𝒑𝒐𝒎)
```
```
𝟏𝟐
−𝟏
(𝟏+𝒕𝒂𝒙𝒂)
```

### 𝟐𝟓𝟐𝒅𝒖𝒊 )

```
𝒏
```
```
𝒊=𝟏
```

### \]+ 𝟏

### (𝟏+𝒕𝒂𝒙𝒂)

### 𝟐𝟓𝟐𝒅𝒖}×𝑽𝑵𝑨^

53

Tal que:

𝒄𝒖𝒑𝒐𝒎 cupom do título definido em sua emissão

𝒕𝒂𝒙𝒂 taxa indicada pelo usuário da CALC expressa ao ano na base 252  
dias uteis

𝒅𝒖𝒊 número de dias úteis entre a data de cálculo e a data de vencimento  
do evento 𝒊

𝒅𝒖 número de dias úteis entre a data de cálculo e a data de vencimento  
do título

𝒏 número total de eventos remanescentes incidentes sobre o titulo

Toma-se por Valor Financeiro da Operação (ou, simplesmente, Financeiro)  
conforme terminologia exibida na ferramenta, o seguinte:

```
𝑭𝒊𝒏𝒂𝒏𝒄𝒆𝒊𝒓𝒐=𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐×𝑸𝒖𝒂𝒏𝒕𝒊𝒅𝒂𝒅𝒆 𝒅𝒆 𝑻í𝒕𝒖𝒍𝒐𝒔 𝑵𝒆𝒈𝒐𝒄𝒊𝒂𝒅𝒐𝒔
```

A Duration do papel é calculada em anos e da seguinte maneira:

```
𝑫𝒖𝒓𝒂𝒕𝒊𝒐𝒏
```

### \=

### {\[∑ ((𝟏+𝒄𝒖𝒑𝒐𝒎)

### 𝟏𝟐−𝟏

### (𝟏+𝒕𝒂𝒙𝒂)

### 𝒏𝒊=𝟏 𝟐𝟓𝟐𝒅𝒖𝒊 )\]×𝒅𝒖𝒊+ 𝟏

### (𝟏+𝒕𝒂𝒙𝒂)

### 𝟐𝟓𝟐𝒅𝒖^ ×^ 𝒅𝒖}×𝑽𝑵𝑨

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐
𝟐𝟓𝟐^
```

54

Tal que:

𝒄𝒖𝒑𝒐𝒎 cupom do título definido em sua emissão

𝒕𝒂𝒙𝒂 taxa indicada pelo usuário da CALC

𝒅𝒖𝒊 número de dias úteis entre a data de cálculo e a data de ocorrência  
do evento 𝒊

𝒅𝒖 número de dias úteis entre a data de cálculo e a data de vencimento  
do título

## 3.3 Metodologia de Cálculo para DI Acumulado e Índice DI

Os critérios para a apuração da taxa DI, objetos dos cálculos deste item,  
encontram-se disponíveis para consulta pública no endereço:

```
http://www.b3.com.br/pt_br/market-data-e-indices/indices/indices-de-
segmentos-e-setoriais/di/metodologia-de-apuracao-da-taxa/
```

## 3.3.1 Metodologia de Cálculo Acumulado de DI

O cálculo do DI-B3 acumulado entre datas é efetuado através da seguinte  
fórmula:

𝑪=∏(𝟏+𝑻𝑫𝑰𝒌∗ (^) 𝟏𝟎𝟎𝒑 )  
𝒏  
𝒌=𝟏  
Onde:  
C Produtório das taxas DI-B3 Over com uso do percentual destacado, da  
data inicial (inclusive) até a data final (exclusive), calculado com  
arredondamento de 8 (oito) casas decimais.

55

n Número total de taxas DI-B3 Over, sendo “n” um número inteiro.

p Percentual destacado para a remuneração, informado com 4 (quatro)  
casas decimais.

𝑻𝑫𝑰𝒌 Taxa DI-B3 Over, expressa ao dia, calculada com arredondamento de 8  
(oito) casas decimais.

Expressão de 𝑻𝑫𝑰𝒌 até 31/12/1997:

```
𝑻𝑫𝑰𝒌=𝟑𝟎𝟎𝟎𝑫𝑰𝒌
```

Sendo k = 1, 2,..., n

Expressão de 𝑻𝑫𝑰𝒌 a partir de 01/01/1998:

### 𝑻𝑫𝑰𝒌=(𝟏+𝑫𝑰𝟏𝟎𝟎𝒌)

```
𝟐𝟓𝟐𝟏
−𝟏
```

Sendo k = 1, 2,..., n

𝑫𝑰𝒌 Taxa DI-B3 Over, informada com 2 (duas) casas decimais.

Observações:

a) O fator resultante da expressão (𝟏+𝑻𝑫𝑰𝒌∗ (^) 𝟏𝟎𝟎𝒑 ) é considerado com 16  
(dezesseis) casas sem arredondamento.  
b) Efetua-se o produtório dos fatores diários (𝟏+𝑻𝑫𝑰𝒌∗ (^) 𝟏𝟎𝟎𝒑), sendo que a  
cada fator diário acumulado, trunca-se o resultado com 16 (dezesseis) casas  
decimais e aplica-se o próximo fator diário, assim por diante até o último fator  
diário considerado.  
c) Uma vez os fatores diários estando acumulados como descrito acima,  
considera-se o fator resultante C com 8 (oito) decimais com arredondamento.

56

## 3.3.2 Metodologia de Cálculo do Índice DI

Índice DI B3 para Operações Futuras

Características

Data de início: 02/01/2008

Valor inicial ou Base do Índice (quant. de pontos): 10.000,00

Precisão: Duas casas decimais, com arredondamento;

Forma de valorização: O índice é valorizado diariamente pelo fator de 100% do  
DI B3 do dia útil imediatamente anterior.

Fórmula de cálculo da valorização do Índice DI B3

```
Í𝒏𝒅𝒊𝒄𝒆 𝑫𝑰 𝑪𝑬𝑻𝑰𝑷𝒅𝒏= Í𝒏𝒅𝒊𝒄𝒆 𝑫𝑰 𝑪𝑬𝑻𝑰𝑷𝒅𝒏−𝟏∗(𝑭𝒂𝒕𝒐𝒓 𝑫𝑰𝒅𝒏−𝟏)
```

Í𝒏𝒅𝒊𝒄𝒆 𝑫𝑰 𝑪𝑬𝑻𝑰𝑷𝒅𝒏 Número índice do dia “n”, valorizado pelo fator diário  
do DI do dia “n-1”, apurado com 2 (duas) casas  
decimais com arredondamento;

𝑭𝒂𝒕𝒐𝒓 𝑫𝑰𝒅𝒏−𝟏 Fator da Taxa DI over do dia “n-1” expressa ao dia,

```
calculado com 8 (oito) casas decimais, com
arredondamento, apurado conforme fórmula:
```

### 𝑭𝒂𝒕𝒐𝒓 𝑫𝑰𝒅𝒏−𝟏= (𝑫𝑰𝟏𝟎𝟎𝒅𝒏−𝟏+𝟏)

```
𝟏⁄𝟐𝟓𝟐
```

𝑫𝑰𝒅𝒏−𝟏 Taxa DI over do dia “n-1”, apurada e divulgada pela  
Cetip com base nos Depósitos Interfinanceiros  
prefixados, pactuados por um dia entre instituições de  
grupos econômicos distintos (extra-grupo), expressa

57

```
ao ano de 252 dias úteis, utilizada com 2 (duas) casas
decimais.
```

Observação:

Os dias “n” e “n-1” mencionados são dias úteis – dias em que há apuração do DI  
B3.

## 3.4 Metodologia de Cálculo para CRA’s e CRI’s

## 3.4.1 CRA’s e CRI’s Indexados a Taxa DI

Título privado cujo fluxo de pagamentos de juros é indexado a um percentual de  
variação da Taxa DI ou à Taxa DI acrescida de um spread.

Os métodos de cálculo disponíveis para esses títulos são denominados por:

DI-SPREAD D-N titulo indexado a 100% da variação do CDI com fixing  
deslocado em N dias uteis acrescido de um spread, indicado  
no termo de securitização do instrumento, em taxa ao ano  
capitalizado de forma composta em base 252 dias uteis

DI-PERC D-N titulo indexado a um percentual, indicado no termo de  
securitização do instrumento, da variação do CDI com fixing  
deslocado em N dias uteis

O Valor Nominal de Emissão (VNE) dessa categoria de títulos não sofre  
atualização monetária, tal que seu Valor Nominal Atualizado (VNA) na data  
indicada para o cálculo é dado por:

### 𝑽𝑵𝑨=𝑽𝑵𝑬− ∑𝑨𝒕𝒊

```
𝒏
```
```
𝒊=𝟏
```

Tal que:

58

𝑨𝒕𝒊 amortização que incide sobre o título na data 𝒕𝒊, tomando-se por 𝒕𝟏  
a data de ocorrência da primeira amortização do papel e 𝒕𝒏 a data  
de ocorrência de amortização imediatamente anterior à data de  
realização do cálculo

Nos casos particulares em que a data de cálculo precede a ocorrência da  
primeira amortização ou o papel não apresente amortizações então VNA = VNE.

O PU Par é calculado conforme equação abaixo:

```
𝑷𝑼 𝑷𝒂𝒓=𝑽𝑵𝑨 × ∏{[(𝟏+𝑻𝒂𝒙𝒂 𝑫𝑰𝒊)𝟐𝟓𝟐𝟏 −𝟏] × %𝑫𝑰𝒆𝒎𝒊+𝟏}
```
```
𝒅𝒖
𝒊=𝟏
```

### ×(𝟏+𝒋𝒆𝒎𝒊)𝟐𝟓𝟐𝒅𝒖

Tal que:

𝑻𝒂𝒙𝒂 𝑫𝑰𝒊 Taxa DI, publicada diariamente pela B3, observada na data i  
considerando-se a quantidade N de dias uteis indicada como  
deslocamento de fixing do título

%𝑫𝑰𝒆𝒎𝒊 corresponde ao percentual do CDI associado ao evento de juros  
vigente na data de calculo indicada, caso o modelo de cálculo seja  
do tipo DI-SPREAD D-N toma-se por 1 o valor desse parâmetro

𝒅𝒖 quantidade de dias úteis entre a data de emissão ou a data do  
último evento de pagamento de juros (o mais recente) até a data  
de cálculo

𝒋𝒆𝒎𝒊 taxa de juros de emissão do papel, expressa em percentual ao ano  
na base 252 dias úteis, caso o modelo de cálculo seja do tipo DI-  
PERC D-N toma-se por 0 o valor desse parâmetro

59

O PU Operação é determinado pelo somatório do valor presente dos eventos  
remanescentes do papel baseados no cálculo da taxa indicada pelo usuário para  
o negócio. É utilizada uma curva estimada para a Taxa DI construída com a  
própria Taxa DI e os contratos futuros DI1 da B3. Destaca-se que são  
considerados os preços de fechamento desses vértices do dia útil imediatamente  
anterior à data de realização do cálculo para construção da curva de desconto  
dos títulos. A maneira como essa curva é interpolada está detalhada no Anexo I

- INTERPOLAÇÃO.

O valor do PU Operação é dado pela equação abaixo e seus argumentos são  
definidos na sequência:

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐= ∑𝑭𝑫𝑽𝑭𝒊𝒊
```
```
𝒏
```

𝒊=𝟏  
Tal que:

𝒊 data de ocorrência do evento calculado  
𝒏 data de ocorrência do último evento incidente sobre o título avaliado

O valor na data de sua ocorrência 𝒊, ou simplesmente valor futuro (𝑽𝑭𝒊), de cada  
evento será dado por:

### 𝑽𝑭𝒊=𝑽𝑵𝑨𝒊×\[{\[(𝟏+𝑫𝑰𝒕)𝟐𝟓𝟐𝟏 −𝟏\] × %𝑫𝑰𝒆𝒎𝒊+𝟏 }

```
𝒅𝒖
×(𝟏+𝒋𝒆𝒎𝒊)𝟐𝟓𝟐𝒅𝒖−𝟏]+𝑨𝒊
```

Tal que:

𝒊 data de ocorrência do evento calculado

𝑽𝑵𝑨𝒊 Valor Nominal Atualizado do papel na data 𝒊

60

𝒅𝒖 quantidade de dias úteis entre a data do evento imediatamente  
anterior à data 𝒊 e o evento a ocorrer na data 𝒊

𝑨𝒊 amortização a ser realizada na data 𝒊

𝑫𝑰𝒕 a Taxa DI vigente ou projetada com base nos vértices dos contratos  
futuros de Taxa DI negociados em ambiente de bolsa, para data 𝒕,  
considerando-se a quantidade N de dias uteis indicada como  
deslocamento de fixing do título

%𝑫𝑰𝒆𝒎𝒊 corresponde ao percentual do CDI associado ao i-ésimo evento de  
juros calculado, caso o método de cálculo seja do tipo DI-SPREAD  
D-N toma-se por 1 o valor desse parâmetro

𝒋𝒆𝒎𝒊 taxa de juros de emissão do papel associada ao i-ésimo evento  
calculado, expressa em percentual ao ano na base 252 dias úteis,  
caso o modelo de cálculo seja do tipo DI-PERC D-N toma-se por 0  
o valor desse parâmetro

O Fator de Desconto do evento a ocorrer na data 𝒊, ou simplesmente 𝑭𝑫𝒊, que  
traz a valor presente o fluxo projetado para a data 𝒊 é dado por:

### 𝑭𝑫𝒊= {\[(𝟏+𝑷𝒓𝒐𝒋 𝑫𝑰𝒛)

```
𝟐𝟓𝟐𝟏
−𝟏] × %𝑫𝑰𝒏𝒆𝒈+𝟏}
```
```
𝒅𝒖
×(𝟏+𝒋𝒏𝒆𝒈)
```
```
𝒅𝒖𝟐𝟓𝟐𝒛
```
```
Tal que:
```

𝒋𝒏𝒆𝒈 taxa de juros expressa em percentual ao ano na base 252 dias  
úteis, para realização do negócio indicada pelo usuário, caso o  
modelo de cálculo seja do tipo DI-PERC D-N toma-se por 0 o valor  
desse parâmetro

61

%𝑫𝑰𝒏𝒆𝒈 corresponde ao percentual da Taxa DI indicado pelo usuário para  
a realização do negócio, caso o modelo de cálculo seja do tipo DI-  
SPREAD D-N toma-se por 1 o valor desse parâmetro

𝒅𝒖𝒛 quantidade de dias úteis entre a data de cálculo do título e o evento  
a ocorrer na data 𝒊

𝑷𝒓𝒐𝒋 𝑫𝑰𝒛 a Taxa DI projetada com base nos vértices dos contratos futuros de  
Taxa DI negociados em ambiente de bolsa, na data 𝒕, tal que  
tomamos por 𝒕=𝟏 o dia útil imediatamente posterior ao de  
ocorrência do evento imediatamente anterior à data 𝒊, ou data de  
cálculo do título (o que for mais recente), e assim sucessivamente

A projeção da Taxa DI entre a data de cálculo e uma data futura qualquer  
expressa nas equações acima pelas variáveis 𝑫𝑰𝒕 e 𝑷𝒓𝒐𝒋 𝑫𝑰𝒛, denotada  
simplesmente 𝑷𝒓𝒐𝒋 𝑫𝑰𝒕 abaixo, é dada por:

### 𝑷𝒓𝒐𝒋 𝑫𝑰𝒕=

### {^

### \[(𝟏+𝑽𝒑)

```
𝒅𝒖𝒑
𝟐𝟓𝟐
(𝟏+𝑽𝒂)𝒅𝒖𝟐𝟓𝟐𝒂
```

### \]

```
𝒅𝒖𝒅𝒖𝒕−𝒅𝒖𝒂
𝒑−𝒅𝒖𝒂
× (𝟏+𝑽𝒂)
```
```
𝒅𝒖𝟐𝟓𝟐𝒂
```
```
}^
```
```
𝟐𝟓𝟐𝒅𝒖
𝒕
− 𝟏
```
```
Tal que:
```

𝒕 data para a qual se deseja calcular a projeção acumulada da Taxa  
DI

𝑽𝒑 valor do vértice de contrato futuro de Taxa DI negociado em bolsa

```
posterior à data 𝒕, expresso em taxa anualizada na base 252 dias
úteis
```

62

𝑽𝒂 valor do vértice de contrato futuro de Taxa DI negociado em bolsa  
anterior à data 𝒕, expresso em taxa anualizada na base 252 dias  
úteis

𝒅𝒖𝒑 quantidade de dias úteis entre as datas de cálculo e de vencimento  
do vértice 𝑽𝒑

𝒅𝒖𝒂 quantidade de dias úteis entre as datas de cálculo e de vencimento  
do vértice 𝑽𝒂

𝒅𝒖𝒕 quantidade de dias úteis entre as datas de cálculo e a data 𝒕 para  
a qual se procura a projeção da Taxa DI

Toma-se por Valor Financeiro da Operação (ou, simplesmente, Financeiro)  
conforme terminologia exibida na ferramenta, o seguinte:

```
𝑭𝒊𝒏𝒂𝒏𝒄𝒆𝒊𝒓𝒐=𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐×𝑸𝒖𝒂𝒏𝒕𝒊𝒅𝒂𝒅𝒆 𝒅𝒆 𝑻í𝒕𝒖𝒍𝒐𝒔 𝑵𝒆𝒈𝒐𝒄𝒊𝒂𝒅𝒐𝒔
```

A Duration do papel é calculada em anos e da seguinte maneira:

### 𝑫𝒖𝒓𝒂𝒕𝒊𝒐𝒏=

### \[∑

### 𝑽𝑭𝒊

### 𝑭𝑫𝒊

```
𝒏
```

𝑷𝑼𝒊= 𝟏𝑶𝒑𝒆𝒓𝒂×çã𝒅𝒖𝒐𝒊\]  
𝟐𝟓𝟐^  
Tal que:

𝑽𝑭𝒊 valor futuro do evento a ocorrer na data 𝒊

𝑭𝑫𝒊 fator de desconto a ser aplicado sobre o fluxo a ocorrer na data 𝒊

𝒅𝒖𝒊 quantidade de dias úteis entre a data de cálculo e a data de ocorrência do  
evento 𝒊

63

Para cálculos retroativos, a CALC não armazena os dados históricos,  
considerando sempre o divulgado e as projeções disponíveis na data de  
apuração.

## 3.4.2 CRA’s e CRI’s Indexados ao IPCA

Título cujo fluxo de pagamentos de juros é corrigido pelo IPCA, índice de preços  
divulgado mensalmente pelo IBGE.

O Valor Nominal Atualizado (VNA) é o Valor Nominal de Emissão (VNE)  
atualizado pela variação mensal do IPCA e/ou das projeções. A atualização do  
VNA deve observar a data de aniversário do CRA/CRI, bem como as datas de  
divulgação do índice e projeção do IPCA, dessa forma segregando a  
determinação de seu VNA em três momentos:

## 3.4.2.1 VNA na data de aniversário do papel............................................................

Nessa data, o Valor Nominal Atualizado é calculado da seguinte maneira:

𝑽𝑵𝑨= (^) 𝑰𝑷𝑪𝑨𝑰𝑷𝑪𝑨𝒕  
𝒕𝟎

### .𝑽𝑵𝑬∙ (𝟏−∑𝑨𝒂𝒏𝒕)

Tal que:

𝑰𝑷𝑪𝑨𝒕 valor do número-índice do mês anterior ao mês de atualização

𝑰𝑷𝑪𝑨𝒕𝟎 valor do número-índice do mês anterior ao primeiro mês de  
rentabilidade do papel

𝑽𝑵𝑬 Valor Nominal de Emissão

∑𝑨𝒂𝒏𝒕 Soma dos percentuais de amortização que ocorreram antes da  
data de cálculo do papel

## 3.4.2.1.1 VNA entre a data de divulgação do IPCA e o próximo aniversário

Será dado pela equação abaixo:

64

### 𝑽𝑵𝑨= 𝑽𝑵𝑨𝒊× (𝑰𝑷𝑪𝑨𝑰𝑷𝑪𝑨𝒕−𝒕𝟏)

```
𝒅𝒖𝒅𝒖𝒊
𝒕∙ (𝟏−∑𝑨
𝒂𝒏𝒕)^
```

Tal que:

𝑽𝑵𝑨𝒊 Valor Nominal Atualizado do papel na última data de aniversário

𝑰𝑷𝑪𝑨𝒕 valor do IPCA divulgado para o mês anterior ao mês corrente

𝑰𝑷𝑪𝑨𝒕−𝟏 valor do IPCA divulgado imediatamente antes do valor de 𝑰𝑷𝑪𝑨𝒕

𝒅𝒖𝒊 quantidade de dias úteis entre a última data de aniversário e a data  
de cálculo do papel

𝒅𝒖𝒕 quantidade de dias úteis entre a última e a próxima data de  
aniversário do papel

∑𝑨𝒂𝒏𝒕 Soma dos percentuais de amortização que ocorreram antes da  
data de cálculo do papel

## 3.4.2.2 VNA entre as datas de aniversário e de divulgação do IPCA

Entre a data de aniversário do papel e a próxima divulgação do IPCA o VNA do  
papel será dado por:

### 𝑽𝑵𝑨= 𝑽𝑵𝑨𝒊× (𝟏+𝑰𝑷𝑪𝑨𝒑𝒓𝒐𝒋)

```
𝒅𝒖𝒅𝒖𝒊
𝒕∙ (𝟏−∑𝑨𝒂𝒏𝒕)
```

Tal que:

𝑽𝑵𝑨𝒊 Valor Nominal Atualizado do papel na última data de aniversário

𝑰𝑷𝑪𝑨𝒑𝒓𝒐𝒋 projeção corrente do IPCA divulgada pela ANBIMA em percentual  
(o usuário poderá indicar um valor para a projeção caso queira  
realizar os cálculos com um valor diferente daquele divulgado pela  
ANBIMA)

65

𝒅𝒖𝒊 quantidade de dias úteis entre a última data de aniversário e a data  
de cálculo do papel

𝒅𝒖𝒕 quantidade de dias úteis entre a última e a próxima data de  
aniversário do papel

∑𝑨𝒂𝒏𝒕 Soma dos percentuais de amortização que ocorreram antes da  
data de cálculo do papel

A CALC utiliza a projeção do IPCA divulgada pela ANBIMA sempre que o cálculo  
for realizado entre as datas de aniversário e de divulgação do IPCA pelo IBGE,  
mesmo que na escritura de emissão conste que o emissor utiliza, na ausência  
do IPCA mais atual, o último IPCA conhecido.

O PU Par é determinado pelo VNA na data de cálculo do papel acrescido da  
remuneração acumulada dos juros desde a data de emissão do papel ou a data  
do último evento de pagamento de juros (o mais recente) até a data de cálculo,  
conforme a equação abaixo:

### 𝑷𝑼 𝑷𝒂𝒓=𝑽𝑵𝑨×(𝟏+𝒋𝒆𝒎𝒊)𝟐𝟓𝟐𝒅𝒖

Tal que:

𝒋𝒆𝒎𝒊 taxa de juros de emissão do papel, expressa em percentual ao ano  
na base 252 dias úteis

𝒅𝒖 quantidade de dias úteis entre a data de emissão ou a data do  
último evento de pagamento de juros (o mais recente) e a data de  
cálculo.

O PU Operação é dado pelo somatório dos eventos remanescentes do papel  
trazidos a valor presente pela taxa indicada pelo usuário (𝒋𝒏𝒆𝒈) no momento do

cálculo, conforme a equação abaixo:

66

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐=
```

### ∑ 𝑱𝒕𝒊

```
𝒏
𝒊=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```

### 𝟐𝟓𝟐𝒅𝒖𝒊+^

### ∑ 𝑨𝒕𝒋

```
𝒏
𝒋=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```
```
𝒅𝒖𝒋
𝟐𝟓𝟐
```

Tal que:

𝑱𝒕𝒊 valor futuro dos juros a serem pagos pelo emissor na data 𝒕𝒊,

```
conforme definido adiante nesse documento, tomando-se por 𝒕𝟏 a
primeira data de pagamento de juros imediatamente posterior à
data de cálculo determinada e 𝒕𝒏 a última data de pagamento de
evento de juros
```

𝑨𝒕𝒋 valor da amortização a ser paga pelo emissor na data 𝒕𝒋, tomando-

```
se por 𝒕𝟏 a primeira data de pagamento de amortização
imediatamente posterior à data de cálculo determinada e 𝒕𝒏 a última
data de ocorrência de amortização
```

𝒋𝒏𝒆𝒈 taxa de juros indicada pelo usuário para a realização do negócio,

```
em percentual ao ano na base 252 dias úteis
```

𝒅𝒖𝒊 quantidade de dias úteis entre a data de cálculo e a data do evento  
de juros considerado

𝒅𝒖𝒋 quantidade de dias úteis entre a data de cálculo e a data do evento  
de amortização considerado  
Tal que:

### 𝑱𝒕𝒊=𝑽𝑵𝑨𝒕𝒊× \[(𝟏+ 𝒋𝒆𝒎𝒊)

```
𝒅𝒖𝟐𝟓𝟐𝒕
−𝟏]
```

Na qual:

𝑽𝑵𝑨𝒕𝒊 Valor Nominal Atualizado do CRA/CRI na data 𝒕𝒊

67

𝒋𝒆𝒎𝒊 taxa de juros de emissão do papel, expressa em percentual ao ano  
na base 252 dias úteis

𝒅𝒖𝒕 quantidade de dias úteis entre a data do evento de juros  
considerado e a data do evento de juros imediatamente anterior a  
este. Caso o evento em questão seja o primeiro pagamento de  
juros, então considera-se a quantidade de dias úteis entre a data  
de início de rentabilidade do papel e a data de ocorrência do evento  
E:

```
𝑨𝒕𝒋=𝑽𝑵𝑨𝒕𝒊×𝑷𝒕𝒊
```

Onde:

𝑷𝒕𝒊 percentual de amortização indicado para o evento de amortização  
que ocorre na data 𝒕𝒊

A amortização poderá incidir sobre o Valor Base de Emissão ou sobre o Valor  
Base Remanescente do Título.

Toma-se por Valor Financeiro da Operação (ou, simplesmente, Financeiro)  
conforme terminologia exibida na ferramenta, o seguinte:

```
𝑭𝒊𝒏𝒂𝒏𝒄𝒆𝒊𝒓𝒐=𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐×𝑸𝒖𝒂𝒏𝒕𝒊𝒅𝒂𝒅𝒆 𝒅𝒆 𝑻í𝒕𝒖𝒍𝒐𝒔 𝑵𝒆𝒈𝒐𝒄𝒊𝒂𝒅𝒐𝒔
```

A Duration do papel é calculada em anos e da seguinte maneira:

### 𝑫𝒖𝒓𝒂𝒕𝒊𝒐𝒏= \[

### ∑ 𝑱𝒕𝒊

```
𝒏
𝒊=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```

### 𝟐𝟓𝟐𝒅𝒖𝒊×𝒅𝒕𝒊+^

### ∑ 𝑨𝒕𝒋

```
𝒏
𝒋=𝟏
(𝟏+𝒋𝒏𝒆𝒈)
```
```
𝒅𝒖𝒋
𝟐𝟓𝟐
```

### ×𝒅𝒕𝒋

```
𝑷𝑼 𝑶𝒑𝒆𝒓𝒂çã𝒐 ]
𝟐𝟓𝟐^
```

68

Tal que:

𝒅𝒕𝒊 quantidade de dias úteis entre a data de cálculo e a data de

```
ocorrência do evento 𝑱𝒕𝒊
```

𝒅𝒕𝒋 quantidade de dias úteis entre a data de cálculo e a data de

```
ocorrência do evento 𝑨𝒕𝒋
```

## Anexo I – Interpolação

A interpolação exponencial das taxas, com base no número de dias úteis, é  
calculada conforme fórmula abaixo:

### 𝑻𝒂𝒙𝒂 𝑰𝒏𝒕𝒆𝒓𝒑𝒐𝒍𝒂𝒅𝒂𝒕=

### {^

### \[(𝟏+𝑽𝒑)

```
𝒅𝒖𝒑
𝟐𝟓𝟐
(𝟏+𝑽𝒂)
```

### 𝒅𝒖𝟐𝟓𝟐𝒂\]

```
𝒅𝒖𝒅𝒖𝒕−𝒅𝒖𝒂
𝒑−𝒅𝒖𝒂
× (𝟏+𝑽𝒂)
```
```
𝒅𝒖𝟐𝟓𝟐𝒂
```
```
}^
```
```
𝟐𝟓𝟐𝒅𝒖
𝒕
− 𝟏
```
```
Tal que:
```

𝒕 data para a qual se deseja calcular a projeção acumulada da Taxa  
DI

𝑽𝒑 valor do vértice de contrato futuro de Taxa DI negociado em bolsa

```
posterior à data 𝒕, expresso em taxa anualizada na base 252 dias
úteis
```

𝑽𝒂 valor do vértice de contrato futuro de Taxa DI negociado em bolsa  
anterior à data 𝒕, expresso em taxa anualizada na base 252 dias  
úteis

```
69
```
```
𝒅𝒖𝒑 quantidade de dias úteis entre as datas de cálculo e de vencimento
do vértice 𝑽𝒑
```
```
𝒅𝒖𝒂 quantidade de dias úteis entre as datas de cálculo e de vencimento
do vértice 𝑽𝒂
```
```
𝒅𝒖𝒕 quantidade de dias úteis entre as datas de cálculo e a data 𝒕 para
a qual se procura a projeção da Taxa DI
```

## Anexo II – Regras de arredondamento e truncamento

```
Critérios de Cálculo para Títulos Públicos Federais
```

T: truncar | A: arredondar

```
70
```
```
Critérios de Cálculo para Debêntures
```
```
T: truncar | A: arredondar
```

**Parametro DI - Spread DI - Percentual IGP - M IPCA Prefixado  
VNE (Valor Nominal de Emissão)** I | 06 I | 06 I | 06 I | 06 I | 06  
**Taxa de Emissão ( % a.a.)** I | 04 I | 02 I | 04 I | 04 I | 04  
**VNA (Valor Nominal Atualizado)** T | 06 T | 06 T | 06 T | 06 T | 06  
**PU Par** T | 06 T | 06 T | 06 T | 06 T | 06  
**Taxa DI Over Cetip** I | 02 I | 02  
**Fator Diário da Taxa DI Over Cetip** A | 08 A | 08  
**Fator Diário da Percentual DI** T | 16  
**Fator Diário Acumulado da Taxa DI Over Cetip ou Percentual do DI** T | 16 T | 16  
**Fator DI Acumulado no Período** A | 08 A | 08  
**Fator de Spread** A | 09  
**Fator de Juros** A | 09 A | 09 A | 09 A | 09  
**Expectativas de Juros Futuros** T | 02 T | 02  
**Projeção de Índices de Preços** A | 02 A | 02  
**Fator Pro Rata (Projeções)** T | 08 T | 08  
**Variação Oficial do Índice** T | 16 T | 16  
**Fator Pro Rata (Variação Oficial)** T | 08 T | 08  
**Fator Acumulado das Variações de Índices** T | 08 T | 08  
**Amortização (R$)** T | 06 T | 06 T | 06 T | 06  
**Fluxos de Pagamentos de Juros / Juros Descontados** T | 06 T | 06 T | 06 T | 06  
**Fator de Capitalização / Fator de Desconto** A | 09  
**PU (Preço Unitário)** T | 06 T | 06 T | 06 T | 06 T | 06  
**Financeiro (R$)** T | 02 T | 02 T | 02 T | 02 T | 02

```
Indexador da Debenture
```

71