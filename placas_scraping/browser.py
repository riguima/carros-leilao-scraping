import re
import itertools

import pandas as pd
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from httpx import AsyncClient
from parsel import Selector


async def get_plates_of_year(year):
    async with AsyncClient() as client:
        result = {
            'Data': [],
            'Local': [],
            'Leiloeiro': [],
        }
        failed_count = 0
        headers = [
            'Lote',
            'Placa',
            'Marca/Modelo',
            'Ano',
            'Nº Motor',
            'Chassi',
            'Cor',
            'Combustivel',
            'Valor Mínimo',
            'Situação Motor',
        ]
        for header in headers:
            result[header] = []
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        driver = Chrome(service=Service(ChromeDriverManager().install()), options=options)
        for c in itertools.count(1):
            while True:
                try:
                    response = await client.get(
                        f'https://www.portaldetransito.rs.gov.br/dtw/servicos/crd/mostraEdital.jsp?nroEdital={c:>02}&anoEdital={year}'
                    )
                    break
                except:
                    continue
            selector = Selector(response.text)
            info = {
                'Data': '',
                'Local': '',
                'Leiloeiro': '',
            }
            driver.get(f'https://www.portaldetransito.rs.gov.br/dtw/servicos/crd/mostraEdital.jsp?nroEdital={c:>02}&anoEdital={year}')
            for p in driver.find_elements(By.CSS_SELECTOR, 'p'):
                if 'data:' in p.text.lower():
                    info['Data'] = p.text.lower().split('data: ')[-1]
                elif 'local:' in p.text.lower():
                    info['Local'] = p.text.lower().split('local: ')[-1].title()
                elif 'nome do leiloeiro(a):' in p.text.lower():
                    info['Leiloeiro'] = p.text.lower().split('nome do leiloeiro(a): ')[-1].title()
                    break
            table_in_content = False
            for table in selector.css('table'):
                header_selector = 'body'
                headers_selectors = [
                    'td p b span::text',
                    'td p span::text',
                    'th b::text',
                    'th::text',
                ]
                for selector in headers_selectors:
                    if table.css(selector):
                        header_selector = selector
                        break
                if len(table.css('tr')[0].css(header_selector)) in range(8, 10):
                    table_in_content = True
                    value_selector = 'body'
                    values_selectors = [
                        'td p span::text',
                        'td p::text',
                        'td::text',
                    ]
                    for selector in values_selectors:
                        if table.css('tr')[1].css(selector):
                            value_selector = selector
                            break
                    for row in table.css('tr')[1:]:
                        result['Data'].append(info['Data'])
                        result['Local'].append(info['Local'])
                        result['Leiloeiro'].append(info['Leiloeiro'])
                        values = row.css(value_selector).getall()
                        if len(values) > len(table.css('tr')[0].css(header_selector)):
                            car_name = ' '.join(
                                values[1 : 2 + len(values) - 8]
                            )
                            values = [
                                values[0],
                                car_name,
                                *values[2 + len(values) - 8 :],
                            ]
                        if len(values) == 8:
                            values = [values[0], values[3], values[1], values[2], '', *values[4:], '']
                        elif len(values) < len(table.css('tr')[0].css(header_selector)):
                            first_row_values = table.css('tr')[1].css(value_selector).getall()
                            values = [first_row_values[0], *values[:4], '', values[-1], '', first_row_values[-1], values[-2]]
                        elif len(values) == 9:
                            values.append('')
                        for e, value in enumerate(values):
                            try:
                                result[headers[e]].append(value)
                            except KeyError:
                                result['Nº Motor'].append(value)
                    length = len(result['Lote'])
                    for value in result.values():
                        if len(value) != length:
                            breakpoint()
                            print('Alterar', c, year)
                            for e, value in enumerate(values):
                                try:
                                    result[headers[e]].remove(value)
                                except KeyError:
                                    result['Nº Motor'].remove(value)
                            break
            if not table_in_content:
                print('Falhou', c, year)
                failed_count += 1
                if failed_count >= 15:
                    break
            else:
                failed_count = 0
        plates = pd.DataFrame.from_dict(result)
        plates.to_excel(f'{year}.xlsx', index=False)
        return plates
