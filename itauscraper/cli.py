"""Command line interface."""
import argparse

from getpass import getpass

from itauscraper.scraper import Chrome, ItauHome


def main():
    parser = argparse.ArgumentParser(prog='itau',
                                     description='Scraper para baixar seus extratos do Itaú com um comando.')

    parser.add_argument('--extrato', action='store_true', help='Lista extrato da conta corrente.')
    parser.add_argument('--cartao', action='store_true', help='Lista extrato do cartão de crédito.')
    parser.add_argument('--agencia', '-a', help='Agência na forma 0000', required=True)
    parser.add_argument('--conta', '-c', help='Conta sem dígito na forma 00000', required=True)
    parser.add_argument('--digito', '-d', help='Dígito da conta na forma 0', required=True)
    parser.add_argument('--senha', '-s', help='Senha eletrônica da conta no Itaú.')
    parser.add_argument('--titular', '-t', help='Nome do titular (apenas para contas conjuntas)')

    args = parser.parse_args()

    #if not (args.extrato or args.cartao):
    #    parser.exit(0, "Indique a operação: --extrato e/ou --cartao\n")

    senha = args.senha or getpass("Digite sua senha do Internet Banking: ")

    try:
        itau = ItauHome(Chrome())
        itau.login(args.agencia, args.conta+args.digito, args.titular, senha)
        itau.go_to_ofx()
        print(itau.salvar_ofx(1, 1, 2018))
    finally:
        itau.cleanup()
