from pathlib import Path
from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Chrome(webdriver.Chrome):
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-web-security')
        options.add_experimental_option(
            "prefs", {
                'download.default_directory': str(Path().absolute()),
            }
        )

        super().__init__(chrome_options=options)

    def wait_until(self, method, timeout=10, interval=1):
        return WebDriverWait(self, timeout, interval).until(method)

    def element(self, locator):
        return self.find_element(*locator)

    @contextmanager
    def frame(self, name):
        self.switch_to.frame(name)
        yield
        self.switch_to.default_content()

    @contextmanager
    def tab(self):
        current = self.current_window_handle
        # open new tab
        self.execute_script('window.open("about:blank", "_blank");')
        # switch to new tab
        self.switch_to_window(self.window_handles[-1])

        yield

        # close tab
        self.close()
        # switch back to previous tab
        self.switch_to_window(current)

    def wait_downloads(self):
        self.get("chrome://downloads/")

        cmd = """
            var items = downloads.Manager.get().items_;
            if (items.every(e => e.state === "COMPLETE"))
                return items.map(e => e.file_path);     
        """

        # waits for all the files to be completed and returns the paths
        return self.wait_until(lambda d: d.execute_script(cmd), timeout=120)


def ID(value):
    return By.ID, value


def css(value):
    return By.CSS_SELECTOR, value


def xpath(value):
    return By.XPATH, value


def link_contains(value):
    return By.PARTIAL_LINK_TEXT, value


present = EC.presence_of_element_located
invisible = EC.invisibility_of_element_located


def js_href(el):
    return el.get_attribute('href').partition(':')[-1]


class ItauHome:
    URL = 'https://www.itau.com.br/'

    def __init__(self, driver):
        self.driver = driver

    def login(self, agencia, conta, titular, password):
        # 1. Acessa o site.
        self.driver.get(self.URL)

        # 2. Preenche agência e conta.
        el = self.driver.element
        el(ID('campo_agencia')).send_keys(agencia)
        el(ID('campo_conta')).send_keys(conta)
        el(css('a.btnSubmit')).click()

        if titular:
            # 3. Identifica o titular
            titular = self.driver.wait_until(present(link_contains(titular)))
            self.driver.execute_script(js_href(titular))
        else:
            # 3. O titular é selecionado automaticamente e
            # a página é redirecionada para o teclado virtual
            self.driver.wait_until(present(
                xpath('//strong[text()="{}"]'.format(titular))
            ))

        # 4. Clica a senha no teclado virtual.
        submit = self.driver.wait_until(present(link_contains('acessar')))
        self.driver.wait_until(invisible(css('div.blockUI.blockOverlay')))

        for digit in password:
            self.driver.element(link_contains(digit)).click()

        submit.click()

        # 5. Aguarda carregar o dashboard.
        self.driver.wait_until(present(xpath("//a[contains(text(),'Saldo e extrato')]")))

    def go_to_extrato(self):
        menu = self.driver.wait_until(present(xpath("//a[contains(text(),'Saldo e extrato')]")))
        self.driver.execute_script(js_href(menu))

    def go_to_ofx(self):
        self.go_to_extrato()

        with self.driver.frame('CORPO'):
            menu = self.driver.wait_until(present(xpath("//a[contains(text(),'Salvar em outros formatos')]")))
            self.driver.execute_script(js_href(menu))

    def salvar_ofx(self, dia, mes, ano):
        with self.driver.frame('CORPO'):
            el = self.driver.element
            el(ID('Dia')).send_keys(f'{dia:02}{mes:02}{ano}')
            el(css("input[value='OFX']")).click()
            el(xpath("//a[img[@alt='Continuar']]")).click()

        with self.driver.tab():
            paths = self.driver.wait_downloads()

        return paths

    def cleanup(self):
        self.driver.quit()
