from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
from decimal import Decimal

app = Flask(__name__)
app.secret_key = 'supersecretkey'

JSON_FILE_PATH = 'data.json'

def carregar_dados():
    try:
        with open(JSON_FILE_PATH, 'r') as file:
            dados = json.load(file)
            print("Dados carregados:", dados)
            return dados
    except FileNotFoundError:
        print("Arquivo JSON não encontrado.")
        return {'quesitos': [], 'jurados': []}
    except json.JSONDecodeError as e:
        flash(f"Erro ao carregar dados do arquivo JSON: {str(e)}")
        return {'quesitos': [], 'jurados': []}

def salvar_dados(dados):
    try:
        with open(JSON_FILE_PATH, 'w') as file:
            json.dump(dados, file, indent=4)
    except IOError as e:
        flash(f"Erro ao salvar dados no arquivo JSON: {str(e)}")

def obter_dados_quesitos():
    dados = carregar_dados()
    grupos = {}
    soma_geral = {}

    for item in dados.get('quesitos', []):
        nome = item['nome']
        if nome not in grupos:
            grupos[nome] = []
        total = (Decimal(item['nota1']) + Decimal(item['nota2']) +
                 Decimal(item['nota3']) + Decimal(item['nota4']) +
                 Decimal(item['nota5']))
        grupos[nome].append((item['id'], item['nome'], item['nota1'], item['nota2'], item['nota3'], item['nota4'], item['nota5'], item['escola'], total))

        escola = item['escola']
        if escola not in soma_geral:
            soma_geral[escola] = {'nota1': Decimal(0), 'nota2': Decimal(0), 'nota3': Decimal(0), 'nota4': Decimal(0), 'nota5': Decimal(0), 'total': Decimal(0)}
        soma_geral[escola]['nota1'] += Decimal(item['nota1'])
        soma_geral[escola]['nota2'] += Decimal(item['nota2'])
        soma_geral[escola]['nota3'] += Decimal(item['nota3'])
        soma_geral[escola]['nota4'] += Decimal(item['nota4'])
        soma_geral[escola]['nota5'] += Decimal(item['nota5'])
        soma_geral[escola]['total'] += total

    return grupos, soma_geral

def obter_dados_jurados():
    dados = carregar_dados()
    return dados.get('jurados', [])

@app.route('/', methods=['GET', 'POST'])
def index():
    grupos, soma_geral = obter_dados_quesitos()
    form_dado = {}
    jurados = obter_dados_jurados()

    if request.method == 'POST':
        nome = request.form.get('nome')
        nota1 = Decimal(request.form.get('nota1'))
        nota2 = Decimal(request.form.get('nota2'))
        nota3 = Decimal(request.form.get('nota3'))
        nota4 = Decimal(request.form.get('nota4'))
        nota5 = Decimal(request.form.get('nota5'))
        escola = request.form.get('escola')
        id = request.form.get('id')

        dados = carregar_dados()
        if id:
            for item in dados.get('quesitos', []):
                if item['id'] == int(id):
                    item.update({
                        'nome': nome,
                        'nota1': str(nota1),
                        'nota2': str(nota2),
                        'nota3': str(nota3),
                        'nota4': str(nota4),
                        'nota5': str(nota5),
                        'escola': escola
                    })
                    flash('Registro atualizado com sucesso!')
                    break
        else:
            novo_id = max([item['id'] for item in dados.get('quesitos', [])], default=0) + 1
            dados.setdefault('quesitos', []).append({
                'id': novo_id,
                'nome': nome,
                'nota1': str(nota1),
                'nota2': str(nota2),
                'nota3': str(nota3),
                'nota4': str(nota4),
                'nota5': str(nota5),
                'escola': escola
            })
            flash('Registro inserido com sucesso!')

        salvar_dados(dados)
        return redirect(url_for('index'))

    return render_template('index.html', grupos=grupos, soma_geral=soma_geral, form_dado=form_dado, jurados=jurados)

@app.route('/edit/<int:id>', methods=['GET'])
def edit(id):
    grupos, soma_geral = obter_dados_quesitos()
    dados = carregar_dados()
    form_dado = {}

    for item in dados.get('quesitos', []):
        if item['id'] == id:
            form_dado = {
                'id': item['id'],
                'nome': item['nome'],
                'nota1': item['nota1'],
                'nota2': item['nota2'],
                'nota3': item['nota3'],
                'nota4': item['nota4'],
                'nota5': item['nota5'],
                'escola': item['escola']
            }
            break

    if not form_dado:
        flash('Registro não encontrado!')
        return redirect(url_for('index'))

    return render_template('index.html', grupos=grupos, soma_geral=soma_geral, form_dado=form_dado)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    dados = carregar_dados()
    dados['quesitos'] = [item for item in dados.get('quesitos', []) if item['id'] != id]
    salvar_dados(dados)
    flash('Registro excluído com sucesso!')
    return redirect(url_for('index'))

@app.route('/api/dados', methods=['GET'])
def api_dados():
    dados = carregar_dados()
    response = jsonify(dados)
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

@app.route('/jurados', methods=['GET', 'POST'])
def jurados():
    dados = carregar_dados()
    form_dado = {}

    if request.method == 'POST':
        nome = request.form.get('nome')
        id = request.form.get('id')

        if id:
            for jurado in dados.get('jurados', []):
                if jurado['id'] == int(id):
                    jurado.update({'nome': nome})
                    flash('Jurador atualizado com sucesso!')
                    break
        else:
            novo_id = max([jurado['id'] for jurado in dados.get('jurados', [])], default=0) + 1
            dados.setdefault('jurados', []).append({
                'id': novo_id,
                'nome': nome
            })
            flash('Jurador inserido com sucesso!')

        salvar_dados(dados)
        return redirect(url_for('jurados'))

    return render_template('jurados.html', jurados=dados.get('jurados', []), form_dado=form_dado)

@app.route('/edit_jurado/<int:id>', methods=['GET'])
def edit_jurado(id):
    dados = carregar_dados()
    form_dado = {}

    for jurado in dados.get('jurados', []):
        if jurado['id'] == id:
            form_dado = {
                'id': jurado['id'],
                'nome': jurado['nome']
            }
            break

    if not form_dado:
        flash('Jurador não encontrado!')
        return redirect(url_for('jurados'))

    return render_template('jurados.html', jurados=dados.get('jurados', []), form_dado=form_dado)

@app.route('/delete_jurado/<int:id>', methods=['POST'])
def delete_jurado(id):
    dados = carregar_dados()
    dados['jurados'] = [jurado for jurado in dados.get('jurados', []) if jurado['id'] != id]
    salvar_dados(dados)
    flash('Jurador excluído com sucesso!')
    return redirect(url_for('jurados'))

@app.route('/api/jurados', methods=['GET'])
def api_jurados():
    dados = carregar_dados()
    response = jsonify({'jurados': dados.get('jurados', [])})
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
