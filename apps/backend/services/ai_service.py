"""
Servicio de IA para integración con OpenAI
"""

import openai
import json
import asyncio
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI

from core.config import settings
from core.redis import RedisCache

class AIService:
    """Servicio para operaciones de IA"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def process_chat_message(
        self, 
        message: str, 
        user_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Procesar mensaje de chat con IA"""
        
        try:
            # Obtener contexto de la conversación
            conversation_context = await self._get_conversation_context(user_id, session_id)
            
            # Construir prompt
            system_prompt = self._build_system_prompt()
            messages = [
                {"role": "system", "content": system_prompt},
                *conversation_context,
                {"role": "user", "content": message}
            ]
            
            # Llamar a OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                functions=[
                    {
                        "name": "search_procedures",
                        "description": "Buscar procedimientos relacionados con la consulta del usuario",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Términos de búsqueda"},
                                "category": {"type": "string", "description": "Categoría del procedimiento"},
                                "entity": {"type": "string", "description": "Entidad gubernamental"}
                            },
                            "required": ["query"]
                        }
                    }
                ],
                function_call="auto"
            )
            
            # Procesar respuesta
            message_content = response.choices[0].message
            
            result = {
                "response": message_content.content,
                "confidence": 0.8,
                "intent": self._extract_intent(message),
                "processed_query": message.strip()
            }
            
            # Si se llamó a función de búsqueda
            if message_content.function_call:
                function_args = json.loads(message_content.function_call.arguments)
                result["procedures_query"] = function_args.get("query")
                result["category"] = function_args.get("category")
                result["entity"] = function_args.get("entity")
            
            # Guardar en contexto de conversación
            await self._save_conversation_context(user_id, session_id, message, result["response"])
            
            return result
            
        except Exception as e:
            return {
                "response": "Lo siento, ocurrió un error procesando tu consulta. Por favor intenta nuevamente.",
                "confidence": 0.1,
                "error": str(e)
            }
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generar embedding para texto"""
        
        cache_key = f"embedding:{hash(text)}"
        cached = await RedisCache.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        try:
            response = await self.client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
            )
            
            embedding = response.data[0].embedding
            
            # Guardar en cache por 24 horas
            await RedisCache.set(cache_key, json.dumps(embedding), expire=86400)
            
            return embedding
            
        except Exception as e:
            print(f"Error generando embedding: {e}")
            return []
    
    def _build_system_prompt(self) -> str:
        """Construir prompt del sistema"""
        
        return """
        Eres un asistente especializado en trámites gubernamentales de Perú. Tu función es ayudar a los ciudadanos con información sobre procedimientos, requisitos y documentación necesaria.

        Instrucciones:
        1. Responde de manera clara, concisa y útil
        2. Si no tienes información específica, dirígelos a la entidad correspondiente
        3. Siempre pregunta por detalles específicos si la consulta es muy general
        4. Usa un tono amigable y profesional
        5. Si la consulta es sobre procedimientos específicos, usa la función search_procedures
        6. Incluye información sobre costos, tiempos y requisitos cuando sea relevante
        
        Cuando no sepas algo específico, sé honesto y sugiere dónde pueden obtener información oficial.
        """
    
    def _extract_intent(self, message: str) -> str:
        """Extraer intención del mensaje"""
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["cómo", "como", "pasos", "proceso"]):
            return "how_to"
        elif any(word in message_lower for word in ["requisitos", "documentos", "necesito"]):
            return "requirements"
        elif any(word in message_lower for word in ["costo", "precio", "cuanto", "cuánto"]):
            return "cost"
        elif any(word in message_lower for word in ["tiempo", "demora", "cuánto tarda"]):
            return "timing"
        elif any(word in message_lower for word in ["dónde", "donde", "oficina", "dirección"]):
            return "location"
        else:
            return "general_info"
    
    async def _get_conversation_context(
        self, 
        user_id: str, 
        session_id: Optional[str]
    ) -> List[Dict[str, str]]:
        """Obtener contexto de conversación desde Redis"""
        
        if not session_id:
            return []
        
        cache_key = f"chat_session:{user_id}:{session_id}"
        context = await RedisCache.get(cache_key)
        
        if context:
            return json.loads(context)
        
        return []
    
    async def _save_conversation_context(
        self,
        user_id: str,
        session_id: Optional[str],
        user_message: str,
        ai_response: str
    ):
        """Guardar contexto de conversación en Redis"""
        
        if not session_id:
            return
        
        cache_key = f"chat_session:{user_id}:{session_id}"
        
        # Obtener contexto existente
        context = await self._get_conversation_context(user_id, session_id)
        
        # Agregar nuevos mensajes
        context.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": ai_response}
        ])
        
        # Mantener solo los últimos 10 intercambios (20 mensajes)
        if len(context) > 20:
            context = context[-20:]
        
        # Guardar por 1 hora
        await RedisCache.set(cache_key, json.dumps(context), expire=3600)
    
    async def summarize_procedure(self, procedure_data: Dict[str, Any]) -> str:
        """Generar resumen de procedimiento con IA"""
        
        try:
            prompt = f"""
            Genera un resumen claro y conciso del siguiente procedimiento gubernamental:
            
            Nombre: {procedure_data.get('name', 'N/A')}
            Descripción: {procedure_data.get('description', 'N/A')}
            Requisitos: {', '.join(procedure_data.get('requirements', []))}
            Costo: {procedure_data.get('cost', 'N/A')} {procedure_data.get('currency', '')}
            Tiempo de procesamiento: {procedure_data.get('processing_time', 'N/A')}
            
            El resumen debe ser de máximo 150 palabras y enfocarse en la información más importante para el ciudadano.
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Resumen no disponible. Error: {str(e)}"
