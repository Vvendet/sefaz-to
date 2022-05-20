"""
O código a seguir segue a seguinte lógica:

1° Definimos FLask em app, para acessarmos os métodos do framework pela variável
2° Definimos uma função para quando a rota /ObterDebitos for requisitada
3° A requisição só procede se conter nos parâmetros da url os dados do usuário
4° A função para esta rota pega os dados informados e configura o driver que será orquestrado pelo bot
5° A função envia o bot para a página, onde ele irá fazer:
    a) Esperar os dados, quando necessário, carregarem;
    b) Preencher os campos necessários;
    c) coletar as informações pessoais do usuário;
    d) baixar o PDF com as informações de débito;
6° A função desta rota então chama outra função, obterNomeDoDownload(), para que o código possa prosseguir com o enderçamento correto do arquivo PDF. E a encontra o no>
7° Tendo o nome do arquivo  e o diretório, a função da rota chama outra função, que irá:
    a) abrir o arquivo PDF;
    b) extrair o texto do arquivo (para leitura);
    c) Procura por uma palavra-chave no texto, para encontrar melhor os dados desejados
    d) guarda o index dessa palavra-chave
    e) chama a função acharDadosBoleto()*, informando o texto e o indice, para que essa função encontre os dados almejados do texto
    f) repete o que foi feito no item c) e depois o que foi feito no item e), para encontrar uma segunda informação
8° retorna os dados.

*A função acharDadosBoleto() varre o texto do PDF, procurando por elementos chaves que facilitam encontrar as informações certas dentro do texto inteiro.
"""

"""
Importando as bibliotecas utilizadas no código...
"""
from flask import Flask
from flask import request
import PyPDF2
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import time
import os

app = Flask(__name__) #Usando a variável para acessar os métodos da classe


def obterNomeDoDownload(pasta):
    while len(os.listdir(pasta)) == 0:
        time.sleep(1)
    print(os.listdir(pasta))
    for i in os.listdir(pasta):
        print(i)
        return i
         #Buscar pelos arquivos dentro do diretório
def acharDadosBoleto(index, texto): #Procurar pelo texto almejado dentro do PDF
    tamanho_texto = len(texto)
    boleto = ""
    data_vencimento = ""
    numeros = ""
    achei_num = False
    index_valor = 0
    valor_boleto = ""
    for k in range(index, tamanho_texto):
        if texto[k].isdigit() or (achei_num == True and ( texto[k] == " " or texto[k] == "-" ) ):
            numeros += texto[k]
            achei_num = True
        elif texto[k] == "/":
            boleto = numeros[0: -2]
            numeros = numeros[-2:]
            data_vencimento += numeros + texto[k:k+8]
            index_valor = k+8
            break
    for l in range(index_valor, tamanho_texto):
        if texto[l] == ',':
            valor_boleto += texto[l:l+3]
            break
        else:
            valor_boleto += texto[l]
    return valor_boleto, boleto, data_vencimento

def extrairDadosPdf(nome_pdf,pasta): #Extrair o texto do PDF
    pdfFileObj = open(f'{pasta}/{nome_pdf}', 'rb')
    # Cria um objeto de leitura do PDF
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    # Cria uma página do objeto
    pageObj = pdfReader.getPage(0)
    # Extrai o texto da página
    texto = pageObj.extractText()

    index = texto.find( "DescontoParcela")
    valor_boleto_com_desconto, boleto_com_desconto, data_vencimento_com_desconto = acharDadosBoleto(index, texto)
    index2 = texto.find("DescontoParcela", index+1)
    valor_boleto_sem_desconto, boleto_sem_desconto, data_vencimento_sem_desconto = acharDadosBoleto(index2, texto)
    pdfFileObj.close()
    os.system(f'rm {pasta}/{nome_pdf}')
    return boleto_com_desconto, valor_boleto_com_desconto, data_vencimento_com_desconto, boleto_sem_desconto, valor_boleto_sem_desconto, data_vencimento_sem_desconto


@app.route('/ObterDebitos', defaults={'renavam' : '0','placa':'0','cpf':'0'})
def get_retorna_debitos(renavam, placa, cpf): ## Função principal do código
    renav = request.args.get('renavam')
    plac = request.args.get('placa')
    cp = request.args.get('cpf')
    download_dir = f'./boletos_' #YOUR PATH HERE !!!!
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "eager"
    profile = {"plugins.plugins_list": [{"enabled": False, "name": "Chrome PDF Viewer"}], # Disable Chrome's PDF Viewer
                "download.default_directory": download_dir, "download.extensions_to_open": "applications/pdf",
                "directory_upgrade": True, "download.prompt_for_download": False, #To auto download the file
                "plugins.always_open_pdf_externally": True }
    options.add_experimental_option("prefs", profile)
    options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 12_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 105.0.0.>
                                                   # YOU PATH BELOW !!!!!
    driver = webdriver.Chrome(options=options,executable_path='./chromedriver', chrome_options=options)
    driver.get("http://www.sefaz2.to.gov.br/ipva/dare.php")
    try:
        driver.find_element(by=By.XPATH, value="//input[@name='renavam']").send_keys(renav)
        driver.find_element(by=By.XPATH, value="//input[@name='placa']").send_keys(plac)
        driver.implicitly_wait(8) #Espera até 8 segundos para um elemento da páginas carregar. Se ele carregar antes, ele prossegue para o próximo
        driver.find_element(by=By.XPATH, value="/html/body/div/div[3]/div[2]/div/div/form/div[3]/div/input").click()
        driver.find_element(by=By.XPATH, value="//input[@name='_IPVINRDO']").send_keys(cp)
        driver.find_element(by=By.XPATH, value="/html/body/form/table/tbody/tr[1]/td/table[2]/tbody/tr/td[1]/p[3]/font/a/img").click()
    except:
        return 'informe dados válidos, por favor'

    #Criação para redução da repetição de texto
    table_4 = '/html/body/form/table/tbody/tr[1]/td/table[4]/tbody/tr/td[2]/dl/dt[1]/div/'
    table_7 = '/html/body/form/table/tbody/tr[1]/td/table[7]/tbody/tr/td[2]/strong/font/'
    Nome = driver.find_element(by=By.XPATH, value=f"{table_4}span").text
    Endereco = driver.find_element(by=By.XPATH, value=f"{table_4}font/span[1]").text
    Bairro = driver.find_element(by=By.XPATH, value=f"{table_4}font/span[2]").text
    Municipio = driver.find_element(by=By.XPATH, value=f"{table_4}font/span[3]").text
    MarcaModelo = driver.find_element(by=By.XPATH, value=f"{table_4}font/span[4]").text
    Fabricacao = driver.find_element(by=By.XPATH, value=f"{table_4}font/span[5]").text
    try:
        driver.find_element(by=By.XPATH, value="/html/body/form/table/tbody/tr[1]/td/table[6]/tbody/tr/td/p/a").click()
        ultimo_pdf = obterNomeDoDownload(download_dir) #Espera 3 minutos para baixar o boleto
        b_c_d, v_c_d, d_c_d, b_s_d, v_s_d, d_s_d = extrairDadosPdf(ultimo_pdf,download_dir)
    except:
        return "verifique que você possui debitos a ser pagos"
    parcelas = [{"valor":v_c_d,"vencimento":d_c_d,"boleto":b_c_d},{"valor":v_s_d,"vencimento":d_s_d,"boleto":b_s_d}]

    """
    b_c_d = Código do Boleto com Desconto
    v_c_d = Valor do Boleto com Desconto
    d_c_d = Data de Vencimento do Boleto com Desconto
    b_s_d = Código do Boleto sem Desconto
    v_s_d = Valor do Boleto sem Desconto
    d_s_d = Data de Vencimento do Boleto sem Desconto
    """

    return  {"Nome": Nome,"Placa":plac,"Renavam":renav,"CPF":cp,
        "Descricao":"ValorDARE Parcelas Unicas","parcela_com_desconto":parcelas[0],"parcela_sem_desconto":parcelas[1]}

#Inicializar o servidor
app.run(host='0.0.0.0',port=9002)
