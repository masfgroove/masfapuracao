from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine, Table, Column, Integer, String, Numeric, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Configurações de conexão com o banco de dados
DATABASE_URI = 'postgresql+psycopg2://postgres:YMDCapmVxXCQYnKrtyhSOpRddhwJSWml@monorail.proxy.rlwy.net:28308/railway'
engine = create_engine(DATABASE_URI, pool_size=10, max_overflow=20)
Session = sessionmaker(bind=engine)

metadata = MetaData()
quesitos = Table('quesitos', metadata,
    Column('id', Integer, primary_key=True),
    Column('nome', String),
    Column('nota1', Numeric),
    Column('nota2', Numeric),
    Column('nota3', Numeric),
    Column('nota4', Numeric),
    Column('escola', String),
)

def obter_dados():
    session = Session()
    try:
        query = session.query(quesitos).order_by(quesitos.c.escola, quesitos.c.nome)
        rows = query.all()
        grupos = {}
        soma_geral = calcular_soma_geral_por_escola(rows)
        
        for row in rows:
            nome = row.nome
            if nome not in grupos:
                grupos[nome] = []
            total = sum([row.nota1, row.nota2, row.nota3, row.nota4])
            grupos[nome].append((row.id, row.nome, row.nota1, row.nota2, row.nota3, row.nota4, row.escola, total))
        
        return grupos, soma_geral
    except SQLAlchemyError as e:
        flash(f"Erro ao Executar Query: {str(e)}")
        return {}, {}
    finally:
        session.close()

def calcular_soma_geral_por_escola(rows):
    soma_geral = {}
    for row in rows:
        escola = row.escola
        if escola not in soma_geral:
            soma_geral[escola] = {'nota1': Decimal(0), 'nota2': Decimal(0), 'nota3': Decimal(0), 'nota4': Decimal(0), 'total': Decimal(0)}
        total = sum([row.nota1, row.nota2, row.nota3, row.nota4])
        soma_geral[escola]['nota1'] += row.nota1
        soma_geral[escola]['nota2'] += row.nota2
        soma_geral[escola]['nota3'] += row.nota3
        soma_geral[escola]['nota4'] += row.nota4
        soma_geral[escola]['total'] += total
    return soma_geral

@app.route('/', methods=['GET', 'POST'])
def index():
    grupos, soma_geral = obter_dados()
    form_dado = {}
    if request.method == 'POST':
        nome = request.form.get('nome')
        nota1 = Decimal(request.form.get('nota1'))
        nota2 = Decimal(request.form.get('nota2'))
        nota3 = Decimal(request.form.get('nota3'))
        nota4 = Decimal(request.form.get('nota4'))
        escola = request.form.get('escola')
        id = request.form.get('id')

        session = Session()
        try:
            if id:
                # Atualizar registro existente
                session.execute(quesitos.update().where(quesitos.c.id == id).values(
                    nome=nome, nota1=nota1, nota2=nota2, nota3=nota3, nota4=nota4, escola=escola))
                flash('Registro atualizado com sucesso!')
            else:
                # Inserir novo registro
                session.execute(quesitos.insert().values(
                    nome=nome, nota1=nota1, nota2=nota2, nota3=nota3, nota4=nota4, escola=escola))
                flash('Registro inserido com sucesso!')
            session.commit()
        except SQLAlchemyError as e:
            flash(f"Erro ao Atualizar/Inserir Registro: {str(e)}")
            session.rollback()
        finally:
            session.close()

        return redirect(url_for('index'))

    return render_template('index.html', grupos=grupos, soma_geral=soma_geral, form_dado=form_dado)

@app.route('/edit/<int:id>', methods=['GET'])
def edit(id):
    grupos, soma_geral = obter_dados()
    session = Session()
    try:
        row = session.query(quesitos).filter_by(id=id).one_or_none()
        if row:
            form_dado = {
                'id': row.id,
                'nome': row.nome,
                'nota1': row.nota1,
                'nota2': row.nota2,
                'nota3': row.nota3,
                'nota4': row.nota4,
                'escola': row.escola
            }
            return render_template('index.html', grupos=grupos, soma_geral=soma_geral, form_dado=form_dado)
        else:
            flash('Registro não encontrado!')
            return redirect(url_for('index'))
    except SQLAlchemyError as e:
        flash(f"Erro ao Buscar Registro: {str(e)}")
        return redirect(url_for('index'))
    finally:
        session.close()



@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    session = Session()
    try:
        session.execute(quesitos.delete().where(quesitos.c.id == id))
        session.commit()
        flash('Registro excluído com sucesso!')
    except SQLAlchemyError as e:
        flash(f"Erro ao Excluir Registro: {str(e)}")
        session.rollback()
    finally:
        session.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
