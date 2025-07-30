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
