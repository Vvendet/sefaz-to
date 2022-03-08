from flask import Flask
from flask import request
import PyPDF2
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import time

app = Flask(__name__) 
def obterNomeDoDownload(waitTime, driver):
    driver.execute_script("window.open()")
    # switch to new tab
    driver.switch_to.window(driver.window_handles[-1])
    # navigate to chrome downloads
    driver.get('chrome://downloads')
    # define the endTime
    endTime = time.time()+waitTime
    driver.implicitly_wait(waitTime)
    return driver.execute_script("return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('div#content  #file-link').text")
def acharDadosBoleto(index, texto):
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

def extrairDadosPdf(nome_pdf):
    pdfFileObj = open(f'C:\\Boletos_Dare\\{nome_pdf}', 'rb')  
    # Cria um objeto de leitura do PDF
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj) 
    # Cria uma página do objeto
    pageObj = pdfReader.getPage(0) 
    # Extrai o texto da página 
    texto = pageObj.extractText()
    index = texto.find("DescontoParcela")
    valor_boleto_com_desconto, boleto_com_desconto, data_vencimento_com_desconto = acharDadosBoleto(index, texto)
    index2 = texto.find("DescontoParcela", index+1)
    valor_boleto_sem_desconto, boleto_sem_desconto, data_vencimento_sem_desconto = acharDadosBoleto(index2, texto)
    pdfFileObj.close() 
    
    return boleto_com_desconto, valor_boleto_com_desconto, data_vencimento_com_desconto, boleto_sem_desconto, valor_boleto_sem_desconto, data_vencimento_sem_desconto

@app.get('/ObterDebitos', defaults={'renavam' : '0','placa':'0','cpf':'0'})
def get_retorna_debitos(renavam, placa, cpf):
    renav = request.args.get('renavam')
    plac = request.args.get('placa')
    cp = request.args.get('cpf')
    download_dir = "C:\\Boletos_Dare" # Para o linux/*nix, download_dir="/usr/Public"
    options = webdriver.ChromeOptions()
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "eager" 
    profile = {"plugins.plugins_list": [{"enabled": False, "name": "Chrome PDF Viewer"}], # Disable Chrome's PDF Viewer
                "download.default_directory": download_dir, "download.extensions_to_open": "applications/pdf",
                "directory_upgrade": True, "download.prompt_for_download": False, #To auto download the file
                "plugins.always_open_pdf_externally": True }
    options.add_experimental_option("prefs", profile)
    options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 12_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 105.0.0.11.118 (iPhone11,8; iOS 12_3_1; en_US; en-US; scale=2.00; 828x1792; 165586599)")
    
    
    driver = webdriver.Chrome(executable_path='C:\chromedriver_win32\chromedriver.exe', chrome_options=options)
    driver.get("http://www.sefaz2.to.gov.br/ipva/dare.php")
    driver.maximize_window()
    driver.find_element(by=By.XPATH, value="//input[@name='renavam']").send_keys(renav)
    driver.find_element(by=By.XPATH, value="//input[@name='placa']").send_keys(plac)
    driver.implicitly_wait(8) #Espera até 8 segundos para um elemento da páginas carregar. Se ele carregar antes, ele prossegue para o próximo
    
    driver.find_element(by=By.XPATH, value="/html/body/div/div[3]/div[2]/div/div/form/div[3]/div/input").click()
    driver.find_element(by=By.XPATH, value="//input[@name='_IPVINRDO']").send_keys(cp)
    driver.find_element(by=By.XPATH, value="/html/body/form/table/tbody/tr[1]/td/table[2]/tbody/tr/td[1]/p[3]/font/a/img").click()
    
    #Criação para redução da repetição de texto
    table_4 = '/html/body/form/table/tbody/tr[1]/td/table[4]/tbody/tr/td[2]/dl/dt[1]/div/'
    table_7 = '/html/body/form/table/tbody/tr[1]/td/table[7]/tbody/tr/td[2]/strong/font/'
    not_info = "Sem informações"

    Nome = driver.find_element(by=By.XPATH, value=f"{table_4}span").text
    Endereco = driver.find_element(by=By.XPATH, value=f"{table_4}font/span[1]").text
    Bairro = driver.find_element(by=By.XPATH, value=f"{table_4}font/span[2]").text  
    Municipio = driver.find_element(by=By.XPATH, value=f"{table_4}font/span[3]").text
    MarcaModelo = driver.find_element(by=By.XPATH, value=f"{table_4}font/span[4]").text
    Fabricacao = driver.find_element(by=By.XPATH, value=f"{table_4}font/span[5]").text
    ValorDare = driver.find_element(by=By.XPATH, value=f"{table_7}p[2]/table/tbody/tr[2]/td/span").text
    try:
        Observacao = driver.find_element(by=By.XPATH, value=f"{table_7}p[1]/span").text
    except NoSuchElementException:
        Observacao = not_info
    
    driver.find_element(by=By.XPATH, value="/html/body/form/table/tbody/tr[1]/td/table[6]/tbody/tr/td/p/a").click()
    ultimo_pdf = obterNomeDoDownload(100, driver) #Espera 3 minutos para baixar o boleto

    b_c_d, v_c_d, d_c_d, b_s_d, v_s_d, d_s_d = extrairDadosPdf(ultimo_pdf)

    """
    b_c_d = Código do Boleto com Desconto
    v_c_d = Valor do Boleto com Desconto
    d_c_d = Data de Vencimento do Boleto com Desconto
    b_s_d = Código do Boleto sem Desconto
    v_s_d = Valor do Boleto sem Desconto
    d_s_d = Data de Vencimento do Boleto sem Desconto   
    """

    return {"CPF": cp, "Renavam": renav, "Placa": plac, "Nome": Nome, "Endereco": Endereco, "Bairro": Bairro, 
    "Municipio": Municipio, "MarcaModelo": MarcaModelo, "Fabricacao": Fabricacao, 
    "Observacao": Observacao, "primeira_parcela": v_c_d, "segunda_parcela": v_s_d,
    "vencimento_primeira_parcela": d_c_d, "vencimento_segunda_parcela": d_s_d, 
    "codigo_primeira_parcela": b_c_d, "codigo_segunda_parcela": b_s_d}