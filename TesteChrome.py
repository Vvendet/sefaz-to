from selenium import webdriver

driver = webdriver.Chrome(executable_path='C:\chromedriver_win32\chromedriver.exe')
driver.get("http://www.sefaz2.to.gov.br/ipva/dare.php")
driver.maximize_window()
