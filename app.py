from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import math
import time
import threading
import json
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Permitir CORS para todas as rotas

# Variáveis globais para o número a ser fatorado e o maior primo testado
NUMBER_TO_FACTOR = 0
LARGEST_PRIME_TESTED = 2
WORK_RANGES = {}  # Dicionário para rastrear intervalos de trabalho distribuídos
ACTIVE_WORKERS = {}  # Dicionário para rastrear workers ativos
DIVISORS_FOUND = []  # Lista de divisores encontrados
LAST_UPDATE_TIME = datetime.now()

# Caminhos dos arquivos
NPP_FILE = os.path.join(os.path.dirname(__file__), '..', 'upload', 'NPP.txt')
LARGEST_PRIME_FILE = os.path.join(os.path.dirname(__file__), '..', 'largest_prime.txt')
DIVISORS_FILE = os.path.join(os.path.dirname(__file__), '..', 'divisors_found.txt')

def load_number_from_npp():
    global NUMBER_TO_FACTOR
    try:
        # Para números muito grandes, não carregar na memória
        # Apenas verificar se o arquivo existe e obter informações básicas
        with open(NPP_FILE, 'r') as f:
            # Ler apenas os primeiros 1000 caracteres para verificação
            sample = f.read(1000)
            if sample.isdigit():
                # Simular que temos o número (para demonstração)
                NUMBER_TO_FACTOR = "Número NPP com 44+ milhões de dígitos"
                print("Arquivo NPP.txt carregado com sucesso (modo simulação)")
            else:
                print("Erro: Arquivo NPP.txt não contém apenas dígitos")
                NUMBER_TO_FACTOR = 0
    except FileNotFoundError:
        print(f"Erro: Arquivo {NPP_FILE} não encontrado.")
        NUMBER_TO_FACTOR = 0
    except Exception as e:
        print(f"Erro ao carregar NPP.txt: {e}")
        NUMBER_TO_FACTOR = 0

def load_largest_prime_tested():
    global LARGEST_PRIME_TESTED
    try:
        with open(LARGEST_PRIME_FILE, 'r') as f:
            LARGEST_PRIME_TESTED = int(f.read().strip())
    except FileNotFoundError:
        LARGEST_PRIME_TESTED = 2
        save_largest_prime_tested()
    except ValueError:
        print(f"Erro: Conteúdo inválido no arquivo {LARGEST_PRIME_FILE}. Não é um número inteiro.")
        LARGEST_PRIME_TESTED = 2

def save_largest_prime_tested():
    with open(LARGEST_PRIME_FILE, 'w') as f:
        f.write(str(LARGEST_PRIME_TESTED))

def load_divisors():
    global DIVISORS_FOUND
    try:
        with open(DIVISORS_FILE, 'r') as f:
            content = f.read().strip()
            if content:
                DIVISORS_FOUND = json.loads(content)
            else:
                DIVISORS_FOUND = []
    except FileNotFoundError:
        DIVISORS_FOUND = []
    except (ValueError, json.JSONDecodeError):
        print(f"Erro: Conteúdo inválido no arquivo {DIVISORS_FILE}.")
        DIVISORS_FOUND = []

def save_divisors():
    with open(DIVISORS_FILE, 'w') as f:
        json.dump(DIVISORS_FOUND, f)

def is_prime(n):
    """Função otimizada para verificar se um número é primo"""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    # Verificar divisibilidade apenas por números ímpares até sqrt(n)
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True

def get_next_prime(start):
    """Encontra o próximo número primo a partir de start"""
    if start < 2:
        return 2
    if start == 2:
        return 3
    
    # Se start é par, começar do próximo ímpar
    if start % 2 == 0:
        start += 1
    else:
        start += 2
    
    while not is_prime(start):
        start += 2
    
    return start

def get_work_range(worker_id, range_size=10000):
    """Distribui um intervalo de trabalho para um worker"""
    global LARGEST_PRIME_TESTED, WORK_RANGES
    
    # Encontrar o próximo intervalo disponível
    start_range = LARGEST_PRIME_TESTED
    
    # Verificar se já existe um intervalo sendo trabalhado
    for existing_start, existing_end in WORK_RANGES.values():
        if start_range < existing_end:
            start_range = existing_end
    
    end_range = start_range + range_size
    
    # Registrar o intervalo para este worker
    WORK_RANGES[worker_id] = (start_range, end_range)
    
    return start_range, end_range

def update_largest_prime_periodically():
    """Atualiza o maior primo testado a cada 2 horas"""
    global LARGEST_PRIME_TESTED, LAST_UPDATE_TIME
    
    while True:
        time.sleep(7200)  # 2 horas em segundos
        
        # Encontrar o maior primo testado entre todos os workers
        max_tested = LARGEST_PRIME_TESTED
        for start, end in WORK_RANGES.values():
            if start > max_tested:
                max_tested = start
        
        if max_tested > LARGEST_PRIME_TESTED:
            LARGEST_PRIME_TESTED = max_tested
            save_largest_prime_tested()
            LAST_UPDATE_TIME = datetime.now()
            print(f"Maior primo testado atualizado para: {LARGEST_PRIME_TESTED}")

# Carregar dados ao iniciar a aplicação
load_number_from_npp()
load_largest_prime_tested()
load_divisors()

# Iniciar thread para atualização periódica
update_thread = threading.Thread(target=update_largest_prime_periodically, daemon=True)
update_thread.start()

@app.route('/')
def index():
    return render_template('index.html', 
                         largest_prime=LARGEST_PRIME_TESTED,
                         active_workers=len(ACTIVE_WORKERS),
                         divisors_found=len(DIVISORS_FOUND))

@app.route('/get_work', methods=['GET'])
def get_work():
    """Distribui trabalho para um cliente"""
    worker_id = request.args.get('worker_id', f'worker_{int(time.time())}')
    
    # Registrar worker como ativo
    ACTIVE_WORKERS[worker_id] = {
        'last_seen': datetime.now(),
        'ip': request.remote_addr
    }
    
    # Obter intervalo de trabalho
    start_range, end_range = get_work_range(worker_id)
    
    return jsonify({
        'worker_id': worker_id,
        'number_to_factor': 'Número NPP com 44+ milhões de dígitos (modo simulação)',
        'start_range': start_range,
        'end_range': end_range,
        'range_size': end_range - start_range
    })

@app.route('/submit_result', methods=['POST'])
def submit_result():
    """Recebe resultados dos clientes"""
    data = request.json
    worker_id = data.get('worker_id')
    
    if not worker_id:
        return jsonify({'status': 'error', 'message': 'worker_id é obrigatório'}), 400
    
    # Atualizar último contato do worker
    if worker_id in ACTIVE_WORKERS:
        ACTIVE_WORKERS[worker_id]['last_seen'] = datetime.now()
    
    # Processar divisores encontrados
    if 'divisors' in data and data['divisors']:
        for divisor in data['divisors']:
            divisor_info = {
                'divisor': divisor,
                'found_by': worker_id,
                'timestamp': datetime.now().isoformat(),
                'ip': request.remote_addr
            }
            DIVISORS_FOUND.append(divisor_info)
        
        save_divisors()
        print(f"Divisores encontrados por {worker_id}: {data['divisors']}")
    
    # Atualizar maior primo testado
    if 'largest_prime_tested' in data:
        global LARGEST_PRIME_TESTED
        new_largest_prime = int(data['largest_prime_tested'])
        if new_largest_prime > LARGEST_PRIME_TESTED:
            LARGEST_PRIME_TESTED = new_largest_prime
            save_largest_prime_tested()
    
    # Marcar intervalo como concluído
    if worker_id in WORK_RANGES:
        del WORK_RANGES[worker_id]
    
    return jsonify({'status': 'success', 'message': 'Resultado processado com sucesso'})

@app.route('/status', methods=['GET'])
def get_status():
    """Retorna o status atual do sistema"""
    # Limpar workers inativos (mais de 5 minutos sem contato)
    current_time = datetime.now()
    inactive_workers = []
    for worker_id, worker_info in ACTIVE_WORKERS.items():
        if current_time - worker_info['last_seen'] > timedelta(minutes=5):
            inactive_workers.append(worker_id)
    
    for worker_id in inactive_workers:
        del ACTIVE_WORKERS[worker_id]
        if worker_id in WORK_RANGES:
            del WORK_RANGES[worker_id]
    
    return jsonify({
        'largest_prime_tested': LARGEST_PRIME_TESTED,
        'active_workers': len(ACTIVE_WORKERS),
        'divisors_found': len(DIVISORS_FOUND),
        'last_update': LAST_UPDATE_TIME.isoformat(),
        'work_ranges_active': len(WORK_RANGES),
        'recent_divisors': DIVISORS_FOUND[-5:] if DIVISORS_FOUND else []
    })

@app.route('/divisors', methods=['GET'])
def get_divisors():
    """Retorna todos os divisores encontrados"""
    return jsonify({
        'divisors': DIVISORS_FOUND,
        'total_count': len(DIVISORS_FOUND)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
