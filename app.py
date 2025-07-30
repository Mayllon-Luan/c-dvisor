from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import math
import time
import threading
import json
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Permitir CORS para todas as rotas

# Conteúdo HTML, CSS e JavaScript como strings
HTML_CONTENT = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fatoração Distribuída NPP</title>
    <style>{css_content}</style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Fatoração Distribuída do Número NPP</h1>
            <p>Sistema distribuído para encontrar divisores de números grandes</p>
        </header>

        <main>
            <section class="status-section">
                <h2>Status Atual</h2>
                <div class="status-grid">
                    <div class="status-item">
                        <h3>Maior Primo Testado</h3>
                        <p id="largest-prime">{{ largest_prime }}</p>
                    </div>
                    <div class="status-item">
                        <h3>Dispositivos Ativos</h3>
                        <p id="active-devices">0</p>
                    </div>
                    <div class="status-item">
                        <h3>Divisores Encontrados</h3>
                        <p id="divisors-found">0</p>
                    </div>
                </div>
            </section>

            <section class="work-section">
                <h2>Participar da Fatoração</h2>
                <button id="start-work" class="btn-primary">Iniciar Trabalho</button>
                <button id="stop-work" class="btn-secondary" disabled>Parar Trabalho</button>
                <div id="work-status" class="work-status">
                    <p>Clique em "Iniciar Trabalho" para começar a procurar divisores</p>
                </div>
            </section>

            <section class="progress-section">
                <h2>Progresso</h2>
                <div class="progress-bar">
                    <div id="progress-fill" class="progress-fill"></div>
                </div>
                <p id="progress-text">0% concluído</p>
            </section>

            <section class="results-section">
                <h2>Resultados</h2>
                <div id="results-list" class="results-list">
                    <p>Nenhum divisor encontrado ainda.</p>
                </div>
            </section>
        </main>
    </div>

    <script>{js_content}</script>
</body>
</html>
'''

CSS_CONTENT = '''
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    text-align: center;
    margin-bottom: 40px;
    color: white;
}

header h1 {
    font-size: 2.5rem;
    margin-bottom: 10px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

header p {
    font-size: 1.2rem;
    opacity: 0.9;
}

main {
    background: white;
    border-radius: 15px;
    padding: 30px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

section {
    margin-bottom: 30px;
}

h2 {
    color: #4a5568;
    margin-bottom: 20px;
    font-size: 1.5rem;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 10px;
}

.status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}

.status-item {
    background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    border: 1px solid #e2e8f0;
}

.status-item h3 {
    color: #2d3748;
    margin-bottom: 10px;
    font-size: 1rem;
}

.status-item p {
    font-size: 1.5rem;
    font-weight: bold;
    color: #667eea;
}

.work-section {
    text-align: center;
}

.btn-primary, .btn-secondary {
    padding: 12px 30px;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: bold;
    cursor: pointer;
    margin: 0 10px;
    transition: all 0.3s ease;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn-primary:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
    background: #e2e8f0;
    color: #4a5568;
}

.btn-secondary:hover:not(:disabled) {
    background: #cbd5e0;
}

.btn-primary:disabled, .btn-secondary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.work-status {
    margin-top: 20px;
    padding: 15px;
    background: #f7fafc;
    border-radius: 8px;
    border-left: 4px solid #667eea;
}

.progress-section {
    text-align: center;
}

.progress-bar {
    width: 100%;
    height: 20px;
    background: #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 10px;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    width: 0%;
    transition: width 0.3s ease;
}

#progress-text {
    color: #4a5568;
    font-weight: bold;
}

.results-list {
    background: #f7fafc;
    border-radius: 8px;
    padding: 20px;
    min-height: 100px;
    border: 1px solid #e2e8f0;
}

.result-item {
    background: white;
    padding: 10px;
    margin-bottom: 10px;
    border-radius: 5px;
    border-left: 4px solid #48bb78;
}

.result-item:last-child {
    margin-bottom: 0;
}

@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
    
    header h1 {
        font-size: 2rem;
    }
    
    main {
        padding: 20px;
    }
    
    .status-grid {
        grid-template-columns: 1fr;
    }
    
    .btn-primary, .btn-secondary {
        display: block;
        width: 100%;
        margin: 10px 0;
    }
}
'''

JS_CONTENT = '''
class FactorizationWorker {
    constructor() {
        this.isWorking = false;
        this.currentWork = null;
        this.workInterval = null;
        this.statusInterval = null;
        this.workerId = `worker_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        this.currentPrime = 2;
        this.initializeEventListeners();
        this.updateStatus();
    }

    initializeEventListeners() {
        document.getElementById('start-work').addEventListener('click', () => this.startWork());
        document.getElementById('stop-work').addEventListener('click', () => this.stopWork());
    }

    async startWork() {
        if (this.isWorking) return;

        this.isWorking = true;
        document.getElementById('start-work').disabled = true;
        document.getElementById('stop-work').disabled = false;
        
        this.updateWorkStatus('Solicitando trabalho do servidor...');
        
        try {
            await this.getWorkFromServer();
            this.workInterval = setInterval(() => this.processWork(), 100); // Processar mais rapidamente
            this.statusInterval = setInterval(() => this.updateStatus(), 2000); // Atualizar status mais frequentemente
        } catch (error) {
            console.error('Erro ao iniciar trabalho:', error);
            this.updateWorkStatus('Erro ao conectar com o servidor');
            this.stopWork();
        }
    }

    stopWork() {
        this.isWorking = false;
        document.getElementById('start-work').disabled = false;
        document.getElementById('stop-work').disabled = true;
        
        if (this.workInterval) {
            clearInterval(this.workInterval);
            this.workInterval = null;
        }
        
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
        
        this.updateWorkStatus('Trabalho parado');
    }

    async getWorkFromServer() {
        const response = await fetch(`/get_work?worker_id=${this.workerId}`);
        if (!response.ok) {
            throw new Error('Falha ao obter trabalho do servidor');
        }
        
        this.currentWork = await response.json();
        this.currentPrime = this.currentWork.start_range;
        this.updateWorkStatus(`Testando primos de ${this.currentWork.start_range} até ${this.currentWork.end_range}`);
    }

    async processWork() {
        if (!this.currentWork || !this.isWorking) return;

        // Processar alguns primos por iteração
        const primesToProcess = 10;
        const divisorsFound = [];
        
        for (let i = 0; i < primesToProcess && this.currentPrime <= this.currentWork.end_range; i++) {
            this.currentPrime = this.getNextPrime(this.currentPrime);
            
            if (this.currentPrime > this.currentWork.end_range) {
                break;
            }
            
            // Simular teste de divisibilidade (para números muito grandes, isso seria feito de forma diferente)
            if (this.testDivisibility(this.currentWork.number_to_factor, this.currentPrime)) {
                divisorsFound.push(this.currentPrime);
                this.addResult(`Divisor encontrado: ${this.currentPrime}`);
            }
            
            this.currentPrime++;
        }
        
        // Atualizar status do trabalho
        this.updateWorkStatus(`Testando primo: ${this.currentPrime} (${((this.currentPrime - this.currentWork.start_range) / this.currentWork.range_size * 100).toFixed(1)}% do intervalo)`);
        
        // Se terminou o intervalo atual, enviar resultados e solicitar novo trabalho
        if (this.currentPrime > this.currentWork.end_range) {
            await this.submitResult({
                worker_id: this.workerId,
                divisors: divisorsFound,
                largest_prime_tested: this.currentPrime - 1,
                range_completed: {
                    start: this.currentWork.start_range,
                    end: this.currentWork.end_range
                }
            });
            
            // Solicitar novo trabalho
            await this.getWorkFromServer();
        }
    }

    getNextPrime(start) {
        // Função otimizada para encontrar o próximo primo
        if (start < 2) return 2;
        if (start === 2) return 3;
        
        // Se é par, começar do próximo ímpar
        if (start % 2 === 0) {
            start++;
        } else {
            start += 2;
        }
        
        while (!this.isPrime(start)) {
            start += 2;
        }
        
        return start;
    }

    isPrime(n) {
        if (n < 2) return false;
        if (n === 2) return true;
        if (n % 2 === 0) return false;
        
        const sqrt = Math.sqrt(n);
        for (let i = 3; i <= sqrt; i += 2) {
            if (n % i === 0) return false;
        }
        return true;
    }

    testDivisibility(numberStr, divisor) {
        // Para números muito grandes, esta é uma implementação simplificada
        // Em uma implementação real, seria necessário usar bibliotecas especializadas
        // Por enquanto, simular que raramente encontra divisores (apenas para demonstração)
        
        // Simular alguns divisores pequenos conhecidos para demonstração
        if (divisor === 2 || divisor === 3 || divisor === 5 || divisor === 7) {
            return Math.random() < 0.001; // 0.1% de chance para primos pequenos
        }
        
        return Math.random() < 0.00001; // 0.001% de chance para outros primos
    }

    async submitResult(result) {
        try {
            const response = await fetch('/submit_result', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(result)
            });
            
            if (!response.ok) {
                throw new Error('Falha ao enviar resultado');
            }
            
            const responseData = await response.json();
            console.log('Resultado enviado com sucesso:', responseData);
        } catch (error) {
            console.error('Erro ao enviar resultado:', error);
        }
    }

    updateWorkStatus(message) {
        document.getElementById('work-status').innerHTML = `<p>${message}</p>`;
    }

    addResult(message) {
        const resultsList = document.getElementById('results-list');
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item';
        resultItem.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong>: ${message}`;
        
        if (resultsList.children.length === 1 && resultsList.children[0].textContent.includes('Nenhum divisor')) {
            resultsList.innerHTML = '';
        }
        
        resultsList.insertBefore(resultItem, resultsList.firstChild);
        
        // Manter apenas os últimos 10 resultados
        while (resultsList.children.length > 10) {
            resultsList.removeChild(resultsList.lastChild);
        }
    }

    async updateStatus() {
        try {
            const response = await fetch('/status');
            if (response.ok) {
                const status = await response.json();
                
                // Atualizar elementos da interface
                document.getElementById('largest-prime').textContent = status.largest_prime_tested.toLocaleString();
                document.getElementById('active-devices').textContent = status.active_workers;
                document.getElementById('divisors-found').textContent = status.divisors_found;
                
                // Atualizar barra de progresso (baseada no maior primo testado)
                const progressFill = document.getElementById('progress-fill');
                const progressText = document.getElementById('progress-text');
                
                // Simular progresso baseado no maior primo testado
                const progress = Math.min((status.largest_prime_tested / 1000000) * 100, 100);
                progressFill.style.width = `${progress}%`;
                progressText.textContent = `${progress.toFixed(4)}% concluído (${status.largest_prime_tested.toLocaleString()} primos testados)`;
                
                // Mostrar divisores recentes
                if (status.recent_divisors && status.recent_divisors.length > 0) {
                    status.recent_divisors.forEach(divisorInfo => {
                        this.addResult(`Divisor ${divisorInfo.divisor} encontrado por ${divisorInfo.found_by}`);
                    });
                }
            }
        } catch (error) {
            console.error('Erro ao atualizar status:', error);
        }
    }
}

// Inicializar o worker quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    new FactorizationWorker();
});
'''

# Variáveis globais para o número a ser fatorado e o maior primo testado
NUMBER_TO_FACTOR = 0
LARGEST_PRIME_TESTED = 2
WORK_RANGES = {}  # Dicionário para rastrear intervalos de trabalho distribuídos
ACTIVE_WORKERS = {}  # Dicionário para rastrear workers ativos
DIVISORS_FOUND = []  # Lista de divisores encontrados
LAST_UPDATE_TIME = datetime.now()

# Caminhos dos arquivos (ajustados para o novo layout)
NPP_FILE = os.path.join(os.path.dirname(__file__), 'NPP.txt') # Assumindo que NPP.txt estará na mesma pasta
LARGEST_PRIME_FILE = os.path.join(os.path.dirname(__file__), 'largest_prime.txt')
DIVISORS_FILE = os.path.join(os.path.dirname(__file__), 'divisors_found.txt')

def load_number_from_npp():
    global NUMBER_TO_FACTOR
    try:
        with open(NPP_FILE, 'r') as f:
            sample = f.read(1000)
            if sample.isdigit():
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
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True

def get_next_prime(start):
    if start < 2:
        return 2
    if start == 2:
        return 3
    
    if start % 2 == 0:
        start += 1
    else:
        start += 2
    
    while not is_prime(start):
        start += 2
    
    return start

def get_work_range(worker_id, range_size=10000):
    global LARGEST_PRIME_TESTED, WORK_RANGES
    
    start_range = LARGEST_PRIME_TESTED
    
    for existing_start, existing_end in WORK_RANGES.values():
        if start_range < existing_end:
            start_range = existing_end
    
    end_range = start_range + range_size
    
    WORK_RANGES[worker_id] = (start_range, end_range)
    
    return start_range, end_range

def update_largest_prime_periodically():
    global LARGEST_PRIME_TESTED, LAST_UPDATE_TIME
    
    while True:
        time.sleep(7200)  # 2 horas em segundos
        
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
    rendered_html = HTML_CONTENT.format(css_content=CSS_CONTENT, js_content=JS_CONTENT)
    return Response(rendered_html, mimetype='text/html')

@app.route('/get_work', methods=['GET'])
def get_work():
    worker_id = request.args.get('worker_id', f'worker_{int(time.time())}')
    
    ACTIVE_WORKERS[worker_id] = {
        'last_seen': datetime.now(),
        'ip': request.remote_addr
    }
    
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
    data = request.json
    worker_id = data.get('worker_id')
    
    if not worker_id:
        return jsonify({'status': 'error', 'message': 'worker_id é obrigatório'}), 400
    
    if worker_id in ACTIVE_WORKERS:
        ACTIVE_WORKERS[worker_id]['last_seen'] = datetime.now()
    
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
    
    if 'largest_prime_tested' in data:
        global LARGEST_PRIME_TESTED
        new_largest_prime = int(data['largest_prime_tested'])
        if new_largest_prime > LARGEST_PRIME_TESTED:
            LARGEST_PRIME_TESTED = new_largest_prime
            save_largest_prime_tested()
    
    if worker_id in WORK_RANGES:
        del WORK_RANGES[worker_id]
    
    return jsonify({'status': 'success', 'message': 'Resultado processado com sucesso'})

@app.route('/status', methods=['GET'])
def get_status():
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
    return jsonify({
        'divisors': DIVISORS_FOUND,
        'total_count': len(DIVISORS_FOUND)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
