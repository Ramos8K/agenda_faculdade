from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
app.secret_key = "agendafacil-secret-key"
DB_PATH = Path(__file__).with_name("agendafacil.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefone TEXT NOT NULL,
        email TEXT
    );

    CREATE TABLE IF NOT EXISTS profissionais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        especialidade TEXT
    );

    CREATE TABLE IF NOT EXISTS servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        valor REAL NOT NULL,
        duracao INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        profissional_id INTEGER NOT NULL,
        servico_id INTEGER NOT NULL,
        data TEXT NOT NULL,
        horario TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Agendado',
        FOREIGN KEY (cliente_id) REFERENCES clientes(id),
        FOREIGN KEY (profissional_id) REFERENCES profissionais(id),
        FOREIGN KEY (servico_id) REFERENCES servicos(id)
    );
    """)
    conn.commit()
    conn.close()

@app.route("/")
def dashboard():
    conn = get_db()
    totais = {
        "clientes": conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0],
        "profissionais": conn.execute("SELECT COUNT(*) FROM profissionais").fetchone()[0],
        "servicos": conn.execute("SELECT COUNT(*) FROM servicos").fetchone()[0],
        "agendamentos": conn.execute("SELECT COUNT(*) FROM agendamentos").fetchone()[0],
    }
    proximos = conn.execute("""
        SELECT a.*, c.nome AS cliente, p.nome AS profissional, s.nome AS servico
        FROM agendamentos a
        JOIN clientes c ON c.id = a.cliente_id
        JOIN profissionais p ON p.id = a.profissional_id
        JOIN servicos s ON s.id = a.servico_id
        ORDER BY a.data, a.horario
        LIMIT 8
    """).fetchall()
    conn.close()
    return render_template("dashboard.html", totais=totais, proximos=proximos)

@app.route("/clientes")
def clientes():
    conn = get_db()
    dados = conn.execute("SELECT * FROM clientes ORDER BY nome").fetchall()
    conn.close()
    return render_template("clientes.html", clientes=dados)

@app.route("/clientes/novo", methods=["POST"])
def novo_cliente():
    nome = request.form["nome"].strip()
    telefone = request.form["telefone"].strip()
    email = request.form.get("email", "").strip()
    if not nome or not telefone:
        flash("Nome e telefone são obrigatórios.", "erro")
        return redirect(url_for("clientes"))
    conn = get_db()
    conn.execute("INSERT INTO clientes (nome, telefone, email) VALUES (?, ?, ?)", (nome, telefone, email))
    conn.commit()
    conn.close()
    flash("Cliente cadastrado com sucesso.", "ok")
    return redirect(url_for("clientes"))

@app.route("/clientes/<int:id>/excluir", methods=["POST"])
def excluir_cliente(id):
    conn = get_db()
    vinculos = conn.execute("SELECT COUNT(*) FROM agendamentos WHERE cliente_id = ?", (id,)).fetchone()[0]
    if vinculos:
        conn.close()
        flash("Não é possível excluir: há agendamentos vinculados.", "erro")
        return redirect(url_for("clientes"))
    conn.execute("DELETE FROM clientes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Cliente excluído.", "ok")
    return redirect(url_for("clientes"))

@app.route("/profissionais")
def profissionais():
    conn = get_db()
    dados = conn.execute("SELECT * FROM profissionais ORDER BY nome").fetchall()
    conn.close()
    return render_template("profissionais.html", profissionais=dados)

@app.route("/profissionais/novo", methods=["POST"])
def novo_profissional():
    nome = request.form["nome"].strip()
    especialidade = request.form.get("especialidade", "").strip()
    if not nome:
        flash("Nome é obrigatório.", "erro")
        return redirect(url_for("profissionais"))
    conn = get_db()
    conn.execute("INSERT INTO profissionais (nome, especialidade) VALUES (?, ?)", (nome, especialidade))
    conn.commit()
    conn.close()
    flash("Profissional cadastrado com sucesso.", "ok")
    return redirect(url_for("profissionais"))

@app.route("/servicos")
def servicos():
    conn = get_db()
    dados = conn.execute("SELECT * FROM servicos ORDER BY nome").fetchall()
    conn.close()
    return render_template("servicos.html", servicos=dados)

@app.route("/servicos/novo", methods=["POST"])
def novo_servico():
    nome = request.form["nome"].strip()
    valor = request.form["valor"]
    duracao = request.form["duracao"]
    if not nome:
        flash("Nome do serviço é obrigatório.", "erro")
        return redirect(url_for("servicos"))
    conn = get_db()
    conn.execute("INSERT INTO servicos (nome, valor, duracao) VALUES (?, ?, ?)", (nome, valor, duracao))
    conn.commit()
    conn.close()
    flash("Serviço cadastrado com sucesso.", "ok")
    return redirect(url_for("servicos"))

@app.route("/agendamentos")
def agendamentos():
    conn = get_db()
    dados = conn.execute("""
        SELECT a.*, c.nome AS cliente, p.nome AS profissional, s.nome AS servico,
               s.valor AS valor
        FROM agendamentos a
        JOIN clientes c ON c.id = a.cliente_id
        JOIN profissionais p ON p.id = a.profissional_id
        JOIN servicos s ON s.id = a.servico_id
        ORDER BY a.data DESC, a.horario DESC
    """).fetchall()
    clientes = conn.execute("SELECT * FROM clientes ORDER BY nome").fetchall()
    profissionais = conn.execute("SELECT * FROM profissionais ORDER BY nome").fetchall()
    servicos = conn.execute("SELECT * FROM servicos ORDER BY nome").fetchall()
    conn.close()
    return render_template(
        "agendamentos.html",
        agendamentos=dados,
        clientes=clientes,
        profissionais=profissionais,
        servicos=servicos,
    )

@app.route("/agendamentos/novo", methods=["POST"])
def novo_agendamento():
    cliente_id = request.form["cliente_id"]
    profissional_id = request.form["profissional_id"]
    servico_id = request.form["servico_id"]
    data = request.form["data"]
    horario = request.form["horario"]

    try:
        datetime.strptime(data, "%Y-%m-%d")
        datetime.strptime(horario, "%H:%M")
    except ValueError:
        flash("Data ou horário inválido.", "erro")
        return redirect(url_for("agendamentos"))

    conn = get_db()
    conflito = conn.execute("""
        SELECT COUNT(*) FROM agendamentos
        WHERE profissional_id = ? AND data = ? AND horario = ?
          AND status != 'Cancelado'
    """, (profissional_id, data, horario)).fetchone()[0]

    if conflito:
        conn.close()
        flash("Este profissional já possui agendamento nesse horário.", "erro")
        return redirect(url_for("agendamentos"))

    conn.execute("""
        INSERT INTO agendamentos
        (cliente_id, profissional_id, servico_id, data, horario, status)
        VALUES (?, ?, ?, ?, ?, 'Agendado')
    """, (cliente_id, profissional_id, servico_id, data, horario))
    conn.commit()
    conn.close()
    flash("Agendamento criado com sucesso.", "ok")
    return redirect(url_for("agendamentos"))

@app.route("/agendamentos/<int:id>/status", methods=["POST"])
def alterar_status(id):
    status = request.form["status"]
    if status not in {"Agendado", "Realizado", "Cancelado"}:
        flash("Status inválido.", "erro")
        return redirect(url_for("agendamentos"))
    conn = get_db()
    conn.execute("UPDATE agendamentos SET status = ? WHERE id = ?", (status, id))
    conn.commit()
    conn.close()
    flash("Status atualizado.", "ok")
    return redirect(url_for("agendamentos"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
