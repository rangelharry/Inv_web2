from flask import Flask, request, jsonify
from typing import Dict, Any
import json

app = Flask(__name__)

class InventarioAPI:
    """API REST para integração com outros sistemas"""
    
    @staticmethod
    def get_insumos() -> Dict[str, Any]:
        """Retorna lista de insumos"""
        try:
            from modules.insumos import InsumosManager
            manager = InsumosManager()
            insumos = manager.get_insumos()
            return {
                'success': True,
                'data': insumos,
                'count': len(insumos)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_equipamentos_eletricos() -> Dict[str, Any]:
        """Retorna lista de equipamentos elétricos"""
        try:
            from modules.equipamentos_eletricos import EquipamentosEletricosManager
            manager = EquipamentosEletricosManager()
            equipamentos = manager.get_equipamentos()
            return {
                'success': True,
                'data': equipamentos,
                'count': len(equipamentos)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Endpoints da API
@app.route('/api/insumos', methods=['GET'])
def api_get_insumos():
    """GET /api/insumos - Lista todos os insumos"""
    resultado = InventarioAPI.get_insumos()
    return jsonify(resultado)

@app.route('/api/equipamentos/eletricos', methods=['GET'])
def api_get_equipamentos_eletricos():
    """GET /api/equipamentos/eletricos - Lista equipamentos elétricos"""
    resultado = InventarioAPI.get_equipamentos_eletricos()
    return jsonify(resultado)

@app.route('/api/health', methods=['GET'])
def api_health():
    """GET /api/health - Health check da API"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': '2025-11-08'
    })

@app.route('/api/webhook/movimentacao', methods=['POST'])
def api_webhook_movimentacao():
    """POST /api/webhook/movimentacao - Webhook para eventos de movimentação"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON inválido'}), 400
        
        # Processar evento de movimentação
        evento = {
            'tipo': data.get('tipo', 'movimentacao'),
            'equipamento_id': data.get('equipamento_id'),
            'usuario': data.get('usuario'),
            'timestamp': data.get('timestamp')
        }
        
        # Aqui você pode adicionar lógica para processar o evento
        # Ex: salvar no banco, enviar notificações, etc.
        
        return jsonify({
            'success': True,
            'message': 'Evento processado com sucesso',
            'evento': evento
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)